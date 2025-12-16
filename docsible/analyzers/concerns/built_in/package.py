"""Package installation concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


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
        return [
            # System packages
            "apt",
            "apt_repository",
            "yum",
            "dnf",
            "package",
            "zypper",
            "pacman",
            "homebrew",
            # Language-specific packages
            "pip",
            "pip3",
            "npm",
            "gem",
            "composer",
            "maven",
            # Container images
            "docker_image",
            "podman_image",
        ]

    @property
    def suggested_filename(self) -> str:
        return "install.yml"

    @property
    def priority(self) -> int:
        return 40  # Higher priority than generic concerns
