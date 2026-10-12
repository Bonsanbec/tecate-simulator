"""Minijuego 2: 'Las Traes' (Roña Urbana, Persecución en Parque Hidalgo y Anti-Camping)."""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

from server.minigames.base import BaseMinigame
from server.minigames.evaluators.anti_camping import ActivityAntiCampingEvaluator
from server.minigames.evaluators.contact import ProximityContactEvaluator
from server.minigames.participant import ParticipantRole, ParticipantState
from server.protocol.codec import EventPayload

if TYPE_CHECKING:
    from server.core.world import SharedWorld


class LasTraesMinigame(BaseMinigame):
    """Juego de persecución y agilidad en el perímetro de Parque Miguel Hidalgo."""

    PARQUE_CENTER_X = -6.684
    PARQUE_CENTER_Y = 401.80
    PARQUE_CENTER_Z = 2.688

    def __init__(self) -> None:
        super().__init__(
            game_id=2,
            name="Las Traes",
            min_players=2,
            max_players=8,
            staging_duration=3.0,
            max_game_duration=75.0,
        )
        self.contact_evaluator = ProximityContactEvaluator(contact_threshold=1.85, default_immunity_duration=2.0)
        self.anti_camping_evaluator = ActivityAntiCampingEvaluator(window_seconds=3.5, min_speed_threshold=0.5)
        self.current_tagger_id: int = 0

    def get_spawn_points(self, count: int) -> list[tuple[float, float, float, float]]:
        """Distribuye a los participantes por distintas áreas del Parque Hidalgo."""
        # Puntos de spawn emblemáticos en el parque (jardineras, bancas, pasillos)
        offsets = [
            (0.0, 10.0, 180.0),
            (12.0, 0.0, 270.0),
            (-12.0, 0.0, 90.0),
            (0.0, -12.0, 0.0),
            (8.0, 8.0, 225.0),
            (-8.0, 8.0, 135.0),
            (8.0, -8.0, 315.0),
            (-8.0, -8.0, 45.0),
        ]
        spawns = []
        for i in range(count):
            ox, oz, yaw = offsets[i % len(offsets)]
            spawns.append((
                self.PARQUE_CENTER_X + ox,
                self.PARQUE_CENTER_Y,
                self.PARQUE_CENTER_Z + oz,
                yaw,
            ))
        return spawns

    def on_game_started(self) -> None:
        """Designa al portador inicial del tag de forma pseudoaleatoria o equilibrada."""
        active_ids = list(self.participants.keys())
        if not active_ids:
            return

        self.current_tagger_id = random.choice(active_ids)
        for p in self.participants.values():
            p.custom_data["tag_time"] = 0.0
            if p.entity_id == self.current_tagger_id:
                p.role = ParticipantRole.ASYMMETRIC_LEADER
            else:
                p.role = ParticipantRole.FFA

        # Anunciar al portador inicial mediante MINIGAME_ACTION (ActionType = 3: Tag Pass)
        if self.on_event_emit:
            ev = EventPayload.create_minigame_action(
                entity_id=0,
                action_type=3,  # TAG_ASSIGN
                target_entity_id=self.current_tagger_id,
                param_float=float(self.max_game_duration),
            )
            self.on_event_emit(ev)

    def on_game_tick(self, dt: float, world: SharedWorld) -> None:
        """Actualiza el árbitro de proximidad, anti-camping e inmunidad."""
        self.contact_evaluator.update(dt)
        now = time.time()

        # 1. Acumular tiempo como portador del tag
        tagger_p = self.participants.get(self.current_tagger_id)
        if tagger_p:
            tagger_p.custom_data["tag_time"] = tagger_p.custom_data.get("tag_time", 0.0) + dt

        tagger_ent = world.get_entity(self.current_tagger_id)
        if not tagger_ent:
            return

        tagger_pos = (tagger_ent.pos_x, tagger_ent.pos_y, tagger_ent.pos_z)

        # 2. Análisis anti-campeo y contacto para cada participante activo
        for p in self.get_active_participants():
            ent = world.get_entity(p.entity_id)
            if not ent:
                continue

            # Anti-camping
            self.anti_camping_evaluator.record_position(p.entity_id, now, ent.pos_x, ent.pos_z)
            if self.anti_camping_evaluator.is_camping(p.entity_id, now):
                if p.entity_id != self.current_tagger_id:
                    # Penalización por campeo: transferencia forzada del tag al que no se mueve
                    self._transfer_tag(p.entity_id, is_penalty=True)
                    return

            # Contacto si es objetivo del tagger
            if p.entity_id != self.current_tagger_id:
                target_pos = (ent.pos_x, ent.pos_y, ent.pos_z)
                if self.contact_evaluator.check_contact(tagger_pos, target_pos, p.entity_id):
                    self._transfer_tag(p.entity_id, is_penalty=False)
                    return

    def _transfer_tag(self, new_tagger_id: int, is_penalty: bool = False) -> None:
        """Transfiere el tag, otorga inmunidad al cedente y notifica a clientes."""
        prev_tagger_id = self.current_tagger_id
        self.current_tagger_id = new_tagger_id

        # Otorgar 2.0s de inmunidad al jugador que entregó el tag
        self.contact_evaluator.set_immunity(prev_tagger_id, 2.0)
        self.anti_camping_evaluator.reset_entity(prev_tagger_id)
        self.anti_camping_evaluator.reset_entity(new_tagger_id)

        # Actualizar roles
        if prev_tagger_id in self.participants:
            self.participants[prev_tagger_id].role = ParticipantRole.FFA
            if not is_penalty:
                self.participants[prev_tagger_id].score += 15  # Recompensa por pasar la roña

        if new_tagger_id in self.participants:
            self.participants[new_tagger_id].role = ParticipantRole.ASYMMETRIC_LEADER

        if self.on_event_emit:
            ev = EventPayload.create_minigame_action(
                entity_id=prev_tagger_id,
                action_type=3,  # TAG_PASS
                target_entity_id=new_tagger_id,
                param_float=2.0 if not is_penalty else 0.0,  # Duración de inmunidad
            )
            self.on_event_emit(ev)

    def handle_action(self, sender_entity_id: int, action_data: dict, world: SharedWorld) -> None:
        """Las Traes no requiere inputs manuales de golpe; el toque es cinemático y volumétrico."""
        pass

    def check_victory_conditions(self, world: SharedWorld) -> bool:
        """Si todos menos uno se desconectan, concluir prematuramente."""
        active = self.get_active_participants()
        if len(active) < 2 and len(self.participants) >= 2:
            winner = active[0].entity_id if active else 0
            self.finish_game(winner, world)
            return True
        return False

    def handle_timeout(self, world: SharedWorld) -> None:
        """Al expirar los 75s, el jugador con menor tiempo portando el tag es el ganador."""
        active = self.get_active_participants()
        if not active:
            self.finish_game(0, world)
            return

        # El que porta el tag al final pierde automáticamente
        loser_id = self.current_tagger_id
        self.eliminate_participant(loser_id, reason=3)  # Reason 3 = Timeout Tagger

        # Ordenar por menor tiempo como tagger
        survivors = [p for p in active if p.entity_id != loser_id]
        if survivors:
            winner = min(survivors, key=lambda p: p.custom_data.get("tag_time", 9999.0))
            self.finish_game(winner.entity_id, world)
        else:
            self.finish_game(0, world)
