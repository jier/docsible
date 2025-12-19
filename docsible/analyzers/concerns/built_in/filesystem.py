"""Filesystem management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


class FilesystemManagementConcern(ConcernDetector):
    """Detects filesystem and storage management tasks."""

    @property
    def concern_name(self) -> str:
        return "filesystem_management"

    @property
    def display_name(self) -> str:
        return "Filesystem Management"

    @property
    def description(self) -> str:
        return "Managing filesystems, mounts, directories, and storage"

    @property
    def module_patterns(self) -> list:
        return [
            # File/Directory operations
            "file",
            "find",
            "stat",
            # Filesystem
            "filesystem",
            "mount",
            # LVM
            "lvg",
            "lvol",
            # Partitions
            "parted",
            "disk",
            # Windows
            "win_file",
            "win_disk_facts",
        ]

    @property
    def suggested_filename(self) -> str:
        return "filesystem.yml"

    @property
    def priority(self) -> int:
        return 50
