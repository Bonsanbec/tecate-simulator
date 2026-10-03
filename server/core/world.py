"""Mundo compartido y gestión espacial (Interest Management) para TKT/1."""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from typing import Iterator

from server.core.controllers.citizen import CitizenController
from server.core.controllers.free_vehicle import FreeVehicleController
from server.core.controllers.npc_pedestrian import NPCPedestrianController
from server.core.controllers.route_vehicle import RouteVehicleController
from server.core.entity import DynamicEntity
from server.core.simulation import SimulationManager
from server.protocol.codec import EntityStateRecord, SnapshotPayload
from server.protocol.constants import EntityType, PlayerFlags, VehicleFlags

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
        # Gestor de simulación autoritativa para todas las entidades
        self.simulation_manager = SimulationManager()

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
            # Desregistrar controlador de simulación si existe
            self.simulation_manager.unregister_controller(entity_id)
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
        included_ids: set[int] = set()
        r = self.broadcast_radius

        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                cell = (center_cell[0] + dx, center_cell[1] + dz)
                entity_ids = self._grid.get(cell)
                if not entity_ids:
                    continue
                for eid in entity_ids:
                    if exclude_entity_id is not None and eid == exclude_entity_id:
                        continue
                    ent = self._entities.get(eid)
                    if ent is not None and eid not in included_ids:
                        relevant_records.append(ent.to_record())
                        included_ids.add(eid)

        # Flota de transporte público de ruta: siempre visible y sincronizada en toda la red
        for eid, ent in self._entities.items():
            if exclude_entity_id is not None and eid == exclude_entity_id:
                continue
            if (ent.flags & VehicleFlags.ROUTE_VEHICLE) and eid not in included_ids:
                relevant_records.append(ent.to_record())
                included_ids.add(eid)

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

    def get_vehicle_by_driver(self, driver_id: int) -> DynamicEntity | None:
        """Encuentra el vehículo conducido por el jugador indicado."""
        for ent in self._entities.values():
            if ent.is_vehicle and ent.driver_id == driver_id:
                return ent
        return None

    def get_vehicles(self) -> list[DynamicEntity]:
        """Retorna todas las entidades que son vehículos."""
        return [ent for ent in self._entities.values() if ent.is_vehicle]

    def spawn_default_vehicles(self) -> None:
        """Instancia los vehículos y entidades iniciales del entorno urbano compartido de Tecate."""
        self.spawn_default_world_entities()

    def spawn_default_world_entities(self) -> None:
        """Instancia la flota autoritativa de transporte público, vehículos libres y NPCs."""

        # 2. Flota autoritativa de autobuses "El Hongo"
        route_path = self._resolve_route_json_path()
        if route_path and os.path.exists(route_path):
            with open(route_path, "r", encoding="utf-8") as f:
                route_meta = json.load(f)
            fleet_cfg = route_meta.get("fleet_configuration", {})
            configured_units = fleet_cfg.get("units", [])
            calibrated_cruise = float(fleet_cfg.get("calibrated_cruise_speed_kmh", 80.0))

            if configured_units:
                for u in configured_units:
                    entity_id = int(u.get("unit_id", 1000))
                    initial_wp = int(u.get("start_waypoint_index", 0))
                    bus_name = u.get("vehicle_name", f"Autobús El Hongo (Unidad {entity_id})")
                    bus = DynamicEntity(
                        entity_id=entity_id,
                        entity_type=EntityType.VEHICLE,
                        flags=(VehicleFlags.ROUTE_VEHICLE | VehicleFlags.ENGINE_RUNNING | VehicleFlags.HEADLIGHTS),
                        properties={
                            "fuel": 999.0,
                            "vehicle_type": "bus_route",
                            "vehicle_name": bus_name,
                            "driver_id": None,
                            "passengers": [],
                        },
                    )
                    bus_ctrl = RouteVehicleController.from_route_json(
                        entity=bus,
                        route_json_path=route_path,
                        initial_waypoint_index=initial_wp,
                        cruise_speed_kmh=calibrated_cruise,
                        max_passengers=30,
                    )
                    self.upsert_entity(bus)
                    self.simulation_manager.register_controller(bus_ctrl)
                logger.info(
                    "Flota autoritativa de autobuses instanciada (%d unidades para frecuencia de %.1f min).",
                    len(configured_units),
                    float(fleet_cfg.get("headway_minutes", 5.0)),
                )
            else:
                bus = DynamicEntity(
                    entity_id=1001,
                    entity_type=EntityType.VEHICLE,
                    flags=(VehicleFlags.ROUTE_VEHICLE | VehicleFlags.ENGINE_RUNNING | VehicleFlags.HEADLIGHTS),
                    properties={
                        "fuel": 999.0,
                        "vehicle_type": "bus_route",
                        "vehicle_name": "Autobús El Hongo (Unidad 24)",
                        "driver_id": None,
                        "passengers": [],
                    },
                )
                bus_ctrl = RouteVehicleController.from_route_json(
                    entity=bus,
                    route_json_path=route_path,
                    initial_waypoint_index=0,
                    cruise_speed_kmh=calibrated_cruise,
                    max_passengers=30,
                )
                self.upsert_entity(bus)
                self.simulation_manager.register_controller(bus_ctrl)
                logger.info("Flota autoritativa instanciada con unidad única de respaldo.")

        # 3. Ciudadanos y peatones autoritativos del centro urbano de Tecate
        # Simulados enteramente por el servidor TKT/1, recorriendo banquetas y áreas cívicas
        citizens_data = [
            {
                "id": 3001,
                "name": "Don Miguel",
                "spawn": (-6.7, 400.2, 2.7),
                "patrol": [
                    (-6.7, 400.2, 2.7),
                    (-6.7, 400.6, -14.0),
                    (-6.7, 401.0, -28.0),
                    (-16.0, 400.7, -14.0),
                    (-16.0, 400.3, 2.7),
                ],
                "speed": 1.25,
            },
            {
                "id": 3002,
                "name": "Doña Rosa",
                "spawn": (-12.0, 400.3, 2.7),
                "patrol": [
                    (-12.0, 400.3, 2.7),
                    (-24.0, 400.7, -5.0),
                    (-38.0, 401.2, -12.0),
                    (-24.0, 400.7, -5.0),
                ],
                "speed": 1.15,
            },
            {
                "id": 3003,
                "name": "Juan Carlos",
                "spawn": (-6.7, 400.2, 5.0),
                "patrol": [
                    (-6.7, 400.2, 5.0),
                    (-6.7, 399.6, 18.0),
                    (-6.7, 398.9, 32.0),
                    (-6.7, 399.6, 18.0),
                ],
                "speed": 1.30,
            },
            {
                "id": 3004,
                "name": "Carmen",
                "spawn": (-2.0, 400.2, 2.7),
                "patrol": [
                    (-2.0, 400.2, 2.7),
                    (15.0, 400.1, 2.7),
                    (32.0, 399.9, 2.7),
                    (44.0, 399.6, 2.7),
                    (32.0, 399.9, 2.7),
                    (15.0, 400.1, 2.7),
                ],
                "speed": 1.20,
            },
        ]

        for c_data in citizens_data:
            c_ent = DynamicEntity(
                entity_id=c_data["id"],
                entity_type=EntityType.NPC,
                pos_x=c_data["spawn"][0],
                pos_y=c_data["spawn"][1],
                pos_z=c_data["spawn"][2],
                flags=PlayerFlags.GROUNDED,
                properties={"name": c_data["name"]},
            )
            self.upsert_entity(c_ent)
            c_ctrl = CitizenController(
                entity=c_ent,
                patrol_points=c_data["patrol"],
                walk_speed=c_data["speed"],
                name=c_data["name"],
            )
            self.simulation_manager.register_controller(c_ctrl)
        logger.info("Población de ciudadanos autoritativos instanciada (%d ciudadanos).", len(citizens_data))

    def _resolve_route_json_path(self) -> str | None:
        """Localiza de forma robusta la ruta al archivo bus_hongo_route.json."""
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "routes", "bus_hongo_route.json"),
            os.path.join("server", "routes", "bus_hongo_route.json"),
            os.path.abspath("server/routes/bus_hongo_route.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "godot_project", "assets", "vehicles", "bus_hongo_route.json"),
            os.path.join("godot_project", "assets", "vehicles", "bus_hongo_route.json"),
            os.path.abspath("godot_project/assets/vehicles/bus_hongo_route.json"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

