from pathlib import Path
from .models import Phase, PhasePattern

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
    def load_from_file(path: Path) -> dict[Phase, PhasePattern]:
        """Parse YAML patterns file."""
        # Pattern loading logic
        pass
    
    @staticmethod
    def get_defaults() -> dict[Phase, PhasePattern]:
        """Get default patterns."""
        return DEFAULT_PATTERNS.copy()
