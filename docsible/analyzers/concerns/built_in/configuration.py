"""Configuration management concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


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
        return [
            "template",
            "copy",
            "lineinfile",
            "blockinfile",
            "replace",
            "assemble",
            "ini_file",
            "xml",
            # Windows
            "win_template",
            "win_copy",
            "win_lineinfile",
        ]

    @property
    def suggested_filename(self) -> str:
        return "configure.yml"

    @property
    def priority(self) -> int:
        return 40
