"""Pruebas unitarias e integración para el Motor Modular de Minijuegos de Tecate Simulator."""

import math
import os
import tempfile
import time
import unittest

from server.core.auth_manager import ServerAuthManager
from server.core.db import DatabaseManager
from server.core.entity import DynamicEntity
from server.core.session_manager import SessionManager
from server.core.world import SharedWorld
from server.minigames.arena import BoxArena, CylinderArena
from server.minigames.evaluators.anti_camping import ActivityAntiCampingEvaluator
from server.minigames.evaluators.ballistic import BallisticHitEvaluator
from server.minigames.evaluators.contact import ProximityContactEvaluator
from server.minigames.evaluators.spatial import SpatialBoundaryEvaluator
from server.minigames.fsm import MinigameState
from server.minigames.games.las_traes import LasTraesMinigame
from server.minigames.games.mi_kiosko import MiKioskoMinigame
from server.minigames.games.quemados import QuemadosMinigame
from server.minigames.orchestrator import MinigameOrchestrator
from server.minigames.participant import Participant, ParticipantRole, ParticipantState
from server.protocol.constants import EventCode


class TestMinigameEvaluators(unittest.TestCase):
    """Pruebas de los evaluadores geométricos y cinemáticos reutilizables."""

    def test_spatial_boundary_evaluator_kiosko(self):
        arena = CylinderArena(
            center_x=-6.684,
            center_y=401.80,
            center_z=2.688,
            radius=4.80,
            min_y=401.10,
            max_y=420.0,
        )
        evaluator = SpatialBoundaryEvaluator(arena)

        # Dentro de la plataforma del Kiosko
        inside, reason = evaluator.check_boundary(-6.684, 401.80, 2.688)
        self.assertTrue(inside)
        self.assertEqual(reason, "")

        # Caída debajo de la tarima (Zócalo / Suelo)
        inside, reason = evaluator.check_boundary(-6.684, 400.95, 2.688)
        self.assertFalse(inside)
        self.assertEqual(reason, "FALL_BELOW_DECK")

        # Expulsión horizontal más allá de la barandilla (R > 4.80m)
        inside, reason = evaluator.check_boundary(-6.684 + 5.50, 401.80, 2.688)
        self.assertFalse(inside)
        self.assertEqual(reason, "RADIAL_RING_OUT")

    def test_proximity_contact_evaluator_and_immunity(self):
        evaluator = ProximityContactEvaluator(contact_threshold=1.85, default_immunity_duration=2.0)

        source_pos = (0.0, 0.0, 0.0)
        target_close = (1.0, 0.0, 1.0)  # Distancia sqrt(2) ~= 1.41m <= 1.85m
        target_far = (3.0, 0.0, 0.0)    # Distancia 3.0m > 1.85m

        # Contacto exitoso
        self.assertTrue(evaluator.check_contact(source_pos, target_close, target_entity_id=10))
        # Fuera de rango
        self.assertFalse(evaluator.check_contact(source_pos, target_far, target_entity_id=11))

        # Asignar inmunidad al objetivo
        evaluator.set_immunity(10, 2.0)
        self.assertTrue(evaluator.has_immunity(10))
        # Contacto rechazado debido a inmunidad activa
        self.assertFalse(evaluator.check_contact(source_pos, target_close, target_entity_id=10))

        # Simular avance del tiempo mayor a 2.0s
        evaluator.update(2.1)
        self.assertFalse(evaluator.has_immunity(10))
        self.assertTrue(evaluator.check_contact(source_pos, target_close, target_entity_id=10))

    def test_anti_camping_evaluator(self):
        evaluator = ActivityAntiCampingEvaluator(window_seconds=3.5, min_speed_threshold=0.5)

        # Jugador 1: Corriendo a velocidad continua (2.0 m/s)
        # 0s: (0, 0), 1s: (2, 0), 2s: (4, 0), 3s: (6, 0)
        for t in range(4):
            evaluator.record_position(1, float(t), float(t * 2.0), 0.0)

        # Jugador 2: Campeando en una banca casi inmóvil (< 0.1 m/s)
        for t in range(4):
            evaluator.record_position(2, float(t), 10.0 + (t * 0.05), 10.0)

        self.assertFalse(evaluator.is_camping(1, 3.0))
        self.assertTrue(evaluator.is_camping(2, 3.0))

    def test_ballistic_hit_evaluator(self):
        evaluator = BallisticHitEvaluator(gravity=9.8, floor_y=0.0)

        # Disparar pelota desde (0, 0, 0) hacia el frente en +Z
        ball = evaluator.spawn_ball(
            thrower_id=1,
            origin=(0.0, 0.0, 0.0),
            direction=(0.0, 0.0, 1.0),
            speed=20.0,
        )
        self.assertEqual(len(evaluator.balls), 1)

        # Objetivo situado a 2 metros de distancia en (0, 0, 2)
        targets = [(2, 0.0, 0.0, 2.0)]

        # Avanzar 0.1s: la pelota viaja ~2m y debe colisionar con la cápsula de objetivo 2
        hits = evaluator.update(0.1, targets)
        self.assertEqual(len(hits), 1)
        hit_id, hit_ball = hits[0]
        self.assertEqual(hit_id, 2)
        self.assertEqual(hit_ball.ball_id, ball.ball_id)
        # La pelota impactada debe quedar inactiva y removerse
        self.assertEqual(len(evaluator.balls), 0)


