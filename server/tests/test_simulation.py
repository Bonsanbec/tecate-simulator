"""Pruebas unitarias para el motor de simulación autoritativa de entidades en el servidor."""

import math
import os
import struct
import unittest

from server.core.controllers.free_vehicle import FreeVehicleController
from server.core.controllers.interactive_object import InteractiveObjectController
from server.core.controllers.npc_pedestrian import NPCPedestrianController
from server.core.controllers.route_vehicle import RouteVehicleController
from server.core.entity import DynamicEntity
from server.core.simulation import SimulationManager
from server.core.world import SharedWorld
from server.protocol.constants import EntityType, EventCode, PlayerFlags, VehicleFlags


class TestSimulationArchitecture(unittest.TestCase):
    def setUp(self):
        self.world = SharedWorld()

    def test_simulation_manager_lifecycle(self):
        sm = SimulationManager()
        ent = DynamicEntity(entity_id=500, entity_type=EntityType.NPC)
        ctrl = NPCPedestrianController(ent, patrol_points=[(0, 0, 0), (10, 0, 0)])

        sm.register_controller(ctrl)
        self.assertEqual(len(sm), 1)
        self.assertIs(sm.get_controller(500), ctrl)

        # Update
        sm.update(0.1, self.world)
        self.assertIn(500, self.world._entities)

        # Unregister
        removed = sm.unregister_controller(500)
        self.assertIs(removed, ctrl)
        self.assertEqual(len(sm), 0)

    def test_route_vehicle_controller_navigation_and_stations(self):
        ent = DynamicEntity(
            entity_id=2001,
            entity_type=EntityType.VEHICLE,
            pos_x=0.0,
            pos_y=400.0,
            pos_z=0.0,
        )
        waypoints = [
            (0.0, 400.0, 0.0),
            (0.0, 400.0, -30.0),  # Hacia el norte (-Z en Godot)
            (30.0, 405.0, -30.0), # Hacia el este (+X)
        ]
        stations = {
            1: {"name": "Parada 1", "dwell_time": 1.0}
        }
        bus_ctrl = RouteVehicleController(
            entity=ent,
            waypoints=waypoints,
            station_indices=stations,
            cruise_speed_kmh=36.0,
            waypoint_reach_threshold=2.0,
            initial_waypoint_index=0,
        )
        # Apuntar hacia el waypoint 1
        bus_ctrl.current_waypoint_index = 1

        # 1. Simular avance hacia el waypoint 1 (que es una estación, a 30m de distancia)
        reached = False
        for _ in range(100):
            bus_ctrl.update(0.1, self.world)
            if bus_ctrl.is_at_station:
                reached = True
                break

        self.assertTrue(reached, "Debe haber alcanzado y entrado en estado de espera en la estación")
        self.assertEqual(ent.vel_x, 0.0)
        self.assertEqual(ent.vel_z, 0.0)

        # 2. Esperar 1.0 segundo de dwell time en estación (15 ticks de 0.1s > 1.0s)
        for _ in range(15):
            bus_ctrl.update(0.1, self.world)

        self.assertFalse(bus_ctrl.is_at_station, "Debe haber reanudado la marcha tras agotar el dwell time")
        self.assertEqual(bus_ctrl.current_waypoint_index, 2, "Debe haber avanzado al waypoint 2")

    def test_route_vehicle_passenger_events(self):
        ent = DynamicEntity(entity_id=2001, entity_type=EntityType.VEHICLE)
        bus_ctrl = RouteVehicleController(
            entity=ent,
            waypoints=[(0, 400, 0), (10, 400, 0)],
            max_passengers=2,
        )

        # Abordar jugador 42
        enter_data = struct.pack("<IBB", 2001, 1, 2) # v_id=2001, seat=1, role=passenger
        handled = bus_ctrl.handle_event(EventCode.VEHICLE_ENTER, enter_data, sender_id=42, world=self.world)
        self.assertTrue(handled)
        self.assertIn(42, ent.properties["passengers"])

        # Abordar jugador 43
        enter_data2 = struct.pack("<IBB", 2001, 2, 2)
        handled2 = bus_ctrl.handle_event(EventCode.VEHICLE_ENTER, enter_data2, sender_id=43, world=self.world)
        self.assertTrue(handled2)
        self.assertEqual(len(ent.properties["passengers"]), 2)

        # Intentar abordar con cupo lleno
        enter_data3 = struct.pack("<IBB", 2001, 3, 2)
        handled3 = bus_ctrl.handle_event(EventCode.VEHICLE_ENTER, enter_data3, sender_id=44, world=self.world)
        self.assertFalse(handled3, "No debe permitir abordar si se alcanzó max_passengers")

        # Descenso de jugador 42
        exit_data = struct.pack("<IB", 2001, 1)
        handled_exit = bus_ctrl.handle_event(EventCode.VEHICLE_EXIT, exit_data, sender_id=42, world=self.world)
        self.assertTrue(handled_exit)
        self.assertNotIn(42, ent.properties["passengers"])
        self.assertEqual(len(ent.properties["passengers"]), 1)

    def test_free_vehicle_friction_and_fuel(self):
        car = DynamicEntity(
            entity_id=1001,
            entity_type=EntityType.VEHICLE,
            vel_x=10.0,
            vel_z=0.0,
            flags=VehicleFlags.ENGINE_RUNNING,
            properties={"fuel": 50.0},
        )
        ctrl = FreeVehicleController(car, max_fuel=80.0, friction_deceleration=5.0)

        # Sin conductor, debe desacelerar por fricción
        ctrl.update(1.0, self.world)
        self.assertAlmostEqual(car.vel_x, 5.0, places=1)

        ctrl.update(1.0, self.world)
        self.assertAlmostEqual(car.vel_x, 0.0, places=1)
        self.assertFalse(car.flags & VehicleFlags.ENGINE_RUNNING, "Motor debe apagarse al detenerse sin conductor")

    def test_npc_pedestrian_states(self):
        npc = DynamicEntity(entity_id=3001, entity_type=EntityType.NPC, pos_x=0.0, pos_y=400.0, pos_z=0.0)
        ctrl = NPCPedestrianController(
            entity=npc,
            patrol_points=[(0, 400, 0), (0, 400, 5)],
            walk_speed=2.0,
            idle_duration=1.0,
        )
        ctrl.current_target_idx = 1
        ctrl.current_state = NPCPedestrianController.STATE_WALKING

        self.assertEqual(ctrl.current_state, NPCPedestrianController.STATE_WALKING)
        # Avanzar hacia (0, 400, 5) a 2 m/s -> en 3.0s alcanza el punto y entra a IDLE
        for _ in range(30):
            ctrl.update(0.1, self.world)

        # Debe haber llegado al punto (0, 400, 5) y entrado a IDLE
        self.assertEqual(ctrl.current_state, NPCPedestrianController.STATE_IDLE)

        # Interacción
        interacted = ctrl.handle_event(EventCode.ENTITY_INTERACT, b"", sender_id=99, world=self.world)
        self.assertTrue(interacted)
        self.assertEqual(ctrl.current_state, NPCPedestrianController.STATE_INTERACTING)

    def test_interactive_object(self):
        obj = DynamicEntity(entity_id=4001, entity_type=EntityType.OBJECT)
        ctrl = InteractiveObjectController(obj, object_type="toll_gate", initial_state="CLOSED")

        handled = ctrl.handle_event(EventCode.ENTITY_INTERACT, b"", sender_id=1, world=self.world)
        self.assertTrue(handled)
        self.assertEqual(obj.properties["state"], "OPEN")

        handled2 = ctrl.handle_event(EventCode.ENTITY_INTERACT, b"", sender_id=1, world=self.world)
        self.assertTrue(handled2)
        self.assertEqual(obj.properties["state"], "CLOSED")

    def test_world_spawn_default_entities(self):
        self.world.spawn_default_world_entities()

        # Debe haber 5 autobuses de ruta autoritativos (1002, 2001, 2002, 2003, 2004)
        for bus_id in [1002, 2001, 2002, 2003, 2004]:
            bus = self.world.get_entity(bus_id)
            self.assertIsNotNone(bus, f"Autobús {bus_id} debe existir en SharedWorld")
            self.assertTrue(bus.flags & VehicleFlags.ROUTE_VEHICLE)
            self.assertIsNotNone(self.world.simulation_manager.get_controller(bus_id))

        # Debe existir el auto libre 1001
        car = self.world.get_entity(1001)
        self.assertIsNotNone(car)
        self.assertIsNotNone(self.world.simulation_manager.get_controller(1001))

        # Deben existir los NPCs 3001 y 3002
        npc1 = self.world.get_entity(3001)
        self.assertIsNotNone(npc1)
        self.assertEqual(npc1.entity_type, EntityType.NPC)
        self.assertIsNotNone(self.world.simulation_manager.get_controller(3001))

        # Probar un ciclo de simulación del mundo completo
        self.world.simulation_manager.update(0.033, self.world)
        snap = self.world.build_snapshot_for_player(player_entity_id=999, server_tick=1, server_time=100)
        self.assertGreater(len(snap.entities), 0)


if __name__ == "__main__":
    unittest.main()
