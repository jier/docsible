"""Command modules for Docsible CLI.

This package contains modular command implementations for the Docsible
documentation generator. Each command is implemented in its own module
for better maintainability and testability.

Commands:
    - init_config: Initialize .docsible.yml configuration
    - doc_the_role: Document an Ansible role
    - document_collection_roles: Document an Ansible collection
"""

from docsible.commands.document_collection import document_collection_roles
from docsible.commands.document_role import doc_the_role
from docsible.commands.init_config import init_config

__all__ = [
    "doc_the_role",
    "document_collection_roles",
    "init_config",
]
