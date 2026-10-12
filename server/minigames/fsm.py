"""Máquina de Estados Finitos para el Ciclo de Vida de Minijuegos en Tecate Simulator."""

from enum import IntEnum


class MinigameState(IntEnum):
    """Estados del ciclo de vida de una sesión de minijuego."""

    IDLE = 0          # Sin minijuego activo
    SUMMONING = 1     # Convocatoria abierta, esperando quórum y aceptaciones
    STAGING = 2       # Cuenta regresiva en arena, avatares posicionados, controles limitados
    ACTIVE = 3        # Partida en curso, árbitros y evaluadores de reglas a 30 Hz activos
    RESOLUTION = 4    # Partida concluida, cálculo de podio, ranking y recompensas
    RESTORATION = 5   # Reaparición de jugadores en coordenadas exactas previas a la partida
