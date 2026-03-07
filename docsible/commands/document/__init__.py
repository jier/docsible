"""Document command group — generate documentation."""
import click

from .role import document_role_cmd


@click.group(name="document")
def document_group() -> None:
    """Generate documentation for Ansible roles and collections."""

document_group.add_command(document_role_cmd, name="role")
__all__ = ["document_group"]
