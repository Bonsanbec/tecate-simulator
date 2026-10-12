"""Evaluador anti-campeo por análisis de desplazamiento cinemático en ventana deslizante."""

from __future__ import annotations

import math
from collections import deque


class ActivityAntiCampingEvaluator:
    """Detecta inmovilidad excesiva calculando el vector de desplazamiento acumulado."""

    def __init__(self, window_seconds: float = 3.5, min_speed_threshold: float = 0.5) -> None:
        self.window_seconds = window_seconds
        self.min_speed_threshold = min_speed_threshold
        # entity_id -> deque de (timestamp, pos_x, pos_z)
        self._history: dict[int, deque[tuple[float, float, float]]] = {}

    def record_position(self, entity_id: int, current_time: float, pos_x: float, pos_z: float) -> None:
        """Registra una muestra de posición y purga las que superan la ventana deslizante."""
        if entity_id not in self._history:
            self._history[entity_id] = deque()

        queue = self._history[entity_id]
        queue.append((current_time, pos_x, pos_z))

        cutoff = current_time - self.window_seconds
        while queue and queue[0][0] < cutoff:
            queue.popleft()

    def is_camping(self, entity_id: int, current_time: float) -> bool:
        """Comprueba si la velocidad promedio en la ventana es inferior al umbral de movilidad."""
        queue = self._history.get(entity_id)
        if not queue or len(queue) < 2:
            return False

        t_start, x_start, z_start = queue[0]
        t_end, x_end, z_end = queue[-1]
        dt = t_end - t_start

        # Requiere al menos el 60% de la ventana cubierta para juzgar
        if dt < (self.window_seconds * 0.6):
            return False

        # Desplazamiento neto horizontal
        dx = x_end - x_start
        dz = z_end - z_start
        displacement = math.sqrt(dx * dx + dz * dz)
        speed = displacement / max(dt, 0.001)

        return speed < self.min_speed_threshold

    def reset_entity(self, entity_id: int) -> None:
        """Limpia el historial de una entidad."""
        self._history.pop(entity_id, None)
