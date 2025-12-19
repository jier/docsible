"""Phase detector implementation."""

from collections import defaultdict
from pathlib import Path

from .models import Phase, PhaseDetectionResult, PhaseMatch, PhasePattern
from .patterns import PatternLoader


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

    def __init__(
        self, min_confidence: float = 0.8, patterns_file: str | Path | None = None
    ):
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
                self.patterns: dict[Phase, PhasePattern] = PatternLoader.load_from_file(patterns_file)
            except Exception:
                # Fall back to defaults on any error
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
            modules= modules or set(),
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
            # Create new pattern if it doesn't exist
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

    def _detect_task_phase(self, task: dict) -> tuple[Phase, float]:
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

        for phase, patterns in self.patterns.items():
            score = 0.0

            # Check module match (strong signal)
            if task_module and task_module in patterns.modules:
                score += 0.7

            # Check name keywords (moderate signal)
            for keyword in patterns.name_keywords:
                if keyword in task_name:
                    score += 0.3
                    break

            phase_scores[phase] = min(score, 1.0)

        # Get highest scoring phase
        if not phase_scores:
            return Phase.UNKNOWN, 0.0

        best_phase = max(phase_scores.items(), key=lambda x: x[1])
        return best_phase[0], best_phase[1]

    def _extract_module(self, task: dict) -> str | None:
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
                module_name = str(key).split(".")[-1]
                return module_name.lower()

        return None

    def _group_by_phase(
        self,
        task_phases: list[tuple[int, Phase, float]],
        line_numbers: list[tuple[int, int]] | None,
    ) -> list[PhaseMatch]:
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
        indices: list[int],
        confidences: list[float],
        line_numbers: list[tuple[int, int]] | None,
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
        phase_groups: list[PhaseMatch],
        task_phases: list[tuple[int, Phase, float]],
    ) -> tuple[bool, float, str]:
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

    def _check_phase_ordering(self, phase_groups: list[PhaseMatch]) -> float:
        """Check if phases appear in expected sequential order.

        Args:
            phase_groups: List of phase groups

        Returns:
            Score between 0.0 and 1.0
        """
        if len(phase_groups) < 2:
            return 1.0

        # Count how many phase transitions are in correct order
        correct_transitions = 0
        total_transitions = len(phase_groups) - 1

        for i in range(total_transitions):
            current_priority = self.patterns[phase_groups[i].phase].priority
            next_priority = self.patterns[phase_groups[i + 1].phase].priority

            if next_priority >= current_priority:
                correct_transitions += 1

        return correct_transitions / total_transitions if total_transitions > 0 else 1.0

    def _check_phase_repetition(self, phase_groups: list[PhaseMatch]) -> float:
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
        self, is_pipeline: bool, phase_groups: list[PhaseMatch]
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