class TestMiKioskoMinigame(unittest.TestCase):
    """Pruebas de la lógica autoritativa y preservación espacial de Mi Kiosko."""

    def setUp(self):
        self.world = SharedWorld()
        self.p1_ent = DynamicEntity(entity_id=101, pos_x=50.0, pos_y=400.0, pos_z=50.0, yaw=0.0)
        self.p2_ent = DynamicEntity(entity_id=102, pos_x=60.0, pos_y=400.0, pos_z=60.0, yaw=45.0)
        self.world.upsert_entity(self.p1_ent)
        self.world.upsert_entity(self.p2_ent)

    def test_staging_snapshots_and_teleport(self):
        game = MiKioskoMinigame()
        emitted_events = []
        game.on_event_emit = emitted_events.append

        participants = [
            Participant(entity_id=101, session_id=1, player_uuid="u1", display_name="Axel"),
            Participant(entity_id=102, session_id=2, player_uuid="u2", display_name="Eli"),
        ]

        game.start_staging(participants, self.world)

        self.assertEqual(game.state, MinigameState.STAGING)
        # Verificar preservación espacial en snapshot
        self.assertEqual(participants[0].snapshot.pos_x, 50.0)
        self.assertEqual(participants[1].snapshot.pos_x, 60.0)

        # Verificar teletransportación a la tarima del Kiosko
        ent1 = self.world.get_entity(101)
        ent2 = self.world.get_entity(102)
        self.assertAlmostEqual(ent1.pos_y, MiKioskoMinigame.KIOSKO_FLOOR_Y)
        self.assertAlmostEqual(ent2.pos_y, MiKioskoMinigame.KIOSKO_FLOOR_Y)

        # Verificar emisión de MINIGAME_START
        self.assertEqual(len(emitted_events), 1)
        self.assertEqual(emitted_events[0].event_code, EventCode.MINIGAME_START)

    def test_minecraft_knockback_and_ringout_elimination(self):
        game = MiKioskoMinigame()
        emitted_events = []
        game.on_event_emit = emitted_events.append

        participants = [
            Participant(entity_id=101, session_id=1, player_uuid="u1", display_name="Axel"),
            Participant(entity_id=102, session_id=2, player_uuid="u2", display_name="Eli"),
        ]
        game.start_staging(participants, self.world)

        # Transicionar a ACTIVE
        game.tick(3.1, self.world)
        self.assertEqual(game.state, MinigameState.ACTIVE)

        # P1 empuja a P2
        ent1 = self.world.get_entity(101)
        ent2 = self.world.get_entity(102)
        # Acercar a P1 a P2 para que esté en rango
        ent1.pos_x = ent2.pos_x - 1.0
        ent1.pos_y = ent2.pos_y
        ent1.pos_z = ent2.pos_z

        push_action = {
            "action_type": 1,
            "target_entity_id": 102,
            "param_float": 8.0,
            "dir": (1.0, 0.0, 0.0),
        }
        game.handle_action(101, push_action, self.world)

        # Verificar impulso estilo Minecraft (+Y pop y empuje horizontal)
        self.assertAlmostEqual(ent2.vel_y, 4.2)
        self.assertAlmostEqual(ent2.vel_x, 8.0)

        # Simular que P2 es arrojado fuera de la tarima (Zócalo / Suelo inferior)
        ent2.pos_y = 400.80  # < 401.10 m (límite de caída)
        game.tick(0.033, self.world)

        # P2 debe quedar eliminado y P1 debe ganar
        self.assertEqual(participants[1].state, ParticipantState.ELIMINATED)
        self.assertEqual(game.state, MinigameState.RESTORATION)
        self.assertEqual(game.winner_id, 101)

        # Verificar restauración espacial garantizada en el mapa abierto
        self.assertEqual(ent1.pos_x, 50.0)
        self.assertEqual(ent2.pos_x, 60.0)


