"""Command for documenting Ansible roles."""

import logging
import os
from pathlib import Path

import click
import yaml

from docsible.renderers.tag_manager import manage_docsible_file_keys
from docsible.utils.git import get_repo_info
from docsible.utils.mermaid import (
    generate_mermaid_playbook,
)
from docsible.utils.project_structure import ProjectStructure
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    get_task_line_ranges,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)

logger = logging.getLogger(__name__)


def extract_playbook_role_dependencies(
    playbook_content: str | None, current_role_name: str
) -> list[str]:
    """Extract role names from playbook that differ from the current role name.

    Searches for roles in:
    - roles: section
    - include_role/import_role tasks in pre_tasks, tasks, post_tasks

    Args:
        playbook_content: YAML content of the playbook as string
        current_role_name: Name of the current role being documented

    Returns:
        List of role names (excluding current role)

    Example:
        >>> content = '''
        ... - hosts: all
        ...   roles:
        ...     - common
        ...     - webserver
        ... '''
        >>> extract_playbook_role_dependencies(content, 'webserver')
        ['common']
    """
    if not playbook_content:
        return []

    try:
        playbook = yaml.safe_load(playbook_content)
        if not isinstance(playbook, list):
            return []

        role_names = set()

        for play in playbook:
            if not isinstance(play, dict):
                continue

            # Extract from roles: section
            roles = play.get("roles", [])
            for role in roles:
                if isinstance(role, str):
                    role_name = role
                elif isinstance(role, dict):
                    role_name = str(role.get("role") or role.get("name") or "")
                else:
                    continue

                if role_name and role_name != current_role_name:
                    role_names.add(role_name)

            # Extract from include_role/import_role in tasks sections
            for section in ["pre_tasks", "tasks", "post_tasks"]:
                tasks = play.get(section, [])
                if not isinstance(tasks, list):
                    continue

                for task in tasks:
                    if not isinstance(task, dict):
                        continue

                    for action in ["include_role", "import_role"]:
                        if action in task:
                            role_spec = task[action]
                            if isinstance(role_spec, str):
                                role_name = role_spec
                            elif isinstance(role_spec, dict):
                                role_name = str(role_spec.get("name", ""))
                            else:
                                continue

                            if role_name and role_name != current_role_name:
                                role_names.add(role_name)

        return sorted(list(role_names))

    except Exception as e:
        logger.warning(f"Could not extract playbook role dependencies: {e}")
        return []


