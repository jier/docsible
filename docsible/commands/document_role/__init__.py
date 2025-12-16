"""Simplified document_role command with modularized options."""

import click

# Import grouped help formatter
from docsible.utils.cli_helpers import GroupedHelpCommand

from .core import build_role_info, extract_playbook_role_dependencies

# Import the original implementation and helper functions
from .core import doc_the_role as core_doc_the_role
from .options import (
    add_content_options,
    add_generation_options,
    add_output_options,
    add_path_options,
    add_repository_options,
    add_template_options,
)


@click.command(name="role", cls=GroupedHelpCommand)
@add_path_options
@add_output_options
@add_content_options
@add_template_options
@add_generation_options
@add_repository_options
def doc_the_role(
    role_path,
    collection_path,
    playbook,
    output,
    no_backup,
    append,
    no_docsible,
    validate_markdown,
    auto_fix,
    strict_validation,
    no_vars,
    no_tasks,
    no_diagrams,
    simplify_diagrams,
    no_examples,
    no_metadata,
    no_handlers,
    minimal,
    md_role_template,
    md_collection_template,
    hybrid,
    generate_graph,
    comments,
    task_line,
    complexity_report,
    include_complexity,
    simplification_report,
    show_dependencies,
    analyze_only,
    repository_url,
    repo_type,
    repo_branch,
):
    """Generate documentation for an Ansible role.

    Supports standard roles, collections, AWX projects, and monorepos.
    Use .docsible.yml to configure custom directory structures.

    Examples:
        # Document a role
        docsible role --role /path/to/role

        # Document with diagrams
        docsible role --role /path/to/role --graph

        # Analyze role complexity without generating docs
        docsible role --role /path/to/role --analyze-only

        # Include complexity analysis and dependency matrix
        docsible role --role /path/to/role --complexity-report --show-dependencies

        # Minimal documentation
        docsible role --role /path/to/role --minimal

        # Collection documentation
        docsible role --collection /path/to/collection
    """
    return core_doc_the_role(
        role_path=role_path,
        collection_path=collection_path,
        playbook=playbook,
        generate_graph=generate_graph,
        no_backup=no_backup,
        no_docsible=no_docsible,
        validate_markdown=validate_markdown,
        auto_fix=auto_fix,
        strict_validation=strict_validation,
        comments=comments,
        task_line=task_line,
        md_collection_template=md_collection_template,
        md_role_template=md_role_template,
        hybrid=hybrid,
        no_vars=no_vars,
        no_tasks=no_tasks,
        no_diagrams=no_diagrams,
        simplify_diagrams=simplify_diagrams,
        no_examples=no_examples,
        no_metadata=no_metadata,
        no_handlers=no_handlers,
        minimal=minimal,
        complexity_report=complexity_report,
        include_complexity=include_complexity,
        simplification_report=simplification_report,
        show_dependencies=show_dependencies,
        analyze_only=analyze_only,
        append=append,
        output=output,
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch,
    )


__all__ = ["doc_the_role", "build_role_info", "extract_playbook_role_dependencies"]
