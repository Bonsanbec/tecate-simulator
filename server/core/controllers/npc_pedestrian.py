"""Controlador autoritativo para NPCs y peatones urbanos en Tecate."""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any

from server.core.controller import EntityController
from server.protocol.constants import EntityType, EventCode, PlayerFlags

if TYPE_CHECKING:
    from server.core.entity import DynamicEntity
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class NPCPedestrianController(EntityController):
    """Controlador para peatones, transeúntes y agentes inteligentes no jugadores.
    
    Gestiona patrullaje por banquetas, estados de reposo (IDLE), caminata y
    reacción a interacciones directas con jugadores.
    """

    STATE_IDLE = "IDLE"
    STATE_WALKING = "WALKING"
    STATE_INTERACTING = "INTERACTING"

    def __init__(
        self,
        entity: DynamicEntity,
        patrol_points: list[tuple[float, float, float]],
        walk_speed: float = 1.35,  # ~4.8 km/h ritmo peatonal estándar
        idle_duration: float = 3.0,
        name: str = "Ciudadano de Tecate",
    ) -> None:
        super().__init__(entity)
        self.entity.entity_type = EntityType.NPC
        self.entity.flags |= PlayerFlags.GROUNDED
        self.patrol_points = patrol_points
        self.walk_speed = walk_speed
        self.default_idle_duration = idle_duration

        self.current_state = self.STATE_WALKING if len(patrol_points) > 1 else self.STATE_IDLE
        self.current_target_idx = 0
        self.state_timer: float = 0.0

        self.entity.properties["name"] = name
        self.entity.properties["npc_state"] = self.current_state

        if self.patrol_points and self.entity.pos_x == 0.0 and self.entity.pos_z == 0.0:
            p0 = self.patrol_points[0]
            self.entity.pos_x = p0[0]
            self.entity.pos_y = p0[1]
            self.entity.pos_z = p0[2]

    def update(self, dt: float, world: SharedWorld) -> None:
        if dt <= 0.0:
            return

        if self.current_state == self.STATE_IDLE:
            self.state_timer += dt
            self.entity.vel_x = 0.0
            self.entity.vel_z = 0.0
            if self.state_timer >= self.default_idle_duration and self.patrol_points:
                self.current_state = self.STATE_WALKING
                self.state_timer = 0.0
                self.entity.properties["npc_state"] = self.current_state

        elif self.current_state == self.STATE_WALKING:
            if not self.patrol_points:
                self.current_state = self.STATE_IDLE
                return

            target = self.patrol_points[self.current_target_idx]
            dx = target[0] - self.entity.pos_x
            dy = target[1] - self.entity.pos_y
            dz = target[2] - self.entity.pos_z
            dist_h = math.hypot(dx, dz)

            if dist_h <= 0.8:
                # Llegó al punto de patrullaje
                self.current_state = self.STATE_IDLE
                self.state_timer = 0.0
                self.entity.properties["npc_state"] = self.current_state
                self.current_target_idx = (self.current_target_idx + 1) % len(self.patrol_points)
                return

            # Calcular dirección y Yaw
            yaw_deg = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0
            self.entity.yaw = yaw_deg

            fwd_x = math.sin(math.radians(yaw_deg))
            fwd_z = -math.cos(math.radians(yaw_deg))

            self.entity.vel_x = fwd_x * self.walk_speed
            self.entity.vel_z = fwd_z * self.walk_speed

            self.entity.pos_x += self.entity.vel_x * dt
            self.entity.pos_z += self.entity.vel_z * dt
            self.entity.pos_y += dy * min(1.0, 5.0 * dt)

        elif self.current_state == self.STATE_INTERACTING:
            self.state_timer += dt
            self.entity.vel_x = 0.0
            self.entity.vel_z = 0.0
            # Regresar a IDLE tras 6 segundos de inactividad
            if self.state_timer >= 6.0:
                self.current_state = self.STATE_IDLE
                self.state_timer = 0.0
                self.entity.properties["npc_state"] = self.current_state

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        if event_code == EventCode.ENTITY_INTERACT:
            self.current_state = self.STATE_INTERACTING
            self.state_timer = 0.0
            self.entity.properties["npc_state"] = self.current_state
            logger.info("NPC '%s' (%d) interactuando con jugador %d", self.entity.properties.get("name"), self.entity_id, sender_id)
            return True
        return False
