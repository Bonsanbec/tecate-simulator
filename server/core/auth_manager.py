"""Gestor de Autenticación, Cuentas y Persistencia para el Servidor TKT/1.

Administra el ciclo de vida de los perfiles de jugadores, hashing seguro de secretos,
consulta y actualización de balances en Pesos Tecatenses, preservación de coordenadas
geográficas y registro de estadísticas de minijuegos sobre SQLite.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from typing import Any

from server.core.db import DatabaseManager

logger = logging.getLogger(__name__)


def hash_secret(secret: str) -> str:
    """Genera un hash SHA-256 seguro para el secreto del cliente."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class ServerAuthManager:
    """Gestor de autenticación autoritativa y persistencia de perfiles cívicos."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        self.db = db_manager or DatabaseManager()

    def authenticate_or_register(
        self,
        auth_token: str,
        fallback_nickname: str = "Ciudadano",
    ) -> tuple[bool, dict[str, Any], str]:
        """Autentica un cliente a partir de su token o registra una cuenta nueva automáticamente.

        Formato esperado de auth_token: 'UUID:SECRET:NICKNAME' o 'UUID:SECRET'.
        Si auth_token está vacío, se aprovisiona un nuevo par criptográfico.

        Retorna:
            (éxito: bool, perfil: dict, mensaje: str)
        """
        parts = auth_token.strip().split(":") if auth_token else []

        if len(parts) >= 2 and parts[0] and parts[1]:
            player_uuid = parts[0].strip()
            secret = parts[1].strip()
            nickname = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else fallback_nickname
        else:
            # Token no provisto o inválido: generar nueva identidad automática
            player_uuid = str(uuid.uuid4())
            secret = uuid.uuid4().hex + uuid.uuid4().hex # 64 chars
            nickname = fallback_nickname

        secret_hash = hash_secret(secret)
        now = time.time()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE player_uuid = ?", (player_uuid,))
            row = cursor.fetchone()

            if row is None:
                # 1. Registro de nuevo ciudadano
                cursor.execute(
                    """
                    INSERT INTO players (player_uuid, auth_secret_hash, display_name, preferred_character_id, balance_pesos, created_at, last_connected_at)
                    VALUES (?, ?, ?, 'axel', 50, ?, ?)
                    """,
                    (player_uuid, secret_hash, nickname, now, now),
                )
                # Crear registro de posición inicial en el Parque Hidalgo
                cursor.execute(
                    """
                    INSERT INTO player_world_states (player_uuid, pos_x, pos_y, pos_z, yaw, updated_at)
                    VALUES (?, -6.684, 401.80, 2.688, 90.0, ?)
                    """,
                    (player_uuid, now),
                )
                conn.commit()
                logger.info("[Auth] Nuevo jugador registrado: UUID=%s, Nombre='%s'", player_uuid, nickname)
                profile = {
                    "player_uuid": player_uuid,
                    "auth_secret": secret,
                    "display_name": nickname,
                    "preferred_character_id": "axel",
                    "balance_pesos": 50,
                    "is_new": True,
                }
                return True, profile, "Registro exitoso"

            # 2. Verificación de credencial de jugador existente
            stored_hash = row["auth_secret_hash"]
            if stored_hash != secret_hash:
                logger.warning("[Auth] Intento de acceso fallido para UUID=%s: secreto incorrecto", player_uuid)
                return False, {}, "Credencial no autorizada (secreto inválido)"

            # Credencial válida: actualizar marca temporal y apodo si cambió
            update_name = nickname if nickname != fallback_nickname else row["display_name"]
            cursor.execute(
                """
                UPDATE players
                SET last_connected_at = ?, display_name = ?
                WHERE player_uuid = ?
                """,
                (now, update_name, player_uuid),
            )
            conn.commit()

            profile = {
                "player_uuid": player_uuid,
                "auth_secret": secret,
                "display_name": update_name,
                "preferred_character_id": row["preferred_character_id"],
                "balance_pesos": row["balance_pesos"],
                "is_new": False,
            }
            logger.info("[Auth] Jugador autenticado: UUID=%s, Nombre='%s', Saldo=%d", player_uuid, update_name, row["balance_pesos"])
            return True, profile, "Autenticación exitosa"

    def get_player_profile(self, player_uuid: str) -> dict[str, Any] | None:
        """Obtiene el perfil persistente de un jugador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE player_uuid = ?", (player_uuid,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def get_player_balance(self, player_uuid: str) -> int:
        """Devuelve el saldo actual de Pesos Tecatenses de un jugador."""
        prof = self.get_player_profile(player_uuid)
        return int(prof["balance_pesos"]) if prof else 0

    def update_player_balance(self, player_uuid: str, delta: int) -> int:
        """Modifica el saldo de Pesos Tecatenses y retorna el nuevo balance (mínimo 0)."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance_pesos FROM players WHERE player_uuid = ?", (player_uuid,))
            row = cursor.fetchone()
            if not row:
                return 0

            new_balance = max(0, row["balance_pesos"] + delta)
            cursor.execute(
                "UPDATE players SET balance_pesos = ? WHERE player_uuid = ?",
                (new_balance, player_uuid),
            )
            conn.commit()
            logger.info("[Economía] Saldo actualizado para %s: %+d -> %d Pesos", player_uuid, delta, new_balance)
            return new_balance

    def save_player_position(self, player_uuid: str, pos_x: float, pos_y: float, pos_z: float, yaw: float) -> None:
        """Guarda la última ubicación geográfica en Tecate del jugador."""
        now = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO player_world_states (player_uuid, pos_x, pos_y, pos_z, yaw, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(player_uuid) DO UPDATE SET
                    pos_x = excluded.pos_x,
                    pos_y = excluded.pos_y,
                    pos_z = excluded.pos_z,
                    yaw = excluded.yaw,
                    updated_at = excluded.updated_at
                """,
                (player_uuid, pos_x, pos_y, pos_z, yaw, now),
            )
            conn.commit()

    def get_player_position(self, player_uuid: str) -> tuple[float, float, float, float] | None:
        """Retorna (pos_x, pos_y, pos_z, yaw) de la última ubicación guardada o None."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pos_x, pos_y, pos_z, yaw FROM player_world_states WHERE player_uuid = ?", (player_uuid,))
            row = cursor.fetchone()
            if row:
                return (row["pos_x"], row["pos_y"], row["pos_z"], row["yaw"])
        return None

    def update_character_id(self, player_uuid: str, character_id: str) -> None:
        """Actualiza el personaje preferido de un jugador."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE players SET preferred_character_id = ? WHERE player_uuid = ?",
                (character_id, player_uuid),
            )
            conn.commit()

    def record_minigame_stat(self, player_uuid: str, game_id: str, won: bool, metric: float = 0.0) -> None:
        """Registra el resultado de una partida de minijuego para el jugador en SQLite."""
        now = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO player_minigame_stats (player_uuid, game_id, wins, matches_played, best_metric, last_played_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(player_uuid, game_id) DO UPDATE SET
                    wins = wins + excluded.wins,
                    matches_played = matches_played + 1,
                    best_metric = MAX(best_metric, excluded.best_metric),
                    last_played_at = excluded.last_played_at
                """,
                (player_uuid, game_id, 1 if won else 0, metric, now),
            )
            conn.commit()
