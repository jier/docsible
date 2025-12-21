"""Configuration for rendering behavior."""

from pydantic import BaseModel, Field


class RenderConfig(BaseModel):
    """Configuration for how to render documentation.
    
    Attributes:
        template_type: Type of template ('standard', 'hybrid', 'hybrid_modular')
        custom_template_path: Path to custom template file
        append: Append to existing README instead of replacing
        backup: Create backup before overwriting
        validate: Run markdown validation
        auto_fix: Automatically fix markdown issues
        strict_validation: Fail on validation errors
    """
    
    template_type: str = Field(
        default="standard",
        description="Template type to use"
    )
    custom_template_path: str | None = Field(
        default=None,
        description="Path to custom template file"
    )
    append: bool = Field(
        default=False,
        description="Append to existing file"
    )
    backup: bool = Field(
        default=True,
        description="Create backup before overwriting"
    )
    markdown_validation: bool = Field(
        default=True,
        description="Run markdown validation"
    )
    auto_fix: bool = Field(
        default=False,
        description="Auto-fix markdown issues"
    )
    strict_validation: bool = Field(
        default=False,
        description="Fail on validation errors"
    )
    
    class ConfigDict:
        frozen = False  # Allow modification if needed
