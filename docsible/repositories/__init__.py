"""Repository pattern implementations for Docsible data access.

This package provides repositories for loading Ansible roles and collections
from the filesystem, implementing clean separation between data access and
business logic.
"""

from docsible.repositories.role_repository import RoleRepository

__all__ = ["RoleRepository"]
