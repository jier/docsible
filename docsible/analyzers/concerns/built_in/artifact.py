"""Artifact management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import ARTIFACT_MODULES


class ArtifactManagementConcern(ConcernDetector):
    """Detects artifact download and deployment tasks."""

    @property
    def concern_name(self) -> str:
        return "artifact_management"

    @property
    def display_name(self) -> str:
        return "Artifact Management"

    @property
    def description(self) -> str:
        return "Downloading and deploying application artifacts"

    @property
    def module_patterns(self) -> list:
        return sorted(ARTIFACT_MODULES)

    @property
    def suggested_filename(self) -> str:
        return "artifact.yml"

    @property
    def priority(self) -> int:
        return 45
