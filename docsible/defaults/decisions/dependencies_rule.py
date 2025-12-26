from docsible.defaults.decisions.base import Decision, DecisionContext, DecisionRule


class DependenciesDecisionRule(DecisionRule):
    """Decides whether to show role dependencies in documentation.

    Business Logic:
    - Roles with dependencies SHOULD document them (helps users understand setup)
    - Roles without dependencies don't need a dependencies section
    - Complex roles with dependencies get higher confidence

    Dependencies are important for:
    - Installation instructions
    - Understanding role relationships
    - Avoiding conflicts
    """

    @property
    def priority(self) -> int:
        """Priority 90 = higher than minimal/graph but not override."""
        return 90

    def decide(self, context: DecisionContext) -> Decision | None:
        """Decide whether to show dependencies in documentation.

        Decision tree:
        1. If user explicitly set show_dependencies → respect it
        2. If role has dependencies → show them with high confidence
        3. If complex role (might have meta/dependencies) → moderate confidence
        4. Otherwise → don't show (no dependencies to document)
        """
        # 1. Check for user override
        if context.user_specified("show_dependencies"):
            # User explicitly set this, don't override
            return None

        # 2. Role has dependencies → definitely show them
        if self._has_dependencies(context):
            return Decision(
                option_name="show_dependencies",
                value=True,
                rationale=(
                    "Role has dependencies that should be documented "
                    "to help users understand installation requirements"
                ),
                confidence=0.9,
                rule_name="DependenciesDecisionRule"
            )

        # 3. Complex role → likely to have dependencies worth checking
        if context.is_complex_role:
            return Decision(
                option_name="show_dependencies",
                value=True,
                rationale=(
                    f"Complex role ({context.complexity_category}) may have "
                    "dependencies worth documenting"
                ),
                confidence=0.5,  # Lower confidence - we're guessing
                rule_name="DependenciesDecisionRule"
            )

        # 4. Default: no dependencies, don't show
        return Decision(
            option_name="show_dependencies",
            value=False,
            rationale="Role has no dependencies to document",
            confidence=0.8,
            rule_name="DependenciesDecisionRule"
        )

    def _has_dependencies(self, context: DecisionContext) -> bool:
        """Check if role has dependencies.

        Note: This relies on ComplexityDetector detecting role_dependencies
        from meta/main.yml. The field is exposed as 'has_dependencies' in findings.
        """
        # The has_dependencies field comes from ComplexityDetector
        # It's set when ComplexityMetrics.role_dependencies > 0
        return context.has_dependencies
