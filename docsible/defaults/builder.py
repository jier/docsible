"""Configuration builder using decisions."""

import logging
from typing import Any

from docsible.defaults.config import DocumentationConfig
from docsible.defaults.decisions.base import Decision

logger = logging.getLogger(__name__)


class ConfigurationBuilder:
    """Builds DocumentationConfig from Decision objects.

    This is the Builder pattern:
    - Constructs complex object step-by-step
    - Handles decision conflicts
    - Provides default values
    - Validates final configuration
    """

    def __init__(self) -> None:
        """Initialize builder with empty state."""
        self._decisions: list[Decision] = []
        self._config_values: dict[str, Any] = {}

    def add_decision(self, decision: Decision) -> "ConfigurationBuilder":
        """Add a decision to the builder.

        Fluent interface (returns self) for chaining:
            builder.add_decision(d1).add_decision(d2).build()

        Args:
            decision: Decision to incorporate

        Returns:
            Self for method chaining
        """
        if decision is None:
            return self

        # Record decision
        self._decisions.append(decision)

        # Check for conflicts
        if decision.option_name in self._config_values:
            existing = self._config_values[decision.option_name]
            logger.warning(
                f"Decision conflict for {decision.option_name}: "
                f"was {existing}, now {decision.value}"
            )

        # Store value
        self._config_values[decision.option_name] = decision.value

        return self

    def add_decisions(self, decisions: list[Decision]) -> "ConfigurationBuilder":
        """Add multiple decisions.

        Args:
            decisions: List of decisions to add

        Returns:
            Self for method chaining
        """
        for decision in decisions:
            self.add_decision(decision)
        return self

    def build(self) -> DocumentationConfig:
        """Build final DocumentationConfig.

        Returns:
            Complete configuration object
        """
        # Calculate overall confidence
        confidence = self._calculate_confidence()

        # Build config with decisions
        config = DocumentationConfig(
            **self._config_values,
            decisions=self._decisions,
            confidence=confidence
        )

        # Validate
        self._validate_config(config)

        logger.info(
            f"Built configuration with {len(self._decisions)} decisions "
            f"({confidence:.0%} confidence)"
        )

        return config

    def _calculate_confidence(self) -> float:
        """Calculate overall confidence from all decisions.

        Uses weighted average based on decision confidence levels.
        """
        if not self._decisions:
            return 1.0  # Default config, full confidence

        total_confidence = sum(d.confidence for d in self._decisions)
        return total_confidence / len(self._decisions)

    def _validate_config(self, config: DocumentationConfig) -> None:
        """Validate configuration makes sense.

        Catches contradictory settings like:
        - minimal=True AND complexity_report=True (contradictory)
        - no_diagrams=True AND generate_graph=True (contradictory)

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Check for contradictions
        if config.minimal and config.complexity_report:
            logger.warning(
                "Contradictory config: minimal=True but complexity_report=True. "
                "Disabling complexity_report."
            )
            config.complexity_report = False

        if config.no_diagrams and config.generate_graph:
            logger.warning(
                "Contradictory config: no_diagrams=True but generate_graph=True. "
                "Respecting no_diagrams."
            )
            config.generate_graph = False