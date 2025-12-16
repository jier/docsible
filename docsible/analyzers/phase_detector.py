"""Phase detection for Ansible task files.

Detects whether tasks follow a chronological pipeline pattern
(setup → deploy → configure → verify → cleanup) or represent
mixed functional concerns that should be split.

Uses a conservative approach to minimize false positives.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple
from collections import defaultdict


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


@dataclass
class PhaseMatch:
    """Represents a detected phase in a task sequence."""

    phase: Phase
    start_line: int
    end_line: int
    task_count: int
    task_indices: List[int]
    confidence: float  # 0.0-1.0


@dataclass
class PhaseDetectionResult:
    """Result of phase detection analysis."""

    detected_phases: List[PhaseMatch]
    is_coherent_pipeline: bool
    confidence: float  # Overall confidence that this is a pipeline
    recommendation: str
    reasoning: str


class PhaseDetector:
    """Detects execution phases in Ansible task files."""

    # Phase detection patterns
    PHASE_PATTERNS = {
        Phase.SETUP: {
            "modules": {
                "assert",
                "debug",
                "set_fact",
                "include_vars",
                "stat",
                "fail",
                "when",
            },
            "name_keywords": [
                "prerequisite",
                "pre-requisite",
                "check",
                "validate",
                "ensure",
                "verify prerequisite",
            ],
            "priority": 1,  # Typically first
        },
        Phase.INSTALL: {
            "modules": {
                "apt",
                "yum",
                "dnf",
                "pip",
                "npm",
                "package",
                "gem",
                "docker_image",
                "get_url",
                "git",
                "unarchive",
                "maven_artifact",
            },
            "name_keywords": [
                "install",
                "download",
                "fetch",
                "pull",
                "clone",
                "acquire",
            ],
            "priority": 2,
        },
        Phase.CONFIGURE: {
            "modules": {
                "template",
                "copy",
                "lineinfile",
                "blockinfile",
                "file",
                "replace",
                "ini_file",
                "xml",
            },
            "name_keywords": [
                "configure",
                "config",
                "setup",
                "set up",
                "create config",
                "apply config",
            ],
            "priority": 3,
        },
        Phase.DEPLOY: {
            "modules": {"command", "shell", "docker_container", "kubernetes", "k8s"},
            "name_keywords": ["deploy", "run", "execute", "launch", "apply"],
            "priority": 4,
        },
        Phase.ACTIVATE: {
            "modules": {"service", "systemd", "supervisorctl", "docker_container"},
            "name_keywords": ["start", "enable", "activate", "restart", "reload"],
            "priority": 5,
        },
        Phase.VERIFY: {
            "modules": {"uri", "wait_for", "assert", "ping", "command", "shell"},
            "name_keywords": [
                "verify",
                "test",
                "check",
                "validate",
                "health check",
                "smoke test",
                "wait for",
                "ensure running",
            ],
            "priority": 6,
        },
        Phase.CLEANUP: {
            "modules": {"file", "command", "shell"},
            "name_keywords": [
                "cleanup",
                "clean up",
                "remove",
                "delete",
                "purge",
                "temporary",
            ],
            "priority": 7,  # Typically last
        },
    }

    def __init__(self, min_confidence: float = 0.8):
        """Initialize phase detector.

        Args:
            min_confidence: Minimum confidence threshold for pipeline detection (default: 0.8)
        """
        self.min_confidence = min_confidence

    def detect_phases(
        self, tasks: List[Dict], line_numbers: Optional[List[Tuple[int, int]]] = None
    ) -> PhaseDetectionResult:
        """Detect execution phases in a task sequence.

        Args:
            tasks: List of task dictionaries
            line_numbers: Optional list of (start_line, end_line) tuples for each task

        Returns:
            PhaseDetectionResult with detected phases and recommendation
        """
        if not tasks or len(tasks) < 3:
            # Too few tasks to detect meaningful phases
            return PhaseDetectionResult(
                detected_phases=[],
                is_coherent_pipeline=False,
                confidence=0.0,
                recommendation="Too few tasks for phase detection",
                reasoning="Need at least 3 tasks to detect pipeline patterns",
            )

        # Assign phases to each task
        task_phases = []
        for idx, task in enumerate(tasks):
            phase, confidence = self._detect_task_phase(task)
            task_phases.append((idx, phase, confidence))

        # Group consecutive tasks by phase
        phase_groups = self._group_by_phase(task_phases, line_numbers)

        # Analyze if this is a coherent pipeline
        is_pipeline, pipeline_confidence, reasoning = self._analyze_pipeline_coherence(
            phase_groups, task_phases
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(is_pipeline, phase_groups)

        return PhaseDetectionResult(
            detected_phases=phase_groups,
            is_coherent_pipeline=is_pipeline,
            confidence=pipeline_confidence,
            recommendation=recommendation,
            reasoning=reasoning,
        )

    def _detect_task_phase(self, task: Dict) -> Tuple[Phase, float]:
        """Detect the phase of a single task.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (Phase, confidence_score)
        """
        if not task:
            return Phase.UNKNOWN, 0.0

        task_name = task.get("name", "").lower()
        task_module = self._extract_module(task)

        # Score each phase
        phase_scores = defaultdict(float)

        for phase, patterns in self.PHASE_PATTERNS.items():
            score = 0.0

            # Check module match (strong signal)
            if task_module and task_module in patterns["modules"]:
                score += 0.7

            # Check name keywords (moderate signal)
            for keyword in patterns["name_keywords"]:
                if keyword in task_name:
                    score += 0.3
                    break

            phase_scores[phase] = min(score, 1.0)

        # Get highest scoring phase
        if not phase_scores:
            return Phase.UNKNOWN, 0.0

        best_phase = max(phase_scores.items(), key=lambda x: x[1])
        return best_phase[0], best_phase[1]

    def _extract_module(self, task: Dict) -> Optional[str]:
        """Extract the Ansible module name from a task.

        Args:
            task: Task dictionary

        Returns:
            Module name or None
        """
        # Skip non-module keys
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
                # Handle fully qualified collection names
                module_name = key.split(".")[-1]
                return module_name.lower()

        return None

    def _group_by_phase(
        self,
        task_phases: List[Tuple[int, Phase, float]],
        line_numbers: Optional[List[Tuple[int, int]]],
    ) -> List[PhaseMatch]:
        """Group consecutive tasks by phase.

        Args:
            task_phases: List of (task_idx, phase, confidence) tuples
            line_numbers: Optional list of (start_line, end_line) tuples

        Returns:
            List of PhaseMatch objects
        """
        if not task_phases:
            return []

        groups = []
        current_phase = task_phases[0][1]
        current_indices = [task_phases[0][0]]
        current_confidences = [task_phases[0][2]]

        for idx, phase, confidence in task_phases[1:]:
            if phase == current_phase and phase != Phase.UNKNOWN:
                # Continue current phase
                current_indices.append(idx)
                current_confidences.append(confidence)
            else:
                # End current phase, start new one
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

        # Add final phase
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
        indices: List[int],
        confidences: List[float],
        line_numbers: Optional[List[Tuple[int, int]]],
    ) -> PhaseMatch:
        """Create a PhaseMatch object.

        Args:
            phase: The phase
            indices: Task indices in this phase
            confidences: Confidence scores for each task
            line_numbers: Optional line number information

        Returns:
            PhaseMatch object
        """
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
        phase_groups: List[PhaseMatch],
        task_phases: List[Tuple[int, Phase, float]],
    ) -> Tuple[bool, float, str]:
        """Analyze if detected phases form a coherent pipeline.

        Args:
            phase_groups: Grouped phases
            task_phases: Individual task phase assignments

        Returns:
            Tuple of (is_pipeline, confidence, reasoning)
        """
        if len(phase_groups) < 2:
            return False, 0.0, "Only one phase detected - not a pipeline"

        # Conservative approach: check multiple signals
        signals = []

        # Signal 1: Sequential ordering (phases appear in expected priority order)
        ordering_score = self._check_phase_ordering(phase_groups)
        signals.append(("sequential_ordering", ordering_score))

        # Signal 2: Phase coverage (what % of tasks are in detected phases)
        total_tasks = len(task_phases)
        tasks_in_phases = sum(group.task_count for group in phase_groups)
        coverage_score = tasks_in_phases / total_tasks if total_tasks > 0 else 0.0
        signals.append(("phase_coverage", coverage_score))

        # Signal 3: Phase distinctiveness (average confidence of phase assignments)
        avg_phase_confidence = sum(group.confidence for group in phase_groups) / len(
            phase_groups
        )
        signals.append(("phase_confidence", avg_phase_confidence))

        # Signal 4: Minimal back-and-forth (phases shouldn't repeat)
        repetition_penalty = self._check_phase_repetition(phase_groups)
        signals.append(("no_repetition", 1.0 - repetition_penalty))

        # Overall confidence: weighted average of signals
        weights = {
            "sequential_ordering": 0.35,
            "phase_coverage": 0.25,
            "phase_confidence": 0.25,
            "no_repetition": 0.15,
        }

        overall_confidence = sum(weights[name] * score for name, score in signals)

        # Build reasoning
        reasoning_parts = []
        for name, score in signals:
            if score >= 0.7:
                reasoning_parts.append(
                    f"✓ {name.replace('_', ' ').title()}: {score:.0%}"
                )
            elif score >= 0.5:
                reasoning_parts.append(
                    f"~ {name.replace('_', ' ').title()}: {score:.0%}"
                )
            else:
                reasoning_parts.append(
                    f"✗ {name.replace('_', ' ').title()}: {score:.0%}"
                )

        reasoning = " | ".join(reasoning_parts)

        is_pipeline = overall_confidence >= self.min_confidence

        return is_pipeline, overall_confidence, reasoning

    def _check_phase_ordering(self, phase_groups: List[PhaseMatch]) -> float:
        """Check if phases appear in expected sequential order.

        Args:
            phase_groups: List of phase groups

        Returns:
            Score between 0.0 and 1.0
        """
        if len(phase_groups) < 2:
            return 1.0

        # Get expected ordering from priorities
        expected_order = sorted(
            phase_groups, key=lambda g: self.PHASE_PATTERNS[g.phase]["priority"]
        )

        # Count how many phase transitions are in correct order
        correct_transitions = 0
        total_transitions = len(phase_groups) - 1

        for i in range(total_transitions):
            current_priority = self.PHASE_PATTERNS[phase_groups[i].phase]["priority"]
            next_priority = self.PHASE_PATTERNS[phase_groups[i + 1].phase]["priority"]

            if next_priority >= current_priority:
                correct_transitions += 1

        return correct_transitions / total_transitions if total_transitions > 0 else 1.0

    def _check_phase_repetition(self, phase_groups: List[PhaseMatch]) -> float:
        """Check for phase repetition (back-and-forth between phases).

        Args:
            phase_groups: List of phase groups

        Returns:
            Penalty score between 0.0 (no repetition) and 1.0 (high repetition)
        """
        if len(phase_groups) < 2:
            return 0.0

        seen_phases = set()
        repetitions = 0

        for group in phase_groups:
            if group.phase in seen_phases:
                repetitions += 1
            seen_phases.add(group.phase)

        # Normalize by number of groups
        return min(repetitions / len(phase_groups), 1.0)

    def _generate_recommendation(
        self, is_pipeline: bool, phase_groups: List[PhaseMatch]
    ) -> str:
        """Generate recommendation based on phase detection.

        Args:
            is_pipeline: Whether a coherent pipeline was detected
            phase_groups: Detected phase groups

        Returns:
            Recommendation string
        """
        if is_pipeline:
            phase_names = " → ".join([g.phase.value.title() for g in phase_groups])
            return (
                f"✅ Keep together - coherent pipeline detected ({phase_names}). "
                f"Sequential workflow is naturally coupled."
            )
        else:
            return (
                "🔀 Consider splitting - no clear pipeline detected. "
                "Tasks may represent mixed functional concerns."
            )
