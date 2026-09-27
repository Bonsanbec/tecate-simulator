"""Modelo de entidad dinámica para el mundo compartido en TKT/1."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from server.protocol.codec import EntityStateRecord
from server.protocol.constants import EntityType, PlayerFlags


@dataclass
class DynamicEntity:
    """Representación en memoria de una entidad dinámica del mundo."""

    entity_id: int
    entity_type: int = EntityType.PLAYER
    pos_x: float = 0.0
    pos_y: float = 0.0
    pos_z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    vel_z: float = 0.0
    flags: int = PlayerFlags.NONE
    last_update_tick: int = 0
    last_update_time: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)

    def get_grid_cell(self, cell_size: float = 150.0) -> tuple[int, int]:
        """Calcula las coordenadas discretas de la cuadrícula espacial (X, Z)."""
        cell_x = math.floor(self.pos_x / cell_size)
        cell_z = math.floor(self.pos_z / cell_size)
        return (cell_x, cell_z)

    def to_record(self) -> EntityStateRecord:
        """Convierte la entidad a un registro binario serializable en SNAPSHOT."""
        return EntityStateRecord(
            entity_id=self.entity_id,
            entity_type=self.entity_type,
            flags=self.flags,
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            pos_z=self.pos_z,
            yaw=self.yaw,
            pitch=self.pitch,
            vel_x=self.vel_x,
            vel_y=self.vel_y,
            vel_z=self.vel_z,
        )
