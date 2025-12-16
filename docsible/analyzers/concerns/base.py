"""Base classes for concern detection."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ConcernMatch(BaseModel):
    """Represents a detected concern in a task file."""

    concern_name: str = Field(description="Name of the concern (e.g., 'package_installation')")
    confidence: float = Field(description="Confidence score 0.0-1.0", ge=0.0, le=1.0)
    task_count: int = Field(description="Number of tasks matching this concern")
    matched_modules: List[str] = Field(default_factory=list, description="Modules that matched")
    task_indices: List[int] = Field(default_factory=list, description="Indices of matching tasks")

    # Human-readable attributes
    display_name: str = Field(description="Human-readable concern name")
    description: str = Field(description="What this concern represents")
    suggested_filename: str = Field(description="Suggested task filename if split")

    @property
    def is_dominant(self) -> bool:
        """Check if this concern is dominant (>60% confidence)."""
        return self.confidence >= 0.6


class ConcernDetector(ABC):
    """
    Abstract base class for concern detectors.

    Each concern detector identifies a specific responsibility/concern
    in Ansible tasks (e.g., package installation, configuration, etc.).

    Example:
        >>> class PackageConcern(ConcernDetector):
        ...     @property
        ...     def concern_name(self) -> str:
        ...         return "package_installation"
        ...
        ...     @property
        ...     def module_patterns(self) -> list:
        ...         return ["apt", "yum", "pip"]
    """

    @property
    @abstractmethod
    def concern_name(self) -> str:
        """
        Unique identifier for this concern.

        Example: 'package_installation'
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for this concern.

        Example: 'Package Installation'
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description of what this concern represents.

        Example: 'Installing and managing system packages'
        """
        pass

    @property
    @abstractmethod
    def module_patterns(self) -> List[str]:
        """
        List of module name patterns that indicate this concern.

        Supports:
        - Exact match: "apt"
        - Prefix match: "win_" (matches win_service, win_user, etc.)
        - Suffix match: "_db" (matches mysql_db, postgresql_db, etc.)

        Example: ["apt", "yum", "dnf", "package", "pip", "npm"]
        """
        pass

    @property
    def suggested_filename(self) -> str:
        """
        Suggested filename if this concern is split into separate file.

        Default: concern_name.yml
        Can be overridden for custom naming.

        Example: 'install.yml' instead of 'package_installation.yml'
        """
        return f"{self.concern_name}.yml"

    @property
    def priority(self) -> int:
        """
        Priority for detection (lower = higher priority).

        Used when multiple concerns match the same tasks.
        Default: 50 (medium priority)

        Example priorities:
        - 10: Very specific (e.g., Windows PowerShell)
        - 50: Common (e.g., package installation)
        - 90: Generic fallback (e.g., verification)
        """
        return 50

    def matches_module(self, module_name: str) -> bool:
        """
        Check if a module name matches this concern's patterns.

        Args:
            module_name: Ansible module name (e.g., "ansible.builtin.apt")

        Returns:
            True if module matches this concern's patterns

        Example:
            >>> detector.module_patterns = ["apt", "yum"]
            >>> detector.matches_module("ansible.builtin.apt")
            True
            >>> detector.matches_module("template")
            False
        """
        # Extract base module name (remove FQCN)
        base_module = module_name.split(".")[-1] if "." in module_name else module_name

        for pattern in self.module_patterns:
            if pattern.endswith("_"):
                # Prefix match: "win_" matches "win_service"
                if base_module.startswith(pattern):
                    return True
            elif pattern.startswith("_"):
                # Suffix match: "_db" matches "mysql_db"
                if base_module.endswith(pattern):
                    return True
            else:
                # Exact match (case-insensitive)
                if pattern.lower() == base_module.lower():
                    return True

        return False

    def detect(self, tasks: List[Dict[str, Any]]) -> ConcernMatch:
        """
        Detect this concern in a list of tasks.

        Args:
            tasks: List of task dictionaries

        Returns:
            ConcernMatch with confidence score and details

        Example:
            >>> tasks = [{"module": "apt", "name": "Install nginx"}]
            >>> match = detector.detect(tasks)
            >>> match.confidence
            1.0
            >>> match.task_count
            1
        """
        if not tasks:
            return ConcernMatch(
                concern_name=self.concern_name,
                confidence=0.0,
                task_count=0,
                display_name=self.display_name,
                description=self.description,
                suggested_filename=self.suggested_filename,
            )

        matched_tasks = []
        matched_modules = []

        for idx, task in enumerate(tasks):
            module_name = task.get("module", "")
            if self.matches_module(module_name):
                matched_tasks.append(idx)
                matched_modules.append(module_name)

        # Calculate confidence as percentage of tasks matched
        confidence = len(matched_tasks) / len(tasks) if tasks else 0.0

        return ConcernMatch(
            concern_name=self.concern_name,
            confidence=confidence,
            task_count=len(matched_tasks),
            matched_modules=list(set(matched_modules)),
            task_indices=matched_tasks,
            display_name=self.display_name,
            description=self.description,
            suggested_filename=self.suggested_filename,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.display_name}>"
