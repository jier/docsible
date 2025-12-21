from pydantic import BaseModel, Field


class DiagramData(BaseModel):
    """Container for all diagram-related data.
    
    Holds Mermaid diagrams and other visualizations.
    """
    
    mermaid_code_per_file: dict[str, str] | None = Field(
        default=None,
        description="Task flow graphs per file"
    )
    sequence_diagram_high_level: str | None = Field(
        default=None,
        description="High-level sequence diagram"
    )
    sequence_diagram_detailed: str | None = Field(
        default=None,
        description="Detailed sequence diagram"
    )
    state_diagram: str | None = Field(
        default=None,
        description="State transition diagram"
    )
    integration_boundary_diagram: str | None = Field(
        default=None,
        description="Integration boundary diagram"
    )
    architecture_diagram: str | None = Field(
        default=None,
        description="Architecture overview diagram"
    )
    
    class ConfigDict:
        frozen = False
    
    def has_any_diagram(self) -> bool:
        """Check if any diagram is present."""
        return any([
            self.mermaid_code_per_file,
            self.sequence_diagram_high_level,
            self.sequence_diagram_detailed,
            self.state_diagram,
            self.integration_boundary_diagram,
            self.architecture_diagram,
        ])
