"""Controlador autoritativo para vehículos de ruta predefinida (Autobuses, Trenes, etc.)."""

from __future__ import annotations

import json
import logging
import math
import struct
from typing import TYPE_CHECKING, Any

from server.core.controller import EntityController
from server.protocol.constants import EventCode, VehicleFlags

if TYPE_CHECKING:
    from server.core.entity import DynamicEntity
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


def _angle_diff_deg(a: float, b: float) -> float:
    """Calcula la menor diferencia angular entre dos ángulos en grados (a - b)."""
    diff = (a - b + 180.0) % 360.0 - 180.0
    return diff


class RouteVehicleController(EntityController):
    """Controlador que guía a un vehículo por un circuito de waypoints tridimensionales.
    
    Admite paradas programadas obligatorias con tiempos de espera configurables,
    adaptación topográfica en Y, desaceleración en curvas pronunciadas y gestión
    autoritativa de pasajeros.
    """

    def __init__(
        self,
        entity: DynamicEntity,
        waypoints: list[tuple[float, float, float]],
        station_indices: dict[int, dict[str, Any]] | None = None,
        cruise_speed_kmh: float = 36.0,
        waypoint_speeds: list[float] | None = None,
        waypoint_reach_threshold: float = 4.5,
        loop_route: bool = True,
        initial_waypoint_index: int = 0,
        max_passengers: int = 30,
    ) -> None:
        super().__init__(entity)
        self.waypoints = waypoints
        self.station_indices = station_indices or {}
        self.cruise_speed_kmh = cruise_speed_kmh
        self.waypoint_speeds = waypoint_speeds or []
        self.waypoint_reach_threshold = waypoint_reach_threshold
        self.loop_route = loop_route
        self.current_waypoint_index = initial_waypoint_index
        self.max_passengers = max_passengers

        self.is_at_station: bool = False
        self.station_timer: float = 0.0
        self.current_speed: float = 0.0  # en m/s

        # Banderas iniciales del vehículo
        self.entity.flags |= VehicleFlags.ROUTE_VEHICLE | VehicleFlags.ENGINE_RUNNING | VehicleFlags.HEADLIGHTS

        # Inicializar propiedades de pasajeros si no existen
        if "passengers" not in self.entity.properties:
            self.entity.properties["passengers"] = []
        if "vehicle_name" not in self.entity.properties:
            self.entity.properties["vehicle_name"] = f"Unidad {self.entity.entity_id}"

        # Posicionar inicialmente en el waypoint y orientar hacia el siguiente punto
        if self.waypoints and 0 <= self.current_waypoint_index < len(self.waypoints):
            wp = self.waypoints[self.current_waypoint_index]
            self.entity.pos_x = wp[0]
            self.entity.pos_y = wp[1]
            self.entity.pos_z = wp[2]
            next_idx = (self.current_waypoint_index + 1) % len(self.waypoints)
            next_wp = self.waypoints[next_idx]
            dx = next_wp[0] - wp[0]
            dz = next_wp[2] - wp[2]
            if dx != 0.0 or dz != 0.0:
                self.entity.yaw = (math.degrees(math.atan2(dx, -dz)) + 360.0) % 360.0

    @classmethod
    def from_route_json(
        cls,
        entity: DynamicEntity,
        route_json_path: str,
        initial_waypoint_index: int = 0,
        cruise_speed_kmh: float = 36.0,
        max_passengers: int = 30,
    ) -> RouteVehicleController:
        """Instancia un controlador cargando waypoints, velocidades y estaciones desde un archivo JSON."""
        with open(route_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_waypoints = data.get("waypoints", [])
        waypoints = [(float(pt[0]), float(pt[1]), float(pt[2])) for pt in raw_waypoints]

        raw_speeds = data.get("waypoint_speeds", [])
        waypoint_speeds = [float(s) for s in raw_speeds] if raw_speeds else None

        raw_stations = data.get("station_indices") or data.get("stations") or {}
        station_indices: dict[int, dict[str, Any]] = {}
        for k, v in raw_stations.items():
            idx = int(k)
            if isinstance(v, str):
                station_indices[idx] = {"name": v, "dwell_time": 8.0}
            elif isinstance(v, dict):
                station_indices[idx] = {
                    "name": v.get("name", f"Estación {idx}"),
                    "dwell_time": float(v.get("dwell_time", 8.0)),
                }

        return cls(
            entity=entity,
            waypoints=waypoints,
            station_indices=station_indices,
            cruise_speed_kmh=cruise_speed_kmh,
            waypoint_speeds=waypoint_speeds,
            initial_waypoint_index=initial_waypoint_index,
            max_passengers=max_passengers,
        )

    def update(self, dt: float, world: SharedWorld) -> None:
        """Avanza la cinemática del vehículo en cada tick del servidor."""
        if not self.waypoints or dt <= 0.0:
            return

        # 1. Comportamiento en parada de estación
        if self.is_at_station:
            self.station_timer += dt
            st_info = self.station_indices.get(self.current_waypoint_index, {"dwell_time": 8.0, "name": "Parada"})
            dwell_time = float(st_info.get("dwell_time", 8.0))

            # Desacelerar hasta detenerse
            self.current_speed = max(0.0, self.current_speed - 12.0 * dt)
            self.entity.vel_x = 0.0
            self.entity.vel_y = 0.0
            self.entity.vel_z = 0.0

            if self.station_timer >= dwell_time:
                self.is_at_station = False
                st_name = st_info.get("name", "Estación")
                logger.info(
                    "[%s] Reanuda marcha desde parada: %s (WP %d)",
                    self.entity.properties.get("vehicle_name"),
                    st_name,
                    self.current_waypoint_index,
                )
                self._advance_waypoint()
            return

        # 2. Navegación hacia el waypoint objetivo
        target_pt = self.waypoints[self.current_waypoint_index]
        dx = target_pt[0] - self.entity.pos_x
        dy = target_pt[1] - self.entity.pos_y
        dz = target_pt[2] - self.entity.pos_z
        dist_h = math.hypot(dx, dz)

        # Comprobar si se alcanzó el waypoint actual
        if dist_h <= self.waypoint_reach_threshold:
            if self.current_waypoint_index in self.station_indices:
                self.is_at_station = True
                self.station_timer = 0.0
                self.current_speed = 0.0
                self.entity.vel_x = 0.0
                self.entity.vel_y = 0.0
                self.entity.vel_z = 0.0
                st_info = self.station_indices[self.current_waypoint_index]
                logger.info(
                    "[%s] Llegó a parada oficial: %s (Espera: %.1f s)",
                    self.entity.properties.get("vehicle_name"),
                    st_info.get("name"),
                    float(st_info.get("dwell_time", 8.0)),
                )
                return
            else:
                self._advance_waypoint()
                target_pt = self.waypoints[self.current_waypoint_index]
                dx = target_pt[0] - self.entity.pos_x
                dy = target_pt[1] - self.entity.pos_y
                dz = target_pt[2] - self.entity.pos_z
                dist_h = math.hypot(dx, dz)

        if dist_h < 0.001:
            return

        # 3. Orientación hacia el objetivo (Yaw)
        # En Godot y nuestro estándar: +X = Derecha, -Z = Adelante
        desired_yaw = math.degrees(math.atan2(dx, -dz))
        yaw_diff = _angle_diff_deg(desired_yaw, self.entity.yaw)
        max_turn_rate = 65.0 * dt  # Grados por segundo
        if abs(yaw_diff) <= max_turn_rate:
            self.entity.yaw = desired_yaw
        else:
            self.entity.yaw += math.copysign(max_turn_rate, yaw_diff)
        self.entity.yaw = (self.entity.yaw + 360.0) % 360.0

        # Inclinación longitudinal (Pitch)
        desired_pitch = math.degrees(math.atan2(dy, dist_h))
        self.entity.pitch += _angle_diff_deg(desired_pitch, self.entity.pitch) * min(1.0, 5.0 * dt)

        # 4. Cálculo de velocidad y aceleración
        speed_kmh = (
            self.waypoint_speeds[self.current_waypoint_index]
            if self.waypoint_speeds and self.current_waypoint_index < len(self.waypoint_speeds)
            else self.cruise_speed_kmh
        )
        target_cruise_speed = speed_kmh / 3.6
        # Reducir velocidad si el ángulo hacia el objetivo es pronunciado
        turn_factor = max(0.35, math.cos(math.radians(yaw_diff)))
        effective_target_speed = target_cruise_speed * turn_factor

        # Desaceleración suave ante proximidad a una parada
        if self.current_waypoint_index in self.station_indices and dist_h < 18.0:
            effective_target_speed = min(effective_target_speed, max(2.0, dist_h * 0.4))

        if self.current_speed < effective_target_speed:
            self.current_speed = min(effective_target_speed, self.current_speed + 3.5 * dt)
        else:
            self.current_speed = max(effective_target_speed, self.current_speed - 8.0 * dt)

        # 5. Aplicar desplazamiento vectorial
        yaw_rad = math.radians(self.entity.yaw)
        fwd_x = math.sin(yaw_rad)
        fwd_z = -math.cos(yaw_rad)

        self.entity.vel_x = fwd_x * self.current_speed
        self.entity.vel_z = fwd_z * self.current_speed

        self.entity.pos_x += self.entity.vel_x * dt
        self.entity.pos_z += self.entity.vel_z * dt

        # Adaptación suave en altitud Y hacia la topografía del waypoint
        y_step = dy * min(1.0, 6.0 * dt)
        self.entity.pos_y += y_step
        self.entity.vel_y = y_step / max(0.0001, dt)

    def _advance_waypoint(self) -> None:
        """Avanza al siguiente índice de waypoint con soporte para circuitos continuos."""
        if not self.waypoints:
            return
        if self.loop_route:
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
        else:
            if self.current_waypoint_index < len(self.waypoints) - 1:
                self.current_waypoint_index += 1

    def handle_event(
        self,
        event_code: int,
        data: bytes,
        sender_id: int,
        world: SharedWorld,
    ) -> bool:
        """Maneja el abordaje y descenso de pasajeros de forma autoritativa."""
        if event_code == EventCode.VEHICLE_ENTER:
            # Desempaquetar vehículo, asiento, rol
            if len(data) < 6:
                return False
            v_id, seat_idx, role = struct.unpack("<IBB", data[:6])
            if v_id != self.entity_id:
                return False

            passengers: list[int] = self.entity.properties.setdefault("passengers", [])
            if sender_id not in passengers:
                if len(passengers) >= self.max_passengers:
                    logger.warning("Vehículo %d lleno. Rechazando pasajero %d", self.entity_id, sender_id)
                    return False
                passengers.append(sender_id)
                logger.info(
                    "Pasajero %d abordó vehículo de ruta %d (Plaza %d, Total: %d)",
                    sender_id,
                    self.entity_id,
                    seat_idx,
                    len(passengers),
                )
            return True

        elif event_code == EventCode.VEHICLE_EXIT:
            if len(data) < 5:
                return False
            v_id, seat_idx = struct.unpack("<IB", data[:5])
            if v_id != self.entity_id:
                return False

            passengers = self.entity.properties.get("passengers", [])
            if sender_id in passengers:
                passengers.remove(sender_id)
                logger.info(
                    "Pasajero %d descendió del vehículo de ruta %d (Total restantes: %d)",
                    sender_id,
                    self.entity_id,
                    len(passengers),
                )
            return True

        return False
