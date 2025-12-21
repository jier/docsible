"""Dependency analysis data for documentation."""

from typing import Any

from pydantic import BaseModel, Field


class DependencyData(BaseModel):
    """Container for dependency analysis information."""
    
    dependency_matrix: str | None = Field(
        default=None,
        description="Dependency matrix visualization"
    )
    dependency_summary: dict[str, Any] | None = Field(
        default=None,
        description="Summary of dependencies"
    )
    show_dependency_matrix: bool = Field(
        default=False,
        description="Whether to display the matrix"
    )
    
    class Config:
        frozen = False
