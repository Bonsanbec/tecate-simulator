"""Gestor de simulación autoritativa para el servidor de Tecate Simulator."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterator

from server.core.controller import EntityController

if TYPE_CHECKING:
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class SimulationManager:
    """Administra y orquesta todos los controladores de entidades activas en el servidor."""

    def __init__(self) -> None:
        self._controllers: dict[int, EntityController] = {}

    def __len__(self) -> int:
        return len(self._controllers)

    def __iter__(self) -> Iterator[EntityController]:
        return iter(list(self._controllers.values()))

    def register_controller(self, controller: EntityController) -> None:
        """Registra un controlador de entidad en el gestor."""
        self._controllers[controller.entity_id] = controller

    def unregister_controller(self, entity_id: int) -> EntityController | None:
        """Remueve y retorna el controlador de una entidad."""
        return self._controllers.pop(entity_id, None)

    def get_controller(self, entity_id: int) -> EntityController | None:
        """Obtiene el controlador registrado para la entidad indicada."""
        return self._controllers.get(entity_id)

    def update(self, dt: float, world: SharedWorld) -> None:
        """Ejecuta el paso de simulación en todos los controladores y sincroniza el mundo espacial."""
        for controller in list(self._controllers.values()):
            try:
                controller.update(dt, world)
                # Re-indexar en la cuadrícula espacial del mundo
                world.upsert_entity(controller.entity)
            except Exception as exc:
                logger.error("Error actualizando controlador de entidad %d: %s", controller.entity_id, exc, exc_info=True)

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        target_entity_id: int,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        """Despacha un evento discreto al controlador correspondiente."""
        controller = self._controllers.get(target_entity_id)
        if controller:
            return controller.handle_event(event_code, data, sender_id, world)
        return False
