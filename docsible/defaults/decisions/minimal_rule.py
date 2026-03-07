"""Decision rule for minimal mode."""

from docsible.defaults.decisions.base import Decision, DecisionContext, DecisionRule


class MinimalModeRule(DecisionRule):
    """Decides when to use minimal documentation mode.

    Minimal mode:
    - Hides variable documentation
    - Hides metadata
    - Hides examples
    - Focuses on tasks only

    When to use:
    - Internal roles (not shared)
    - Simple, self-explanatory roles
    - Quick reference docs
    """

    @property
    def priority(self) -> int:
        """Priority 80 = lower than feature decisions, composes them."""
        return 80

    def decide(self, context: DecisionContext) -> Decision | None:
        """Decide whether to enable minimal mode."""

        # User explicitly set minimal?
        if context.user_specified("minimal"):
            return None  # Already handled by CLI

        # Auto-detect: simple role with no advanced features
        if self._should_be_minimal(context):
            return Decision(
                option_name="minimal",
                value=True,
                rationale=(
                    "Simple role without handlers, includes, or complex structure - "
                    "minimal docs sufficient"
                ),
                confidence=0.7,
                rule_name="MinimalModeRule"
            )

        # Default: not minimal
        return Decision(
            option_name="minimal",
            value=False,
            rationale="Role complexity justifies full documentation",
            confidence=0.6,
            rule_name="MinimalModeRule"
        )

    def _should_be_minimal(self, context: DecisionContext) -> bool:
        """Heuristic for when minimal mode is appropriate."""
        return (
            context.total_tasks <= 5 and
            not context.has_handlers and
            not context.uses_advanced_features and
            context.task_file_count == 1
        )