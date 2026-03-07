"""Output-related CLI options for document_role command."""

from collections.abc import Callable
from typing import TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_output_options(f: F) -> F:
    """Add output-related options to the command.

    Args:
        f: Click command function to decorate

    Returns:
        Decorated command function with output options added

    Options:
    - --output/-o: Output readme file name
    - --no-backup: Don't backup existing README
    - --append/-a: Append to existing README instead of replacing
    - --no-docsible: Don't generate .docsible file
    - --dry-run: Preview changes without writing files
    - --validate/--no-validate: Enable/disable markdown formatting validation
    - --auto-fix: Automatically fix formatting issues
    - --strict-validation: Fail generation if validation errors found
    """
    f = click.option(
        "--dry-run",
        "dry_run",
        is_flag=True,
        help="Preview what would be generated without writing any files.",
    )(f)
    f = click.option(
        "--strict-validation",
        "strict_validation",
        is_flag=True,
        help="Fail generation if markdown validation errors are found (default: warn only).",
    )(f)
    f = click.option(
        "--auto-fix",
        "auto_fix",
        is_flag=True,
        help="Automatically fix common markdown formatting issues (whitespace, tables).",
    )(f)
    f = click.option(
        "--validate/--no-validate",
        "validate_markdown",
        default=True,
        help="Validate markdown formatting before writing (default: enabled).",
    )(f)
    f = click.option(
        "--no-docsible",
        "-nod",
        "no_docsible",
        is_flag=True,
        help="Do not generate .docsible file and do not include it in README.md.",
    )(f)
    f = click.option(
        "--append",
        "-a",
        "append",
        is_flag=True,
        help="Append to the existing README.md instead of replacing it.",
    )(f)
    f = click.option(
        "--no-backup",
        "-nob",
        "no_backup",
        is_flag=True,
        help="Do not backup the readme before remove.",
    )(f)
    f = click.option(
        "--output", "-o", "output", default="README.md", help="Output readme file name."
    )(f)
    return f
