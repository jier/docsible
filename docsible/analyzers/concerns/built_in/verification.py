"""Verification and health check concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import VERIFY_MODULES


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
        return sorted(VERIFY_MODULES)

    @property
    def suggested_filename(self) -> str:
        return "verify.yml"

    @property
    def priority(self) -> int:
        return 60  # Lower priority (more generic)
