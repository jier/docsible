"""Canonical Ansible module groupings shared across analyzer subsystems.

These frozensets are the single source of truth for which modules belong to
which functional category. Import these constants instead of defining inline
lists in individual analyzers.

Each frozenset includes both short names (``apt``) and FQCN variants
(``ansible.builtin.apt``) to handle both old and modern Ansible style.

Note: Prefix/suffix pattern strings (e.g. ``"win_"``, ``"_db"``) used by
concern detectors for partial matching are intentionally excluded — those live
in the concern detectors themselves. This file only contains exact module names.
"""

PACKAGE_MODULES: frozenset[str] = frozenset({
    # System package managers
    "apt",
    "apt_repository",
    "yum",
    "dnf",
    "package",
    "zypper",
    "pacman",
    "homebrew",
    # Language-specific package managers
    "pip",
    "pip3",
    "npm",
    "gem",
    "composer",
    "maven",
    # Container images
    "docker_image",
    "podman_image",
    # FQCNs
    "ansible.builtin.apt",
    "ansible.builtin.yum",
    "ansible.builtin.dnf",
    "ansible.builtin.package",
    "ansible.builtin.pip",
    "community.general.npm",
    "community.general.gem",
    "community.general.homebrew",
})

SERVICE_MODULES: frozenset[str] = frozenset({
    "service",
    "systemd",
    "supervisorctl",
    "sysvinit",
    # Windows
    "win_service",
    # FQCNs
    "ansible.builtin.service",
    "ansible.builtin.systemd",
    "ansible.builtin.systemd_service",
})

CONFIG_MODULES: frozenset[str] = frozenset({
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
    # FQCNs
    "ansible.builtin.template",
    "ansible.builtin.copy",
    "ansible.builtin.lineinfile",
    "ansible.builtin.blockinfile",
    "ansible.builtin.replace",
    "ansible.builtin.assemble",
})

FILE_MODULES: frozenset[str] = frozenset({
    "file",
    "find",
    "stat",
    "tempfile",
    "unarchive",
    "archive",
    # Filesystem/storage
    "filesystem",
    "mount",
    "lvg",
    "lvol",
    "parted",
    # Windows
    "win_file",
    # FQCNs
    "ansible.builtin.file",
    "ansible.builtin.stat",
    "ansible.builtin.find",
    "ansible.builtin.tempfile",
    "ansible.builtin.unarchive",
})

VERIFY_MODULES: frozenset[str] = frozenset({
    "assert",
    "fail",
    "wait_for",
    "wait_for_connection",
    "ping",
    "uri",
    # Commands often used for verification
    "command",
    "shell",
    # Debug
    "debug",
    "pause",
    # Windows
    "win_ping",
    "win_wait_for",
    # FQCNs
    "ansible.builtin.assert",
    "ansible.builtin.uri",
    "ansible.builtin.wait_for",
    "ansible.builtin.wait_for_connection",
    "ansible.builtin.ping",
    "ansible.builtin.fail",
    "ansible.builtin.debug",
    "ansible.builtin.pause",
    "ansible.builtin.command",
    "ansible.builtin.shell",
})

NETWORK_MODULES: frozenset[str] = frozenset({
    "firewalld",
    "iptables",
    "ufw",
    "nmcli",
    "network",
    "route",
    "hostname",
    # Network devices
    "cisco",
    "junos",
    "vyos",
    # FQCNs
    "ansible.builtin.iptables",
    "community.general.ufw",
    "community.general.firewalld",
    "ansible.builtin.hostname",
})

IDENTITY_MODULES: frozenset[str] = frozenset({
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
    # FQCNs
    "ansible.builtin.user",
    "ansible.builtin.group",
    "ansible.builtin.authorized_key",
    "ansible.builtin.acl",
})

DATABASE_MODULES: frozenset[str] = frozenset({
    "mysql_db",
    "mysql_user",
    "mysql_query",
    "postgresql_db",
    "postgresql_user",
    "postgresql_query",
    "mongodb_user",
    "redis",
    # FQCNs
    "community.mysql.mysql_db",
    "community.mysql.mysql_user",
    "community.postgresql.postgresql_db",
    "community.postgresql.postgresql_user",
})

ARTIFACT_MODULES: frozenset[str] = frozenset({
    # Download/fetch
    "get_url",
    "uri",
    # Archives
    "unarchive",
    "archive",
    # Source control
    "git",
    "svn",
    "hg",
    # Artifact repositories
    "maven_artifact",
    "nexus_artifact",
    # Windows
    "win_get_url",
    "win_unzip",
    # FQCNs
    "ansible.builtin.get_url",
    "ansible.builtin.uri",
    "ansible.builtin.unarchive",
    "ansible.builtin.git",
})
