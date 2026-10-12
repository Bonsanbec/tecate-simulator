"""Evaluador de contacto por proximidad e inmunidad para Las Traes y persecuciones."""

from __future__ import annotations

import math


class ProximityContactEvaluator:
    """Valida toques y transferencias por cercanía euclidiana entre participantes."""

    def __init__(self, contact_threshold: float = 1.85, default_immunity_duration: float = 2.0) -> None:
        self.contact_threshold = contact_threshold
        self.default_immunity_duration = default_immunity_duration
        self._immunities: dict[int, float] = {}  # entity_id -> tiempo restante de inmunidad

    def update(self, dt: float) -> None:
        """Actualiza los temporizadores de inmunidad."""
        to_remove = []
        for entity_id, remaining in self._immunities.items():
            new_val = remaining - dt
            if new_val <= 0:
                to_remove.append(entity_id)
            else:
                self._immunities[entity_id] = new_val
        for entity_id in to_remove:
            del self._immunities[entity_id]

    def set_immunity(self, entity_id: int, duration: float | None = None) -> None:
        """Otorga inmunidad temporal contra transferencia de tag."""
        self._immunities[entity_id] = duration if duration is not None else self.default_immunity_duration

    def has_immunity(self, entity_id: int) -> bool:
        """Comprueba si la entidad tiene inmunidad activa."""
        return self._immunities.get(entity_id, 0.0) > 0.0

    def check_contact(
        self,
        source_pos: tuple[float, float, float],
        target_pos: tuple[float, float, float],
        target_entity_id: int,
    ) -> bool:
        """Verifica si source tocó a target_entity_id dentro de la distancia de contacto."""
        if self.has_immunity(target_entity_id):
            return False

        dx = source_pos[0] - target_pos[0]
        dy = source_pos[1] - target_pos[1]
        dz = source_pos[2] - target_pos[2]
        dist_sq = dx * dx + dy * dy + dz * dz
        return dist_sq <= (self.contact_threshold * self.contact_threshold)
