"""Pydantic models for pattern analysis.

This module defines the data structures used throughout the pattern
analysis system. Using Pydantic provides:
- Automatic validation
- Type safety
- JSON serialization
- Clear schema documentation
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SeverityLevel(str, Enum):
    """Severity levels for pattern findings.

    Used to prioritize which patterns need immediate attention.
    """

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PatternCategory(str, Enum):
    """Categories of patterns detected.

    Helps organize findings by type of issue.
    """

    DUPLICATION = "duplication"
    COMPLEXITY = "complexity"
    IDEMPOTENCY = "idempotency"
    ORGANIZATION = "organization"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ERROR_HANDLING = "error_handling"


class SimplificationSuggestion(BaseModel):
    """Suggestion for improving a role by addressing an anti-pattern.

    Each suggestion represents one detected pattern with:
    - What was found (description)
    - Where it was found (affected_files)
    - Why it matters (impact)
    - How to fix it (suggestion)

    Attributes:
        pattern: Unique identifier for the pattern type
        category: High-level categorization
        severity: How important this issue is
        description: Human-readable explanation of what was found
        example: Code snippet showing the problematic pattern
        suggestion: Detailed refactoring guidance with examples
        affected_files: Files where this pattern appears
        impact: Expected benefit of applying the suggestion
        line_numbers: Optional specific line numbers where pattern appears
        confidence: How certain we are this is actually a problem (0.0-1.0)
    """

    pattern: str = Field(
        description="Pattern identifier (e.g., 'repeated_package_install')",
        min_length=1,
    )

    category: PatternCategory = Field(description="Category this pattern belongs to")

    severity: SeverityLevel = Field(
        description="Severity level: info, warning, or critical"
    )

    description: str = Field(
        description="Human-readable description of the issue", min_length=1
    )

    example: str = Field(
        default="", description="Code example showing the problematic pattern"
    )

    suggestion: str = Field(
        description="Recommended refactoring approach with code examples", min_length=1
    )

    affected_files: list[str] = Field(
        default_factory=list, description="List of files affected by this pattern"
    )

    impact: str = Field(
        description="Expected impact of applying the suggestion", min_length=1
    )

    line_numbers: list[int] | None = Field(
        default=None, description="Specific line numbers where pattern appears"
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0) that this is a real issue",
    )

    @field_validator("affected_files")
    @classmethod
    def validate_files(cls, v: list[str]) -> list[str]:
        """Ensure file paths are unique."""
        return list(set(v))

    class ConfigDict:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "pattern": "repeated_package_install",
                "category": "duplication",
                "severity": "warning",
                "description": "Found 12 separate apt tasks",
                "example": "- name: Install nginx\\n  apt: name=nginx",
                "suggestion": "Combine into single task with loop",
                "affected_files": ["tasks/install.yml"],
                "impact": "Reduces 12 tasks to 1 task (-11 tasks)",
                "confidence": 0.95,
            }
        }


class PatternAnalysisReport(BaseModel):
    """Complete report of all patterns found in a role.

    Aggregates findings from all pattern detectors and provides
    summary statistics.

    Attributes:
        suggestions: List of all detected patterns
        total_patterns: Total number of patterns found
        by_severity: Count of patterns by severity level
        by_category: Count of patterns by category
        overall_health_score: Overall role health (0-100)
    """

    suggestions: list[SimplificationSuggestion] = Field(
        default_factory=list, description="All detected patterns and suggestions"
    )

    total_patterns: int = Field(
        default=0, ge=0, description="Total number of patterns detected"
    )

    by_severity: dict[str, int] = Field(
        default_factory=dict, description="Count of patterns grouped by severity"
    )

    by_category: dict[str, int] = Field(
        default_factory=dict, description="Count of patterns grouped by category"
    )

    overall_health_score: float = Field(
        default=100.0,
        ge=0.0,
        le=100.0,
        description="Overall role health score (0-100, higher is better)",
    )

    def calculate_metrics(self) -> None:
        """Calculate summary metrics from suggestions.

        This should be called after all suggestions are added.
        """
        self.total_patterns = len(self.suggestions)

        # Count by severity
        self.by_severity = {"info": 0, "warning": 0, "critical": 0}
        for suggestion in self.suggestions:
            self.by_severity[suggestion.severity.value] += 1

        # Count by category
        self.by_category = {}
        for suggestion in self.suggestions:
            cat = suggestion.category.value
            self.by_category[cat] = self.by_category.get(cat, 0) + 1

        # Calculate health score (simplified algorithm)
        # Start at 100, deduct points for issues
        score = 100.0
        score -= self.by_severity["info"] * 2
        score -= self.by_severity["warning"] * 5
        score -= self.by_severity["critical"] * 15

        self.overall_health_score = max(0.0, score)

    class ConfigDict:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "suggestions": [],
                "total_patterns": 5,
                "by_severity": {"info": 2, "warning": 2, "critical": 1},
                "by_category": {"duplication": 3, "security": 2},
                "overall_health_score": 75.0,
            }
        }
