"""Módulo de Minijuegos y Competiciones Urbanas para Tecate Simulator.

Provee el motor de orquestación autoritativo, máquinas de estado finitas,
evaluadores de reglas de juego y los minijuegos de la Fase 1:
- Mi Kiosko (All-v-All Knockback / Slapstick / Ring-Out)
- Las Traes (Roña Urbana / Contacto / Anti-Camping)
- Quemados (Balón Prisionero Balístico)
"""

from server.minigames.fsm import MinigameState
from server.minigames.participant import Participant, ParticipantRole, ParticipantState
from server.minigames.base import BaseMinigame
from server.minigames.orchestrator import MinigameOrchestrator

__all__ = [
    "MinigameState",
    "Participant",
    "ParticipantRole",
    "ParticipantState",
    "BaseMinigame",
    "MinigameOrchestrator",
]
