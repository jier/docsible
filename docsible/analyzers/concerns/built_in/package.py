"""Package installation concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import PACKAGE_MODULES


class PackageInstallationConcern(ConcernDetector):
    """Detects package installation and management tasks."""

    @property
    def concern_name(self) -> str:
        return "package_installation"

    @property
    def display_name(self) -> str:
        return "Package Installation"

    @property
    def description(self) -> str:
        return "Installing and managing system packages"

    @property
    def module_patterns(self) -> list:
        return sorted(PACKAGE_MODULES)

    @property
    def suggested_filename(self) -> str:
        return "install.yml"

    @property
    def priority(self) -> int:
        return 40  # Higher priority than generic concerns
