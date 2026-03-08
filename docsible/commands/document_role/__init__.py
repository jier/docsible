"""document_role command package.

The deprecated top-level ``docsible role`` Click command has been moved to
``docsible.commands.legacy.role``.  This package now re-exports only the
core implementation helpers that other commands depend on.
"""

from .core import build_role_info, doc_the_role, extract_playbook_role_dependencies

__all__ = ["doc_the_role", "build_role_info", "extract_playbook_role_dependencies"]
