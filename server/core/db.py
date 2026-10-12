"""Capa de Persistencia y Base de Datos Relacional SQLite para Tecate Simulator.

Gestiona la conexión local autoritativa, inicialización de esquemas relacionales,
transacciones ACID y modo WAL (Write-Ahead Logging) para garantizar integridad
de datos y descartar archivos JSON frágiles en tiempo de ejecución.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tecate_world.db"


class DatabaseManager:
    """Administrador centralizado de la base de datos SQLite del servidor."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Crea y configura una conexión SQLite con modo WAL y claves foráneas activas."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_schema(self) -> None:
        """Inicializa las tablas e índices si no existen."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Tabla Principal de Jugadores y Cuentas Cívicas
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    player_uuid TEXT PRIMARY KEY,
                    auth_secret_hash TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    preferred_character_id TEXT NOT NULL DEFAULT 'axel',
                    balance_pesos INTEGER NOT NULL DEFAULT 50,
                    created_at REAL NOT NULL,
                    last_connected_at REAL NOT NULL
                );
                """
            )

            # 2. Última Posición Geográfica y Orientación en Tecate
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS player_world_states (
                    player_uuid TEXT PRIMARY KEY,
                    pos_x REAL NOT NULL DEFAULT -6.684,
                    pos_y REAL NOT NULL DEFAULT 401.80,
                    pos_z REAL NOT NULL DEFAULT 2.688,
                    yaw REAL NOT NULL DEFAULT 90.0,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(player_uuid) REFERENCES players(player_uuid) ON DELETE CASCADE
                );
                """
            )

            # 3. Cosméticos e Indumentaria Desbloqueada
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS player_cosmetics (
                    player_uuid TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    is_equipped INTEGER NOT NULL DEFAULT 0,
                    slot TEXT NOT NULL,
                    acquired_at REAL NOT NULL,
                    PRIMARY KEY(player_uuid, item_id),
                    FOREIGN KEY(player_uuid) REFERENCES players(player_uuid) ON DELETE CASCADE
                );
                """
            )

            # 4. Estadísticas y Récords de Minijuegos
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS player_minigame_stats (
                    player_uuid TEXT NOT NULL,
                    game_id TEXT NOT NULL,
                    wins INTEGER NOT NULL DEFAULT 0,
                    matches_played INTEGER NOT NULL DEFAULT 0,
                    best_metric REAL NOT NULL DEFAULT 0.0,
                    last_played_at REAL NOT NULL,
                    PRIMARY KEY(player_uuid, game_id),
                    FOREIGN KEY(player_uuid) REFERENCES players(player_uuid) ON DELETE CASCADE
                );
                """
            )

            conn.commit()
            logger.info("Base de datos SQLite inicializada exitosamente en: %s", self.db_path)
