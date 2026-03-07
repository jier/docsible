import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """Result from a single detector.

    This is our contract - every detector must return this shape.
    Enforces consistency and makes testing easier.
    """

    detector_name: str = Field(description="Name of the detector that produced this result")
    findings: dict[str, Any] = Field(description="Dictionary of findings from detection")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level (0.0 - 1.0) in the findings")
    metadata: dict[str, Any] | None = Field(default=None, description="Optional metadata about the detection process")


class Detector(ABC):
    """Abstract base class for all detectors.

    Why abstract class?
    - Enforces interface contract via type system
    - Provides common functionality (like logging)
    - Makes it impossible to forget to implement detect()
    - Self-documenting: "This is a Detector, it must detect()"
    """

    def __init__(self) -> None:
        """Initialize detector with common setup."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def detect(self, role_path: Path) -> DetectionResult:
        """Detect specific aspect of the role.

        Args:
            role_path: Path to the Ansible role directory

        Returns:
            DetectionResult with findings

        Raises:
            ValueError: If role_path doesn't exist or is invalid
        """
        pass

    def validate_role_path(self, role_path: Path) -> None:
        """Common validation logic - DRY principle.

        Args:
            role_path: Path to validate

        Raises:
            ValueError: If path is invalid
        """
        if not role_path.exists():
            raise ValueError(f"Role path does not exist: {role_path}")

        if not role_path.is_dir():
            raise ValueError(f"Role path must be a directory: {role_path}")