
from pydantic import BaseModel, Field

from docsible.models.severity import Severity


class Recommendation(BaseModel):
    """Enhanced recommendation with severity."""

    # Core fields (existing)
    category: str = Field(description="Category like 'security', 'documentation'")
    message: str = Field(description="User-facing message")
    rationale: str = Field(description="Why this matters")

    # New severity field
    severity: Severity = Field(
        default=Severity.INFO,
        description="Severity level for prioritization"
    )

    # Optional context
    file_path: str | None = Field(None, description="Affected file")
    line_number: int | None= Field(None, description="Line number if applicable")
    remediation: str | None = Field(None, description="How to fix")

    # Metadata
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence in this recommendation (0.0-1.0)"
    )
    auto_fixable: bool = Field(
        default=False,
        description="Can be auto-fixed with --auto-fix"
    )

    @property
    def location(self) -> str:
        """Format file location for display."""
        if self.file_path:
            if self.line_number:
                return f"{self.file_path}:{self.line_number}"
            return self.file_path
        return ""