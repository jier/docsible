"""CLI helper utilities for improved help formatting."""

import click
from typing import List, Tuple


class GroupedHelpCommand(click.Command):
    """Command class that groups options by category in help output.

    Options are automatically grouped based on naming patterns:
    - Path options: --role, --collection, --playbook, --output
    - Content options: --no-vars, --no-tasks, --no-diagrams, etc.
    - Visualization options: --graph, --hybrid, --simplify-diagrams
    - Analysis options: --complexity-report, --analyze-only, --show-dependencies
    - Repository options: --repository-url, --repo-type, --repo-branch
    - Output control: --no-backup, --append, --no-docsible
    - Template options: --md-role-template, --md-collection-template
    """

    def format_options(self, ctx, formatter):
        """Format options grouped by category."""
        # Collect all options
        opts_by_group = {
            "📂 Input Paths": [],
            "💾 Output Control": [],
            "📄 Content Sections": [],
            "🎨 Templates": [],
            "📊 Visualization": [],
            "🔍 Analysis & Complexity": [],
            "🔗 Repository Integration": [],
            "⚙️  Other Options": [],
        }

        # Categorize options based on name patterns
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                opt_name = rv[0]

                # Categorize by option name
                if any(x in opt_name for x in ['--role', '--collection', '--playbook']):
                    opts_by_group["📂 Input Paths"].append(rv)
                elif any(x in opt_name for x in ['--output', '--no-backup', '--append', '--no-docsible', '--validate', '--auto-fix', '--strict']):
                    opts_by_group["💾 Output Control"].append(rv)
                elif any(x in opt_name for x in ['--no-vars', '--no-tasks', '--no-diagrams', '--no-examples', '--no-metadata', '--no-handlers', '--minimal', '--include-complexity']):
                    opts_by_group["📄 Content Sections"].append(rv)
                elif any(x in opt_name for x in ['--md-role-template', '--md-collection-template', '--hybrid']):
                    opts_by_group["🎨 Templates"].append(rv)
                elif any(x in opt_name for x in ['--graph', '--simplify-diagrams', '--comments', '--task-line']):
                    opts_by_group["📊 Visualization"].append(rv)
                elif any(x in opt_name for x in ['--complexity-report', '--simplification-report', '--show-dependencies', '--analyze-only']):
                    opts_by_group["🔍 Analysis & Complexity"].append(rv)
                elif any(x in opt_name for x in ['--repository-url', '--repo-type', '--repo-branch']):
                    opts_by_group["🔗 Repository Integration"].append(rv)
                else:
                    opts_by_group["⚙️  Other Options"].append(rv)

        # Write groups (only non-empty ones)
        for group_name in opts_by_group:
            if opts_by_group[group_name]:
                with formatter.section(group_name):
                    formatter.write_dl(opts_by_group[group_name])


def format_help_section(title: str, items: List[Tuple[str, str]]) -> str:
    """Format a help section with title and items.

    Args:
        title: Section title
        items: List of (term, description) tuples

    Returns:
        Formatted help text
    """
    lines = [f"\n{title}:", "=" * len(title)]
    for term, desc in items:
        lines.append(f"  {term}")
        lines.append(f"    {desc}")
    return "\n".join(lines)
