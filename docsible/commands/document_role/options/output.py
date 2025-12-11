"""Output-related CLI options for document_role command."""

import click


def add_output_options(f):
    """Add output-related options to the command.

    Options:
    - --output/-o: Output readme file name
    - --no-backup: Don't backup existing README
    - --append/-a: Append to existing README instead of replacing
    - --no-docsible: Don't generate .docsible file
    """
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
