"""Administrador centralizado de sesiones para el servidor TKT/1."""

from __future__ import annotations

import logging
from typing import Iterator

from server.core.session import ClientSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Administra el ciclo de vida de sesiones clientes y su asignación desacoplada de IDs."""

    def __init__(self, max_clients: int = 64) -> None:
        self.max_clients = max_clients
        self._sessions_by_id: dict[int, ClientSession] = {}
        self._sessions_by_addr: dict[tuple[str, int], ClientSession] = {}
        self._sessions_by_uuid: dict[str, ClientSession] = {}
        self._uuid_to_entity_id: dict[str, int] = {}
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

    def get_by_uuid(self, player_uuid: str) -> ClientSession | None:
        return self._sessions_by_uuid.get(player_uuid)

    def create_or_renew_session(
        self,
        addr: tuple[str, int],
        client_version: str = "1.0",
        auth_token: str = "",
        player_uuid: str = "",
        display_name: str = "",
    ) -> ClientSession:
        """Crea una nueva sesión o renueva una existente, reanclando entity_id por player_uuid."""
        # 1. Si ya existe una sesión con ese player_uuid (reconexión rápida / cambio de puerto NAT)
        if player_uuid and player_uuid in self._sessions_by_uuid:
            existing = self._sessions_by_uuid[player_uuid]
            # Desvincular de la dirección previa si cambió
            if existing.addr != addr:
                old_addr = existing.addr
                self._sessions_by_addr.pop(existing.addr, None)
                existing.addr = addr
                self._sessions_by_addr[addr] = existing
                logger.warning(
                    "[Sesión] Reasignada dirección para UUID=%s: %s:%d -> %s:%d (posible duplicación de player_identity.json)",
                    player_uuid,
                    old_addr[0],
                    old_addr[1],
                    addr[0],
                    addr[1],
                )
            existing.touch()
            existing.client_version = client_version
            existing.auth_token = auth_token
            existing.display_name = display_name or existing.display_name
            logger.info(
                "[Sesión] Reanclada sesión existente ID=%d para UUID=%s en %s:%d",
                existing.session_id,
                player_uuid,
                addr[0],
                addr[1],
            )
            return existing

        # 2. Si ya existe una sesión en la misma dirección IP:puerto
        existing_by_addr = self._sessions_by_addr.get(addr)
        if existing_by_addr:
            existing_by_addr.touch()
            existing_by_addr.client_version = client_version
            existing_by_addr.auth_token = auth_token
            if player_uuid:
                existing_by_addr.player_uuid = player_uuid
                self._sessions_by_uuid[player_uuid] = existing_by_addr
            if display_name:
                existing_by_addr.display_name = display_name
            return existing_by_addr

        if len(self._sessions_by_id) >= self.max_clients:
            raise RuntimeError(f"Capacidad máxima de clientes alcanzada ({self.max_clients})")

        session_id = self._next_session_id
        self._next_session_id += 1

        # Reusar entity_id si el player_uuid ya tenía uno asignado previamente en el servidor
        if player_uuid and player_uuid in self._uuid_to_entity_id:
            player_entity_id = self._uuid_to_entity_id[player_uuid]
        else:
            player_entity_id = self._next_entity_id
            self._next_entity_id += 1
            if player_uuid:
                self._uuid_to_entity_id[player_uuid] = player_entity_id

        session = ClientSession(
            session_id=session_id,
            player_entity_id=player_entity_id,
            addr=addr,
            client_version=client_version,
            auth_token=auth_token,
            player_uuid=player_uuid,
            display_name=display_name,
            is_authenticated=bool(player_uuid),
        )

        self._sessions_by_id[session_id] = session
        self._sessions_by_addr[addr] = session
        if player_uuid:
            self._sessions_by_uuid[player_uuid] = session

        logger.info(
            "Sesión creada: ID=%d, EntityID=%d, UUID=%s, Cliente=%s:%d",
            session_id,
            player_entity_id,
            player_uuid,
            addr[0],
            addr[1],
        )
        return session

    def remove_session(self, session_id: int) -> ClientSession | None:
        session = self._sessions_by_id.pop(session_id, None)
        if session:
            self._sessions_by_addr.pop(session.addr, None)
            if session.player_uuid:
                self._sessions_by_uuid.pop(session.player_uuid, None)
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
