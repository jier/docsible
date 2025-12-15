"""Pattern detector modules.

Each detector module focuses on a specific category of anti-patterns.
"""

from docsible.analyzers.patterns.detectors.duplication import DuplicationDetector
from docsible.analyzers.patterns.detectors.complexity import ComplexityDetector
from docsible.analyzers.patterns.detectors.security import SecurityDetector
from docsible.analyzers.patterns.detectors.maintainability import MaintainabilityDetector

__all__ = [
    'DuplicationDetector',
    'ComplexityDetector',
    'SecurityDetector',
    'MaintainabilityDetector',
]
