from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Critical issues that must be fixed
    WARNING = "warning"  # Issues that should be addressed
    INFO = "info"  # Suggestions for improvement


class ValidationType(str, Enum):
    """Types of validation checks."""

    CLARITY = "clarity"
    MAINTENANCE = "maintenance"
    TRUTH = "truth"
    VALUE = "value"


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""

    type: ValidationType
    severity: ValidationSeverity
    message: str
    line_number: int | None = None
    section: str | None = None
    suggestion: str | None = None


class ValidationResult(BaseModel):
    """Results from documentation validation."""

    passed: bool
    score: float = Field(ge=0.0, le=100.0, description="Overall quality score 0-100")
    issues: list[ValidationIssue] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)

    def get_issues_by_type(
        self, validation_type: ValidationType
    ) -> list[ValidationIssue]:
        """Get all issues of a specific validation type."""
        return [issue for issue in self.issues if issue.type == validation_type]

    def get_issues_by_severity(
        self, severity: ValidationSeverity
    ) -> list[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)