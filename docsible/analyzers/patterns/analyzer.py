"""Main pattern analyzer that orchestrates all pattern detectors.

This module provides the high-level API for pattern analysis,
coordinating multiple specialized detectors.
"""

import logging
from typing import Any, Dict, List, Type

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.detectors import (
    ComplexityDetector,
    DuplicationDetector,
    MaintainabilityDetector,
    SecurityDetector,
)
from docsible.analyzers.patterns.models import (
    PatternAnalysisReport,
    SeverityLevel,
    SimplificationSuggestion,
)

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """Main pattern analyzer coordinating all detectors.

    Design Pattern: Facade + Strategy
    - Provides simple interface to complex subsystem
    - Each detector implements the strategy pattern

    Example:
        >>> analyzer = PatternAnalyzer()
        >>> report = analyzer.analyze(role_info)
        >>> print(f"Found {report.total_patterns} issues")
        >>> for suggestion in report.suggestions:
        ...     print(f"{suggestion.severity}: {suggestion.description}")
    """

    def __init__(
        self,
        enabled_detectors: List[Type[BasePatternDetector]] | None = None,
        min_confidence: float = 0.0,
    ):
        """Initialize pattern analyzer.

        Args:
            enabled_detectors: List of detector classes to use.
                              If None, uses all available detectors.
            min_confidence: Minimum confidence score (0.0-1.0) for
                           reporting a pattern. Patterns below this
                           threshold will be filtered out.
        """
        self.min_confidence = min_confidence

        # Use all detectors by default
        if enabled_detectors is None:
            enabled_detectors = [
                DuplicationDetector,
                ComplexityDetector,
                SecurityDetector,
                MaintainabilityDetector,
            ]

        # Instantiate detectors
        self.detectors: List[BasePatternDetector] = [
            detector_class() for detector_class in enabled_detectors
        ]

        logger.debug(
            f"Initialized PatternAnalyzer with {len(self.detectors)} detectors "
            f"(min_confidence={min_confidence})"
        )

    def analyze(self, role_info: Dict[str, Any]) -> PatternAnalysisReport:
        """Analyze role for all patterns.

        This is the main entry point for pattern analysis.

        Args:
            role_info: Parsed role information dictionary containing:
                - tasks: List of task files with their tasks
                - vars: Role variables
                - defaults: Default variables
                - handlers: Handler definitions
                - meta: Role metadata

        Returns:
            Comprehensive report of all detected patterns
        """
        logger.info("Starting pattern analysis...")

        all_suggestions: List[SimplificationSuggestion] = []

        # Run each detector
        for detector in self.detectors:
            detector_name = detector.__class__.__name__
            logger.debug(f"Running {detector_name}...")

            try:
                suggestions = detector.detect(role_info)

                # Filter by confidence
                filtered_suggestions = [
                    s for s in suggestions if s.confidence >= self.min_confidence
                ]

                logger.debug(
                    f"{detector_name} found {len(suggestions)} patterns "
                    f"({len(filtered_suggestions)} above confidence threshold)"
                )

                all_suggestions.extend(filtered_suggestions)

            except Exception as e:
                logger.error(f"Error in {detector_name}: {e}", exc_info=True)
                # Continue with other detectors

        # Create report
        report = PatternAnalysisReport(suggestions=all_suggestions)
        report.calculate_metrics()

        logger.info(
            f"Pattern analysis complete: {report.total_patterns} patterns found "
            f"(health score: {report.overall_health_score:.1f}/100)"
        )

        return report

    def analyze_by_severity(
        self, role_info: Dict[str, Any], severity: SeverityLevel
    ) -> List[SimplificationSuggestion]:
        """Analyze role and return only patterns of specified severity.

        Args:
            role_info: Parsed role information
            severity: Severity level to filter by

        Returns:
            List of suggestions matching the severity level
        """
        report = self.analyze(role_info)
        return [s for s in report.suggestions if s.severity == severity]

    def analyze_critical_only(
        self, role_info: Dict[str, Any]
    ) -> List[SimplificationSuggestion]:
        """Analyze role and return only critical issues.

        Convenience method for getting high-priority items.

        Args:
            role_info: Parsed role information

        Returns:
            List of critical suggestions
        """
        return self.analyze_by_severity(role_info, SeverityLevel.CRITICAL)

    def get_detector_by_name(self, name: str) -> BasePatternDetector | None:
        """Get specific detector by class name.

        Args:
            name: Detector class name (e.g., 'DuplicationDetector')

        Returns:
            Detector instance if found, None otherwise
        """
        for detector in self.detectors:
            if detector.__class__.__name__ == name:
                return detector
        return None


def analyze_role_patterns(
    role_info: Dict[str, Any], min_confidence: float = 0.7
) -> PatternAnalysisReport:
    """Convenience function to analyze role patterns.

    This is the main public API for simple usage.

    Args:
        role_info: Parsed role information
        min_confidence: Minimum confidence threshold (default: 0.7)

    Returns:
        Complete pattern analysis report

    Example:
        >>> from docsible.parsers.role_parser import parse_role
        >>> role_info = parse_role('/path/to/role')
        >>> report = analyze_role_patterns(role_info)
        >>>
        >>> # Show critical issues only
        >>> critical = [s for s in report.suggestions if s.severity == 'critical']
        >>> for issue in critical:
        ...     print(f"CRITICAL: {issue.description}")
        ...     print(f"Fix: {issue.suggestion}")
    """
    analyzer = PatternAnalyzer(min_confidence=min_confidence)
    return analyzer.analyze(role_info)
