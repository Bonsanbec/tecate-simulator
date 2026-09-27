"""Módulo de Configuración para el Servidor TKT/1 de Tecate Simulator.

Carga variables de entorno desde el archivo .env o desde el entorno del sistema operativo.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _load_env_file(env_path: Path) -> dict[str, str]:
    """Carga pares clave-valor de un archivo .env plano."""
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    values[key] = val
    except Exception as exc:
        print(f"[Config] Advertencia: No se pudo leer {env_path}: {exc}")

    return values


class ServerConfig:
    """Contenedor de configuración tipada para el servidor TKT/1."""

    def __init__(self, env_dict: dict[str, str] | None = None) -> None:
        raw: dict[str, str] = {}

        # 1. Cargar desde archivo .env local en server/.env
        server_dir = Path(__file__).resolve().parent
        env_file = server_dir / ".env"
        raw.update(_load_env_file(env_file))

        # 2. Sobrescribir con variables de entorno del SO si existen
        for key in raw.copy():
            if key in os.environ:
                raw[key] = os.environ[key]

        # 3. Si se pasaron valores explícitos, sobrescribir
        if env_dict:
            raw.update(env_dict)

        self.bind_host: str = raw.get("SERVER_BIND_HOST", "0.0.0.0")
        self.port: int = int(raw.get("SERVER_PORT", "52665"))
        self.public_domain: str = raw.get("PUBLIC_DOMAIN", "bonsanbec.dev")
        self.public_subdomain: str = raw.get("PUBLIC_SUBDOMAIN", "api.tecate")
        self.public_host: str = raw.get(
            "PUBLIC_HOST", f"{self.public_subdomain}.{self.public_domain}"
        )

        self.tick_rate: int = int(raw.get("TICK_RATE", "30"))
        self.session_timeout: float = float(raw.get("SESSION_TIMEOUT_SECONDS", "10.0"))
        self.max_clients: int = int(raw.get("MAX_CLIENTS", "64"))
        self.max_packet_size: int = int(raw.get("MAX_PACKET_SIZE", "1400"))

        self.spatial_cell_size: float = float(raw.get("SPATIAL_GRID_CELL_SIZE", "150.0"))
        self.broadcast_radius_cells: int = int(raw.get("BROADCAST_RADIUS_CELLS", "1"))

        self.auth_required: bool = raw.get("AUTH_REQUIRED", "false").lower() in ("true", "1", "yes")
        self.auth_secret_key: str = raw.get("AUTH_SECRET_KEY", "tecate_default_key")
        self.log_level: str = raw.get("LOG_LEVEL", "INFO").upper()

    def to_dict(self) -> dict[str, Any]:
        return {
            "bind_host": self.bind_host,
            "port": self.port,
            "public_host": self.public_host,
            "tick_rate": self.tick_rate,
            "session_timeout": self.session_timeout,
            "max_clients": self.max_clients,
            "spatial_cell_size": self.spatial_cell_size,
            "broadcast_radius_cells": self.broadcast_radius_cells,
            "auth_required": self.auth_required,
            "log_level": self.log_level,
        }
