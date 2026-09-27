#!/usr/bin/env python3
"""Punto de entrada principal para el servidor de juego TKT/1 (Tecate Simulator).

Uso:
    python3 server/main.py
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Asegurar que el directorio raíz de Tecate Simulator se encuentre en sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from server.config import ServerConfig
from server.network.udp_server import TKTGameServer


def setup_logging(level_name: str) -> None:
    """Configura el formato de registros en consola."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def main() -> None:
    config = ServerConfig()
    setup_logging(config.log_level)

    logger = logging.getLogger("TKTServer")
    logger.info("Iniciando servidor de juego Tecate Simulator...")
    logger.info("Configuración cargada:")
    for key, val in config.to_dict().items():
        logger.info("  • %s: %s", key, val)

    server = TKTGameServer(config)
    await server.start()

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Señal de detención recibida. Finalizando servidor...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Soporte en plataformas donde add_signal_handler no esté implementado (ej. Windows)
            pass

    try:
        await stop_event.wait()
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
