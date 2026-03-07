"""Validate command group."""
import click

from .role import validate_role_cmd


@click.group(name="validate")
def validate_group() -> None:
    """Validate Ansible role documentation and structure."""

validate_group.add_command(validate_role_cmd, name="role")
__all__ = ["validate_group"]
