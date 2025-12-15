"""Pattern analysis for Ansible roles.

This package provides comprehensive pattern detection to identify
anti-patterns, code smells, and opportunities for simplification.

Main Components:
- models: Pydantic models for pattern data (SimplificationSuggestion, etc.)
- base: Base classes for implementing new detectors
- detectors: Specialized pattern detectors (duplication, security, etc.)
- analyzer: Main analysis orchestration

Quick Start:
    >>> from docsible.analyzers.patterns import analyze_role_patterns
    >>> from docsible.parsers.role_parser import parse_role
    >>>
    >>> role_info = parse_role('/path/to/role')
    >>> report = analyze_role_patterns(role_info)
    >>>
    >>> print(f"Health Score: {report.overall_health_score}/100")
    >>> for suggestion in report.suggestions:
    ...     if suggestion.severity == 'critical':
    ...         print(f"CRITICAL: {suggestion.description}")

Advanced Usage:
    >>> from docsible.analyzers.patterns import PatternAnalyzer
    >>> from docsible.analyzers.patterns.detectors import SecurityDetector
    >>>
    >>> # Only run security checks
    >>> analyzer = PatternAnalyzer(
    ...     enabled_detectors=[SecurityDetector],
    ...     min_confidence=0.8
    ... )
    >>> report = analyzer.analyze(role_info)
"""

from docsible.analyzers.patterns.models import (
    SimplificationSuggestion,
    PatternAnalysisReport,
    SeverityLevel,
    PatternCategory,
)
from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.analyzer import (
    PatternAnalyzer,
    analyze_role_patterns,
)

__all__ = [
    # Models
    'SimplificationSuggestion',
    'PatternAnalysisReport',
    'SeverityLevel',
    'PatternCategory',
    # Base class
    'BasePatternDetector',
    # Main API
    'PatternAnalyzer',
    'analyze_role_patterns',
]

__version__ = '1.0.0'
