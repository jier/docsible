"""Framing and help options for documentation output."""
import click


def _show_full_help_callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """Callback to display full help when --help-full is used."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(ctx.get_help())
    ctx.exit()


def add_framing_options(func):
    """Add output framing and help options to a Click command."""
    func = click.option(
        "--positive/--neutral",
        "positive_framing",
        default=True,
        help="Use positive output framing (default: positive)",
    )(func)
    func = click.option(
        "--help-full",
        is_flag=True,
        is_eager=True,
        expose_value=False,
        callback=_show_full_help_callback,
        help="Show all available options and advanced settings",
    )(func)
    return func
