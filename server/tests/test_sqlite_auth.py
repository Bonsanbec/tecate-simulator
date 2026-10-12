"""Suite de pruebas unitarias para DatabaseManager, ServerAuthManager y SessionManager."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from server.core.auth_manager import ServerAuthManager
from server.core.db import DatabaseManager
from server.core.session_manager import SessionManager


class TestSQLiteAuthAndPersistence(unittest.TestCase):
    """Verifica el esquema SQLite, autenticación con tokens y desacoplamiento de IDs."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_tecate.db"
        self.db_manager = DatabaseManager(self.db_path)
        self.auth_manager = ServerAuthManager(self.db_manager)
        self.session_manager = SessionManager(max_clients=10)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_database_schema_initialization(self) -> None:
        """Verifica que las tablas principales se creen con modo WAL activo."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            mode = cursor.fetchone()[0]
            self.assertEqual(mode.lower(), "wal")

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            self.assertIn("players", tables)
            self.assertIn("player_world_states", tables)
            self.assertIn("player_cosmetics", tables)
            self.assertIn("player_minigame_stats", tables)

    def test_auto_register_new_player(self) -> None:
        """Verifica el auto-registro con saldo inicial de 50 Pesos."""
        ok, profile, msg = self.auth_manager.authenticate_or_register("", fallback_nickname="Axel Tecate")
        self.assertTrue(ok)
        self.assertTrue(profile["is_new"])
        self.assertEqual(profile["display_name"], "Axel Tecate")
        self.assertEqual(profile["balance_pesos"], 50)
        self.assertTrue(len(profile["player_uuid"]) > 0)
        self.assertTrue(len(profile["auth_secret"]) > 0)

    def test_reconnect_existing_player(self) -> None:
        """Verifica que al reconectarse con el mismo UUID y secreto se recupere el perfil."""
        # 1. Registro inicial
        ok, prof1, _ = self.auth_manager.authenticate_or_register("", fallback_nickname="Eli")
        token = f"{prof1['player_uuid']}:{prof1['auth_secret']}:Eli"

        # 2. Modificar saldo y posición
        self.auth_manager.update_player_balance(prof1["player_uuid"], 100) # 50 + 100 = 150
        self.auth_manager.save_player_position(prof1["player_uuid"], 15.0, 402.0, -10.0, 180.0)

        # 3. Reconexión
        ok2, prof2, _ = self.auth_manager.authenticate_or_register(token)
        self.assertTrue(ok2)
        self.assertFalse(prof2["is_new"])
        self.assertEqual(prof2["balance_pesos"], 150)

        pos = self.auth_manager.get_player_position(prof1["player_uuid"])
        self.assertIsNotNone(pos)
        self.assertAlmostEqual(pos[0], 15.0)
        self.assertAlmostEqual(pos[1], 402.0)
        self.assertAlmostEqual(pos[2], -10.0)
        self.assertAlmostEqual(pos[3], 180.0)

    def test_reject_invalid_secret(self) -> None:
        """Verifica que se rechace un intento de inicio de sesión con secreto incorrecto."""
        ok, prof, _ = self.auth_manager.authenticate_or_register("", fallback_nickname="Astorga")
        bad_token = f"{prof['player_uuid']}:clave_falsa_12345:Astorga"

        ok_bad, _, msg = self.auth_manager.authenticate_or_register(bad_token)
        self.assertFalse(ok_bad)
        self.assertIn("no autorizada", msg)

    def test_session_manager_entity_reanchoring(self) -> None:
        """Verifica que el mismo player_uuid conserve su player_entity_id sin duplicar avatares."""
        uuid_1 = "test-uuid-1234"
        addr_1 = ("127.0.0.1", 50001)

        # Primera sesión
        s1 = self.session_manager.create_or_renew_session(
            addr=addr_1, player_uuid=uuid_1, display_name="Jugador 1"
        )
        eid_1 = s1.player_entity_id
        sid_1 = s1.session_id

        # Salto de puerto NAT o reconexión rápida (misma máquina, puerto 50002)
        addr_2 = ("127.0.0.1", 50002)
        s2 = self.session_manager.create_or_renew_session(
            addr=addr_2, player_uuid=uuid_1, display_name="Jugador 1"
        )

        # Debe reanclar la misma entidad física en el mundo
        self.assertEqual(s2.player_entity_id, eid_1)
        self.assertEqual(s2.session_id, sid_1)
        self.assertEqual(s2.addr, addr_2)

    def test_minigame_stats_recording(self) -> None:
        """Verifica la agregación de estadísticas de minijuegos en SQLite."""
        ok, prof, _ = self.auth_manager.authenticate_or_register("", fallback_nickname="Campeón")
        p_uuid = prof["player_uuid"]

        self.auth_manager.record_minigame_stat(p_uuid, "mi_kiosko", won=True, metric=1.0)
        self.auth_manager.record_minigame_stat(p_uuid, "mi_kiosko", won=False, metric=0.0)
        self.auth_manager.record_minigame_stat(p_uuid, "mi_kiosko", won=True, metric=2.0)

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT wins, matches_played, best_metric FROM player_minigame_stats WHERE player_uuid = ? AND game_id = ?", (p_uuid, "mi_kiosko"))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["wins"], 2)
            self.assertEqual(row["matches_played"], 3)
            self.assertAlmostEqual(row["best_metric"], 2.0)


if __name__ == "__main__":
    unittest.main()
