"""Gestión de sesiones individuales de clientes conectados."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ClientSession:
    """Representa la sesión activa de un cliente conectado vía UDP."""

    session_id: int
    player_entity_id: int
    addr: tuple[str, int]
    client_version: str = "1.0"
    auth_token: str = ""
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    sequence_out: int = 0
    last_sequence_in: int = 0
    rtt_ms: float = 0.0
    is_authenticated: bool = False

    def touch(self) -> None:
        """Actualiza la marca temporal de última actividad."""
        self.last_seen = time.time()

    def next_sequence(self) -> int:
        """Incrementa y devuelve el siguiente número de secuencia saliente."""
        self.sequence_out = (self.sequence_out + 1) & 0xFFFFFFFF
        return self.sequence_out

    def is_timed_out(self, timeout_seconds: float) -> bool:
        """Determina si la sesión ha superado el tiempo máximo de inactividad."""
        return (time.time() - self.last_seen) > timeout_seconds
