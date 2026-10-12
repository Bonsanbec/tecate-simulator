"""Modelado de participantes y preservación de estado espacial en minijuegos."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class ParticipantRole(IntEnum):
    """Roles de los participantes en la partida."""

    FFA = 0               # Todos contra todos simétrico
    ASYMMETRIC_LEADER = 1 # Portador del tag en Las Traes, chofer en Cóbrese, instructor en Zumba
    DUELIST = 2           # Competidor en justa 1v1
    SPECTATOR = 3         # Espectador pasivo fuera de la arena


class ParticipantState(IntEnum):
    """Estado de supervivencia y competición del participante."""

    ACTIVE = 0     # Compitiendo activamente
    ELIMINATED = 1 # Fuera de la ronda / eliminado
    WINNER = 2     # Vencedor coronado


@dataclass
class ParticipantSnapshot:
    """Instantánea de posición previa para restauración espacial garantizada."""

    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    yaw: float = 0.0


@dataclass
class Participant:
    """Registro autoritativo de un jugador participante en una sesión de minijuego."""

    entity_id: int
    session_id: int
    player_uuid: str = ""
    display_name: str = ""
    character_id: str = "axel"
    role: ParticipantRole = ParticipantRole.FFA
    state: ParticipantState = ParticipantState.ACTIVE
    snapshot: ParticipantSnapshot = field(default_factory=ParticipantSnapshot)
    score: int = 0
    coins_rewarded: int = 0
    elimination_order: int = 0
    custom_data: dict = field(default_factory=dict)