class TestLasTraesMinigame(unittest.TestCase):
    """Pruebas de Las Traes (roña, transferencias e inmunidad)."""

    def setUp(self):
        self.world = SharedWorld()
        self.p1_ent = DynamicEntity(entity_id=201, pos_x=0.0, pos_y=401.80, pos_z=0.0)
        self.p2_ent = DynamicEntity(entity_id=202, pos_x=10.0, pos_y=401.80, pos_z=0.0)
        self.world.upsert_entity(self.p1_ent)
        self.world.upsert_entity(self.p2_ent)

    def test_las_traes_tag_transfer_and_immunity(self):
        game = LasTraesMinigame()
        participants = [
            Participant(entity_id=201, session_id=1, display_name="Axel"),
            Participant(entity_id=202, session_id=2, display_name="Eli"),
        ]
        game.start_staging(participants, self.world)
        game.tick(3.1, self.world)

        self.assertEqual(game.state, MinigameState.ACTIVE)
        tagger_id = game.current_tagger_id
        victim_id = 202 if tagger_id == 201 else 201

        # Acercar al tagger a la víctima a menos de 1.85m
        tagger_ent = self.world.get_entity(tagger_id)
        victim_ent = self.world.get_entity(victim_id)
        tagger_ent.pos_x = victim_ent.pos_x + 0.5
        tagger_ent.pos_y = victim_ent.pos_y
        tagger_ent.pos_z = victim_ent.pos_z

        # El tick autoritativo detecta el contacto y transfiere el tag
        game.tick(0.033, self.world)

        self.assertEqual(game.current_tagger_id, victim_id)
        # El antiguo tagger ahora tiene inmunidad
        self.assertTrue(game.contact_evaluator.has_immunity(tagger_id))


class TestQuemadosMinigame(unittest.TestCase):
    """Pruebas de Quemados (lanzamiento balístico y eliminación)."""

    def setUp(self):
        self.world = SharedWorld()
        self.p1_ent = DynamicEntity(entity_id=301, pos_x=-5.0, pos_y=401.80, pos_z=0.0)
        self.p2_ent = DynamicEntity(entity_id=302, pos_x=5.0, pos_y=401.80, pos_z=0.0)
        self.world.upsert_entity(self.p1_ent)
        self.world.upsert_entity(self.p2_ent)

    def test_ball_throw_and_elimination(self):
        game = QuemadosMinigame()
        participants = [
            Participant(entity_id=301, session_id=1, display_name="Axel"),
            Participant(entity_id=302, session_id=2, display_name="Eli"),
        ]
        game.start_staging(participants, self.world)
        game.tick(3.1, self.world)

        # Reposicionar intencionalmente para la prueba de balística directa
        self.p1_ent.pos_x = -5.0
        self.p1_ent.pos_z = 0.0
        self.p2_ent.pos_x = 5.0
        self.p2_ent.pos_z = 0.0

        # P1 lanza pelota hacia +X (directo a P2)
        throw_action = {
            "action_type": 4,
            "dir": (1.0, 0.0, 0.0),
        }
        game.handle_action(301, throw_action, self.world)
        self.assertEqual(len(game.ballistic_evaluator.balls), 1)

        # Simular avance del tiempo hasta que la pelota llegue a P2 (~10m / 18m/s ~= 0.55s)
        # En ticks sucesivos de 30Hz:
        for _ in range(25):
            if game.state != MinigameState.ACTIVE:
                break
            game.tick(0.033, self.world)

        # P2 debe haber sido eliminado por el impacto y P1 coronado vencedor
        self.assertEqual(participants[1].state, ParticipantState.ELIMINATED)
        self.assertEqual(game.winner_id, 301)


