"""Submódulo de red UDP para TKT/1."""

from server.network.udp_server import TKTGameServer, TKTServerProtocol

__all__ = ["TKTGameServer", "TKTServerProtocol"]
