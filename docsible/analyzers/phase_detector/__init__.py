"""Phase detection for Ansible task files."""

from .detector import PhaseDetector
from .models import Phase, PhaseDetectionResult, PhaseMatch

__all__ = ["Phase", "PhaseMatch", "PhaseDetectionResult", "PhaseDetector"]
