"""Delimitación espacial y geometrías de arenas para minijuegos."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class CylinderArena:
    """Arena cilíndrica vertical (ideal para Kiosko de Parque Hidalgo y Fuente)."""

    center_x: float
    center_y: float
    center_z: float
    radius: float
    min_y: float
    max_y: float

    def is_inside(self, x: float, y: float, z: float) -> bool:
        if y < self.min_y or y > self.max_y:
            return False
        dx = x - self.center_x
        dz = z - self.center_z
        return (dx * dx + dz * dz) <= (self.radius * self.radius)

    def horizontal_distance_to_center(self, x: float, z: float) -> float:
        dx = x - self.center_x
        dz = z - self.center_z
        return math.sqrt(dx * dx + dz * dz)


@dataclass
class BoxArena:
    """Arena rectangular ortogonal en 3D (para explanadas y canchas)."""

    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float

    def is_inside(self, x: float, y: float, z: float) -> bool:
        return (
            self.min_x <= x <= self.max_x
            and self.min_y <= y <= self.max_y
            and self.min_z <= z <= self.max_z
        )
