"""Codec binario para empaquetado y desempaquetado de paquetes TKT/1.

Garantiza interoperabilidad exacta con StreamPeerBuffer de Godot 4 en formato Little-Endian.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any

from server.protocol.constants import (
    HEADER_SIZE,
    MAGIC_BYTES,
    PROTOCOL_VERSION,
    ChatChannel,
    EntityType,
    MessageType,
    PacketFlags,
)

HEADER_FORMAT = "<4sBBBBIIIIHH"


def calculate_checksum(data: bytes) -> int:
    """Calcula un checksum aritmético modular simple de 16 bits."""
    return sum(data) & 0xFFFF


@dataclass
class PacketHeader:
    """Encabezado binario común de 28 bytes de TKT/1."""

    magic: bytes = MAGIC_BYTES
    protocol_version: int = PROTOCOL_VERSION
    message_type: int = MessageType.HELLO
    flags: int = PacketFlags.NONE
    reserved: int = 0
    session_id: int = 0
    sequence: int = 0
    ack: int = 0
    timestamp: int = 0
    payload_length: int = 0
    payload_checksum: int = 0

    def pack(self) -> bytes:
        return struct.pack(
            HEADER_FORMAT,
            self.magic,
            self.protocol_version,
            self.message_type,
            self.flags,
            self.reserved,
            self.session_id,
            self.sequence,
            self.ack,
            self.timestamp,
            self.payload_length,
            self.payload_checksum,
        )

    @classmethod
    def unpack(cls, buffer: bytes) -> PacketHeader:
        if len(buffer) < HEADER_SIZE:
            raise ValueError(f"Búfer insuficiente para cabecera TKT/1: {len(buffer)} < {HEADER_SIZE}")

        (
            magic,
            proto_ver,
            msg_type,
            flags,
            reserved,
            session_id,
            seq,
            ack,
            timestamp,
            payload_len,
            checksum,
        ) = struct.unpack(HEADER_FORMAT, buffer[:HEADER_SIZE])

        if magic != MAGIC_BYTES:
            raise ValueError(f"Magic inválido: {magic!r}, esperado {MAGIC_BYTES!r}")

        return cls(
            magic=magic,
            protocol_version=proto_ver,
            message_type=msg_type,
            flags=flags,
            reserved=reserved,
            session_id=session_id,
            sequence=seq,
            ack=ack,
            timestamp=timestamp,
            payload_length=payload_len,
            payload_checksum=checksum,
        )


# =============================================================================
# PAYLOADS DE MENSAJES
# =============================================================================


@dataclass
class HelloPayload:
    """Solicitud de inicio de sesión de cliente."""

    client_version: str = "1.0"
    auth_token: str = ""

    def pack(self) -> bytes:
        v_bytes = self.client_version.encode("utf-8")
        t_bytes = self.auth_token.encode("utf-8")
        return struct.pack(f"<B{len(v_bytes)}sH{len(t_bytes)}s", len(v_bytes), v_bytes, len(t_bytes), t_bytes)

    @classmethod
    def unpack(cls, payload: bytes) -> HelloPayload:
        if len(payload) < 3:
            return cls()
        v_len = payload[0]
        offset = 1 + v_len
        if len(payload) < offset + 2:
            return cls()
        version = payload[1:offset].decode("utf-8", errors="replace")
        (t_len,) = struct.unpack("<H", payload[offset : offset + 2])
        offset += 2
        token = payload[offset : offset + t_len].decode("utf-8", errors="replace")
        return cls(client_version=version, auth_token=token)


@dataclass
class WelcomePayload:
    """Confirmación y datos iniciales de sesión asignada por el servidor."""

    session_id: int = 0
    player_entity_id: int = 0
    server_tick: int = 0
    server_time: int = 0

    def pack(self) -> bytes:
        return struct.pack("<IIII", self.session_id, self.player_entity_id, self.server_tick, self.server_time)

    @classmethod
    def unpack(cls, payload: bytes) -> WelcomePayload:
        if len(payload) < 16:
            raise ValueError("Payload insuficiente para WELCOME (requiere 16 bytes)")
        s_id, p_id, tick, s_time = struct.unpack("<IIII", payload[:16])
        return cls(session_id=s_id, player_entity_id=p_id, server_tick=tick, server_time=s_time)


@dataclass
class InputPayload:
    """Estado y cinemática transmitida por el cliente hacia el servidor."""

    tick: int = 0
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    flags: int = 0
    reserved: int = 0

    def pack(self) -> bytes:
        return struct.pack(
            "<IffffffffBB",
            self.tick,
            self.pos_x,
            self.pos_y,
            self.pos_z,
            self.yaw,
            self.pitch,
            self.vel_x,
            self.vel_y,
            self.vel_z,
            self.flags,
            self.reserved,
        )

    @classmethod
    def unpack(cls, payload: bytes) -> InputPayload:
        if len(payload) < 38:
            raise ValueError(f"Payload insuficiente para INPUT ({len(payload)} < 38 bytes)")
        (
            tick,
            px,
            py,
            pz,
            yaw,
            pitch,
            vx,
            vy,
            vz,
            flags,
            reserved,
        ) = struct.unpack("<IffffffffBB", payload[:38])
        return cls(
            tick=tick,
            pos_x=px,
            pos_y=py,
            pos_z=pz,
            yaw=yaw,
            pitch=pitch,
            vel_x=vx,
            vel_y=vy,
            vel_z=vz,
            flags=flags,
            reserved=reserved,
        )


@dataclass
class EntityStateRecord:
    """Registro individual de entidad dentro de un SNAPSHOT (38 bytes)."""

    entity_id: int = 0
    entity_type: int = EntityType.PLAYER
    flags: int = 0
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0

    def pack(self) -> bytes:
        return struct.pack(
            "<IBBffffffff",
            self.entity_id,
            self.entity_type,
            self.flags,
            self.pos_x,
            self.pos_y,
            self.pos_z,
            self.yaw,
            self.pitch,
            self.vel_x,
            self.vel_y,
            self.vel_z,
        )

    @classmethod
    def unpack_from(cls, payload: bytes, offset: int) -> tuple[EntityStateRecord, int]:
        if len(payload) < offset + 38:
            raise ValueError(f"Búfer insuficiente para EntityStateRecord en offset {offset}")
        (
            e_id,
            e_type,
            flags,
            px,
            py,
            pz,
            yaw,
            pitch,
            vx,
            vy,
            vz,
        ) = struct.unpack_from("<IBBffffffff", payload, offset)
        return (
            cls(
                entity_id=e_id,
                entity_type=e_type,
                flags=flags,
                pos_x=px,
                pos_y=py,
                pos_z=pz,
                yaw=yaw,
                pitch=pitch,
                vel_x=vx,
                vel_y=vy,
                vel_z=vz,
            ),
            offset + 38,
        )


@dataclass
class SnapshotPayload:
    """Estado global o de interés espacial transmitido del servidor a los clientes."""

    server_tick: int = 0
    server_time: int = 0
    entities: list[EntityStateRecord] = field(default_factory=list)

    def pack(self) -> bytes:
        header = struct.pack("<IIH", self.server_tick, self.server_time, len(self.entities))
        chunks = [header]
        for ent in self.entities:
            chunks.append(ent.pack())
        return b"".join(chunks)

    @classmethod
    def unpack(cls, payload: bytes) -> SnapshotPayload:
        if len(payload) < 10:
            raise ValueError("Payload insuficiente para SNAPSHOT (mínimo 10 bytes)")
        tick, s_time, count = struct.unpack("<IIH", payload[:10])
        entities: list[EntityStateRecord] = []
        offset = 10
        for _ in range(count):
            ent, offset = EntityStateRecord.unpack_from(payload, offset)
            entities.append(ent)
        return cls(server_tick=tick, server_time=s_time, entities=entities)


@dataclass
class PingPongPayload:
    """Medición de latencia (RTT) y presencia activa."""

    ping_id: int = 0
    timestamp: int = 0

    def pack(self) -> bytes:
        return struct.pack("<II", self.ping_id, self.timestamp)

    @classmethod
    def unpack(cls, payload: bytes) -> PingPongPayload:
        if len(payload) < 8:
            raise ValueError("Payload insuficiente para PING/PONG (8 bytes requeridos)")
        p_id, ts = struct.unpack("<II", payload[:8])
        return cls(ping_id=p_id, timestamp=ts)


@dataclass
class GoodbyePayload:
    """Cierre explícito de sesión."""

    reason_code: int = 0

    def pack(self) -> bytes:
        return struct.pack("<H", self.reason_code)

    @classmethod
    def unpack(cls, payload: bytes) -> GoodbyePayload:
        if len(payload) < 2:
            return cls(reason_code=0)
        (reason,) = struct.unpack("<H", payload[:2])
        return cls(reason_code=reason)


@dataclass
class ChatPayload:
    """Mensaje textual entre participantes."""

    channel: int = ChatChannel.GLOBAL
    sender_id: int = 0
    message: str = ""

    def pack(self) -> bytes:
        msg_bytes = self.message.encode("utf-8")
        return struct.pack(f"<BIH{len(msg_bytes)}s", self.channel, self.sender_id, len(msg_bytes), msg_bytes)

    @classmethod
    def unpack(cls, payload: bytes) -> ChatPayload:
        if len(payload) < 7:
            return cls()
        channel, sender_id, msg_len = struct.unpack("<BIH", payload[:7])
        msg = payload[7 : 7 + msg_len].decode("utf-8", errors="replace")
        return cls(channel=channel, sender_id=sender_id, message=msg)


@dataclass
class EventPayload:
    """Evento discreto en TKT/1 (ej. VEHICLE_ENTER, VEHICLE_EXIT, PROPERTY_CHANGED)."""

    event_id: int = 0
    event_code: int = 0
    entity_id: int = 0
    timestamp: int = 0
    data: bytes = field(default_factory=bytes)

    def pack(self) -> bytes:
        data_len = len(self.data)
        base = struct.pack("<IHIIH", self.event_id, self.event_code, self.entity_id, self.timestamp, data_len)
        return base + self.data

    @classmethod
    def unpack(cls, payload: bytes) -> EventPayload:
        if len(payload) < 16:
            raise ValueError(f"Payload insuficiente para EVENT ({len(payload)} < 16 bytes)")
        event_id, event_code, entity_id, timestamp, data_len = struct.unpack("<IHIIH", payload[:16])
        data = payload[16 : 16 + data_len]
        return cls(
            event_id=event_id,
            event_code=event_code,
            entity_id=entity_id,
            timestamp=timestamp,
            data=data,
        )

    def unpack_vehicle_enter(self) -> tuple[int, int, int]:
        """Retorna (vehicle_id, seat_index, role) desde data."""
        if len(self.data) < 6:
            raise ValueError(f"Datos insuficientes para VEHICLE_ENTER ({len(self.data)} < 6 bytes)")
        v_id, seat_idx, role = struct.unpack("<IBB", self.data[:6])
        return (v_id, seat_idx, role)

    def unpack_vehicle_exit(self) -> tuple[int, int]:
        """Retorna (vehicle_id, seat_index) desde data."""
        if len(self.data) < 5:
            raise ValueError(f"Datos insuficientes para VEHICLE_EXIT ({len(self.data)} < 5 bytes)")
        v_id, seat_idx = struct.unpack("<IB", self.data[:5])
        return (v_id, seat_idx)

    def unpack_vehicle_refuel(self) -> tuple[int, float]:
        """Retorna (vehicle_id, fuel_amount) desde data."""
        if len(self.data) < 8:
            raise ValueError(f"Datos insuficientes para VEHICLE_REFUEL ({len(self.data)} < 8 bytes)")
        v_id, fuel = struct.unpack("<If", self.data[:8])
        return (v_id, fuel)

    @classmethod
    def create_character_select(cls, entity_id: int, character_id: str, event_id: int = 0, timestamp: int = 0) -> EventPayload:
        """Crea un EventPayload con código CHARACTER_SELECT."""
        from server.protocol.constants import EventCode
        c_bytes = character_id.encode("utf-8")
        data = struct.pack(f"<H{len(c_bytes)}s", len(c_bytes), c_bytes)
        return cls(
            event_id=event_id,
            event_code=EventCode.CHARACTER_SELECT,
            entity_id=entity_id,
            timestamp=timestamp,
            data=data,
        )

    def unpack_character_select(self) -> str:
        """Retorna el character_id desde data."""
        if len(self.data) < 2:
            raise ValueError(f"Datos insuficientes para CHARACTER_SELECT ({len(self.data)} < 2 bytes)")
        str_len = struct.unpack("<H", self.data[:2])[0]
        if len(self.data) < 2 + str_len:
            raise ValueError(f"Longitud de string declarada no coincide: {str_len} > {len(self.data) - 2}")
        return self.data[2 : 2 + str_len].decode("utf-8")

    # --- Métodos de serialización y deserialización para Minijuegos ---

    @classmethod
    def create_minigame_summon(
        cls, entity_id: int, game_id: int, mode: int, max_players: int, arena_id: int, event_id: int = 0, timestamp: int = 0
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = struct.pack("<HBBHI", game_id, mode, max_players, arena_id, 0)
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_SUMMON, entity_id=entity_id, timestamp=timestamp, data=data)

    def unpack_minigame_summon(self) -> dict:
        if len(self.data) < 10:
            raise ValueError(f"Datos insuficientes para MINIGAME_SUMMON ({len(self.data)} < 10 bytes)")
        game_id, mode, max_players, arena_id, reserved = struct.unpack("<HBBHI", self.data[:10])
        return {"game_id": game_id, "mode": mode, "max_players": max_players, "arena_id": arena_id}

    @classmethod
    def create_minigame_join(cls, entity_id: int, game_id: int, accepted: bool, event_id: int = 0, timestamp: int = 0) -> EventPayload:
        from server.protocol.constants import EventCode
        data = struct.pack("<HBB", game_id, 1 if accepted else 0, 0)
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_JOIN, entity_id=entity_id, timestamp=timestamp, data=data)

    def unpack_minigame_join(self) -> dict:
        if len(self.data) < 4:
            raise ValueError(f"Datos insuficientes para MINIGAME_JOIN ({len(self.data)} < 4 bytes)")
        game_id, accepted_val, reserved = struct.unpack("<HBB", self.data[:4])
        return {"game_id": game_id, "accepted": bool(accepted_val)}

    @classmethod
    def create_minigame_start(
        cls, entity_id: int, game_id: int, countdown_seconds: int, participants: list[dict], event_id: int = 0, timestamp: int = 0
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = bytearray(struct.pack("<HBB", game_id, countdown_seconds, len(participants)))
        for p in participants:
            data.extend(
                struct.pack(
                    "<Iffff",
                    p["entity_id"],
                    float(p.get("spawn_x", 0.0)),
                    float(p.get("spawn_y", 0.0)),
                    float(p.get("spawn_z", 0.0)),
                    float(p.get("spawn_yaw", 0.0)),
                )
            )
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_START, entity_id=entity_id, timestamp=timestamp, data=bytes(data))

    def unpack_minigame_start(self) -> dict:
        if len(self.data) < 4:
            raise ValueError(f"Datos insuficientes para MINIGAME_START ({len(self.data)} < 4 bytes)")
        game_id, countdown, count = struct.unpack("<HBB", self.data[:4])
        offset = 4
        participants = []
        for _ in range(count):
            if offset + 20 > len(self.data):
                break
            e_id, sx, sy, sz, syaw = struct.unpack("<Iffff", self.data[offset : offset + 20])
            participants.append({"entity_id": e_id, "spawn_x": sx, "spawn_y": sy, "spawn_z": sz, "spawn_yaw": syaw})
            offset += 20
        return {"game_id": game_id, "countdown_seconds": countdown, "participants": participants}

    @classmethod
    def create_minigame_action(
        cls,
        entity_id: int,
        action_type: int,
        target_entity_id: int,
        param_float: float,
        dir_vec: tuple[float, float, float] = (0.0, 0.0, 0.0),
        event_id: int = 0,
        timestamp: int = 0,
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = struct.pack(
            "<BIffff",
            action_type,
            target_entity_id,
            float(param_float),
            float(dir_vec[0]),
            float(dir_vec[1]),
            float(dir_vec[2]),
        )
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_ACTION, entity_id=entity_id, timestamp=timestamp, data=data)

    def unpack_minigame_action(self) -> dict:
        if len(self.data) < 21:
            raise ValueError(f"Datos insuficientes para MINIGAME_ACTION ({len(self.data)} < 21 bytes)")
        act_type, target_id, p_float, dx, dy, dz = struct.unpack("<BIffff", self.data[:21])
        return {
            "action_type": act_type,
            "target_entity_id": target_id,
            "param_float": p_float,
            "dir": (dx, dy, dz),
        }

    @classmethod
    def create_minigame_eliminate(
        cls, entity_id: int, game_id: int, eliminated_entity_id: int, reason: int, event_id: int = 0, timestamp: int = 0
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = struct.pack("<HIBB", game_id, eliminated_entity_id, reason, 0)
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_ELIMINATE, entity_id=entity_id, timestamp=timestamp, data=data)

    def unpack_minigame_eliminate(self) -> dict:
        if len(self.data) < 8:
            raise ValueError(f"Datos insuficientes para MINIGAME_ELIMINATE ({len(self.data)} < 8 bytes)")
        game_id, elim_id, reason, reserved = struct.unpack("<HIBB", self.data[:8])
        return {"game_id": game_id, "eliminated_entity_id": elim_id, "reason": reason}

    @classmethod
    def create_minigame_end(
        cls, entity_id: int, game_id: int, winner_entity_id: int, rankings: list[dict], event_id: int = 0, timestamp: int = 0
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = bytearray(struct.pack("<HIB", game_id, winner_entity_id, len(rankings)))
        for r in rankings:
            data.extend(struct.pack("<IiH", r["entity_id"], int(r.get("score", 0)), int(r.get("coins_rewarded", 0))))
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_END, entity_id=entity_id, timestamp=timestamp, data=bytes(data))

    def unpack_minigame_end(self) -> dict:
        if len(self.data) < 7:
            raise ValueError(f"Datos insuficientes para MINIGAME_END ({len(self.data)} < 7 bytes)")
        game_id, winner_id, count = struct.unpack("<HIB", self.data[:7])
        offset = 7
        rankings = []
        for _ in range(count):
            if offset + 10 > len(self.data):
                break
            e_id, score, coins = struct.unpack("<IiH", self.data[offset : offset + 10])
            rankings.append({"entity_id": e_id, "score": score, "coins_rewarded": coins})
            offset += 10
        return {"game_id": game_id, "winner_entity_id": winner_id, "rankings": rankings}

    @classmethod
    def create_minigame_cancel(
        cls, entity_id: int, game_id: int, reason: int, event_id: int = 0, timestamp: int = 0
    ) -> EventPayload:
        from server.protocol.constants import EventCode
        data = struct.pack("<HBB", game_id, reason, 0)
        return cls(event_id=event_id, event_code=EventCode.MINIGAME_CANCEL, entity_id=entity_id, timestamp=timestamp, data=data)

    def unpack_minigame_cancel(self) -> dict:
        if len(self.data) < 4:
            raise ValueError(f"Datos insuficientes para MINIGAME_CANCEL ({len(self.data)} < 4 bytes)")
        game_id, reason, reserved = struct.unpack("<HBB", self.data[:4])
        return {"game_id": game_id, "reason": reason}


# =============================================================================
# FUNCIONES DE ALTO NIVEL PARA ARMAR / DESARMAR PAQUETES COMPLETOS
# =============================================================================


def encode_packet(header: PacketHeader, payload_bytes: bytes) -> bytes:
    """Ensambla cabecera y payload, computando longitud y checksum automáticamente."""
    header.payload_length = len(payload_bytes)
    header.payload_checksum = calculate_checksum(payload_bytes)
    return header.pack() + payload_bytes


def decode_packet(data: bytes) -> tuple[PacketHeader, bytes]:
    """Valida y extrae la cabecera y el payload verificado de un datagrama UDP."""
    if len(data) < HEADER_SIZE:
        raise ValueError(f"Datagrama menor al tamaño mínimo de cabecera: {len(data)} < {HEADER_SIZE}")

    header = PacketHeader.unpack(data[:HEADER_SIZE])
    payload = data[HEADER_SIZE : HEADER_SIZE + header.payload_length]

    if len(payload) != header.payload_length:
        raise ValueError(f"Longitud de payload no coincide: declarada {header.payload_length}, real {len(payload)}")

    expected_checksum = calculate_checksum(payload)
    if header.payload_checksum != expected_checksum:
        raise ValueError(f"Checksum inválido: recibido {header.payload_checksum}, calculado {expected_checksum}")

    return header, payload
