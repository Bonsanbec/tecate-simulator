"""Constantes del Protocolo Tecate Game Protocol (TKT/1).

Define los códigos numéricos de mensajes, banderas de transporte y tipos de entidad.
"""

from enum import IntEnum

# Identificador Mágico de 4 bytes ("TKT1")
MAGIC_BYTES = b"TKT1"
PROTOCOL_VERSION = 1

# Longitud fija de la cabecera en bytes
HEADER_SIZE = 28


class MessageType(IntEnum):
    """Tipos de mensaje definidos en TKT/1."""

    HELLO = 1
    WELCOME = 2
    INPUT = 3
    SNAPSHOT = 4
    EVENT = 5
    CHAT = 6
    TELEMETRY = 7
    PING = 8
    PONG = 9
    GOODBYE = 10


class PacketFlags(IntEnum):
    """Banderas de cabecera para control de fiabilidad y flujo."""

    NONE = 0x00
    RELIABLE = 0x01
    ACK = 0x02
    RESEND = 0x04
    COMPRESSED = 0x08


class EntityType(IntEnum):
    """Tipos semánticos de entidades dinámicas en el mundo."""

    PLAYER = 1
    VEHICLE = 2
    OBJECT = 3
    NPC = 4
    ITEM = 5


class PlayerFlags(IntEnum):
    """Banderas de estado biomecánico del jugador."""

    NONE = 0x00
    GROUNDED = 0x01
    SPRINTING = 0x02
    FLYING = 0x04
    SLIDING = 0x08


class ChatChannel(IntEnum):
    """Canales de comunicación de texto."""

    GLOBAL = 0
    LOCAL = 1
    PRIVATE = 2
    SYSTEM = 3
