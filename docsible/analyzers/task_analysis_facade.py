"""Thin facade for running all task-file level analysis in one call.

Use this when you need classification (concern), pipeline detection (phase),
and anti-pattern analysis (patterns) from a single entry point. Internally
delegates to each subsystem without merging their APIs.

Quick reference for choosing the right subsystem directly:
    concerns/  → "What is this file FOR?" — returns a classification label
    patterns/  → "What is WRONG with this role?" — returns fix suggestions
    phase.py   → "Is this file a pipeline?" — returns ordering analysis
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TaskFileAnalysis:
    """Unified result from analyzing a single task file."""

    concern: Any | None = None          # ConcernMatch or None
    phase: Any | None = None            # PhaseDetectionResult or None
    patterns: Any | None = None         # PatternAnalysisReport or None (role-level)


def analyze_task_file(
    tasks: list[dict[str, Any]],
    role_info: dict[str, Any] | None = None,
) -> TaskFileAnalysis:
    """Run all task-file level analyzers and return a unified result.

    Args:
        tasks: Flat list of parsed task dicts from a single task file.
        role_info: Full role info dict. If provided, also runs the role-level
            pattern analysis (expensive). If None, pattern analysis is skipped.

    Returns:
        TaskFileAnalysis with concern, phase, and optional patterns.

    Example::

        from docsible.analyzers.task_analysis_facade import analyze_task_file

        # Classification + pipeline detection only (fast)
        analysis = analyze_task_file(tasks)
        print(analysis.concern.name if analysis.concern else "unknown")

        # Full analysis including anti-patterns (slow)
        analysis = analyze_task_file(tasks, role_info=role_info)
        if analysis.patterns:
            print(f"Health: {analysis.patterns.overall_health_score}/100")
    """
    concern = None
    phase = None
    patterns = None

    # Concern detection: what domain does this task file belong to?
    try:
        from docsible.analyzers.concerns.registry import ConcernRegistry
        concern = ConcernRegistry.detect_primary_concern(tasks)
    except Exception:
        pass

    # Phase detection: does this task file form an ordered pipeline?
    try:
        from docsible.analyzers.complexity_analyzer.phase import PhaseDetector
        detector = PhaseDetector()
        phase = detector.detect_phases(tasks)
    except Exception:
        pass

    # Pattern analysis: role-level anti-pattern detection (requires full role_info)
    if role_info is not None:
        try:
            from docsible.analyzers.patterns import analyze_role_patterns
            patterns = analyze_role_patterns(role_info)
        except Exception:
            pass

    return TaskFileAnalysis(concern=concern, phase=phase, patterns=patterns)
