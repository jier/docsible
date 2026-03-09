from collections.abc import Callable
from typing import TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])


def add_recommendation_options(f: F) -> F:
    """Add recommendation options as one of the intents

    Args:
        f: Click command function to decorate

    Returns:
        Decorated commnad function with recommendation options added

    Options:
        --show-info: Show INFO-level recommendaitons, hidden by default
        --recommendations-only: Show recommendations without generating documentation
    """
    f = click.option(
        "--show-info",
        "show_info",
        is_flag=True,
        help="Give INFO-level recommendation, hidden by default",
    )(f)

    f = click.option(
        "--recommendations-only",
        "recommendations_only",
        is_flag=True,
        help="Show recommendations based on the role without generating documentation",
    )(f)

    f = click.option(
        "--fail-on",
        "fail_on",
        type=click.Choice(["none", "info", "warning", "critical"]),
        default="none",
        show_default=True,
        help="Exit with code 1 if findings at or above this severity are found. Use in CI pipelines.",
    )(f)

    f = click.option(
        "--advanced-patterns",
        "advanced_patterns",
        is_flag=True,
        default=False,
        help="Show all findings including INFO-level. Removes the default 5-recommendation cap.",
    )(f)

    return f
