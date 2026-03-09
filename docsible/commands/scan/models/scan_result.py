from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RoleResult:
    name: str
    path: Path
    task_count: int
    variable_count: int
    complexity: str  # "low", "medium", "high", "unknown"
    critical_count: int
    warning_count: int
    info_count: int
    top_recommendations: list[str] = field(default_factory=list)
    error: str | None = None  # set if role processing failed


@dataclass
class ScanCollectionResult:
    collection_path: Path
    total_roles: int
    roles: list[RoleResult]

    @property
    def roles_with_critical(self) -> list[RoleResult]:
        return [r for r in self.roles if r.critical_count > 0]

    @property
    def roles_with_warnings(self) -> list[RoleResult]:
        return [r for r in self.roles if r.warning_count > 0]

    @property
    def total_critical(self) -> int:
        return sum(r.critical_count for r in self.roles)

    @property
    def total_warnings(self) -> int:
        return sum(r.warning_count for r in self.roles)
