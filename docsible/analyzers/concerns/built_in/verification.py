"""Verification and health check concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


class VerificationConcern(ConcernDetector):
    """Detects verification, health check, and validation tasks."""

    @property
    def concern_name(self) -> str:
        return "verification"

    @property
    def display_name(self) -> str:
        return "Verification & Health Checks"

    @property
    def description(self) -> str:
        return "Validating state and running health checks"

    @property
    def module_patterns(self) -> list:
        return [
            # Assertions and checks
            "assert",
            "fail",
            "wait_for",
            "ping",
            # Commands (often used for verification)
            "command",
            "shell",
            # Debug
            "debug",
            "pause",
            # Windows
            "win_ping",
            "win_wait_for",
        ]

    @property
    def suggested_filename(self) -> str:
        return "verify.yml"

    @property
    def priority(self) -> int:
        return 60  # Lower priority (more generic)
