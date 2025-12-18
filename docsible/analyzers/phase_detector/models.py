
from enum import Enum

from pydantic import BaseModel, Field


class Phase(Enum):
    """Common execution phases in Ansible workflows."""

    SETUP = "setup"
    INSTALL = "install"
    CONFIGURE = "configure"
    DEPLOY = "deploy"
    ACTIVATE = "activate"
    VERIFY = "verify"
    CLEANUP = "cleanup"
    UNKNOWN = "unknown"


class PhaseMatch(BaseModel):
    """Represents a detected phase in a task sequence."""

    phase: Phase
    start_line: int = Field(ge=0, description="Starting line number in source file")
    end_line: int = Field(ge=0, description="Ending line number in source file")
    task_count: int = Field(gt=0, description="Number of tasks in this phase")
    task_indices: list[int] = Field(description="Task indices belonging to this phase")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0")


class PhaseDetectionResult(BaseModel):
    """Result of phase detection analysis."""

    detected_phases: list[PhaseMatch] = Field(default_factory=list)
    is_coherent_pipeline: bool = Field(
        description="Whether tasks form a coherent pipeline"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Overall pipeline confidence"
    )
    recommendation: str = Field(description="Human-readable recommendation")
    reasoning: str = Field(description="Explanation of the analysis")


class PhasePattern(BaseModel):
    """Pattern for detecting a specific phase.

    Converted from TypedDict to BaseModel for consistency with other models
    and to get validation, serialization, and better IDE support.
    """

    modules: set[str] = Field(
        default_factory=set, description="Ansible modules associated with this phase"
    )
    name_keywords: list[str] = Field(
        default_factory=list, description="Keywords in task names indicating this phase"
    )
    priority: int = Field(default=99, description="Priority for phase detection (lower = higher priority)")