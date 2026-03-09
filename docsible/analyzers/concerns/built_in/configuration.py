"""Configuration management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import CONFIG_MODULES


class ConfigurationConcern(ConcernDetector):
    """Detects configuration file management tasks."""

    @property
    def concern_name(self) -> str:
        return "configuration"

    @property
    def display_name(self) -> str:
        return "Configuration Management"

    @property
    def description(self) -> str:
        return "Managing configuration files and templates"

    @property
    def module_patterns(self) -> list:
        return sorted(CONFIG_MODULES)

    @property
    def suggested_filename(self) -> str:
        return "configure.yml"

    @property
    def priority(self) -> int:
        return 40
