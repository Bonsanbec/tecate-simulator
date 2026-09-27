"""Mundo compartido y gestión espacial (Interest Management) para TKT/1."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Iterator

from server.core.entity import DynamicEntity
from server.protocol.codec import EntityStateRecord, SnapshotPayload

logger = logging.getLogger(__name__)


class SharedWorld:
    """Mantiene el estado dinámico compartido y la partición espacial en cuadrícula."""

    def __init__(self, cell_size: float = 150.0, broadcast_radius: int = 1) -> None:
        self.cell_size = cell_size
        self.broadcast_radius = broadcast_radius
        self._entities: dict[int, DynamicEntity] = {}
        # Cuadrícula espacial (cell_x, cell_z) -> set de entity_ids
        self._grid: dict[tuple[int, int], set[int]] = defaultdict(set)
        # Mapeo inverso entity_id -> (cell_x, cell_z)
        self._entity_cells: dict[int, tuple[int, int]] = {}

    def __len__(self) -> int:
        return len(self._entities)

    def __iter__(self) -> Iterator[DynamicEntity]:
        return iter(list(self._entities.values()))

    def get_entity(self, entity_id: int) -> DynamicEntity | None:
        return self._entities.get(entity_id)

    def upsert_entity(self, entity: DynamicEntity) -> None:
        """Inserta o actualiza una entidad y ajusta su registro en la cuadrícula espacial."""
        entity_id = entity.entity_id
        new_cell = entity.get_grid_cell(self.cell_size)

        old_cell = self._entity_cells.get(entity_id)
        if old_cell != new_cell:
            if old_cell is not None:
                self._grid[old_cell].discard(entity_id)
                if not self._grid[old_cell]:
                    del self._grid[old_cell]
            self._grid[new_cell].add(entity_id)
            self._entity_cells[entity_id] = new_cell

        self._entities[entity_id] = entity

    def remove_entity(self, entity_id: int) -> DynamicEntity | None:
        entity = self._entities.pop(entity_id, None)
        if entity:
            cell = self._entity_cells.pop(entity_id, None)
            if cell and cell in self._grid:
                self._grid[cell].discard(entity_id)
                if not self._grid[cell]:
                    del self._grid[cell]
        return entity

    def get_relevant_entities(
        self,
        center_x: float,
        center_z: float,
        exclude_entity_id: int | None = None,
    ) -> list[EntityStateRecord]:
        """Obtiene los registros de entidades ubicadas en las celdas circundantes al jugador."""
        center_cell = (
            int(center_x // self.cell_size),
            int(center_z // self.cell_size),
        )

        relevant_records: list[EntityStateRecord] = []
        r = self.broadcast_radius

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cell = (center_cell[0] + dx, center_cell[1] + dz)
                entity_ids = self._grid.get(cell)
                if not entity_ids:
                    continue
                for eid in entity_ids:
                    if exclude_entity_id is not None and eid == exclude_entity_id:
                        # Excluir la propia entidad local del jugador si se desea eco-filtering
                        continue
                    ent = self._entities.get(eid)
                    if ent is not None:
                        relevant_records.append(ent.to_record())

        return relevant_records

    def build_snapshot_for_player(
        self,
        player_entity_id: int,
        server_tick: int,
        server_time: int,
    ) -> SnapshotPayload:
        """Construye un SNAPSHOT espacialmente optimizado para un jugador conectado."""
        player = self._entities.get(player_entity_id)
        if player is None:
            # Si el jugador aún no tiene posición registrada, enviar todas las entidades
            records = [ent.to_record() for eid, ent in self._entities.items() if eid != player_entity_id]
        else:
            records = self.get_relevant_entities(player.pos_x, player.pos_z, exclude_entity_id=player_entity_id)

        return SnapshotPayload(
            server_tick=server_tick,
            server_time=server_time,
            entities=records,
        )
