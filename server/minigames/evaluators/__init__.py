"""Evaluadores modulares de reglas físicas y espaciales para minijuegos."""

from server.minigames.evaluators.spatial import SpatialBoundaryEvaluator
from server.minigames.evaluators.contact import ProximityContactEvaluator
from server.minigames.evaluators.anti_camping import ActivityAntiCampingEvaluator
from server.minigames.evaluators.ballistic import BallisticHitEvaluator

__all__ = [
    "SpatialBoundaryEvaluator",
    "ProximityContactEvaluator",
    "ActivityAntiCampingEvaluator",
    "BallisticHitEvaluator",
]
