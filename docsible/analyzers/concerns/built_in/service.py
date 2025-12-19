"""Service management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


class ServiceManagementConcern(ConcernDetector):
    """Detects service and daemon management tasks."""

    @property
    def concern_name(self) -> str:
        return "service_management"

    @property
    def display_name(self) -> str:
        return "Service Management"

    @property
    def description(self) -> str:
        return "Managing systemd services and daemons"

    @property
    def module_patterns(self) -> list:
        return [
            "service",
            "systemd",
            "sysvinit",
            "supervisorctl",
            # Windows
            "win_service",
        ]

    @property
    def suggested_filename(self) -> str:
        return "service.yml"

    @property
    def priority(self) -> int:
        return 40
