"""Pruebas unitarias para session_manager y world de server/core/."""

import time
import unittest
from server.core.entity import DynamicEntity
from server.core.session_manager import SessionManager
from server.core.world import SharedWorld
from server.protocol.constants import EntityType, PlayerFlags


class TestServerCore(unittest.TestCase):
    def test_session_creation_and_lookup(self):
        sm = SessionManager(max_clients=10)
        addr = ("192.168.1.50", 52665)
        session = sm.create_or_renew_session(addr, client_version="1.0.0")

        self.assertIsNotNone(session)
        self.assertEqual(session.addr, addr)
        self.assertEqual(session.session_id, 100)
        self.assertEqual(session.player_entity_id, 1)

        # Lookup por dirección y por ID
        by_addr = sm.get_by_addr(addr)
        self.assertEqual(by_addr, session)

        by_id = sm.get_by_id(100)
        self.assertEqual(by_id, session)

        # Renovación de sesión existente
        renewed = sm.create_or_renew_session(addr, client_version="1.0.1")
        self.assertEqual(renewed.session_id, 100)
        self.assertEqual(renewed.client_version, "1.0.1")
        self.assertEqual(len(sm), 1)

    def test_session_timeout_purge(self):
        sm = SessionManager()
        s1 = sm.create_or_renew_session(("10.0.0.1", 1001))
        s2 = sm.create_or_renew_session(("10.0.0.2", 1002))

        # Simular inactividad en s1
        s1.last_seen = time.time() - 20.0

        purged = sm.purge_timed_out(timeout_seconds=10.0)
        self.assertEqual(len(purged), 1)
        self.assertEqual(purged[0].session_id, s1.session_id)
        self.assertEqual(len(sm), 1)
        self.assertIsNone(sm.get_by_id(s1.session_id))
        self.assertIsNotNone(sm.get_by_id(s2.session_id))

    def test_world_spatial_interest_management(self):
        world = SharedWorld(cell_size=100.0, broadcast_radius=1)

        # Jugador 1 en celda (0, 0) -> X=10, Z=10
        p1 = DynamicEntity(entity_id=1, pos_x=10.0, pos_z=10.0)
        # Jugador 2 en celda (1, 0) -> X=120, Z=10 (celda adyacente, dentro de radio 1)
        p2 = DynamicEntity(entity_id=2, pos_x=120.0, pos_z=10.0)
        # Jugador 3 en celda (5, 5) -> X=550, Z=550 (fuera de radio de interés)
        p3 = DynamicEntity(entity_id=3, pos_x=550.0, pos_z=550.0)

        world.upsert_entity(p1)
        world.upsert_entity(p2)
        world.upsert_entity(p3)

        self.assertEqual(len(world), 3)

        # Generar snapshot para Jugador 1: debe ver a p2 pero NO a p3 (y no a sí mismo p1)
        snap = world.build_snapshot_for_player(player_entity_id=1, server_tick=50, server_time=1000)
        visible_ids = [e.entity_id for e in snap.entities]

        self.assertIn(2, visible_ids)
        self.assertNotIn(3, visible_ids)
        self.assertNotIn(1, visible_ids)

        # Eliminar p2
        world.remove_entity(2)
        snap_after = world.build_snapshot_for_player(player_entity_id=1, server_tick=51, server_time=1033)
        self.assertEqual(len(snap_after.entities), 0)


if __name__ == "__main__":
    unittest.main()
