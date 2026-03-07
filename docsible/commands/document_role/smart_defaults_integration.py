"""Smart defaults integration for CLI commands."""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def apply_smart_defaults(
    role_path: Path,
    user_overrides: dict[str, bool],
) -> tuple[bool, bool, bool, Any | None]:
    """Apply smart defaults based on role complexity analysis.

    Args:
        role_path: Path to the role directory
        user_overrides: Dictionary of flags explicitly set by user

    Returns:
        Tuple of (generate_graph, minimal, show_dependencies, complexity_report)

        The complexity_report is the full ComplexityReport from the analysis,
        which can be reused by the orchestrator to avoid duplicate analysis.

    Example:
        >>> overrides = {"generate_graph": True}  # User set --graph
        >>> graph, minimal, deps, report = apply_smart_defaults(role_path, overrides)
        >>> graph  # True (user override)
        >>> minimal  # False (smart default)
        >>> report  # ComplexityReport for reuse
    """
    try:
        from docsible.defaults.engine import SmartDefaultsEngine

        logger.info(f"Analyzing role for smart defaults: {role_path}")

        # Run smart defaults engine
        engine = SmartDefaultsEngine()
        config, complexity_report = engine.generate_config(
            role_path, user_overrides=user_overrides
        )

        # Log decisions made
        logger.info(f"Smart defaults applied (confidence: {config.confidence:.0%})")
        for decision in config.decisions:
            logger.debug(
                f"  {decision.option_name} = {decision.value} "
                f"({decision.confidence:.0%} confident: {decision.rationale})"
            )

        return (
            config.generate_graph,
            config.minimal,
            config.show_dependencies,
            complexity_report,  # Return for reuse by orchestrator
        )

    except Exception as e:
        # Fallback to safe defaults if analysis fails
        logger.warning(f"Smart defaults analysis failed: {e}")
        logger.warning("Using manual configuration")
        # Return conservative defaults (no complexity report available)
        return (False, False, False, None)
