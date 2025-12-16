"""Identity and permission concern detector."""

from docsible.analyzers.concerns.base import ConcernDetector


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
        return [
            # User/Group management
            "user",
            "group",
            "authorized_key",
            # Permissions
            "acl",
            # SELinux
            "selinux",
            "seboolean",
            "seport",
            "sefcontext",
            # Windows
            "win_user",
            "win_group",
            "win_acl",
        ]

    @property
    def suggested_filename(self) -> str:
        return "identity.yml"

    @property
    def priority(self) -> int:
        return 45
