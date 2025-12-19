"""Repository-related CLI options for document_role command."""

import click


def add_repository_options(f):
    """Add repository-related options to the command.

    Options:
    - --repository-url: Repository base URL
    - --repo-type: Repository type (github, gitlab, gitea)
    - --repo-branch: Repository branch name
    """
    f = click.option(
        "--repo-branch",
        "-rb",
        "repo_branch",
        default=None,
        help="Repository branch name (e.g., main or master)",
    )(f)
    f = click.option(
        "--repo-type",
        "-rt",
        "repo_type",
        default=None,
        help="Repository type: github, gitlab, gitea, etc.",
    )(f)
    f = click.option(
        "--repository-url",
        "-ru",
        "repository_url",
        default="detect",
        help="Repository base URL (used for standalone roles)",
    )(f)
    return f
