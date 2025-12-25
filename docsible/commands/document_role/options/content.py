"""Content control CLI options for document_role command."""

from typing import Callable, TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_content_options(f: F) -> F:
    """Add content control options to the command.

    Args:
        f: Click command function to decorate

    Returns:
        Decorated command function with content control options added

    Options:
    - --no-vars: Hide variable documentation
    - --no-tasks: Hide task lists and details
    - --no-diagrams: Hide all Mermaid diagrams
    - --simplify-diagrams: Show only high-level diagrams
    - --no-examples: Hide example playbook sections
    - --no-metadata: Hide role metadata
    - --no-handlers: Hide handlers section
    - --minimal: Generate minimal documentation (enables all --no-* flags)
    """
    f = click.option(
        "--minimal",
        "minimal",
        is_flag=True,
        help="Generate minimal documentation (enables all --no-* flags).",
    )(f)
    f = click.option(
        "--include-complexity",
        "include_complexity",
        is_flag=True,
        help="Include complexity analysis section in README",
    )(f)

    f = click.option(
        "--no-handlers", "no_handlers", is_flag=True, help="Hide handlers section."
    )(f)
    f = click.option(
        "--no-metadata",
        "no_metadata",
        is_flag=True,
        help="Hide role metadata, author, and license information.",
    )(f)
    f = click.option(
        "--no-examples",
        "no_examples",
        is_flag=True,
        help="Hide example playbook sections.",
    )(f)
    f = click.option(
        "--simplify-diagrams",
        "simplify_diagrams",
        is_flag=True,
        help="Show only high-level diagrams, hide detailed task flowcharts.",
    )(f)
    f = click.option(
        "--no-diagrams",
        "no_diagrams",
        is_flag=True,
        help="Hide all Mermaid diagrams (flowcharts, sequence diagrams).",
    )(f)
    f = click.option(
        "--no-tasks", "no_tasks", is_flag=True, help="Hide task lists and task details."
    )(f)
    f = click.option(
        "--no-vars",
        "no_vars",
        is_flag=True,
        help="Hide variable documentation (defaults, vars, argument_specs).",
    )(f)
    return f
