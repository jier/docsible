"""Path-related CLI options for document_role command."""

from typing import Callable, TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_path_options(f: F) -> F:
    """Add path-related options to the command.

    Args:
        f: Click command function to decorate

    Returns:
        Decorated command function with path options added

    Options:
    - --role/-r: Path to the Ansible role directory
    - --collection/-c: Path to the Ansible collection directory
    - --playbook/-p: Path to the playbook file
    """
    f = click.option(
        "--playbook", "-p", default=None, help="Path to the playbook file."
    )(f)
    f = click.option(
        "--collection",
        "-c",
        "collection_path",
        default=None,
        help="Path to the Ansible collection directory.",
    )(f)
    f = click.option(
        "--role",
        "-r",
        "role_path",
        default=None,
        help="Path to the Ansible role directory.",
    )(f)
    return f
