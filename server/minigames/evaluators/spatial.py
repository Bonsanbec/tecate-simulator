"""Evaluador de límites espaciales (Ring-Out, Caída de Tarima y Desborde de Arena)."""

from __future__ import annotations

from typing import Union
from server.minigames.arena import BoxArena, CylinderArena


class SpatialBoundaryEvaluator:
    """Valida si un participante se mantiene dentro de los confines físicos autorizados."""

    def __init__(self, arena: Union[CylinderArena, BoxArena]) -> None:
        self.arena = arena

    def check_boundary(self, pos_x: float, pos_y: float, pos_z: float) -> tuple[bool, str]:
        """Comprueba si la posición está dentro de la arena.

        Retorna:
            (True, "") si está dentro.
            (False, motivo) si ocurrió ring-out o salida de arena.
        """
        if isinstance(self.arena, CylinderArena):
            if pos_y < self.arena.min_y:
                return (False, "FALL_BELOW_DECK")
            if pos_y > self.arena.max_y:
                return (False, "ALTITUDE_EXCEEDED")
            dist = self.arena.horizontal_distance_to_center(pos_x, pos_z)
            if dist > self.arena.radius:
                return (False, "RADIAL_RING_OUT")
            return (True, "")

        elif isinstance(self.arena, BoxArena):
            if not self.arena.is_inside(pos_x, pos_y, pos_z):
                return (False, "BOX_BOUNDARY_EXIT")
            return (True, "")

        return (True, "")
