"""Administrador centralizado de sesiones para el servidor TKT/1."""

from __future__ import annotations

import logging
from typing import Iterator

from server.core.session import ClientSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Administra el ciclo de vida de sesiones clientes y su asignación de IDs."""

    def __init__(self, max_clients: int = 64) -> None:
        self.max_clients = max_clients
        self._sessions_by_id: dict[int, ClientSession] = {}
        self._sessions_by_addr: dict[tuple[str, int], ClientSession] = {}
        self._next_session_id = 100
        self._next_entity_id = 1

    def __len__(self) -> int:
        return len(self._sessions_by_id)

    def __iter__(self) -> Iterator[ClientSession]:
        return iter(list(self._sessions_by_id.values()))

    def get_by_addr(self, addr: tuple[str, int]) -> ClientSession | None:
        return self._sessions_by_addr.get(addr)

    def get_by_id(self, session_id: int) -> ClientSession | None:
        return self._sessions_by_id.get(session_id)

    def create_or_renew_session(
        self,
        addr: tuple[str, int],
        client_version: str = "1.0",
        auth_token: str = "",
    ) -> ClientSession:
        """Crea una nueva sesión o renueva una existente para la misma dirección IP:puerto."""
        existing = self._sessions_by_addr.get(addr)
        if existing:
            existing.touch()
            existing.client_version = client_version
            existing.auth_token = auth_token
            return existing

        if len(self._sessions_by_id) >= self.max_clients:
            raise RuntimeError(f"Capacidad máxima de clientes alcanzada ({self.max_clients})")

        session_id = self._next_session_id
        self._next_session_id += 1

        player_entity_id = self._next_entity_id
        self._next_entity_id += 1

        session = ClientSession(
            session_id=session_id,
            player_entity_id=player_entity_id,
            addr=addr,
            client_version=client_version,
            auth_token=auth_token,
        )

        self._sessions_by_id[session_id] = session
        self._sessions_by_addr[addr] = session
        logger.info(
            "Sesión creada: ID=%d, EntityID=%d, Cliente=%s:%d",
            session_id,
            player_entity_id,
            addr[0],
            addr[1],
        )
        return session

    def remove_session(self, session_id: int) -> ClientSession | None:
        session = self._sessions_by_id.pop(session_id, None)
        if session:
            self._sessions_by_addr.pop(session.addr, None)
            logger.info("Sesión removida: ID=%d, Addr=%s:%d", session_id, session.addr[0], session.addr[1])
        return session

    def purge_timed_out(self, timeout_seconds: float) -> list[ClientSession]:
        """Identifica y desaloja sesiones que superen el límite de inactividad."""
        timed_out: list[ClientSession] = []
        for session in list(self._sessions_by_id.values()):
            if session.is_timed_out(timeout_seconds):
                timed_out.append(session)
                self.remove_session(session.session_id)
        return timed_out
