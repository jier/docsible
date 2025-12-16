"""Option group utilities for better CLI help organization."""

import click


class GroupedOption(click.Option):
    """Custom Option class that supports grouping in help output."""

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super().__init__(*args, **kwargs)


class OptionGroupMixin:
    """Mixin to add option grouping support to Click commands."""

    def format_options(self, ctx, formatter):
        """Group options by category in help output."""
        # Group options by their 'group' attribute
        groups = {}
        ungrouped = []

        for param in self.get_params(ctx):
            if isinstance(param, GroupedOption) and param.group:
                if param.group not in groups:
                    groups[param.group] = []
                groups[param.group].append(param)
            else:
                ungrouped.append(param)

        # Define display order for groups
        group_order = [
            ("Input Paths", "📂 Input Paths"),
            ("Output Control", "💾 Output Control"),
            ("Content Sections", "📄 Content Sections"),
            ("Templates", "🎨 Templates"),
            ("Visualization", "📊 Visualization"),
            ("Analysis", "🔍 Analysis"),
            ("Repository", "🔗 Repository"),
        ]

        # Write grouped options
        for group_key, group_title in group_order:
            if group_key in groups:
                opts = []
                for param in groups[group_key]:
                    rv = param.get_help_record(ctx)
                    if rv is not None:
                        opts.append(rv)

                if opts:
                    with formatter.section(group_title):
                        formatter.write_dl(opts)

        # Write ungrouped options
        if ungrouped:
            opts = []
            for param in ungrouped:
                rv = param.get_help_record(ctx)
                if rv is not None:
                    opts.append(rv)

            if opts:
                with formatter.section("Other Options"):
                    formatter.write_dl(opts)


class GroupedCommand(OptionGroupMixin, click.Command):
    """Command class with option grouping support."""

    pass


def option_group(group_name: str):
    """Decorator to assign an option to a group.

    Args:
        group_name: Name of the group (e.g., "Input Paths", "Visualization")

    Example:
        @click.option('--graph', cls=GroupedOption, group='Visualization')
    """

    def decorator(f):
        # Get the last option decorator applied (Click stores them in reverse)
        if hasattr(f, "__click_params__"):
            for param in f.__click_params__:
                if isinstance(param, GroupedOption):
                    param.group = group_name
                    break
        return f

    return decorator
