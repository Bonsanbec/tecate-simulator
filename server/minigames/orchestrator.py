"""Orquestador Central de Minijuegos para Tecate Simulator (Servidor Autoritativo TKT/1)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Type

from server.minigames.base import BaseMinigame
from server.minigames.fsm import MinigameState
from server.minigames.games.las_traes import LasTraesMinigame
from server.minigames.games.mi_kiosko import MiKioskoMinigame
from server.minigames.games.quemados import QuemadosMinigame
from server.minigames.participant import Participant, ParticipantRole
from server.protocol.codec import EventPayload

if TYPE_CHECKING:
    from server.core.auth_manager import ServerAuthManager
    from server.core.session import ClientSession
    from server.core.session_manager import SessionManager
    from server.core.world import SharedWorld

logger = logging.getLogger(__name__)


class MinigameOrchestrator:
    """Gestiona el catálogo de minijuegos, convocatorias, lobbys y persistencia de recompensas."""

    def __init__(
        self,
        auth_manager: ServerAuthManager,
        session_manager: SessionManager,
        broadcast_callback: Callable[[EventPayload], None],
    ) -> None:
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self.broadcast_callback = broadcast_callback

        # Catálogo de minijuegos registrados
        self.game_catalog: dict[int, Type[BaseMinigame]] = {
            1: MiKioskoMinigame,
            2: LasTraesMinigame,
            3: QuemadosMinigame,
        }

        self.active_game: BaseMinigame | None = None
        self.pending_summon: dict | None = None
        self.pending_participants: dict[int, Participant] = {}
        self.summon_timer: float = 0.0
        self.summon_timeout: float = 12.0

    def is_minigame_running(self) -> bool:
        """Indica si hay una partida en curso o en staging."""
        return self.active_game is not None and self.active_game.state in (MinigameState.STAGING, MinigameState.ACTIVE)

    def handle_summon(self, sender_session: ClientSession, summon_data: dict, world: SharedWorld) -> bool:
        """Procesa una petición de convocatoria (MINIGAME_SUMMON)."""
        if self.is_minigame_running() or self.pending_summon is not None:
            logger.warning("[Orquestador] Rechazando SUMMON de jugador %d: ya hay un minijuego en curso.", sender_session.player_entity_id)
            return False

        game_id = summon_data.get("game_id", 0)
        if game_id not in self.game_catalog:
            logger.warning("[Orquestador] ID de minijuego desconocido: %d", game_id)
            return False

        max_players = summon_data.get("max_players", 8)
        if max_players <= 0:
            max_players = 8

        self.pending_summon = {
            "game_id": game_id,
            "host_entity_id": sender_session.player_entity_id,
            "max_players": max_players,
            "mode": summon_data.get("mode", 0),
            "arena_id": summon_data.get("arena_id", 1),
        }
        self.pending_participants.clear()
        self.summon_timer = 0.0

        # El anfitrión entra automáticamente a la lista de participantes
        host_participant = Participant(
            entity_id=sender_session.player_entity_id,
            session_id=sender_session.session_id,
            player_uuid=sender_session.player_uuid,
            display_name=sender_session.display_name,
            role=ParticipantRole.FFA,
        )
        self.pending_participants[sender_session.player_entity_id] = host_participant

        logger.info(
            "[Orquestador] Convocatoria abierta para Minijuego %d por jugador %d ('%s')",
            game_id,
            sender_session.player_entity_id,
            sender_session.display_name,
        )

        # Difundir la invitación a todos los clientes conectados
        ev = EventPayload.create_minigame_summon(
            entity_id=sender_session.player_entity_id,
            game_id=game_id,
            mode=self.pending_summon["mode"],
            max_players=max_players,
            arena_id=self.pending_summon["arena_id"],
        )
        self.broadcast_callback(ev)

        # Si solo hay 1 sesión o se alcanzó el máximo, verificar inicio inmediato
        if len(self.session_manager) <= 1:
            # En modo dev o solitario, permitir arrancar si la clase lo admite o para pruebas
            pass

        return True

    def handle_join(self, sender_session: ClientSession, join_data: dict, world: SharedWorld) -> bool:
        """Procesa la respuesta a una invitación (MINIGAME_JOIN)."""
        if self.pending_summon is None:
            return False

        game_id = join_data.get("game_id", 0)
        accepted = join_data.get("accepted", False)

        if game_id != self.pending_summon["game_id"]:
            return False

        if not accepted:
            logger.info("[Orquestador] Jugador %d declinó invitación a minijuego.", sender_session.player_entity_id)
            return True

        p = Participant(
            entity_id=sender_session.player_entity_id,
            session_id=sender_session.session_id,
            player_uuid=sender_session.player_uuid,
            display_name=sender_session.display_name,
            role=ParticipantRole.FFA,
        )
        self.pending_participants[sender_session.player_entity_id] = p
        logger.info(
            "[Orquestador] Jugador %d ('%s') se unió a la convocatoria (%d/%d)",
            sender_session.player_entity_id,
            sender_session.display_name,
            len(self.pending_participants),
            self.pending_summon["max_players"],
        )

        # Si alcanzamos el máximo de jugadores o todas las sesiones conectadas se unieron
        if len(self.pending_participants) >= self.pending_summon["max_players"] or len(self.pending_participants) >= len(self.session_manager):
            self._launch_pending_game(world)

        return True

    def handle_action(self, sender_session: ClientSession, action_data: dict, world: SharedWorld) -> None:
        """Canaliza una acción al minijuego activo."""
        if self.active_game and self.active_game.state == MinigameState.ACTIVE:
            self.active_game.handle_action(sender_session.player_entity_id, action_data, world)

    def tick(self, dt: float, world: SharedWorld) -> None:
        """Ciclo autoritativo del orquestador ejecutado a 30 Hz."""
        # 1. Gestionar temporizador de convocatoria
        if self.pending_summon is not None:
            self.summon_timer += dt
            if self.summon_timer >= self.summon_timeout:
                game_cls = self.game_catalog.get(self.pending_summon["game_id"])
                min_req = game_cls.min_players if game_cls else 2

                # Si tenemos quórum suficiente, arrancar; sino cancelar
                if len(self.pending_participants) >= min_req:
                    self._launch_pending_game(world)
                else:
                    self._cancel_pending_summon(reason=1)  # Quórum no alcanzado

        # 2. Gestionar avance de la partida activa
        if self.active_game is not None:
            self.active_game.tick(dt, world)

    def _launch_pending_game(self, world: SharedWorld) -> None:
        """Instancia e inicializa la partida con los participantes reunidos."""
        if self.pending_summon is None:
            return

        game_id = self.pending_summon["game_id"]
        game_cls = self.game_catalog.get(game_id)
        if not game_cls:
            self._cancel_pending_summon(reason=3)
            return

        self.active_game = game_cls()
        self.active_game.on_event_emit = self.broadcast_callback
        self.active_game.on_game_ended = self._on_minigame_completed

        participants_list = list(self.pending_participants.values())
        self.pending_summon = None
        self.pending_participants.clear()

        self.active_game.start_staging(participants_list, world)

    def _cancel_pending_summon(self, reason: int) -> None:
        """Cancela la convocatoria y notifica a clientes."""
        if self.pending_summon is None:
            return

        game_id = self.pending_summon["game_id"]
        logger.info("[Orquestador] Convocatoria de minijuego %d cancelada (motivo=%d)", game_id, reason)

        ev = EventPayload.create_minigame_cancel(entity_id=0, game_id=game_id, reason=reason)
        self.broadcast_callback(ev)

        self.pending_summon = None
        self.pending_participants.clear()

    def _on_minigame_completed(self, game: BaseMinigame) -> None:
        """Acredita Pesos Tecatenses en SQLite y limpia la instancia de partida."""
        logger.info("[Orquestador] Procesando recompensas en SQLite para '%s'", game.name)

        for p in game.participants.values():
            if p.coins_rewarded > 0 and p.player_uuid:
                new_bal = self.auth_manager.update_player_balance(p.player_uuid, p.coins_rewarded)
                logger.info(
                    "[Economía SQLite] +%d Pesos para '%s' (%s). Nuevo saldo: %d",
                    p.coins_rewarded,
                    p.display_name,
                    p.player_uuid,
                    new_bal,
                )

        self.active_game = None