class TestMinigameOrchestratorIntegration(unittest.TestCase):
    """Pruebas de integración del Orquestador con SQLite y sesiones de red."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_minigames.db")
        self.db_mgr = DatabaseManager(self.db_path)
        self.auth_mgr = ServerAuthManager(self.db_mgr)
        self.sess_mgr = SessionManager()
        self.world = SharedWorld()

        # Registrar dos jugadores en la base de datos
        _, self.prof1, _ = self.auth_mgr.authenticate_or_register("u1:sec1:Axel")
        _, self.prof2, _ = self.auth_mgr.authenticate_or_register("u2:sec2:Eli")

        self.sess1 = self.sess_mgr.create_or_renew_session(
            addr=("127.0.0.1", 10001),
            auth_token="u1:sec1:Axel",
            player_uuid=self.prof1["player_uuid"],
            display_name="Axel",
        )
        self.sess2 = self.sess_mgr.create_or_renew_session(
            addr=("127.0.0.1", 10002),
            auth_token="u2:sec2:Eli",
            player_uuid=self.prof2["player_uuid"],
            display_name="Eli",
        )

        ent1 = DynamicEntity(entity_id=self.sess1.player_entity_id, pos_x=10.0, pos_y=400.0, pos_z=10.0)
        ent2 = DynamicEntity(entity_id=self.sess2.player_entity_id, pos_x=20.0, pos_y=400.0, pos_z=20.0)
        self.world.upsert_entity(ent1)
        self.world.upsert_entity(ent2)

        self.broadcasted_events = []
        self.orchestrator = MinigameOrchestrator(
            auth_manager=self.auth_mgr,
            session_manager=self.sess_mgr,
            broadcast_callback=self.broadcasted_events.append,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_summon_join_and_sqlite_reward_flow(self):
        # 1. P1 convoca Mi Kiosko (game_id=1)
        summon_data = {"game_id": 1, "max_players": 2, "mode": 0, "arena_id": 1}
        ok = self.orchestrator.handle_summon(self.sess1, summon_data, self.world)
        self.assertTrue(ok)
        self.assertIsNotNone(self.orchestrator.pending_summon)

        # 2. P2 acepta la invitación
        join_data = {"game_id": 1, "accepted": True}
        ok = self.orchestrator.handle_join(self.sess2, join_data, self.world)
        self.assertTrue(ok)

        # Como se alcanzó el cupo (2/2), la partida debe arrancar automáticamente en STAGING
        self.assertTrue(self.orchestrator.is_minigame_running())
        self.assertEqual(self.orchestrator.active_game.state, MinigameState.STAGING)

        # 3. Avanzar STAGING a ACTIVE
        self.orchestrator.tick(3.1, self.world)
        self.assertEqual(self.orchestrator.active_game.state, MinigameState.ACTIVE)

        # 4. P2 cae fuera de la tarima
        ent2 = self.world.get_entity(self.sess2.player_entity_id)
        ent2.pos_y = 399.0
        self.orchestrator.tick(0.033, self.world)

        # 5. La partida concluyó: verificar que el saldo de Pesos en SQLite aumentó
        self.assertFalse(self.orchestrator.is_minigame_running())

        # P1 (ganador) debe haber recibido +50 Pesos (saldo base 50 + 50 = 100)
        bal1 = self.auth_mgr.get_player_balance(self.prof1["player_uuid"])
        self.assertEqual(bal1, 100)

        # P2 (participante / 2do lugar) debe haber recibido +30 Pesos (saldo base 50 + 30 = 80)
        bal2 = self.auth_mgr.get_player_balance(self.prof2["player_uuid"])
        self.assertEqual(bal2, 80)


if __name__ == "__main__":
    unittest.main()
