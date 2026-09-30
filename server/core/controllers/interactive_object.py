"""Controlador autoritativo para objetos interactivos y elementos urbanos dinámicos."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from server.core.controller import EntityController
from server.protocol.constants import EntityType, EventCode

if TYPE_CHECKING:
    from server.core.entity import DynamicEntity
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class InteractiveObjectController(EntityController):
    """Controlador para infraestructura dinámica (plumas, puertas, bombas, semáforos)."""

    def __init__(
        self,
        entity: DynamicEntity,
        object_type: str = "prop",
        initial_state: str = "DEFAULT",
        toggleable: bool = True,
    ) -> None:
        super().__init__(entity)
        self.entity.entity_type = EntityType.OBJECT
        self.object_type = object_type
        self.toggleable = toggleable
        self.entity.properties["object_type"] = object_type
        self.entity.properties["state"] = initial_state

    def update(self, dt: float, world: SharedWorld) -> None:
        # Objetos estáticos o de lógica temporizada
        pass

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        if event_code == EventCode.ENTITY_INTERACT:
            if self.toggleable:
                curr = self.entity.properties.get("state", "DEFAULT")
                new_state = "OPEN" if curr == "CLOSED" else ("CLOSED" if curr == "OPEN" else "ACTIVATED")
                self.entity.properties["state"] = new_state
                logger.info(
                    "Objeto %s (%d) cambió estado a %s por interacción de jugador %d",
                    self.object_type,
                    self.entity_id,
                    new_state,
                    sender_id,
                )
                return True
        return False
