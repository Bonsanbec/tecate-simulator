"""Submódulo de especificación y codecs del protocolo TKT/1."""

from server.protocol.constants import (
    HEADER_SIZE,
    MAGIC_BYTES,
    PROTOCOL_VERSION,
    ChatChannel,
    EntityType,
    MessageType,
    PacketFlags,
    PlayerFlags,
)

__all__ = [
    "HEADER_SIZE",
    "MAGIC_BYTES",
    "PROTOCOL_VERSION",
    "MessageType",
    "PacketFlags",
    "EntityType",
    "PlayerFlags",
    "ChatChannel",
]
