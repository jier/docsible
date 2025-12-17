"""Phase detection for Ansible task files."""

from .models import Phase, PhaseMatch, PhaseDetectionResult
from .detector import PhaseDetector

__all__ = ["Phase", "PhaseMatch", "PhaseDetectionResult", "PhaseDetector"]
