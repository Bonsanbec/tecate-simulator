"""Controlador autoritativo para vehículos libres y conducibles."""

from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING

from server.core.controller import EntityController
from server.protocol.constants import EventCode, VehicleFlags

if TYPE_CHECKING:
    from server.core.entity import DynamicEntity
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class FreeVehicleController(EntityController):
    """Controlador para automóviles urbanos y vehículos conducibles por jugadores.
    
    Gestiona la desaceleración por inercia/fricción cuando no hay chofer activo,
    el consumo de combustible y la asignación de plazas de conductor y pasajeros.
    """

    def __init__(
        self,
        entity: DynamicEntity,
        max_fuel: float = 100.0,
        fuel_consumption_rate: float = 0.05,  # Litros por segundo en ralentí/marcha
        friction_deceleration: float = 4.5,
    ) -> None:
        super().__init__(entity)
        self.max_fuel = max_fuel
        self.fuel_consumption_rate = fuel_consumption_rate
        self.friction_deceleration = friction_deceleration

        if "fuel" not in self.entity.properties:
            self.entity.properties["fuel"] = max_fuel
        if "passengers" not in self.entity.properties:
            self.entity.properties["passengers"] = []

    def update(self, dt: float, world: SharedWorld) -> None:
        """Avanza la inercia o consumo del vehículo cuando no es controlado activamente."""
        if dt <= 0.0:
            return

        has_driver = bool(self.entity.flags & VehicleFlags.HAS_DRIVER) and (self.entity.driver_id is not None)

        if not has_driver:
            # Desaceleración por inercia y fricción sobre el pavimento
            h_speed = (self.entity.vel_x ** 2 + self.entity.vel_z ** 2) ** 0.5
            if h_speed > 0.01:
                new_speed = max(0.0, h_speed - self.friction_deceleration * dt)
                ratio = new_speed / h_speed if h_speed > 0.0 else 0.0
                self.entity.vel_x *= ratio
                self.entity.vel_z *= ratio
                self.entity.pos_x += self.entity.vel_x * dt
                self.entity.pos_z += self.entity.vel_z * dt
                current_speed = new_speed
            else:
                self.entity.vel_x = 0.0
                self.entity.vel_z = 0.0
                current_speed = 0.0

            # Si el motor sigue encendido sin chofer, apagarlo tras detenerse
            if current_speed < 0.05 and (self.entity.flags & VehicleFlags.ENGINE_RUNNING):
                self.entity.flags &= ~VehicleFlags.ENGINE_RUNNING
        else:
            # Si tiene conductor y el motor está encendido, consumir combustible
            if self.entity.flags & VehicleFlags.ENGINE_RUNNING:
                current_fuel = self.entity.fuel
                if current_fuel > 0.0:
                    self.entity.fuel = max(0.0, current_fuel - self.fuel_consumption_rate * dt)
                else:
                    self.entity.flags &= ~VehicleFlags.ENGINE_RUNNING
                    logger.info("Vehículo %d sin combustible.", self.entity_id)

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        if event_code == EventCode.VEHICLE_ENTER:
            if len(data) < 6:
                return False
            v_id, seat_idx, role = struct.unpack("<IBB", data[:6])
            if v_id != self.entity_id:
                return False

            if role == 1 or seat_idx == 0:  # Rol conductor o plaza 0
                if self.entity.driver_id is not None and self.entity.driver_id != sender_id:
                    logger.warning("Puesto de conductor en vehículo %d ya ocupado por %d", self.entity_id, self.entity.driver_id)
                    return False
                self.entity.driver_id = sender_id
                self.entity.flags |= (VehicleFlags.HAS_DRIVER | VehicleFlags.ENGINE_RUNNING)
                logger.info("Jugador %d asumió la conducción de vehículo %d", sender_id, self.entity_id)
            else:
                passengers: list[int] = self.entity.properties.setdefault("passengers", [])
                if sender_id not in passengers:
                    passengers.append(sender_id)
                logger.info("Jugador %d abordó vehículo %d como pasajero", sender_id, self.entity_id)
            return True

        elif event_code == EventCode.VEHICLE_EXIT:
            if len(data) < 5:
                return False
            v_id, seat_idx = struct.unpack("<IB", data[:5])
            if v_id != self.entity_id:
                return False

            if self.entity.driver_id == sender_id:
                self.entity.driver_id = None
                self.entity.flags &= ~VehicleFlags.HAS_DRIVER
                logger.info("Conductor %d abandonó vehículo %d", sender_id, self.entity_id)
            passengers = self.entity.properties.get("passengers", [])
            if sender_id in passengers:
                passengers.remove(sender_id)
                logger.info("Pasajero %d descendió del vehículo %d", sender_id, self.entity_id)
            return True

        elif event_code == EventCode.VEHICLE_REFUEL:
            if len(data) < 8:
                return False
            v_id, fuel_amount = struct.unpack("<If", data[:8])
            if v_id != self.entity_id:
                return False
            self.entity.fuel = min(self.max_fuel, fuel_amount)
            logger.info("Vehículo %d reabastecido a %.1f L", self.entity_id, self.entity.fuel)
            return True

        return False
