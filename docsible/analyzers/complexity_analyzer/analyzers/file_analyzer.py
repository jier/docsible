"""Per-file complexity analysis."""

import logging
from typing import Any

from docsible.analyzers.concerns.registry import ConcernRegistry
from docsible.analyzers.phase_detector import PhaseDetector

from ..models import FileComplexityDetail, IntegrationPoint

logger = logging.getLogger(__name__)


def analyze_file_complexity(
    role_info: dict[str, Any], integration_points: list[IntegrationPoint]
) -> list[FileComplexityDetail]:
    """Analyze complexity metrics for each task file.

    Args:
        role_info: Role information dictionary
        integration_points: Detected integration points

    Returns:
        List of FileComplexityDetail objects, sorted by task count (descending)

    Example:
        >>> files = analyze_file_complexity(role_info, integrations)
        >>> largest = files[0]
        >>> print(f"{largest.file_path}: {largest.task_count} tasks")
    """
    file_details = []
    phase_detector = PhaseDetector(min_confidence=0.8)  # Conservative threshold

    for task_file_info in role_info.get("tasks", []):
        file_path = task_file_info.get("file", "unknown")
        tasks = task_file_info.get("tasks", [])

        if not tasks:
            continue

        # Count conditionals
        conditional_tasks = [t for t in tasks if t.get("when")]
        conditional_count = len(conditional_tasks)
        conditional_percentage = (
            (conditional_count / len(tasks)) * 100 if tasks else 0.0
        )

        # Detect integrations in this file
        has_integrations = False
        integration_types = []
        for integration in integration_points:
            # Check if any integration modules are used in this file
            file_modules = set(t.get("module", "") for t in tasks)
            if any(mod in file_modules for mod in integration.modules_used):
                has_integrations = True
                integration_types.append(integration.type.value)

        # Count unique modules (diversity indicator)
        unique_modules = len(set(t.get("module", "") for t in tasks if t.get("module")))

        # Detect primary concern (simple heuristic based on modules)
        primary_concern = _detect_file_concern(tasks)

        # Get line ranges if available
        line_ranges = task_file_info.get("line_ranges")

        # Perform phase detection
        phase_detection_result = None
        try:
            result = phase_detector.detect_phases(tasks, line_ranges)
            if result.detected_phases or result.is_coherent_pipeline:
                # Serialize phase detection result for storage
                phase_detection_result = {
                    "is_coherent_pipeline": result.is_coherent_pipeline,
                    "confidence": result.confidence,
                    "recommendation": result.recommendation,
                    "reasoning": result.reasoning,
                    "phases": [
                        {
                            "phase": phase.phase.value,
                            "start_line": phase.start_line,
                            "end_line": phase.end_line,
                            "task_count": phase.task_count,
                            "confidence": phase.confidence,
                        }
                        for phase in result.detected_phases
                    ],
                }
        except Exception as e:
            logger.debug(f"Phase detection failed for {file_path}: {e}")
        #FIXME Missing detailed concern
        file_details.append(
            FileComplexityDetail(
                file_path=file_path,
                task_count=len(tasks),
                conditional_count=conditional_count,
                conditional_percentage=conditional_percentage,
                has_integrations=has_integrations,
                integration_types=list(set(integration_types)),
                module_diversity=unique_modules,
                primary_concern=primary_concern,
                phase_detection=phase_detection_result,
                line_ranges=line_ranges,
            )
        )

    # Sort by task count (largest first)
    return sorted(file_details, key=lambda f: f.task_count, reverse=True)

#FIXME Unused function
def _detect_file_concerns(
    tasks: list[dict[str, Any]],
) -> tuple[str | None, list[tuple[str, str, int]]]:
    """Detect all concerns in a task file and return primary + detailed breakdown.

    Args:
        tasks: List of tasks in the file

    Returns:
        Tuple of (primary_concern, [(concern_name, display_name, count)])

    Example:
        >>> primary, concerns = _detect_file_concerns(tasks)
        >>> print(primary)  # 'package_installation'
        >>> print(concerns)  # [('package_installation', 'Package Installation', 5), ...]
    """
    # Get all concerns
    all_matches = ConcernRegistry.detect_all(tasks)

    # Primary concern
    primary = ConcernRegistry.detect_primary_concern(tasks, min_confidence=0.6)
    primary_name = primary.concern_name if primary else None

    # Detailed breakdown (only concerns with >0 tasks)
    concerns_breakdown = [
        (match.concern_name, match.display_name, match.task_count)
        for match in all_matches
        if match.task_count > 0
    ]

    return primary_name, concerns_breakdown


def _detect_file_concern(tasks: list[dict[str, Any]]) -> str | None:
    """Detect the primary concern/responsibility of a task file.

    Uses pluggable concern detection system for extensibility.

    Args:
        tasks: List of tasks in the file

    Returns:
        String describing primary concern, or None if mixed

    Example:
        >>> tasks = [{"module": "apt"}, {"module": "yum"}]
        >>> _detect_file_concern(tasks)
        'package_installation'
    """
    # Use pluggable concern registry
    primary = ConcernRegistry.detect_primary_concern(tasks, min_confidence=0.6)
    return primary.concern_name if primary else None
