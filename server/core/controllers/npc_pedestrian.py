"""Módulo de compatibilidad retroactiva para controladores de peatones.

Redirige a server.core.controllers.citizen.CitizenController.
"""

from server.core.controllers.citizen import CitizenController, NPCPedestrianController

__all__ = ["CitizenController", "NPCPedestrianController"]
