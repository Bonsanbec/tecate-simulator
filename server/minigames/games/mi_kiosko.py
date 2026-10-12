"""Minijuego 1: 'Mi Kiosko' (All-vs-All Empujones, Bloqueos y Ring-Out en Parque Hidalgo)."""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from server.minigames.arena import CylinderArena
from server.minigames.base import BaseMinigame
from server.minigames.evaluators.spatial import SpatialBoundaryEvaluator
from server.minigames.participant import ParticipantState
from server.protocol.codec import EventPayload

if TYPE_CHECKING:
    from server.core.world import SharedWorld


class MiKioskoMinigame(BaseMinigame):
    """Batalla campal en la plataforma octagonal del Kiosko de Parque Hidalgo."""

    KIOSKO_CENTER_X = -6.684
    KIOSKO_CENTER_Y = 401.80
    KIOSKO_CENTER_Z = 2.688
    KIOSKO_RADIUS = 4.80
    KIOSKO_FLOOR_Y = 401.80
    KIOSKO_DROP_LIMIT_Y = 401.10

    def __init__(self) -> None:
        super().__init__(
            game_id=1,
            name="Mi Kiosko",
            min_players=2,
            max_players=8,
            staging_duration=3.0,
            max_game_duration=90.0,
        )
        self.arena = CylinderArena(
            center_x=self.KIOSKO_CENTER_X,
            center_y=self.KIOSKO_CENTER_Y,
            center_z=self.KIOSKO_CENTER_Z,
            radius=self.KIOSKO_RADIUS,
            min_y=self.KIOSKO_DROP_LIMIT_Y,
            max_y=420.0,
        )
        self.spatial_evaluator = SpatialBoundaryEvaluator(self.arena)

    def get_spawn_points(self, count: int) -> list[tuple[float, float, float, float]]:
        """Distribuye a los participantes en círculo de 2.5m de radio mirando hacia el centro."""
        spawns = []
        radius = 2.50
        angle_step = (2.0 * math.pi) / max(count, 1)

        for i in range(count):
            angle = i * angle_step
            sx = self.KIOSKO_CENTER_X + math.cos(angle) * radius
            sz = self.KIOSKO_CENTER_Z + math.sin(angle) * radius
            sy = self.KIOSKO_FLOOR_Y

            # Yaw orientado hacia el centro del Kiosko
            dx = self.KIOSKO_CENTER_X - sx
            dz = self.KIOSKO_CENTER_Z - sz
            yaw = math.degrees(math.atan2(-dx, -dz))

            spawns.append((sx, sy, sz, yaw))

        return spawns

    def on_game_tick(self, dt: float, world: SharedWorld) -> None:
        """Verifica cada tick si algún avatar cayó o fue expulsado de la tarima."""
        for p in self.get_active_participants():
            ent = world.get_entity(p.entity_id)
            if not ent:
                continue

            is_inside, reason = self.spatial_evaluator.check_boundary(ent.pos_x, ent.pos_y, ent.pos_z)
            if not is_inside:
                # 1 = Ring-Out / Caída de plataforma
                self.eliminate_participant(p.entity_id, reason=1)

    def handle_action(self, sender_entity_id: int, action_data: dict, world: SharedWorld) -> None:
        """Procesa empujones con retroceso estilo Minecraft (+Y pop) y parry."""
        if self.state != self.state.ACTIVE:
            return

        action_type = action_data.get("action_type", 0)
        now = time.time()

        if action_type == 1:  # EMPUJÓN / PUNCH
            target_id = action_data.get("target_entity_id", 0)
            if target_id not in self.participants:
                return

            target_p = self.participants[target_id]
            if target_p.state != ParticipantState.ACTIVE:
                return

            attacker_ent = world.get_entity(sender_entity_id)
            target_ent = world.get_entity(target_id)
            if not attacker_ent or not target_ent:
                return

            # Distancia de alcance de golpe
            dx = target_ent.pos_x - attacker_ent.pos_x
            dy = target_ent.pos_y - attacker_ent.pos_y
            dz = target_ent.pos_z - attacker_ent.pos_z
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist > 3.2:  # Alcance máximo de empujón
                return

            # Comprobar si el objetivo estaba haciendo bloqueo oportuno (Parry)
            target_parry_until = target_p.custom_data.get("parry_until", 0.0)
            if now < target_parry_until:
                # ¡Parry exitoso! El atacante es rechazado
                attacker_ent.vel_x = -dx * 4.0
                attacker_ent.vel_y = 3.5
                attacker_ent.vel_z = -dz * 4.0
                world.upsert_entity(attacker_ent)

                target_p.score += 25
                if self.on_event_emit:
                    ev = EventPayload.create_minigame_action(
                        entity_id=target_id,
                        action_type=2,  # PARRY_SUCCESS
                        target_entity_id=sender_entity_id,
                        param_float=10.0,
                        dir_vec=(-dx, 1.0, -dz),
                    )
                    self.on_event_emit(ev)
                return

            # Empujón exitoso estilo Minecraft: retroceso horizontal + salto involuntario +Y
            dir_tuple = action_data.get("dir", (0.0, 0.0, 0.0))
            push_dir_x, _, push_dir_z = dir_tuple
            mag = math.sqrt(push_dir_x * push_dir_x + push_dir_z * push_dir_z)
            if mag > 0.001:
                push_dir_x /= mag
                push_dir_z /= mag
            else:
                push_dir_x, push_dir_z = (dx / max(dist, 0.001), dz / max(dist, 0.001))

            force_h = float(action_data.get("param_float", 7.5))
            if force_h <= 0.0:
                force_h = 7.5
            force_v = 4.2  # Salto vertical slapstick

            target_ent.vel_x = push_dir_x * force_h
            target_ent.vel_y = force_v
            target_ent.vel_z = push_dir_z * force_h
            world.upsert_entity(target_ent)

            if sender_entity_id in self.participants:
                self.participants[sender_entity_id].score += 10

            # Retransmitir a clientes para flash rojo y partículas de impacto
            if self.on_event_emit:
                ev = EventPayload.create_minigame_action(
                    entity_id=sender_entity_id,
                    action_type=1,
                    target_entity_id=target_id,
                    param_float=force_h,
                    dir_vec=(push_dir_x, force_v, push_dir_z),
                )
                self.on_event_emit(ev)

        elif action_type == 2:  # BLOQUEO / PARRY
            sender_p = self.participants.get(sender_entity_id)
            if sender_p:
                sender_p.custom_data["parry_until"] = now + 0.65  # Ventana de 650 ms de bloqueo

    def check_victory_conditions(self, world: SharedWorld) -> bool:
        """La partida termina cuando queda a lo sumo un participante activo."""
        active = self.get_active_participants()
        if len(active) <= 1:
            winner = active[0].entity_id if active else 0
            self.finish_game(winner, world)
            return True
        return False

    def handle_timeout(self, world: SharedWorld) -> None:
        """Al vencer el temporizador, gana quien acumuló mayor puntuación o está más cerca del centro."""
        active = self.get_active_participants()
        if not active:
            self.finish_game(0, world)
            return

        best_p = max(active, key=lambda p: p.score)
        self.finish_game(best_p.entity_id, world)
