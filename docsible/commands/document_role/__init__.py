"""Simplified document_role command with modularized options."""

import sys

import click

from docsible.presets.registry import PresetRegistry
from docsible.presets.resolver import resolve_settings

# Import grouped help formatter
from docsible.utils.cli_helpers import BriefHelpCommand

from .core import build_role_info, extract_playbook_role_dependencies

# Import the original implementation and helper functions
from .core import doc_the_role as core_doc_the_role
from .options import (
    add_content_options,
    add_framing_options,
    add_generation_options,
    add_output_options,
    add_path_options,
    add_recommendation_options,
    add_repository_options,
    add_template_options,
)


@click.command(name="role", cls=BriefHelpCommand)
@add_path_options
@add_output_options
@add_content_options
@add_template_options
@add_generation_options
@add_repository_options
@add_recommendation_options
@add_framing_options
@click.option(
    "--preset",
    type=click.Choice(PresetRegistry.names()),
    default=None,
    help="Apply a built-in preset (personal/team/enterprise/consultant).",
)
def doc_the_role(
    preset,
    role_path: str | None,
    collection_path: str | None,
    playbook: str | None,
    output: str,
    no_backup: bool,
    append: bool,
    no_docsible: bool,
    dry_run: bool,
    validate_markdown: bool,
    auto_fix: bool,
    strict_validation: bool,
    no_vars: bool,
    no_tasks: bool,
    no_diagrams: bool,
    simplify_diagrams: bool,
    no_examples: bool,
    no_metadata: bool,
    no_handlers: bool,
    minimal: bool,
    md_role_template: str | None,
    md_collection_template: str | None,
    hybrid: bool,
    generate_graph: bool,
    comments: bool,
    task_line: bool,
    complexity_report: bool,
    include_complexity: bool,
    simplification_report: bool,
    show_dependencies: bool,
    analyze_only: bool,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
    show_info: bool,
    recommendations_only: bool,
    positive_framing: bool,
) -> None:
    """Generate documentation for an Ansible role.

    Supports standard roles, collections, AWX projects, and monorepos.
    Use .docsible.yml to configure custom directory structures.
    Run with --help-full to see all available options.

    \f
    # Click convention: \f (form-feed) truncates --help output here.
    # Everything below is visible in source but never rendered to the terminal.

    Args:
        role_path: Path to role directory
        collection_path: Path to collection directory
        playbook: Path to playbook file
        output: Output file path
        no_backup: Skip backup creation
        append: Append to existing README
        no_docsible: Skip docsible tags in output
        dry_run: Show what would be generated without writing
        validate_markdown: Validate generated markdown
        auto_fix: Automatically fix markdown issues
        strict_validation: Fail on validation warnings
        no_vars: Exclude variables section
        no_tasks: Exclude tasks section
        no_diagrams: Exclude all diagrams
        simplify_diagrams: Simplify diagram output
        no_examples: Exclude examples section
        no_metadata: Exclude metadata section
        no_handlers: Exclude handlers section
        minimal: Generate minimal documentation
        md_role_template: Custom role template path
        md_collection_template: Custom collection template path
        hybrid: Use hybrid template format
        generate_graph: Generate Mermaid diagrams
        comments: Include task comments in output
        task_line: Include task line numbers
        complexity_report: Show complexity analysis
        include_complexity: Include complexity in README
        simplification_report: Show simplification suggestions
        show_dependencies: Show dependency matrix
        analyze_only: Only analyze, don't generate docs
        repository_url: Repository URL for links
        repo_type: Repository type (github, gitlab, etc)
        repo_branch: Repository branch name
        show_info: Show INFO-level recommendations
        recommendations_only: Show only recommendations without generating docs
        positive_framing: Use positive output framing

    Examples:
        docsible role --role /path/to/role
        docsible role --role /path/to/role --graph
        docsible role --role /path/to/role --analyze-only
        docsible role --role /path/to/role --complexity-report --show-dependencies
        docsible role --role /path/to/role --minimal
        docsible role --collection /path/to/collection
    """
    click.echo(
        "DeprecationWarning: 'docsible role' is deprecated. "
        "Use 'docsible document role' instead.",
        file=sys.stderr,
    )

    # Collect all explicit kwargs and apply preset resolution
    cli_kwargs = {
        "role_path": role_path,
        "collection_path": collection_path,
        "playbook": playbook,
        "generate_graph": generate_graph,
        "no_backup": no_backup,
        "no_docsible": no_docsible,
        "dry_run": dry_run,
        "validate_markdown": validate_markdown,
        "auto_fix": auto_fix,
        "strict_validation": strict_validation,
        "comments": comments,
        "task_line": task_line,
        "md_collection_template": md_collection_template,
        "md_role_template": md_role_template,
        "hybrid": hybrid,
        "no_vars": no_vars,
        "no_tasks": no_tasks,
        "no_diagrams": no_diagrams,
        "simplify_diagrams": simplify_diagrams,
        "no_examples": no_examples,
        "no_metadata": no_metadata,
        "no_handlers": no_handlers,
        "minimal": minimal,
        "complexity_report": complexity_report,
        "include_complexity": include_complexity,
        "simplification_report": simplification_report,
        "show_dependencies": show_dependencies,
        "analyze_only": analyze_only,
        "append": append,
        "output": output,
        "repository_url": repository_url,
        "repo_type": repo_type,
        "repo_branch": repo_branch,
        "show_info": show_info,
        "recommendations_only": recommendations_only,
        "positive_framing": positive_framing,
    }
    resolved = resolve_settings(preset_name=preset, cli_overrides=cli_kwargs)
    cli_kwargs.update(resolved)
    core_doc_the_role(**cli_kwargs)  # type: ignore[arg-type]


__all__ = ["doc_the_role", "build_role_info", "extract_playbook_role_dependencies"]
