"""Controlador base abstracto para la simulación autoritativa de entidades en TKT/1."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from server.core.entity import DynamicEntity
    from server.core.world import SharedWorld


class EntityController(ABC):
    """Clase base para todos los controladores autoritativos de entidades en el servidor.
    
    Cada subclase implementa la cinemática, toma de decisiones o comportamiento
    específico de un tipo de entidad (vehículos de ruta, vehículos libres, NPCs, objetos).
    """

    def __init__(self, entity: DynamicEntity) -> None:
        self.entity = entity

    @property
    def entity_id(self) -> int:
        return self.entity.entity_id

    @property
    def entity_type(self) -> int:
        return self.entity.entity_type

    @abstractmethod
    def update(self, dt: float, world: SharedWorld) -> None:
        """Avanza la simulación en un delta de tiempo (dt en segundos).
        
        Debe actualizar las propiedades cinemáticas de self.entity (pos, vel, yaw, pitch, flags).
        """
        pass

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        """Maneja un evento de red discreto dirigido a esta entidad (ej. VEHICLE_ENTER, INTERACT).
        
        Retorna True si el evento fue procesado con éxito, False en caso contrario.
        """
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serializa el estado interno del controlador para depuración o persistencia."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "controller_class": self.__class__.__name__,
        }
