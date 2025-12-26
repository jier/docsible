"""Structure detection for Ansible roles."""

import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from docsible.constants import MINIMUM_TASK_FILES, MINIMUM_WELL_ORGANISED
from docsible.defaults.detectors.base import DetectionResult, Detector

logger = logging.getLogger(__name__)


class StructureFindings(BaseModel):
    """What structural elements exist in the role."""

    has_tasks: bool = Field(description="Does Role has tasks files")
    has_handlers: bool = Field(description="Does Role has handlers files")
    has_defaults: bool = Field(description="Does Role has defaults")
    has_vars: bool = Field(description="Does Role has vars files")
    has_meta: bool = Field(description="Does Role has meta files")
    has_templates: bool = Field(description="Does Role has template files")
    has_files: bool = Field(description="Does Role has files at all")

    # Advanced structure
    uses_includes: bool = Field(description="Does Role use include of tasks/roles")
    uses_imports: bool = Field(description="Does Role use imports of tasks/roles")
    uses_roles: bool = Field(description="Does Role uses Roles")
    uses_blocks: bool = Field(description="Does Role tasks use Block sections")

    # File organization
    task_file_count: int = Field(ge=0, description="Amount of tasks in current Role folder")
    handler_file_count: int = Field(ge=0, description="Amount of Handlers in Role folder")

    @property
    def is_well_organized(self) -> bool:
        """Heuristic: Is this role well-organized?"""
        return (
            self.has_meta
            and self.has_defaults
            and self.task_file_count <= MINIMUM_WELL_ORGANISED  # Not too fragmented
        )

    @property
    def needs_detailed_docs(self) -> bool:
        """Should we generate detailed documentation?"""
        return (
            self.uses_includes
            or self.uses_imports
            or self.uses_roles
            or self.task_file_count > MINIMUM_TASK_FILES
        )


class StructureDetector(Detector):
    """Detects structural characteristics of an Ansible role.

    This detector examines:
    - What standard directories exist
    - What advanced features are used
    - How files are organized
    """

    def detect(self, role_path: Path) -> DetectionResult:
        """Detect structural characteristics.

        Args:
            role_path: Path to Ansible role

        Returns:
            DetectionResult with StructureFindings
        """
        self.validate_role_path(role_path)

        try:
            findings = StructureFindings(
                # Standard directories
                has_tasks=(role_path / "tasks").exists(),
                has_handlers=(role_path / "handlers").exists(),
                has_defaults=(role_path / "defaults").exists(),
                has_vars=(role_path / "vars").exists(),
                has_meta=(role_path / "meta").exists(),
                has_templates=(role_path / "templates").exists(),
                has_files=(role_path / "files").exists(),
                # Advanced features (detected by scanning task files)
                uses_includes=self._detect_includes(role_path),
                uses_imports=self._detect_imports(role_path),
                uses_roles=self._detect_role_usage(role_path),
                uses_blocks=self._detect_blocks(role_path),
                # File counts
                task_file_count=self._count_yaml_files(role_path / "tasks"),
                handler_file_count=self._count_yaml_files(role_path / "handlers"),
            )

            return DetectionResult(
                detector_name="StructureDetector",
                findings=findings.model_dump(),
                confidence=1.0,  # File existence checks are always confident
                metadata={
                    "scanned_directories": [
                        "tasks",
                        "handlers",
                        "defaults",
                        "vars",
                        "meta",
                        "templates",
                        "files",
                    ]
                },
            )

        except Exception as e:
            logger.error(f"Structure detection failed for {role_path}: {e}")
            return DetectionResult(
                detector_name="StructureDetector",
                findings=self._default_findings(),
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _detect_includes(self, role_path: Path) -> bool:
        """Check if role uses include_tasks."""
        return self._pattern_exists(role_path, "include_tasks")

    def _detect_imports(self, role_path: Path) -> bool:
        """Check if role uses import_tasks."""
        return self._pattern_exists(role_path, "import_tasks")

    def _detect_role_usage(self, role_path: Path) -> bool:
        """Check if role calls other roles."""
        return self._pattern_exists(role_path, "include_role") or self._pattern_exists(
            role_path, "import_role"
        )

    def _detect_blocks(self, role_path: Path) -> bool:
        """Check if role uses block/rescue/always."""
        return (
            self._pattern_exists(role_path, "block:")
            or self._pattern_exists(role_path, "rescue:")
            or self._pattern_exists(role_path, "always:")
        )

    def _pattern_exists(self, role_path: Path, pattern: str) -> bool:
        """Check if pattern exists in any YAML file.

        This is a simple implementation. Production version might use:
        - YAML parsing for accuracy
        - Caching for performance
        - Parallel scanning for speed
        """
        tasks_dir = role_path / "tasks"
        if not tasks_dir.exists():
            return False

        for yaml_file in tasks_dir.glob("**/*.yml"):
            try:
                content = yaml_file.read_text()
                if pattern in content:
                    return True
            except Exception:
                # Ignore files we can't read
                continue

        return False

    def _count_yaml_files(self, directory: Path) -> int:
        """Count YAML files in directory."""
        if not directory.exists():
            return 0

        return len(list(directory.glob("*.yml"))) + len(list(directory.glob("*.yaml")))

    def _default_findings(self) -> dict[str, Any]:
        """Safe defaults when detection fails."""
        return StructureFindings(
            has_tasks=False,
            has_handlers=False,
            has_defaults=False,
            has_vars=False,
            has_meta=False,
            has_templates=False,
            has_files=False,
            uses_includes=False,
            uses_imports=False,
            uses_roles=False,
            uses_blocks=False,
            task_file_count=0,
            handler_file_count=0,
        ).model_dump()
