"""Mundo compartido y gestión espacial (Interest Management) para TKT/1."""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from typing import Iterator

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
        # 1. Automóvil urbano conducible en estacionamiento sobre Calle Ortiz Rubio
        car = DynamicEntity(
            entity_id=1001,
            entity_type=EntityType.VEHICLE,
            pos_x=-58.0,
            pos_y=399.6,
            pos_z=8.0,
            yaw=0.0,
            pitch=0.0,
            flags=VehicleFlags.NONE,
            properties={"fuel": 80.0, "vehicle_type": "car", "driver_id": None, "passengers": []},
        )
        self.upsert_entity(car)
        car_ctrl = FreeVehicleController(car, max_fuel=80.0)
        self.simulation_manager.register_controller(car_ctrl)

        # 2. Flota autoritativa de autobuses "El Hongo"
        route_path = self._resolve_route_json_path()
        if route_path and os.path.exists(route_path):
            bus_fleet_configs = [
                (1002, 133, "Autobús El Hongo (Unidad 24)"), # Central Camionera
                (2001, 120, "Autobús El Hongo (Unidad 18)"), # Arribando a Centro / Parque Hidalgo
                (2002, 145, "Autobús El Hongo (Unidad 23)"), # Blvd. Defensores hacia carretera
                (2003, 180, "Autobús El Hongo (Unidad 07)"), # Carretera Libre Este
                (2004, 990, "Autobús El Hongo (Unidad 12)"), # Retorno hacia Centro
            ]
            for entity_id, initial_wp, bus_name in bus_fleet_configs:
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
                    cruise_speed_kmh=36.8,
                    max_passengers=30,
                )
                self.upsert_entity(bus)
                self.simulation_manager.register_controller(bus_ctrl)
            logger.info("Flota autoritativa de autobuses instanciada (%d unidades).", len(bus_fleet_configs))
        else:
            logger.warning("No se encontró bus_hongo_route.json en '%s'. Usando circuito urbano procedural activo de emergencia.", route_path)
            fallback_waypoints = [
                (164.0, 402.25, -32.0),
                (167.7, 403.45, -47.5),
                (250.8, 404.39, -69.2),
                (368.1, 409.85, -81.2),
                (189.2, 401.02, 88.6),
                (99.5, 399.51, 99.6),
                (32.4, 398.06, 107.5),
                (-7.8, 397.62, 111.5),
                (-127.4, 397.9, 126.3),
                (160.0, 401.99, -6.0),
            ]
            bus = DynamicEntity(
                entity_id=1002,
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
            bus_ctrl = RouteVehicleController(
                entity=bus,
                waypoints=fallback_waypoints,
                station_indices={0: {"name": "Central Camionera", "dwell_time": 6.0}},
                cruise_speed_kmh=36.0,
                max_passengers=30,
            )
            self.upsert_entity(bus)
            self.simulation_manager.register_controller(bus_ctrl)

        # 3. Peatones y NPCs del centro urbano (Parque Miguel Hidalgo y Presidencia)
        npc1 = DynamicEntity(
            entity_id=3001,
            entity_type=EntityType.NPC,
            pos_x=-15.0,
            pos_y=400.0,
            pos_z=20.0,
            flags=PlayerFlags.GROUNDED,
            properties={"name": "Don Miguel (Transeúnte)"},
        )
        self.upsert_entity(npc1)
        npc1_ctrl = NPCPedestrianController(
            entity=npc1,
            patrol_points=[
                (-15.0, 400.0, 20.0),
                (-5.0, 400.0, 25.0),
                (10.0, 400.0, 15.0),
                (-10.0, 400.0, 5.0),
            ],
            walk_speed=1.30,
            name="Don Miguel (Transeúnte)",
        )
        self.simulation_manager.register_controller(npc1_ctrl)

        npc2 = DynamicEntity(
            entity_id=3002,
            entity_type=EntityType.NPC,
            pos_x=-30.0,
            pos_y=400.0,
            pos_z=-10.0,
            flags=PlayerFlags.GROUNDED,
            properties={"name": "Doña Rosa (Comerciante)"},
        )
        self.upsert_entity(npc2)
        npc2_ctrl = NPCPedestrianController(
            entity=npc2,
            patrol_points=[
                (-30.0, 400.0, -10.0),
                (-10.0, 400.0, -15.0),
                (-15.0, 400.0, -5.0),
            ],
            walk_speed=1.15,
            name="Doña Rosa (Comerciante)",
        )
        self.simulation_manager.register_controller(npc2_ctrl)

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

