"""Legacy commands for Docsible CLI.

This package contains deprecated command implementations that are maintained
for backward compatibility. Users should migrate to the new command equivalents.
"""

from .role import doc_the_role

__all__ = ["doc_the_role"]
