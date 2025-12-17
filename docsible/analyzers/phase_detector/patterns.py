"""Phase pattern definitions and loading logic."""

import logging
from pathlib import Path

from .models import Phase, PhasePattern

logger = logging.getLogger(__name__)

DEFAULT_PATTERNS: dict[Phase, PhasePattern] = {
    Phase.SETUP: {
            "modules": {
                "assert",
                "debug",
                "set_fact",
                "include_vars",
                "stat",
                "fail",
                "when",
            },
            "name_keywords": [
                "prerequisite",
                "pre-requisite",
                "check",
                "validate",
                "ensure",
                "verify prerequisite",
            ],
            "priority": 1,  # Typically first
        },
        Phase.INSTALL: {
            "modules": {
                "apt",
                "yum",
                "dnf",
                "pip",
                "npm",
                "package",
                "gem",
                "docker_image",
                "get_url",
                "git",
                "unarchive",
                "maven_artifact",
            },
            "name_keywords": [
                "install",
                "download",
                "fetch",
                "pull",
                "clone",
                "acquire",
            ],
            "priority": 2,
        },
        Phase.CONFIGURE: {
            "modules": {
                "template",
                "copy",
                "lineinfile",
                "blockinfile",
                "file",
                "replace",
                "ini_file",
                "xml",
            },
            "name_keywords": [
                "configure",
                "config",
                "setup",
                "set up",
                "create config",
                "apply config",
            ],
            "priority": 3,
        },
        Phase.DEPLOY: {
            "modules": {"command", "shell", "docker_container", "kubernetes", "k8s"},
            "name_keywords": ["deploy", "run", "execute", "launch", "apply"],
            "priority": 4,
        },
        Phase.ACTIVATE: {
            "modules": {"service", "systemd", "supervisorctl", "docker_container"},
            "name_keywords": ["start", "enable", "activate", "restart", "reload"],
            "priority": 5,
        },
        Phase.VERIFY: {
            "modules": {"uri", "wait_for", "assert", "ping", "command", "shell"},
            "name_keywords": [
                "verify",
                "test",
                "check",
                "validate",
                "health check",
                "smoke test",
                "wait for",
                "ensure running",
            ],
            "priority": 6,
        },
        Phase.CLEANUP: {
            "modules": {"file", "command", "shell"},
            "name_keywords": [
                "cleanup",
                "clean up",
                "remove",
                "delete",
                "purge",
                "temporary",
            ],
            "priority": 7,  # Typically last
        },
}


class PatternLoader:
    """Loads phase patterns from files or defaults."""

    @staticmethod
    def load_from_file(path: Path | str) -> dict[Phase, PhasePattern]:
        """Parse YAML patterns file.

        Args:
            path: Path to YAML patterns file

        Returns:
            Dictionary mapping Phase to PhasePattern

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        import yaml

        patterns_path = Path(path)
        with open(patterns_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        patterns = {}
        phases_config = config.get("phases", {})

        for phase_name, pattern_config in phases_config.items():
            # Try to match to existing Phase enum
            phase = PatternLoader._get_phase_by_name(phase_name)

            patterns[phase] = {
                "modules": set(pattern_config.get("modules", [])),
                "name_keywords": pattern_config.get("name_keywords", []),
                "priority": pattern_config.get("priority", 99),
            }

        return patterns

    @staticmethod
    def _get_phase_by_name(name: str) -> Phase:
        """Get Phase enum by name, case-insensitive.

        Args:
            name: Phase name

        Returns:
            Phase enum member

        Note:
            If phase name doesn't match any existing Phase, returns Phase.UNKNOWN
        """
        name_upper = name.upper()
        for phase in Phase:
            if phase.name == name_upper:
                return phase
        return Phase.UNKNOWN

    @staticmethod
    def get_defaults() -> dict[Phase, PhasePattern]:
        """Get default patterns (as a copy).

        Returns:
            Copy of DEFAULT_PATTERNS dictionary
        """
        return {phase: patterns.copy() for phase, patterns in DEFAULT_PATTERNS.items()}
