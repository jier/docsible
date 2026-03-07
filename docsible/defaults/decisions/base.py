"""Base classes for decision-making system."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from docsible.defaults.detectors.complexity import Category


class DecisionContext(BaseModel):
    """All information available for making decisions.

    This is the "world state" that decision rules examine.
    Aggregates all detection results into one queryable object.
    """

    # From ComplexityDetector
    complexity_category: Category = Field(description="Which complexity category do we base our decision on")
    total_tasks: int = Field(ge=0, description="Amount of total tasks")
    complexity_score: float = Field(ge=0.0, description="Score on complexity calculation")
    has_dependencies: bool = Field(default=False, description="Does Role have dependencies in meta/main.yml")

    # From StructureDetector
    has_handlers: bool = Field(description="Does Role has handlers check")
    uses_advanced_features: bool = Field(description="Does Role uses advance futures")
    task_file_count: int = Field(ge=0, description="Amount of tasks file count in the Role")

    # User overrides (CLI flags that were explicitly set)
    user_overrides: dict[str, Any] = Field(description="User has the choice to override decision")

    @property
    def is_simple_role(self) -> bool:
        """Convenience method for rules."""
        return self.complexity_category == Category.SIMPLE

    @property
    def is_complex_role(self) -> bool:
        """Convenience method for rules."""
        return self.complexity_category in (Category.COMPLEX, Category.ENTERPRISE)

    def user_specified(self, option: str) -> bool:
        """Check if user explicitly set an option."""
        return option in self.user_overrides



class Decision(BaseModel):
    """A single configuration decision.

    Immutable decision object that can be logged, traced, and audited.
    """

    option_name: str = Field(description="CLI option being decided (e.g., 'generate_graph'")
    value: Any = Field(default=list[bool | str],description="Decided value (e.g., True, False, 'auto')")
    rationale: str = Field(description="Why this decision was made (for debugging/logging)")
    confidence: float = Field(ge=0.0, le=1.0, description="How confident we are (0.0 - 1.0)")
    rule_name: str = Field(description="Which rule made this decision")
    overrideable: bool = Field(default=True, description="Can user override this decision?")


class DecisionRule(ABC):
    """Abstract base for decision rules.

    Each rule examines the context and makes ONE decision.
    Rules are composable and independently testable.
    """

    @abstractmethod
    def decide(self, context: DecisionContext) -> Decision | None:
        """Make a decision based on context.

        Args:
            context: All available information for decision-making

        Returns:
            Decision if rule applies, None if rule doesn't apply

        Example:
            If context shows simple role, GraphRule returns Decision(generate_graph=False)
            If context shows complex role, GraphRule returns Decision(generate_graph=True)
            If context is ambiguous, GraphRule might return None (delegate to next rule)
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Rule priority (higher = evaluated first).

        Why priority?
        - User overrides should be highest priority
        - Explicit detections should beat heuristics
        - Provides deterministic rule ordering
        """
        pass