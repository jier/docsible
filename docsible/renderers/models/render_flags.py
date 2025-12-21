from pydantic import BaseModel, Field


class RenderFlags(BaseModel):
    """Feature flags controlling what content to include.
    
    All flags default to False (include everything).
    Set to True to exclude that section.
    """
    
    no_vars: bool = Field(
        default=False,
        description="Exclude variables section"
    )
    no_tasks: bool = Field(
        default=False,
        description="Exclude tasks section"
    )
    no_diagrams: bool = Field(
        default=False,
        description="Exclude all diagrams"
    )
    simplify_diagrams: bool = Field(
        default=False,
        description="Show only high-level diagrams"
    )
    no_examples: bool = Field(
        default=False,
        description="Exclude example playbooks"
    )
    no_metadata: bool = Field(
        default=False,
        description="Exclude metadata section"
    )
    no_handlers: bool = Field(
        default=False,
        description="Exclude handlers section"
    )
    
    class ConfigDict:
        frozen = False
