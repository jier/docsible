"""Analyze command group."""

import click

from .role import analyze_role_cmd


@click.group(name="analyze")
def analyze_group() -> None:
    """Analyze Ansible roles for complexity and quality."""


analyze_group.add_command(analyze_role_cmd, name="role")
__all__ = ["analyze_group"]
