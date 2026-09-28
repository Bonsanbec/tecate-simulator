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
