from .models import Phase, PhaseMatch, PhaseDetectionResult
from .patterns import PatternLoader

class PhaseDetector:
    """Detects execution phases in task files."""
    
    def __init__(self, min_confidence=0.8, patterns_file=None):
        """Initialize phase detector.
        
        Args:
            min_confidence: Minimum confidence threshold
            patterns_file: Path to custom phase patterns YAML file
        """
        self.min_confidence = min_confidence
        self.patterns = PatternLoader.load_from_file(patterns_file) if patterns_file else PatternLoader.get_defaults()
    
    # All detection methods
