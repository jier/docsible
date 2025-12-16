"""Artifact management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


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
        return [
            # Download/fetch
            "get_url",
            "uri",
            # Archive
            "unarchive",
            "archive",
            # Source control
            "git",
            "svn",
            "hg",
            # Artifact repositories
            "maven_artifact",
            "nexus_artifact",
            # Windows
            "win_get_url",
            "win_unzip",
        ]

    @property
    def suggested_filename(self) -> str:
        return "artifact.yml"

    @property
    def priority(self) -> int:
        return 45
