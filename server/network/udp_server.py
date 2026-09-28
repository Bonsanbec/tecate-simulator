"""Servidor UDP asíncrono basado en asyncio.DatagramProtocol para TKT/1."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from server.config import ServerConfig
from server.core.entity import DynamicEntity
from server.core.session import ClientSession
from server.core.session_manager import SessionManager
from server.core.world import SharedWorld
from server.protocol.codec import (
    ChatPayload,
    EventPayload,
    GoodbyePayload,
    HelloPayload,
    InputPayload,
    PacketHeader,
    PingPongPayload,
    SnapshotPayload,
    WelcomePayload,
    decode_packet,
    encode_packet,
)
from server.protocol.constants import ChatChannel, EventCode, MessageType, PacketFlags, PlayerFlags, VehicleFlags


logger = logging.getLogger(__name__)


class TKTServerProtocol(asyncio.DatagramProtocol):
    """Protocolo de datagramas UDP para el servidor TKT/1."""

    def __init__(self, config: ServerConfig, server_controller: TKTGameServer) -> None:
        self.config = config
        self.controller = server_controller
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport  # type: ignore[assignment]
        logger.info(
            "Socket UDP TKT/1 iniciado en %s:%d (Endpoint público: %s)",
            self.config.bind_host,
            self.config.port,
            self.config.public_host,
        )

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        try:
            header, payload = decode_packet(data)
        except Exception as exc:
            logger.debug("Datagrama descartado desde %s:%d: %s", addr[0], addr[1], exc)
            return

        self.controller.handle_packet(header, payload, addr)

    def error_received(self, exc: Exception) -> None:
        logger.error("Error en socket UDP TKT/1: %s", exc)

    def connection_lost(self, exc: Exception | None) -> None:
        logger.info("Socket UDP TKT/1 cerrado: %s", exc)


class TKTGameServer:
    """Controlador principal del servidor de juego TKT/1."""

    def __init__(self, config: ServerConfig | None = None) -> None:
        self.config = config or ServerConfig()
        self.session_manager = SessionManager(max_clients=self.config.max_clients)
        self.world = SharedWorld(
            cell_size=self.config.spatial_cell_size,
            broadcast_radius=self.config.broadcast_radius_cells,
        )
        self.world.spawn_default_vehicles()
        self.protocol: TKTServerProtocol | None = None

        self.transport: asyncio.DatagramTransport | None = None
        self._is_running = False
        self._tick_task: asyncio.Task[None] | None = None
        self.current_tick: int = 0
        self.start_time: float = time.time()
        self._last_purge_time: float = time.time()

    def get_server_time_ms(self) -> int:
        """Devuelve el tiempo transcurrido del servidor en milisegundos."""
        return int((time.time() - self.start_time) * 1000)

    async def start(self) -> None:
        """Inicializa el socket UDP y arranca el bucle de ticks."""
        loop = asyncio.get_running_loop()
        self._is_running = True
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: TKTServerProtocol(self.config, self),
            local_addr=(self.config.bind_host, self.config.port),
        )
        self.transport = transport
        self.protocol = protocol
        self._tick_task = asyncio.create_task(self._simulation_loop())

    async def stop(self) -> None:
        """Detiene el bucle y cierra el socket UDP limpiamente."""
        self._is_running = False
        if self._tick_task:
            self._tick_task.cancel()
            try:
                await self._tick_task
            except asyncio.CancelledError:
                pass
        if self.transport:
            self.transport.close()
        logger.info("Servidor TKT/1 detenido correctamente.")

    def send_to(self, packet_bytes: bytes, addr: tuple[str, int]) -> None:
        """Envía un paquete empaquetado a una dirección remota."""
        if self.transport and not self.transport.is_closing():
            self.transport.sendto(packet_bytes, addr)

    def handle_packet(
        self,
        header: PacketHeader,
        payload_bytes: bytes,
        addr: tuple[str, int],
    ) -> None:
        """Enruta los mensajes entrantes según su tipo."""
        session = self.session_manager.get_by_addr(addr)

        if header.message_type == MessageType.HELLO:
            self._handle_hello(header, payload_bytes, addr)
            return

        # Para todos los demás mensajes se requiere una sesión establecida
        if not session:
            logger.debug(
                "Mensaje %d ignorado de %s:%d: Sesión no encontrada",
                header.message_type,
                addr[0],
                addr[1],
            )
            return

        session.touch()
        session.last_sequence_in = header.sequence

        if header.message_type == MessageType.INPUT:
            self._handle_input(session, payload_bytes)
        elif header.message_type == MessageType.EVENT:
            self._handle_event(session, payload_bytes)
        elif header.message_type == MessageType.PING:
            self._handle_ping(session, payload_bytes)

        elif header.message_type == MessageType.PONG:
            self._handle_pong(session, payload_bytes)
        elif header.message_type == MessageType.CHAT:
            self._handle_chat(session, payload_bytes)
        elif header.message_type == MessageType.GOODBYE:
            self._handle_goodbye(session, payload_bytes)

    def _handle_hello(
        self,
        header: PacketHeader,
        payload_bytes: bytes,
        addr: tuple[str, int],
    ) -> None:
        try:
            hello = HelloPayload.unpack(payload_bytes)
        except Exception:
            hello = HelloPayload()

        session = self.session_manager.create_or_renew_session(
            addr=addr,
            client_version=hello.client_version,
            auth_token=hello.auth_token,
        )

        # Registrar entidad del jugador en el mundo compartido
        entity = DynamicEntity(
            entity_id=session.player_entity_id,
            pos_x=0.0,
            pos_y=400.0,
            pos_z=0.0,
            last_update_tick=self.current_tick,
            last_update_time=time.time(),
        )
        self.world.upsert_entity(entity)

        # Enviar respuesta WELCOME
        welcome = WelcomePayload(
            session_id=session.session_id,
            player_entity_id=session.player_entity_id,
            server_tick=self.current_tick,
            server_time=self.get_server_time_ms(),
        )
        welcome_hdr = PacketHeader(
            message_type=MessageType.WELCOME,
            flags=PacketFlags.RELIABLE,
            session_id=session.session_id,
            sequence=session.next_sequence(),
            timestamp=self.get_server_time_ms(),
        )
        self.send_to(encode_packet(welcome_hdr, welcome.pack()), addr)
        logger.info(
            "WELCOME enviado a %s:%d (SessionID=%d, PlayerID=%d)",
            addr[0],
            addr[1],
            session.session_id,
            session.player_entity_id,
        )

    def _handle_input(self, session: ClientSession, payload_bytes: bytes) -> None:
        try:
            inp = InputPayload.unpack(payload_bytes)
        except Exception as exc:
            logger.debug("Error al desempaquetar INPUT de sesión %d: %s", session.session_id, exc)
            return

        entity = self.world.get_entity(session.player_entity_id)
        if not entity:
            entity = DynamicEntity(entity_id=session.player_entity_id)

        entity.pos_x = inp.pos_x
        entity.pos_y = inp.pos_y
        entity.pos_z = inp.pos_z
        entity.yaw = inp.yaw
        entity.pitch = inp.pitch
        entity.vel_x = inp.vel_x
        entity.vel_y = inp.vel_y
        entity.vel_z = inp.vel_z
        entity.flags = inp.flags
        entity.last_update_tick = inp.tick
        entity.last_update_time = time.time()

        self.world.upsert_entity(entity)

        # Si el jugador está al volante de un vehículo, sincronizar la cinemática del vehículo
        if inp.flags & PlayerFlags.DRIVING_VEHICLE:
            vehicle = self.world.get_vehicle_by_driver(session.player_entity_id)
            if vehicle:
                vehicle.pos_x = inp.pos_x
                vehicle.pos_y = inp.pos_y
                vehicle.pos_z = inp.pos_z
                vehicle.yaw = inp.yaw
                vehicle.pitch = inp.pitch
                vehicle.vel_x = inp.vel_x
                vehicle.vel_y = inp.vel_y
                vehicle.vel_z = inp.vel_z
                vehicle.flags |= VehicleFlags.HAS_DRIVER
                vehicle.last_update_tick = inp.tick
                vehicle.last_update_time = time.time()
                self.world.upsert_entity(vehicle)

    def _handle_event(self, session: ClientSession, payload_bytes: bytes) -> None:
        try:
            event = EventPayload.unpack(payload_bytes)
        except Exception as exc:
            logger.debug("Error al desempaquetar EVENT de sesión %d: %s", session.session_id, exc)
            return

        # El servidor fuerza la autoría de la entidad origen
        event.entity_id = session.player_entity_id

        if event.event_code == EventCode.VEHICLE_ENTER:
            try:
                vehicle_id, seat_idx, role = event.unpack_vehicle_enter()
                vehicle = self.world.get_entity(vehicle_id)
                player_ent = self.world.get_entity(session.player_entity_id)
                if vehicle and vehicle.is_vehicle:
                    if role == 1:  # Rol Conductor
                        vehicle.driver_id = session.player_entity_id
                        vehicle.flags |= VehicleFlags.HAS_DRIVER
                        if player_ent:
                            player_ent.flags |= (PlayerFlags.IN_VEHICLE | PlayerFlags.DRIVING_VEHICLE)
                    else:  # Rol Pasajero
                        if player_ent:
                            player_ent.flags |= PlayerFlags.IN_VEHICLE
                            player_ent.flags &= ~PlayerFlags.DRIVING_VEHICLE
                    logger.info(
                        "[Vehículo] Jugador %d abordó vehículo %d (asiento=%d, conductor=%s)",
                        session.player_entity_id,
                        vehicle_id,
                        seat_idx,
                        role == 1,
                    )
            except Exception as exc:
                logger.warning("Error procesando VEHICLE_ENTER: %s", exc)

        elif event.event_code == EventCode.VEHICLE_EXIT:
            try:
                vehicle_id, seat_idx = event.unpack_vehicle_exit()
                vehicle = self.world.get_entity(vehicle_id)
                if vehicle and vehicle.is_vehicle:
                    if vehicle.driver_id == session.player_entity_id:
                        vehicle.driver_id = None
                        vehicle.flags &= ~VehicleFlags.HAS_DRIVER
                player_ent = self.world.get_entity(session.player_entity_id)
                if player_ent:
                    player_ent.flags &= ~(PlayerFlags.IN_VEHICLE | PlayerFlags.DRIVING_VEHICLE)
                logger.info(
                    "[Vehículo] Jugador %d descendió del vehículo %d (asiento=%d)",
                    session.player_entity_id,
                    vehicle_id,
                    seat_idx,
                )
            except Exception as exc:
                logger.warning("Error procesando VEHICLE_EXIT: %s", exc)

        elif event.event_code == EventCode.VEHICLE_REFUEL:
            try:
                vehicle_id, fuel_amount = event.unpack_vehicle_refuel()
                vehicle = self.world.get_entity(vehicle_id)
                if vehicle and vehicle.is_vehicle:
                    vehicle.fuel = fuel_amount
                    logger.info(
                        "[Vehículo] Vehículo %d reabastecido a %.1fL por jugador %d",
                        vehicle_id,
                        fuel_amount,
                        session.player_entity_id,
                    )
            except Exception as exc:
                logger.warning("Error procesando VEHICLE_REFUEL: %s", exc)

        # Retransmitir evento fiable a todas las demás sesiones conectadas
        event_bytes = event.pack()
        now_ms = self.get_server_time_ms()
        for other_session in self.session_manager:
            if other_session.session_id == session.session_id:
                continue
            hdr = PacketHeader(
                message_type=MessageType.EVENT,
                flags=PacketFlags.RELIABLE,
                session_id=other_session.session_id,
                sequence=other_session.next_sequence(),
                timestamp=now_ms,
            )
            self.send_to(encode_packet(hdr, event_bytes), other_session.addr)

    def _handle_ping(self, session: ClientSession, payload_bytes: bytes) -> None:

        try:
            ping = PingPongPayload.unpack(payload_bytes)
        except Exception:
            return

        pong = PingPongPayload(ping_id=ping.ping_id, timestamp=ping.timestamp)
        pong_hdr = PacketHeader(
            message_type=MessageType.PONG,
            session_id=session.session_id,
            sequence=session.next_sequence(),
            timestamp=self.get_server_time_ms(),
        )
        self.send_to(encode_packet(pong_hdr, pong.pack()), session.addr)

    def _handle_pong(self, session: ClientSession, payload_bytes: bytes) -> None:
        try:
            pong = PingPongPayload.unpack(payload_bytes)
            # Calcular latencia de ida y vuelta (RTT)
            now_ms = self.get_server_time_ms()
            if now_ms >= pong.timestamp:
                session.rtt_ms = float(now_ms - pong.timestamp)
        except Exception:
            pass

    def _handle_chat(self, session: ClientSession, payload_bytes: bytes) -> None:
        try:
            chat = ChatPayload.unpack(payload_bytes)
        except Exception:
            return

        # Sanitizar mensaje (máximo 256 caracteres)
        clean_msg = chat.message.strip()[:256]
        if not clean_msg:
            return

        chat.sender_id = session.player_entity_id
        chat.message = clean_msg
        chat_bytes = chat.pack()

        logger.info("[Chat] Jugador %d: %s", session.player_entity_id, clean_msg)

        # Retransmitir a los clientes conectados
        for other_session in self.session_manager:
            hdr = PacketHeader(
                message_type=MessageType.CHAT,
                flags=PacketFlags.RELIABLE,
                session_id=other_session.session_id,
                sequence=other_session.next_sequence(),
                timestamp=self.get_server_time_ms(),
            )
            self.send_to(encode_packet(hdr, chat_bytes), other_session.addr)

    def _handle_goodbye(self, session: ClientSession, payload_bytes: bytes) -> None:
        v = self.world.get_vehicle_by_driver(session.player_entity_id)
        if v:
            v.driver_id = None
            v.flags &= ~VehicleFlags.HAS_DRIVER
        self.world.remove_entity(session.player_entity_id)
        self.session_manager.remove_session(session.session_id)
        logger.info("Cliente %s:%d finalizó sesión explícitamente (GOODBYE)", session.addr[0], session.addr[1])

    async def _simulation_loop(self) -> None:
        """Bucle principal de ticks a frecuencia fija (TICK_RATE)."""
        interval = 1.0 / max(1, self.config.tick_rate)
        while self._is_running:
            start_tick = time.monotonic()
            self.current_tick += 1
            now_ms = self.get_server_time_ms()

            # Purgar sesiones inactivas cada segundo
            if (time.time() - self._last_purge_time) >= 1.0:
                self._last_purge_time = time.time()
                timed_out = self.session_manager.purge_timed_out(self.config.session_timeout)
                for s in timed_out:
                    v = self.world.get_vehicle_by_driver(s.player_entity_id)
                    if v:
                        v.driver_id = None
                        v.flags &= ~VehicleFlags.HAS_DRIVER
                    self.world.remove_entity(s.player_entity_id)
                    logger.info("Sesión %d expirada por inactividad", s.session_id)


            # Despachar SNAPSHOT a cada sesión conectada
            for session in self.session_manager:
                snapshot = self.world.build_snapshot_for_player(
                    player_entity_id=session.player_entity_id,
                    server_tick=self.current_tick,
                    server_time=now_ms,
                )
                snap_bytes = snapshot.pack()
                hdr = PacketHeader(
                    message_type=MessageType.SNAPSHOT,
                    session_id=session.session_id,
                    sequence=session.next_sequence(),
                    timestamp=now_ms,
                )
                self.send_to(encode_packet(hdr, snap_bytes), session.addr)

            elapsed = time.monotonic() - start_tick
            sleep_time = max(0.0, interval - elapsed)
            await asyncio.sleep(sleep_time)
