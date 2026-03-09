"""Phase detection for Ansible task files.

This module consolidates all phase detection logic previously located in
``docsible.analyzers.phase_detector``.  It is now the canonical location
for phase-related models, patterns, and the detector implementation.
"""

import logging
from collections import defaultdict
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from docsible.analyzers.shared.module_taxonomy import (
    CONFIG_MODULES,
    FILE_MODULES,
    PACKAGE_MODULES,
    SERVICE_MODULES,
    VERIFY_MODULES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Phase(Enum):
    """Common execution phases in Ansible workflows."""

    SETUP = "setup"
    INSTALL = "install"
    CONFIGURE = "configure"
    DEPLOY = "deploy"
    ACTIVATE = "activate"
    VERIFY = "verify"
    CLEANUP = "cleanup"
    UNKNOWN = "unknown"


class PhaseMatch(BaseModel):
    """Represents a detected phase in a task sequence."""

    phase: Phase
    start_line: int = Field(ge=0, description="Starting line number in source file")
    end_line: int = Field(ge=0, description="Ending line number in source file")
    task_count: int = Field(gt=0, description="Number of tasks in this phase")
    task_indices: list[int] = Field(description="Task indices belonging to this phase")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


class PhaseDetectionResult(BaseModel):
    """Result of phase detection analysis."""

    detected_phases: list[PhaseMatch] = Field(default_factory=list)
    is_coherent_pipeline: bool = Field(description="Whether tasks form a coherent pipeline")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall pipeline confidence")
    recommendation: str = Field(description="Human-readable recommendation")
    reasoning: str = Field(description="Explanation of the analysis")


class PhasePattern(BaseModel):
    """Pattern for detecting a specific phase.

    Converted from TypedDict to BaseModel for consistency with other models
    and to get validation, serialization, and better IDE support.
    """

    modules: set[str] = Field(
        default_factory=set, description="Ansible modules associated with this phase"
    )
    name_keywords: list[str] = Field(
        default_factory=list, description="Keywords in task names indicating this phase"
    )
    priority: int = Field(
        default=99, description="Priority for phase detection (lower = higher priority)"
    )


# ---------------------------------------------------------------------------
# Default patterns
# ---------------------------------------------------------------------------

DEFAULT_PATTERNS: dict[Phase, PhasePattern] = {
    Phase.SETUP: PhasePattern(
        modules={
            "assert",
            "debug",
            "set_fact",
            "include_vars",
            "stat",
            "fail",
            "when",
        },
        name_keywords=[
            "prerequisite",
            "pre-requisite",
            "check",
            "validate",
            "ensure",
            "verify prerequisite",
        ],
        priority=1,  # Typically first
    ),
    Phase.INSTALL: PhasePattern(
        # Seed from shared taxonomy, then add phase-specific extras
        modules=set(PACKAGE_MODULES) | {
            "get_url",
            "git",
            "unarchive",
            "maven_artifact",
        },
        name_keywords=[
            "install",
            "download",
            "fetch",
            "pull",
            "clone",
            "acquire",
        ],
        priority=2,
    ),
    Phase.CONFIGURE: PhasePattern(
        # Seed from shared taxonomy, then add file module for config file placement
        modules=set(CONFIG_MODULES) | set(FILE_MODULES),
        name_keywords=[
            "configure",
            "config",
            "setup",
            "set up",
            "create config",
            "apply config",
        ],
        priority=3,
    ),
    Phase.DEPLOY: PhasePattern(
        modules={"command", "shell", "docker_container", "kubernetes", "k8s"},
        name_keywords=["deploy", "run", "execute", "launch", "apply"],
        priority=4,
    ),
    Phase.ACTIVATE: PhasePattern(
        # Seed from shared taxonomy, then add docker_container which is phase-specific
        modules=set(SERVICE_MODULES) | {"docker_container"},
        name_keywords=["start", "enable", "activate", "restart", "reload"],
        priority=5,
    ),
    Phase.VERIFY: PhasePattern(
        # Seed from shared taxonomy (already includes uri, wait_for, assert, ping, command, shell)
        modules=set(VERIFY_MODULES),
        name_keywords=[
            "verify",
            "test",
            "check",
            "validate",
            "health check",
            "smoke test",
            "wait for",
            "ensure running",
        ],
        priority=6,
    ),
    Phase.CLEANUP: PhasePattern(
        modules={"file", "command", "shell"},
        name_keywords=[
            "cleanup",
            "clean up",
            "remove",
            "delete",
            "purge",
            "temporary",
        ],
        priority=7,  # Typically last
    ),
}


# ---------------------------------------------------------------------------
# Pattern loader
# ---------------------------------------------------------------------------


class PatternLoader:
    """Loads phase patterns from files or defaults."""

    @staticmethod
    def load_from_file(path: Path | str) -> dict[Phase, PhasePattern]:
        """Parse YAML patterns file.

        Args:
            path: Path to YAML patterns file

        Returns:
            Dictionary mapping Phase to PhasePattern

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        import yaml

        patterns_path = Path(path)
        with open(patterns_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        patterns: dict[Phase, PhasePattern] = {}
        phases_config = config.get("phases", {})

        for phase_name, pattern_config in phases_config.items():
            phase = PatternLoader._get_phase_by_name(phase_name)
            patterns[phase] = PhasePattern(
                modules=set(pattern_config.get("modules", [])),
                name_keywords=pattern_config.get("name_keywords", []),
                priority=pattern_config.get("priority", 99),
            )

        return patterns

    @staticmethod
    def _get_phase_by_name(name: str) -> Phase:
        """Get Phase enum by name, case-insensitive.

        Args:
            name: Phase name

        Returns:
            Phase enum member

        Note:
            If phase name doesn't match any existing Phase, returns Phase.UNKNOWN
        """
        name_upper = name.upper()
        for phase in Phase:
            if phase.name == name_upper:
                return phase
        return Phase.UNKNOWN

    @staticmethod
    def get_defaults() -> dict[Phase, PhasePattern]:
        """Get default patterns (as a copy).

        Returns:
            Copy of DEFAULT_PATTERNS dictionary
        """
        return {phase: pattern.model_copy() for phase, pattern in DEFAULT_PATTERNS.items()}


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class PhaseDetector:
    """Detects execution phases in Ansible task files.

    Supports custom phase patterns via:
    1. Configuration file (.docsible/phase_patterns.yml)
    2. Programmatic API (add_custom_phase, extend_phase)

    Example:
        # Use defaults
        detector = PhaseDetector()

        # Load custom patterns from file
        detector = PhaseDetector(patterns_file=".docsible/phase_patterns.yml")

        # Add custom phase programmatically
        detector.extend_phase(
            Phase.INSTALL,
            additional_modules={"brew", "chocolatey"},
            additional_keywords=["provision"]
        )
    """

    def __init__(self, min_confidence: float = 0.8, patterns_file: str | Path | None = None):
        """Initialize phase detector.

        Args:
            min_confidence: Minimum confidence threshold for pipeline detection (default: 0.8)
            patterns_file: Optional path to custom phase patterns YAML file

        Example:
            >>> detector = PhaseDetector()  # Use defaults
            >>> detector = PhaseDetector(patterns_file=".docsible/phase_patterns.yml")
        """
        self.min_confidence = min_confidence
        if patterns_file:
            try:
                self.patterns: dict[Phase, PhasePattern] = PatternLoader.load_from_file(
                    patterns_file
                )
            except Exception:
                self.patterns = PatternLoader.get_defaults()
        else:
            self.patterns = PatternLoader.get_defaults()

    def add_custom_phase(
        self,
        phase: Phase,
        modules: set[str] | None = None,
        keywords: list[str] | None = None,
        priority: int | None = None,
    ) -> None:
        """Add or replace a phase pattern.

        Args:
            phase: Phase enum member
            modules: Set of module names for this phase
            keywords: List of name keywords for this phase
            priority: Priority order (lower = earlier in pipeline)

        Example:
            >>> detector = PhaseDetector()
            >>> detector.add_custom_phase(
            ...     Phase.SETUP,
            ...     modules={"custom_setup_module"},
            ...     keywords=["initialize"],
            ...     priority=1
            ... )
        """
        self.patterns[phase] = PhasePattern(
            modules=modules or set(),
            name_keywords=keywords or [],
            priority=priority if priority is not None else 99,
        )

    def extend_phase(
        self,
        phase: Phase,
        additional_modules: set[str] | None = None,
        additional_keywords: list[str] | None = None,
    ) -> None:
        """Extend an existing phase with additional patterns.

        Args:
            phase: Phase enum member to extend
            additional_modules: Additional module names to add
            additional_keywords: Additional keywords to add

        Example:
            >>> detector = PhaseDetector()
            >>> detector.extend_phase(
            ...     Phase.INSTALL,
            ...     additional_modules={"brew", "chocolatey"},
            ...     additional_keywords=["provision"]
            ... )
        """
        if phase not in self.patterns:
            self.patterns[phase] = PhasePattern(
                modules=set(),
                name_keywords=[],
                priority=99,
            )

        if additional_modules:
            self.patterns[phase].modules.update(additional_modules)
        if additional_keywords:
            self.patterns[phase].name_keywords.extend(additional_keywords)

    def detect_phases(
        self, tasks: list[dict], line_numbers: list[tuple[int, int]] | None = None
    ) -> PhaseDetectionResult:
        """Detect execution phases in a task sequence.

        Args:
            tasks: List of task dictionaries
            line_numbers: Optional list of (start_line, end_line) tuples for each task

        Returns:
            PhaseDetectionResult with detected phases and recommendation
        """
        if not tasks or len(tasks) < 3:
            return PhaseDetectionResult(
                detected_phases=[],
                is_coherent_pipeline=False,
                confidence=0.0,
                recommendation="Too few tasks for phase detection",
                reasoning="Need at least 3 tasks to detect pipeline patterns",
            )

        task_phases = []
        for idx, task in enumerate(tasks):
            phase, confidence = self._detect_task_phase(task)
            task_phases.append((idx, phase, confidence))

        phase_groups = self._group_by_phase(task_phases, line_numbers)

        is_pipeline, pipeline_confidence, reasoning = self._analyze_pipeline_coherence(
            phase_groups, task_phases
        )

        recommendation = self._generate_recommendation(is_pipeline, phase_groups)

        return PhaseDetectionResult(
            detected_phases=phase_groups,
            is_coherent_pipeline=is_pipeline,
            confidence=pipeline_confidence,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    def _detect_task_phase(self, task: dict) -> tuple[Phase, float]:
        """Detect the phase of a single task."""
        if not task:
            return Phase.UNKNOWN, 0.0

        task_name = task.get("name", "").lower()
        task_module = self._extract_module(task)

        phase_scores: dict[Phase, float] = defaultdict(float)

        for phase, patterns in self.patterns.items():
            score = 0.0
            if task_module and task_module in patterns.modules:
                score += 0.7
            for keyword in patterns.name_keywords:
                if keyword in task_name:
                    score += 0.3
                    break
            phase_scores[phase] = min(score, 1.0)

        if not phase_scores:
            return Phase.UNKNOWN, 0.0

        best_phase = max(phase_scores.items(), key=lambda x: x[1])
        return best_phase[0], best_phase[1]

    def _extract_module(self, task: dict) -> str | None:
        """Extract the Ansible module name from a task."""
        skip_keys = {
            "name",
            "when",
            "with_items",
            "loop",
            "notify",
            "tags",
            "become",
            "become_user",
            "register",
            "changed_when",
            "failed_when",
            "ignore_errors",
            "vars",
            "environment",
            "delegate_to",
            "run_once",
            "no_log",
        }

        for key in task.keys():
            if key not in skip_keys:
                module_name = str(key).split(".")[-1]
                return module_name.lower()

        return None

    def _group_by_phase(
        self,
        task_phases: list[tuple[int, Phase, float]],
        line_numbers: list[tuple[int, int]] | None,
    ) -> list[PhaseMatch]:
        """Group consecutive tasks by phase."""
        if not task_phases:
            return []

        groups = []
        current_phase = task_phases[0][1]
        current_indices = [task_phases[0][0]]
        current_confidences = [task_phases[0][2]]

        for idx, phase, confidence in task_phases[1:]:
            if phase == current_phase and phase != Phase.UNKNOWN:
                current_indices.append(idx)
                current_confidences.append(confidence)
            else:
                if current_phase != Phase.UNKNOWN:
                    groups.append(
                        self._create_phase_match(
                            current_phase,
                            current_indices,
                            current_confidences,
                            line_numbers,
                        )
                    )
                current_phase = phase
                current_indices = [idx]
                current_confidences = [confidence]

        if current_phase != Phase.UNKNOWN:
            groups.append(
                self._create_phase_match(
                    current_phase, current_indices, current_confidences, line_numbers
                )
            )

        return groups

    def _create_phase_match(
        self,
        phase: Phase,
        indices: list[int],
        confidences: list[float],
        line_numbers: list[tuple[int, int]] | None,
    ) -> PhaseMatch:
        """Create a PhaseMatch object."""
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        if line_numbers and indices:
            start_line = line_numbers[indices[0]][0]
            end_line = line_numbers[indices[-1]][1]
        else:
            start_line = 0
            end_line = 0

        return PhaseMatch(
            phase=phase,
            start_line=start_line,
            end_line=end_line,
            task_count=len(indices),
            task_indices=indices,
            confidence=avg_confidence,
        )

    def _analyze_pipeline_coherence(
        self,
        phase_groups: list[PhaseMatch],
        task_phases: list[tuple[int, Phase, float]],
    ) -> tuple[bool, float, str]:
        """Analyze if detected phases form a coherent pipeline."""
        if len(phase_groups) < 2:
            return False, 0.0, "Only one phase detected - not a pipeline"

        signals = []

        ordering_score = self._check_phase_ordering(phase_groups)
        signals.append(("sequential_ordering", ordering_score))

        total_tasks = len(task_phases)
        tasks_in_phases = sum(group.task_count for group in phase_groups)
        coverage_score = tasks_in_phases / total_tasks if total_tasks > 0 else 0.0
        signals.append(("phase_coverage", coverage_score))

        avg_phase_confidence = sum(group.confidence for group in phase_groups) / len(phase_groups)
        signals.append(("phase_confidence", avg_phase_confidence))

        repetition_penalty = self._check_phase_repetition(phase_groups)
        signals.append(("no_repetition", 1.0 - repetition_penalty))

        weights = {
            "sequential_ordering": 0.35,
            "phase_coverage": 0.25,
            "phase_confidence": 0.25,
            "no_repetition": 0.15,
        }

        overall_confidence = sum(weights[name] * score for name, score in signals)

        reasoning_parts = []
        for name, score in signals:
            if score >= 0.7:
                reasoning_parts.append(f"\u2713 {name.replace('_', ' ').title()}: {score:.0%}")
            elif score >= 0.5:
                reasoning_parts.append(f"~ {name.replace('_', ' ').title()}: {score:.0%}")
            else:
                reasoning_parts.append(f"\u2717 {name.replace('_', ' ').title()}: {score:.0%}")

        reasoning = " | ".join(reasoning_parts)
        is_pipeline = overall_confidence >= self.min_confidence

        return is_pipeline, overall_confidence, reasoning

    def _check_phase_ordering(self, phase_groups: list[PhaseMatch]) -> float:
        """Check if phases appear in expected sequential order."""
        if len(phase_groups) < 2:
            return 1.0

        correct_transitions = 0
        total_transitions = len(phase_groups) - 1

        for i in range(total_transitions):
            current_priority = self.patterns[phase_groups[i].phase].priority
            next_priority = self.patterns[phase_groups[i + 1].phase].priority
            if next_priority >= current_priority:
                correct_transitions += 1

        return correct_transitions / total_transitions if total_transitions > 0 else 1.0

    def _check_phase_repetition(self, phase_groups: list[PhaseMatch]) -> float:
        """Check for phase repetition (back-and-forth between phases)."""
        if len(phase_groups) < 2:
            return 0.0

        seen_phases: set[Phase] = set()
        repetitions = 0

        for group in phase_groups:
            if group.phase in seen_phases:
                repetitions += 1
            seen_phases.add(group.phase)

        return min(repetitions / len(phase_groups), 1.0)

    def _generate_recommendation(self, is_pipeline: bool, phase_groups: list[PhaseMatch]) -> str:
        """Generate recommendation based on phase detection."""
        if is_pipeline:
            phase_names = " \u2192 ".join([g.phase.value.title() for g in phase_groups])
            return (
                f"\u2705 Keep together - coherent pipeline detected ({phase_names}). "
                f"Sequential workflow is naturally coupled."
            )
        else:
            return (
                "\U0001f500 Consider splitting - no clear pipeline detected. "
                "Tasks may represent mixed functional concerns."
            )


__all__ = [
    "DEFAULT_PATTERNS",
    "PatternLoader",
    "Phase",
    "PhaseDetectionResult",
    "PhaseDetector",
    "PhaseMatch",
    "PhasePattern",
]
