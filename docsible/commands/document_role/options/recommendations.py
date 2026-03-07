
from collections.abc import Callable
from typing import TypeVar

import click

F = TypeVar("F", bound=Callable[..., None])

def add_recommendation_options(f: F)-> F:
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
        help="Give INFO-level recommendation, hidden by default"
    )(f)

    f = click.option(
        "--recommendations-only",
        "recommendations_only",
        is_flag=True,
        help="Show recommendations based on the role without generating documentation"
    )(f)
    
    return f