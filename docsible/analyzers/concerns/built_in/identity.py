"""Identity and permission concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector
from docsible.analyzers.shared.module_taxonomy import IDENTITY_MODULES


class IdentityPermissionConcern(ConcernDetector):
    """Detects user, group, and permission management tasks."""

    @property
    def concern_name(self) -> str:
        return "identity_permission"

    @property
    def display_name(self) -> str:
        return "Identity & Permission Management"

    @property
    def description(self) -> str:
        return "Managing users, groups, SSH keys, and file permissions"

    @property
    def module_patterns(self) -> list:
        # SELinux modules are identity-specific and not in the shared taxonomy
        selinux_modules = ["selinux", "seboolean", "seport", "sefcontext"]
        return sorted(IDENTITY_MODULES) + selinux_modules

    @property
    def suggested_filename(self) -> str:
        return "identity.yml"

    @property
    def priority(self) -> int:
        return 45
