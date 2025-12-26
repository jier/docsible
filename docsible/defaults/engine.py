"""Smart defaults engine - orchestrates detection and decision-making."""

import logging
from pathlib import Path
from typing import Any

from docsible.defaults.builder import ConfigurationBuilder
from docsible.defaults.config import DocumentationConfig
from docsible.defaults.decisions.base import DecisionContext
from docsible.defaults.decisions.dependencies_rule import DependenciesDecisionRule
from docsible.defaults.decisions.graph_rule import GraphDecisionRule
from docsible.defaults.decisions.minimal_rule import MinimalModeRule
from docsible.defaults.detectors.complexity import Category, ComplexityDetector
from docsible.defaults.detectors.structure import StructureDetector

logger = logging.getLogger(__name__)


class SmartDefaultsEngine:
    """Orchestrates detection → decision → configuration pipeline.

    This is the Facade pattern:
    - Hides complexity of detection/decision subsystems
    - Provides simple interface for CLI
    - Coordinates multiple components
    """

    def __init__(self) -> None:
        """Initialize engine with detectors and rules."""
        # Detection layer
        self.detectors = [
            ComplexityDetector(),
            StructureDetector(),
        ]

        # Decision layer (ordered by priority)
        self.rules = sorted(
            [
                GraphDecisionRule(),
                MinimalModeRule(),
                DependenciesDecisionRule(),
            ],
            key=lambda r: r.priority,
            reverse=True  # Highest priority first
        )

    def generate_config(
        self,
        role_path: Path,
        user_overrides: dict[str, Any] | None = None
    ) -> tuple[DocumentationConfig, Any | None]:
        """Generate smart configuration for role.

        This is the main entry point used by CLI.

        Args:
            role_path: Path to Ansible role
            user_overrides: CLI flags user explicitly set

        Returns:
            Tuple of (DocumentationConfig, ComplexityReport | None)

            The ComplexityReport is returned for reuse by the orchestrator
            to avoid duplicate complexity analysis. Returns None if detection fails.
        """
        logger.info(f"Generating smart defaults for {role_path}")

        # Phase 1: Detection
        detection_results = self._run_detectors(role_path)

        # Phase 2: Build context
        context = self._build_context(detection_results, user_overrides or {})

        # Phase 3: Make decisions
        decisions = self._make_decisions(context)

        # Phase 4: Build configuration
        config = (
            ConfigurationBuilder()
            .add_decisions(decisions)
            .build()
        )

        logger.info(
            f"Generated config with {len(config.decisions)} decisions "
            f"({config.confidence:.0%} confidence)"
        )

        # Extract ComplexityReport from detection results for reuse
        complexity_report = self._extract_complexity_report(detection_results)

        return config, complexity_report

    def _run_detectors(self, role_path: Path) -> list[Any]:
        """Run all detectors and collect results.

        Args:
            role_path: Path to analyze

        Returns:
            List of DetectionResult objects
        """
        results = []

        for detector in self.detectors:
            try:
                result = detector.detect(role_path)
                results.append(result)
                logger.debug(
                    f"{detector.__class__.__name__}: "
                    f"{result.confidence:.0%} confidence"
                )
            except Exception as e:
                logger.error(
                    f"Detector {detector.__class__.__name__} failed: {e}"
                )
                # Continue with other detectors

        return results

    def _build_context(
        self,
        detection_results: list[Any],
        user_overrides: dict[str, Any]
    ) -> DecisionContext:
        """Build decision context from detection results.

        Aggregates all detection findings into single context object.

        Args:
            detection_results: Results from all detectors
            user_overrides: User-provided CLI flags

        Returns:
            DecisionContext for rules to examine
        """
        # Type-safe extraction with defaults - initialize as empty dicts
        complexity_findings: dict[str, Any] = {}
        structure_findings: dict[str, Any] = {}

        for result in detection_results:
            if result.detector_name == "ComplexityDetector":
                complexity_findings = result.findings
            elif result.detector_name == "StructureDetector":
                structure_findings = result.findings

        # Extract category value - convert to Category enum
        category_value = complexity_findings.get("category", Category.MEDIUM)

        # Ensure it's a Category enum (handle both enum and string)
        if isinstance(category_value, Category):
            category_enum = category_value
        elif isinstance(category_value, str):
            # Map string to enum
            category_map = {
                "simple": Category.SIMPLE,
                "medium": Category.MEDIUM,
                "complex": Category.COMPLEX,
                "enterprise": Category.ENTERPRISE,
            }
            category_enum = category_map.get(category_value.lower(), Category.MEDIUM)
        else:
            # Fallback
            category_enum = Category.MEDIUM

        # Build context with safe defaults - clean, no ternaries needed
        context = DecisionContext(
            # Complexity
            complexity_category=category_enum,
            total_tasks=complexity_findings.get("total_tasks", 0),
            complexity_score=complexity_findings.get("complexity_score", 0.5),
            has_dependencies=complexity_findings.get("has_dependencies", False),

            # Structure
            has_handlers=structure_findings.get("has_handlers", False),
            uses_advanced_features=(
                structure_findings.get("uses_includes", False) or
                structure_findings.get("uses_imports", False) or
                structure_findings.get("uses_roles", False)
            ),
            task_file_count=structure_findings.get("task_file_count", 0),

            # User overrides
            user_overrides=user_overrides
        )

        return context

    def _make_decisions(self, context: DecisionContext) -> list[Any]:
        """Apply all decision rules to context.

        Args:
            context: Complete decision context

        Returns:
            List of Decision objects
        """
        decisions = []

        for rule in self.rules:
            try:
                decision = rule.decide(context)
                if decision is not None:
                    decisions.append(decision)
                    logger.debug(
                        f"{rule.__class__.__name__}: "
                        f"{decision.option_name} = {decision.value}"
                    )
            except Exception as e:
                logger.error(f"Rule {rule.__class__.__name__} failed: {e}")
                # Continue with other rules

        return decisions

    def _extract_complexity_report(self, detection_results: list[Any]) -> Any | None:
        """Extract ComplexityReport from detection results for reuse.

        Args:
            detection_results: Results from all detectors

        Returns:
            ComplexityReport if available, None otherwise
        """
        for result in detection_results:
            if result.detector_name == "ComplexityDetector":
                # Check if the detector stored the full report in metadata
                complexity_report = result.metadata.get("complexity_report")
                if complexity_report:
                    logger.debug("Extracted ComplexityReport for reuse by orchestrator")
                    return complexity_report

        logger.debug("No ComplexityReport found in detection results")
        return None