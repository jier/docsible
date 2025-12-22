from typing import Any

from pydantic import BaseModel, Field


class RenderContext(BaseModel):
    """Complete context for rendering a role README.

    Encapsulates all data needed for template rendering, reducing
    the parameter count from 25+ individual parameters to structured
    data objects.

    This Pydantic model provides validation, serialization, and a clean
    API for configuring role rendering.

    Example:
        >>> context = RenderContext(
        ...     role_info={'name': 'my_role', 'description': 'A test role'},
        ...     template_type='hybrid',
        ...     no_vars=False,
        ...     no_diagrams=False
        ... )
        >>> renderer.render_role_from_context(context, Path('README.md'))
    """

    # Core data (required)
    role_info: dict[str, Any] = Field(..., description="Role information dictionary")

    # Template configuration
    template_type: str = Field(
        default="standard",
        description="Template type ('standard', 'hybrid', 'hybrid_modular')"
    )
    custom_template_path: str | None = Field(
        default=None,
        description="Optional custom template file path"
    )

    # Diagrams
    mermaid_code_per_file: dict[str, str] | None = Field(
        default=None, description="Task flow graphs per file"
    )
    sequence_diagram_high_level: str | None = Field(
        default=None, description="High-level sequence diagram"
    )
    sequence_diagram_detailed: str | None = Field(
        default=None, description="Detailed sequence diagram"
    )
    state_diagram: str | None = Field(
        default=None, description="State transition diagram"
    )
    integration_boundary_diagram: str | None = Field(
        default=None, description="Integration boundary diagram"
    )
    architecture_diagram: str | None = Field(
        default=None, description="Architecture overview diagram"
    )

    # Dependencies
    dependency_matrix: str | None = Field(
        default=None, description="Dependency matrix diagram"
    )
    dependency_summary: dict[str, Any] | None = Field(
        default=None, description="Dependency analysis summary"
    )
    show_dependency_matrix: bool = Field(
        default=False, description="Show dependency matrix in output"
    )

    # Complexity
    complexity_report: Any | None = Field(
        default=None, description="Complexity analysis results"
    )
    include_complexity: bool | None = Field(
        default=None, description="Include complexity report in output"
    )

    # Content control flags
    no_vars: bool = Field(default=False, description="Skip variable documentation")
    no_tasks: bool = Field(default=False, description="Skip task documentation")
    no_diagrams: bool = Field(default=False, description="Skip all diagrams")
    simplify_diagrams: bool = Field(default=False, description="Show only simplified diagrams")
    no_examples: bool = Field(default=False, description="Skip example playbooks")
    no_metadata: bool = Field(default=False, description="Skip metadata section")
    no_handlers: bool = Field(default=False, description="Skip handlers documentation")

    # Output mode
    append: bool = Field(
        default=False,
        description="Append to existing README instead of replacing"
    )

    class ConfigDict:
        """Pydantic configuration."""
        frozen = False  # Allow modification if needed
        validate_assignment = True  # Validate on attribute assignment
    
    def to_template_dict(self) -> dict[str, Any]:
        """Convert to dictionary for template rendering.

        Returns:
            Dictionary with all template variables properly formatted

        Example:
            >>> context = RenderContext(role_info={'name': 'test'})
            >>> template_vars = context.to_template_dict()
            >>> template.render(**template_vars)
        """
        return {
            "role": self.role_info,
            "mermaid_code_per_file": self.mermaid_code_per_file or {},
            "sequence_diagram_high_level": self.sequence_diagram_high_level,
            "sequence_diagram_detailed": self.sequence_diagram_detailed,
            "state_diagram": self.state_diagram,
            "integration_boundary_diagram": self.integration_boundary_diagram,
            "architecture_diagram": self.architecture_diagram,
            "complexity_report": self.complexity_report,
            "include_complexity": self.include_complexity,
            "dependency_matrix": self.dependency_matrix,
            "dependency_summary": self.dependency_summary,
            "show_dependency_matrix": self.show_dependency_matrix,
            "no_vars": self.no_vars,
            "no_tasks": self.no_tasks,
            "no_diagrams": self.no_diagrams,
            "simplify_diagrams": self.simplify_diagrams,
            "no_examples": self.no_examples,
            "no_metadata": self.no_metadata,
            "no_handlers": self.no_handlers,
        }