def build_role_info(
    role_path: Path,
    playbook_content: str | None,
    generate_graph: bool,
    no_docsible: bool,
    comments: bool,
    task_line: bool,
    belongs_to_collection: dict | None,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> dict:
    """Build comprehensive role information dictionary.

    Args:
        role_path: Path to role directory
        playbook_content: Optional playbook YAML content
        generate_graph: Whether to generate Mermaid graphs
        no_docsible: Skip .docsible file handling
        comments: Extract comments from task files
        task_line: Extract line numbers from tasks
        belongs_to_collection: Collection info if role is part of collection
        repository_url: Repository URL (or 'detect' for auto-detection)
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name

    Returns:
        Dictionary with complete role information
    """
    project_structure = ProjectStructure(str(role_path))
    role_name = role_path.name
    docsible_path = role_path / ".docsible"

    # Handle .docsible metadata file
    if not no_docsible:
        manage_docsible_file_keys(docsible_path)

    # Get meta file path
    meta_path = project_structure.get_meta_file(role_path)
    if meta_path is None:
        logger.warning(f"No meta file found for role {role_name}")
        meta_path = role_path / "meta" / "main.yml"  # Fallback

    # Get argument specs
    argument_specs_path = project_structure.get_argument_specs_file(role_path)
    argument_specs = None
    if argument_specs_path and argument_specs_path.exists():
        argument_specs = load_yaml_generic(argument_specs_path)

    # Get defaults and vars
    defaults_dir = project_structure.get_defaults_dir(role_path)
    vars_dir = project_structure.get_vars_dir(role_path)
    defaults_data = load_yaml_files_from_dir_custom(defaults_dir) or []
    vars_data = load_yaml_files_from_dir_custom(vars_dir) or []

    # Detect repository info if requested
    if repository_url == "detect":
        try:
            git_info = get_repo_info(str(role_path)) or {}
            repository_url = git_info.get("repository")
            repo_branch = repo_branch or git_info.get("branch", "main")
            repo_type = repo_type or git_info.get("repository_type")
        except Exception as e:
            logger.warning(f"Could not get Git info: {e}")
            repository_url = None

    # Extract playbook role dependencies
    playbook_dependencies = extract_playbook_role_dependencies(
        playbook_content, role_name
    )

    # Build base role info
    role_info = {
        "name": role_name,
        "defaults": defaults_data,
        "vars": vars_data,
        "tasks": [],
        "handlers": [],
        "meta": load_yaml_generic(meta_path) if meta_path.exists() else {},
        "playbook": {
            "content": playbook_content,
            "graph": (
                generate_mermaid_playbook(yaml.safe_load(playbook_content))
                if generate_graph and playbook_content
                else None
            ),
            "dependencies": playbook_dependencies,
        },
        "docsible": load_yaml_generic(docsible_path) if not no_docsible else None,
        "belongs_to_collection": belongs_to_collection,
        "repository": repository_url,
        "repository_type": repo_type,
        "repository_branch": repo_branch,
        "argument_specs": argument_specs,
    }

    # Extract tasks
    tasks_dir = project_structure.get_tasks_dir(role_path)
    if tasks_dir.exists() and tasks_dir.is_dir():
        yaml_extensions = project_structure.get_yaml_extensions()

        for dirpath, _, filenames in os.walk(str(tasks_dir)):
            for task_file in filenames:
                if any(task_file.endswith(ext) for ext in yaml_extensions):
                    file_path = Path(dirpath) / task_file
                    tasks_data = load_yaml_generic(file_path)

                    if tasks_data:
                        relative_path = file_path.relative_to(tasks_dir)
                        from typing import Any
                        task_info: dict[str, Any] = {
                            "file": str(relative_path),
                            "tasks": [],
                            "mermaid": [],
                            "comments": [],
                            "lines": [],
                            "line_ranges": [],
                        }

                        if comments:
                            task_info["comments"] = get_task_comments(str(file_path))
                        if task_line:
                            task_info["lines"] = get_task_line_numbers(str(file_path))

                        # Always extract line ranges for phase detection (lightweight operation)
                        try:
                            task_info["line_ranges"] = get_task_line_ranges(
                                str(file_path)
                            )
                        except Exception as e:
                            logger.debug(
                                f"Could not extract line ranges for {file_path}: {e}"
                            )

                        if isinstance(tasks_data, list):
                            for task in tasks_data:
                                if isinstance(task, dict) and task:
                                    processed_tasks = process_special_task_keys(task)
                                    task_info["tasks"].extend(processed_tasks)
                                    task_info["mermaid"].append(task)

                            role_info["tasks"].append(task_info)

    # Extract handlers
    handlers_dir = role_path / "handlers"
    if handlers_dir.exists() and handlers_dir.is_dir():
        yaml_extensions = project_structure.get_yaml_extensions()

        for dirpath, _, filenames in os.walk(str(handlers_dir)):
            for handler_file in filenames:
                if any(handler_file.endswith(ext) for ext in yaml_extensions):
                    file_path = Path(dirpath) / handler_file
                    handlers_data = load_yaml_generic(file_path)

                    if handlers_data and isinstance(handlers_data, list):
                        for handler in handlers_data:
                            if isinstance(handler, dict) and "name" in handler:
                                handler_info = {
                                    "name": handler.get("name", "Unnamed handler"),
                                    "module": next(
                                        (
                                            k
                                            for k in handler.keys()
                                            if k
                                            not in [
                                                "name",
                                                "notify",
                                                "when",
                                                "tags",
                                                "listen",
                                            ]
                                        ),
                                        "unknown",
                                    ),
                                    "listen": handler.get("listen", []),
                                    "file": str(
                                        Path(file_path).relative_to(handlers_dir)
                                    ),
                                }
                                role_info["handlers"].append(handler_info)

    return role_info


def _display_dry_run_summary(
    role_info: dict,
    role_path: Path,
    output: str,
    analysis_report,
    mermaid_code_per_file: dict,
    sequence_diagram_high_level: str | None,
    sequence_diagram_detailed: str | None,
    state_diagram: str | None,
    integration_boundary_diagram: str | None,
    architecture_diagram: str | None,
    dependency_matrix: str | None,
    no_backup: bool,
    no_docsible: bool,
    generate_graph: bool,
    hybrid: bool,
    minimal: bool,
) -> None:
    """Display dry-run summary without writing files.

    Args:
        role_info: Role information dictionary
        role_path: Path to role directory
        output: Output filename
        analysis_report: Complexity analysis report
        mermaid_code_per_file: Generated task flowcharts
        sequence_diagram_high_level: High-level sequence diagram
        sequence_diagram_detailed: Detailed sequence diagram
        state_diagram: State transition diagram
        integration_boundary_diagram: Integration boundary diagram
        architecture_diagram: Component architecture diagram
        dependency_matrix: Dependency matrix
        no_backup: Whether backup is disabled
        no_docsible: Whether .docsible file is disabled
        generate_graph: Whether diagrams are generated
        hybrid: Whether hybrid template is used
        minimal: Whether minimal mode is enabled
    """
    click.echo("\n" + "=" * 70)
    click.echo("🔍 DRY RUN MODE - No files will be modified")
    click.echo("=" * 70)

    # Role information
    click.echo("\n📁 Analysis Complete:")
    click.echo(f"   Role: {role_info.get('name', 'unknown')}")
    click.echo(f"   Path: {role_path}")

    # Complexity analysis
    click.echo("\n📊 Complexity Analysis:")
    click.echo(f"   Category: {analysis_report.category.value.upper()}")
    click.echo(f"   Total Tasks: {analysis_report.metrics.total_tasks}")
    click.echo(f"   Task Files: {analysis_report.metrics.task_files}")

    # Variables
    defaults_count = sum(len(df.get("data", {})) for df in role_info.get("defaults", []))
    vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
    click.echo(
        f"   Variables: {defaults_count + vars_count} ({defaults_count} defaults, {vars_count} vars)"
    )

    # Handlers
    handlers_count = len(role_info.get("handlers", []))
    if handlers_count > 0:
        click.echo(f"   Handlers: {handlers_count}")

    # What would be generated
    click.echo("\n📈 Would Generate:")

    if generate_graph:
        if mermaid_code_per_file:
            click.echo(f"   ✓ Task flowcharts ({len(mermaid_code_per_file)} files)")
        if sequence_diagram_high_level:
            click.echo("   ✓ Sequence diagram (high-level)")
        if sequence_diagram_detailed:
            click.echo("   ✓ Sequence diagram (detailed)")
        if state_diagram:
            click.echo("   ✓ State transition diagram")
        if integration_boundary_diagram:
            integration_count = len(analysis_report.integration_points)
            click.echo(
                f"   ✓ Integration boundary diagram ({integration_count} external systems)"
            )
        if architecture_diagram:
            click.echo("   ✓ Component architecture diagram")

    if dependency_matrix:
        click.echo("   ✓ Dependency matrix")

    if not generate_graph and not dependency_matrix:
        click.echo("   (No diagrams or matrices - use --graph for visualizations)")

    # Files that would be created/modified
    click.echo("\n📝 Files That Would Be Created/Modified:")
    readme_path = role_path / output

    if readme_path.exists():
        # Estimate new content size
        click.echo(f"   → {output} (existing file would be updated)")
        if not no_backup:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{output.rsplit('.', 1)[0]}_backup_{timestamp}.{output.rsplit('.', 1)[1] if '.' in output else 'md'}"
            click.echo(f"   → {backup_name} (backup of existing)")
    else:
        click.echo(f"   → {output} (new file)")

    if not no_docsible:
        docsible_path = role_path / ".docsible"
        if docsible_path.exists():
            click.echo("   → .docsible (metadata file - would be updated)")
        else:
            click.echo("   → .docsible (metadata file - new)")

    # Active flags
    click.echo("\n⚙️  Active Flags:")
    click.echo(f"   --graph: {'✓' if generate_graph else '✗'}")
    click.echo(f"   --hybrid: {'✓' if hybrid else '✗'}")
    click.echo(f"   --no-backup: {'✓' if no_backup else '✗'}")
    click.echo(f"   --minimal: {'✓' if minimal else '✗'}")

    click.echo("\n💡 To generate documentation, run without --dry-run")
    click.echo("=" * 70 + "\n")


def doc_the_role(
    role_path: str | None,
    collection_path: str | None,
    playbook: str | None,
    generate_graph: bool,
    no_backup: bool,
    no_docsible: bool,
    dry_run: bool,
    comments: bool,
    task_line: bool,
    md_collection_template: str | None,
    md_role_template: str | None,
    hybrid: bool,
    no_vars: bool,
    no_tasks: bool,
    no_diagrams: bool,
    simplify_diagrams: bool,
    no_examples: bool,
    no_metadata: bool,
    no_handlers: bool,
    minimal: bool,
    complexity_report: bool,
    include_complexity: bool,
    simplification_report: bool,
    show_dependencies: bool,
    analyze_only: bool,
    append: bool,
    output: str,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
    validate_markdown: bool,
    auto_fix: bool,
    strict_validation: bool,
    show_info: bool = False,
    recommendations_only: bool = False,
) -> None:
    """Generate documentation for an Ansible role.

    This command analyzes an Ansible role and generates comprehensive
    README documentation including variables, tasks, handlers, and
    optional Mermaid diagrams.

    Args:
        role_path: Path to role directory
        collection_path: Path to collection directory
        playbook: Path to playbook file
        generate_graph: Generate Mermaid diagrams
        no_backup: Skip backup creation
        no_docsible: Skip docsible tags
        dry_run: Show what would be generated without writing
        comments: Include task comments
        task_line: Include task line numbers
        md_collection_template: Custom collection template path
        md_role_template: Custom role template path
        hybrid: Use hybrid template format
        no_vars: Exclude variables section
        no_tasks: Exclude tasks section
        no_diagrams: Exclude all diagrams
        simplify_diagrams: Simplify diagram output
        no_examples: Exclude examples section
        no_metadata: Exclude metadata section
        no_handlers: Exclude handlers section
        minimal: Generate minimal documentation
        complexity_report: Show complexity analysis
        include_complexity: Include complexity in README
        simplification_report: Show simplification suggestions
        show_dependencies: Show dependency matrix
        analyze_only: Only analyze, don't generate docs
        append: Append to existing README
        output: Output file path
        repository_url: Repository URL for links
        repo_type: Repository type (github, gitlab, etc)
        repo_branch: Repository branch name
        validate_markdown: Validate generated markdown
        auto_fix: Automatically fix markdown issues
        strict_validation: Fail on validation warnings
        show_info: Show INFO-level recommendations
        recommendations_only: Show only recommendations without generating docs

    Example:
        docsible role --role ./my-role --graph --hybrid
    """

    from docsible.commands.document_role.core_orchestrated import (
        doc_the_role_orchestrated,
    )


    # New orchestrator-based implementation
    return doc_the_role_orchestrated(
        role_path=role_path,
        collection_path=collection_path,
        playbook=playbook,
        generate_graph=generate_graph,
        no_backup=no_backup,
        no_docsible=no_docsible,
        dry_run=dry_run,
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
        validate_markdown=validate_markdown,
        auto_fix=auto_fix,
        strict_validation=strict_validation,
        show_info=show_info,
        recommendations_only=recommendations_only,
    )

