"""Template-related CLI options for document_role command."""

from collections.abc import Callable
from typing import TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_template_options(f: F) -> F:
    """Add template-related options to the command.

    Args:
        f: Click command function to decorate

    Returns:
        Decorated command function with template options added

    Options:
    - --md-role-template/--md-template: Path to role markdown template
    - --md-collection-template: Path to collection markdown template
    - --hybrid: Use hybrid template (manual + auto-generated)
    """
    f = click.option(
        "--hybrid",
        "hybrid",
        is_flag=True,
        help="Use hybrid template (combines manual sections with auto-generated content).",
    )(f)
    f = click.option(
        "--md-collection-template",
        "-ctpl",
        "md_collection_template",
        default=None,
        help="Path to the collection markdown template file.",
    )(f)
    f = click.option(
        "--md-role-template",
        "--md-template",
        "-rtpl",
        "-tpl",
        "md_role_template",
        default=None,
        help="Path to the role markdown template file.",
    )(f)
    return f
