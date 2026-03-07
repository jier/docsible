from enum import Enum


class Severity(Enum):
    """Recommendation severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

    @property
    def icon(self) -> str:
        """Get emoji icon for severity."""
        return {
            Severity.CRITICAL: "🔴",
            Severity.WARNING: "🟡",
            Severity.INFO: "💡",
        }[self]

    @property
    def label(self) -> str:
        """Get human-readable label."""
        return {
            Severity.CRITICAL: "CRITICAL",
            Severity.WARNING: "WARNING",
            Severity.INFO: "INFO",
        }[self]

    @property
    def priority(self) -> int:
        """Get sort priority (higher = more urgent)."""
        return {
            Severity.CRITICAL: 3,
            Severity.WARNING: 2,
            Severity.INFO: 1,
        }[self]


