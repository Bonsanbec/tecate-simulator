"""Minijuego 3: 'Quemados' (Balón Prisionero Callejero con Balística y Rebotes)."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from server.minigames.base import BaseMinigame
from server.minigames.evaluators.ballistic import BallisticHitEvaluator
from server.minigames.participant import ParticipantState
from server.protocol.codec import EventPayload

if TYPE_CHECKING:
    from server.core.world import SharedWorld


class QuemadosMinigame(BaseMinigame):
    """Partida de balón prisionero con pelotas balísticas rebotantes en Parque Hidalgo."""

    EXPLANADA_CENTER_X = -6.684
    EXPLANADA_CENTER_Y = 401.80
    EXPLANADA_CENTER_Z = 2.688
    THROW_COOLDOWN = 1.25

    def __init__(self) -> None:
        super().__init__(
            game_id=3,
            name="Quemados",
            min_players=2,
            max_players=8,
            staging_duration=3.0,
            max_game_duration=90.0,
        )
        self.ballistic_evaluator = BallisticHitEvaluator(
            gravity=9.8,
            restitution=0.70,
            floor_y=self.EXPLANADA_CENTER_Y,
            capsule_radius=0.45,
            capsule_height=1.80,
        )

    def get_spawn_points(self, count: int) -> list[tuple[float, float, float, float]]:
        """Posiciona a los jugadores en dos líneas opuestas de 4 jugadores mirándose de frente."""
        spawns = []
        half = max(count // 2, 1)

        for i in range(count):
            is_team_b = (i >= half)
            team_index = i if not is_team_b else (i - half)
            offset_z = (team_index - half / 2.0) * 3.5

            if not is_team_b:
                # Equipo A (Lado Oeste, mirando hacia +X)
                sx = self.EXPLANADA_CENTER_X - 10.0
                sz = self.EXPLANADA_CENTER_Z + offset_z
                yaw = 90.0
            else:
                # Equipo B (Lado Este, mirando hacia -X)
                sx = self.EXPLANADA_CENTER_X + 10.0
                sz = self.EXPLANADA_CENTER_Z + offset_z
                yaw = 270.0

            spawns.append((sx, self.EXPLANADA_CENTER_Y, sz, yaw))

        return spawns

    def handle_action(self, sender_entity_id: int, action_data: dict, world: SharedWorld) -> None:
        """Procesa el lanzamiento balístico de una pelota por un jugador."""
        if self.state != self.state.ACTIVE:
            return

        action_type = action_data.get("action_type", 0)
        if action_type != 4:  # 4 = TIRO DE PELOTA
            return

        p = self.participants.get(sender_entity_id)
        if not p or p.state != ParticipantState.ACTIVE:
            return

        now = time.time()
        last_throw = p.custom_data.get("last_throw_time", 0.0)
        if (now - last_throw) < self.THROW_COOLDOWN:
            return  # Cooldown activo

        p.custom_data["last_throw_time"] = now

        ent = world.get_entity(sender_entity_id)
        if not ent:
            return

        origin = (ent.pos_x, ent.pos_y, ent.pos_z)
        dir_tuple = action_data.get("dir", (0.0, 0.0, 1.0))

        # Instanciar proyectil balístico en el evaluador
        ball = self.ballistic_evaluator.spawn_ball(
            thrower_id=sender_entity_id,
            origin=origin,
            direction=dir_tuple,
            speed=18.0,
        )

        # Retransmitir a clientes para spawn de pelota sincronizada
        if self.on_event_emit:
            ev = EventPayload.create_minigame_action(
                entity_id=sender_entity_id,
                action_type=4,  # BALL_THROW
                target_entity_id=ball.ball_id,
                param_float=18.0,
                dir_vec=dir_tuple,
            )
            self.on_event_emit(ev)

    def on_game_tick(self, dt: float, world: SharedWorld) -> None:
        """Avanza la balística y detecta eliminaciones directas por impacto de pelota."""
        active_participants = self.get_active_participants()
        targets = []
        for p in active_participants:
            ent = world.get_entity(p.entity_id)
            if ent:
                targets.append((p.entity_id, ent.pos_x, ent.pos_y, ent.pos_z))

        hits = self.ballistic_evaluator.update(dt, targets)
        for hit_entity_id, ball in hits:
            # 2 = Eliminado por impacto balístico
            self.eliminate_participant(hit_entity_id, reason=2)

            if ball.thrower_id in self.participants:
                self.participants[ball.thrower_id].score += 25

    def check_victory_conditions(self, world: SharedWorld) -> bool:
        """Termina cuando queda un único superviviente en pie."""
        active = self.get_active_participants()
        if len(active) <= 1:
            winner = active[0].entity_id if active else 0
            self.finish_game(winner, world)
            return True
        return False

    def handle_timeout(self, world: SharedWorld) -> None:
        """Al expirar los 90s, gana quien tenga mayor puntuación."""
        active = self.get_active_participants()
        if not active:
            self.finish_game(0, world)
            return

        best = max(active, key=lambda p: p.score)
        self.finish_game(best.entity_id, world)
