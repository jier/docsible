"""Framing options for documentation output style."""
import click


def add_framing_options(func):
    """Add output framing options to a Click command."""
    func = click.option(
        "--positive/--neutral",
        "positive_framing",
        default=True,
        help="Use positive output framing (default: positive)",
    )(func)
    return func
