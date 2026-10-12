"""Clase Base y Motor Reutilizable para todos los Minijuegos en Tecate Simulator."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

from server.minigames.fsm import MinigameState
from server.minigames.participant import Participant, ParticipantRole, ParticipantSnapshot, ParticipantState
from server.protocol.codec import EventPayload

if TYPE_CHECKING:
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class BaseMinigame(ABC):
    """Clase base abstracta que define las invariantes del motor de minijuegos."""

    def __init__(
        self,
        game_id: int,
        name: str,
        min_players: int = 2,
        max_players: int = 8,
        staging_duration: float = 3.0,
        max_game_duration: float = 60.0,
    ) -> None:
        self.game_id = game_id
        self.name = name
        self.min_players = min_players
        self.max_players = max_players
        self.staging_duration = staging_duration
        self.max_game_duration = max_game_duration

        self.state: MinigameState = MinigameState.IDLE
        self.participants: dict[int, Participant] = {}
        self.staging_timer: float = 0.0
        self.game_timer: float = 0.0
        self._elimination_counter: int = 0
        self.winner_id: int = 0

        # Callbacks inyectados por el orquestador
        self.on_event_emit: Callable[[EventPayload], None] | None = None
        self.on_game_ended: Callable[[BaseMinigame], None] | None = None

    @abstractmethod
    def get_spawn_points(self, count: int) -> list[tuple[float, float, float, float]]:
        """Calcula las coordenadas de inicio `(x, y, z, yaw)` para cada participante."""
        pass

    @abstractmethod
    def on_game_tick(self, dt: float, world: SharedWorld) -> None:
        """Ciclo autoritativo de reglas y físicas a 30 Hz ejecutado durante MinigameState.ACTIVE."""
        pass

    @abstractmethod
    def handle_action(self, sender_entity_id: int, action_data: dict, world: SharedWorld) -> None:
        """Procesa una acción contextual de juego recibida vía MINIGAME_ACTION."""
        pass

    @abstractmethod
    def check_victory_conditions(self, world: SharedWorld) -> bool:
        """Evalúa si se alcanzó la condición de victoria para concluir la partida."""
        pass

    @abstractmethod
    def handle_timeout(self, world: SharedWorld) -> None:
        """Gestiona la conclusión de la partida cuando expira el temporizador máximo."""
        pass

    def start_staging(self, participants: list[Participant], world: SharedWorld) -> None:
        """Inicia la cuenta regresiva, toma snapshots espaciales y posiciona a los avatares."""
        self.participants.clear()
        self.staging_timer = 0.0
        self.game_timer = 0.0
        self._elimination_counter = 0
        self.winner_id = 0

        spawn_points = self.get_spawn_points(len(participants))
        participant_start_payloads = []

        for idx, p in enumerate(participants):
            self.participants[p.entity_id] = p
            p.state = ParticipantState.ACTIVE
            p.score = 0
            p.coins_rewarded = 0
            p.elimination_order = 0

            # 1. Snapshot espacial del jugador en SharedWorld
            ent = world.get_entity(p.entity_id)
            if ent:
                p.snapshot = ParticipantSnapshot(
                    pos_x=ent.pos_x,
                    pos_y=ent.pos_y,
                    pos_z=ent.pos_z,
                    yaw=ent.yaw,
                )
            else:
                p.snapshot = ParticipantSnapshot(-6.684, 401.80, 2.688, 0.0)

            # 2. Asignar punto de spawn
            sx, sy, sz, syaw = spawn_points[idx] if idx < len(spawn_points) else (-6.684, 401.80, 2.688, 0.0)
            if ent:
                ent.pos_x = sx
                ent.pos_y = sy
                ent.pos_z = sz
                ent.yaw = syaw
                ent.vel_x = 0.0
                ent.vel_y = 0.0
                ent.vel_z = 0.0
                world.upsert_entity(ent)

            participant_start_payloads.append({
                "entity_id": p.entity_id,
                "spawn_x": sx,
                "spawn_y": sy,
                "spawn_z": sz,
                "spawn_yaw": syaw,
            })

        self.state = MinigameState.STAGING

        # Emitir evento fiable MINIGAME_START
        if self.on_event_emit:
            start_event = EventPayload.create_minigame_start(
                entity_id=0,
                game_id=self.game_id,
                countdown_seconds=int(self.staging_duration),
                participants=participant_start_payloads,
            )
            self.on_event_emit(start_event)

        logger.info("[MinigameEngine] Minijuego '%s' (ID=%d) en STAGING con %d jugadores.", self.name, self.game_id, len(participants))

    def tick(self, dt: float, world: SharedWorld) -> None:
        """Avanza la máquina de estados en cada tick de simulación (30 Hz)."""
        if self.state == MinigameState.STAGING:
            self.staging_timer += dt
            if self.staging_timer >= self.staging_duration:
                self.state = MinigameState.ACTIVE
                self.on_game_started()
                logger.info("[MinigameEngine] Minijuego '%s' ahora está ACTIVE.", self.name)

        elif self.state == MinigameState.ACTIVE:
            self.game_timer += dt
            self.on_game_tick(dt, world)

            if self.check_victory_conditions(world):
                return

            if self.game_timer >= self.max_game_duration:
                logger.info("[MinigameEngine] Tiempo límite alcanzado (%.1fs) en '%s'.", self.max_game_duration, self.name)
                self.handle_timeout(world)

    def on_game_started(self) -> None:
        """Hook opcional invocado al pasar de STAGING a ACTIVE."""
        pass

    def eliminate_participant(self, entity_id: int, reason: int) -> None:
        """Decreta la eliminación autoritativa de un participante."""
        p = self.participants.get(entity_id)
        if not p or p.state != ParticipantState.ACTIVE:
            return

        self._elimination_counter += 1
        p.state = ParticipantState.ELIMINATED
        p.elimination_order = self._elimination_counter

        logger.info(
            "[MinigameEngine] Participante %d eliminado en '%s' (motivo=%d, orden=%d)",
            entity_id,
            self.name,
            reason,
            p.elimination_order,
        )

        if self.on_event_emit:
            elim_event = EventPayload.create_minigame_eliminate(
                entity_id=0,
                game_id=self.game_id,
                eliminated_entity_id=entity_id,
                reason=reason,
            )
            self.on_event_emit(elim_event)

    def get_active_participants(self) -> list[Participant]:
        """Devuelve la lista de participantes aún vivos."""
        return [p for p in self.participants.values() if p.state == ParticipantState.ACTIVE]

    def finish_game(self, winner_id: int, world: SharedWorld) -> None:
        """Finaliza la partida, asigna recompensas y restaura a los jugadores en el mapa."""
        self.state = MinigameState.RESOLUTION
        self.winner_id = winner_id

        # Asignar estado de ganador
        if winner_id in self.participants:
            self.participants[winner_id].state = ParticipantState.WINNER

        # Calcular ranking de podio
        # Ganador primero, luego orden inverso de eliminación (el que cayó al final queda 2do)
        sorted_participants = sorted(
            self.participants.values(),
            key=lambda p: (
                0 if p.entity_id == winner_id else 1,
                -p.elimination_order if p.elimination_order > 0 else -999,
                -p.score,
            ),
        )

        rankings = []
        for idx, p in enumerate(sorted_participants):
            coins = 15  # Participación base
            if idx == 0:
                coins = 50  # 1er Lugar
            elif idx == 1:
                coins = 30  # 2do Lugar
            elif idx == 2:
                coins = 20  # 3er Lugar

            p.coins_rewarded = coins
            rankings.append({
                "entity_id": p.entity_id,
                "score": p.score,
                "coins_rewarded": coins,
            })

        logger.info("[MinigameEngine] Minijuego '%s' finalizado. Ganador: %d. Podio: %s", self.name, winner_id, rankings)

        # Emitir MINIGAME_END
        if self.on_event_emit:
            end_event = EventPayload.create_minigame_end(
                entity_id=0,
                game_id=self.game_id,
                winner_entity_id=winner_id,
                rankings=rankings,
            )
            self.on_event_emit(end_event)

        # 4. Restauración espacial garantizada
        self.restore_participants(world)
        self.state = MinigameState.RESTORATION

        if self.on_game_ended:
            self.on_game_ended(self)

    def restore_participants(self, world: SharedWorld) -> None:
        """Restaura las coordenadas exactas previas a la partida en SharedWorld."""
        for p in self.participants.values():
            ent = world.get_entity(p.entity_id)
            if ent:
                ent.pos_x = p.snapshot.pos_x
                ent.pos_y = p.snapshot.pos_y
                ent.pos_z = p.snapshot.pos_z
                ent.yaw = p.snapshot.yaw
                ent.vel_x = 0.0
                ent.vel_y = 0.0
                ent.vel_z = 0.0
                world.upsert_entity(ent)
                logger.info(
                    "[MinigameEngine] Restaurada entidad %d a (%.3f, %.3f, %.3f, yaw=%.1f)",
                    p.entity_id,
                    p.snapshot.pos_x,
                    p.snapshot.pos_y,
                    p.snapshot.pos_z,
                    p.snapshot.yaw,
                )
