"""Windows/PowerShell concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


class WindowsPowerShellConcern(ConcernDetector):
    """Detects Windows-specific and PowerShell tasks."""

    @property
    def concern_name(self) -> str:
        return "windows_management"

    @property
    def display_name(self) -> str:
        return "Windows Management"

    @property
    def description(self) -> str:
        return "Windows-specific tasks using PowerShell and win_* modules"

    @property
    def module_patterns(self) -> list:
        return [
            # Windows prefix (matches all win_* modules)
            "win_",
            # PowerShell
            "win_shell",
            "win_command",
            "win_powershell",
            # Specific Windows modules
            "win_feature",
            "win_regedit",
            "win_updates",
        ]

    @property
    def suggested_filename(self) -> str:
        return "windows.yml"

    @property
    def priority(self) -> int:
        return 10  # Very specific, high priority
