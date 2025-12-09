"""Command for documenting Ansible roles."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import click
import yaml

from docsible.renderers.readme_renderer import ReadmeRenderer
from docsible.renderers.tag_manager import manage_docsible_file_keys
from docsible.utils.git import get_repo_info
from docsible.utils.mermaid import (
    generate_mermaid_playbook,
    generate_mermaid_role_tasks_per_file,
)
from docsible.utils.mermaid_sequence import (
    generate_mermaid_sequence_playbook_high_level,
    generate_mermaid_sequence_role_detailed,
)
from docsible.utils.project_structure import ProjectStructure
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)
from docsible.exceptions import CollectionNotFoundError

logger = logging.getLogger(__name__)


def extract_playbook_role_dependencies(
    playbook_content: Optional[str],
    current_role_name: str
) -> List[str]:
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
                    role_name = role.get("role") or role.get("name")
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
                                role_name = role_spec.get("name")
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
    playbook_content: Optional[str],
    generate_graph: bool,
    no_docsible: bool,
    comments: bool,
    task_line: bool,
    belongs_to_collection: Optional[Dict],
    repository_url: Optional[str],
    repo_type: Optional[str],
    repo_branch: Optional[str],
) -> Dict:
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
        argument_specs = load_yaml_generic(str(argument_specs_path))

    # Get defaults and vars
    defaults_dir = project_structure.get_defaults_dir(role_path)
    vars_dir = project_structure.get_vars_dir(role_path)
    defaults_data = load_yaml_files_from_dir_custom(str(defaults_dir)) or []
    vars_data = load_yaml_files_from_dir_custom(str(vars_dir)) or []

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
        "meta": load_yaml_generic(str(meta_path)) or {},
        "playbook": {
            "content": playbook_content,
            "graph": (
                generate_mermaid_playbook(yaml.safe_load(playbook_content))
                if generate_graph and playbook_content
                else None
            ),
            "dependencies": playbook_dependencies,
        },
        "docsible": load_yaml_generic(str(docsible_path)) if not no_docsible else None,
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
                    tasks_data = load_yaml_generic(str(file_path))

                    if tasks_data:
                        relative_path = file_path.relative_to(tasks_dir)
                        task_info = {
                            "file": str(relative_path),
                            "tasks": [],
                            "mermaid": [],
                            "comments": [],
                            "lines": [],
                        }

                        if comments:
                            task_info["comments"] = get_task_comments(str(file_path))
                        if task_line:
                            task_info["lines"] = get_task_line_numbers(str(file_path))

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
                    handlers_data = load_yaml_generic(str(file_path))

                    if handlers_data and isinstance(handlers_data, list):
                        for handler in handlers_data:
                            if isinstance(handler, dict) and "name" in handler:
                                handler_info = {
                                    "name": handler.get("name", "Unnamed handler"),
                                    "module": next(
                                        (
                                            k for k in handler.keys()
                                            if k not in ["name", "notify", "when", "tags", "listen"]
                                        ),
                                        "unknown",
                                    ),
                                    "listen": handler.get("listen", []),
                                    "file": str(Path(file_path).relative_to(handlers_dir)),
                                }
                                role_info["handlers"].append(handler_info)

    return role_info


@click.command(name="role")
@click.option("--role", "-r", "role_path", default=None, help="Path to the Ansible role directory.")
@click.option(
    "--collection", "-c", "collection_path", default=None,
    help="Path to the Ansible collection directory."
)
@click.option(
    "--playbook", "-p", default=None,
    help="Path to the playbook file."
)
@click.option("--graph", "-g", "generate_graph", is_flag=True, help="Generate Mermaid graph for tasks.")
@click.option(
    "--no-backup", "-nob", "no_backup", is_flag=True,
    help="Do not backup the readme before remove."
)
@click.option(
    "--no-docsible", "-nod", "no_docsible", is_flag=True,
    help="Do not generate .docsible file and do not include it in README.md."
)
@click.option("--comments", "-com", "comments", is_flag=True, help="Read comments from tasks files")
@click.option("--task-line", "-tl", "task_line", is_flag=True, help="Read line numbers from tasks")
@click.option(
    "--md-collection-template", "-ctpl", "md_collection_template", default=None,
    help="Path to the collection markdown template file."
)
@click.option(
    "--md-role-template", "--md-template", "-rtpl", "-tpl", "md_role_template", default=None,
    help="Path to the role markdown template file."
)
@click.option(
    "--hybrid", "hybrid", is_flag=True,
    help="Use hybrid template (combines manual sections with auto-generated content)."
)
@click.option(
    "--no-vars", "no_vars", is_flag=True,
    help="Hide variable documentation (defaults, vars, argument_specs)."
)
@click.option(
    "--no-tasks", "no_tasks", is_flag=True,
    help="Hide task lists and task details."
)
@click.option(
    "--no-diagrams", "no_diagrams", is_flag=True,
    help="Hide all Mermaid diagrams (flowcharts, sequence diagrams)."
)
@click.option(
    "--simplify-diagrams", "simplify_diagrams", is_flag=True,
    help="Show only high-level diagrams, hide detailed task flowcharts."
)
@click.option(
    "--no-examples", "no_examples", is_flag=True,
    help="Hide example playbook sections."
)
@click.option(
    "--no-metadata", "no_metadata", is_flag=True,
    help="Hide role metadata, author, and license information."
)
@click.option(
    "--no-handlers", "no_handlers", is_flag=True,
    help="Hide handlers section."
)
@click.option(
    "--minimal", "minimal", is_flag=True,
    help="Generate minimal documentation (enables all --no-* flags)."
)
@click.option(
    "--complexity-report", "complexity_report", is_flag=True,
    help="Show role complexity analysis before generating documentation."
)
@click.option(
    "--append", "-a", "append", is_flag=True,
    help="Append to the existing README.md instead of replacing it."
)
@click.option("--output", "-o", "output", default="README.md", help="Output readme file name.")
@click.option(
    "--repository-url", "-ru", "repository_url", default="detect",
    help="Repository base URL (used for standalone roles)"
)
@click.option(
    "--repo-type", "-rt", "repo_type", default=None,
    help="Repository type: github, gitlab, gitea, etc."
)
@click.option(
    "--repo-branch", "-rb", "repo_branch", default=None,
    help="Repository branch name (e.g., main or master)"
)
def doc_the_role(
    role_path,
    collection_path,
    playbook,
    generate_graph,
    no_backup,
    no_docsible,
    comments,
    task_line,
    md_collection_template,
    md_role_template,
    hybrid,
    no_vars,
    no_tasks,
    no_diagrams,
    simplify_diagrams,
    no_examples,
    no_metadata,
    no_handlers,
    minimal,
    complexity_report,
    append,
    output,
    repository_url,
    repo_type,
    repo_branch,
):
    """Generate documentation for an Ansible role.

    This command analyzes an Ansible role and generates comprehensive
    README documentation including variables, tasks, handlers, and
    optional Mermaid diagrams.

    Example:
        docsible role --role ./my-role --graph --hybrid
    """
    # Import here to avoid circular imports
    from docsible.commands.document_collection import document_collection_roles

    # If --minimal is set, enable all --no-* flags
    if minimal:
        no_vars = True
        no_tasks = True
        no_diagrams = True
        no_examples = True
        no_metadata = True
        no_handlers = True

    # If --no-diagrams is set, it overrides --simplify-diagrams
    if no_diagrams:
        simplify_diagrams = False

    # Determine if documenting a collection or role
    if collection_path:
        try:
            document_collection_roles(
                collection_path=collection_path,
                playbook=playbook,
                graph=generate_graph,
                no_backup=no_backup,
                no_docsible=no_docsible,
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
                append=append,
                output=output,
                repository_url=repository_url,
                repo_type=repo_type,
                repo_branch=repo_branch,
            )
        except CollectionNotFoundError as e:
            raise click.ClickException(str(e))
        return

    if not role_path:
        raise click.UsageError("Either --role or --collection must be specified.")

    role_path = Path(role_path).resolve()

    # Load playbook content if provided
    playbook_content = None
    if playbook:
        playbook_path = Path(playbook)
        if playbook_path.exists():
            with open(playbook_path, 'r', encoding='utf-8') as f:
                playbook_content = f.read()
        else:
            logger.warning(f"Playbook file not found: {playbook}")

    if not role_path.exists():
        raise click.ClickException(f"Role directory does not exist: {role_path}")
        
    if not role_path.is_dir():
        raise click.ClickException(f"Path is not a directory: {role_path}")
    
    # Build role information
    role_info = build_role_info(
        role_path=role_path,
        playbook_content=playbook_content,
        generate_graph=generate_graph,
        no_docsible=no_docsible,
        comments=comments,
        task_line=task_line,
        belongs_to_collection=None,  # Set by collection command if needed
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch,
    )

    # Analyze complexity for adaptive visualization
    from docsible.analyzers import analyze_role_complexity
    analysis_report = analyze_role_complexity(role_info)

    # Display complexity analysis if requested
    if complexity_report:
        from docsible.utils.console import display_complexity_report
        display_complexity_report(analysis_report, role_name=role_info.get("name"))

    # Generate Mermaid diagrams if requested
    mermaid_code_per_file = {}
    sequence_diagram_high_level = None
    sequence_diagram_detailed = None
    state_diagram = None

    if generate_graph:
        mermaid_code_per_file = generate_mermaid_role_tasks_per_file(role_info["tasks"])

        # High-level sequence diagram (playbook → roles)
        if playbook_content:
            try:
                playbook_parsed = yaml.safe_load(playbook_content)
                sequence_diagram_high_level = generate_mermaid_sequence_playbook_high_level(
                    playbook_parsed, role_meta=role_info.get("meta")
                )
            except Exception as e:
                logger.warning(f"Could not generate high-level sequence diagram: {e}")

        # Detailed sequence diagram (role → tasks → handlers)
        # Only simplify if --minimal or --simplify-diagrams is set
        # Otherwise, always show full detailed task execution flow
        try:
            should_simplify = minimal or simplify_diagrams
            sequence_diagram_detailed = generate_mermaid_sequence_role_detailed(
                role_info,
                include_handlers=len(role_info.get("handlers", [])) > 0,
                simplify_large=should_simplify,
                max_lines=20
            )
        except Exception as e:
            logger.warning(f"Could not generate detailed sequence diagram: {e}")

        # Generate state transition diagram for MEDIUM complexity roles
        # State diagrams show workflow phases (install -> configure -> validate -> start)
        try:
            from docsible.utils.state_diagram import generate_state_diagram, should_generate_state_diagram

            if should_generate_state_diagram(role_info, analysis_report.category.value):
                state_diagram = generate_state_diagram(role_info, role_name=role_info.get("name"))
                logger.info(f"Generated state transition diagram for MEDIUM complexity role")
        except Exception as e:
            logger.warning(f"Could not generate state diagram: {e}")

    # Determine template type
    template_type = 'hybrid' if hybrid else 'standard'

    # Render README
    renderer = ReadmeRenderer(backup=not no_backup)
    readme_path = role_path / output

    renderer.render_role(
        role_info=role_info,
        output_path=readme_path,
        template_type=template_type,
        custom_template_path=md_role_template,
        mermaid_code_per_file=mermaid_code_per_file,
        sequence_diagram_high_level=sequence_diagram_high_level,
        sequence_diagram_detailed=sequence_diagram_detailed,
        state_diagram=state_diagram,
        no_vars=no_vars,
        no_tasks=no_tasks,
        no_diagrams=no_diagrams,
        simplify_diagrams=simplify_diagrams,
        no_examples=no_examples,
        no_metadata=no_metadata,
        no_handlers=no_handlers,
        append=append,
    )

    click.echo(f"✓ Role documentation generated: {readme_path}")
