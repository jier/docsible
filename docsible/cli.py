# Import libraries
import os
from datetime import datetime
from pathlib import Path
from shutil import copyfile

import click
import yaml
from jinja2 import BaseLoader, Environment, FileSystemLoader

from docsible.hybrid_template import hybrid_role_template
from docsible.markdown_template import collection_template, static_template
from docsible.utils.git import get_repo_info
from docsible.utils.mermaid import (
    generate_mermaid_playbook,
    generate_mermaid_role_tasks_per_file,
)
from docsible.utils.mermaid_sequence import (
    generate_mermaid_sequence_playbook_high_level,
    generate_mermaid_sequence_role_detailed,
)
from docsible.utils.project_structure import ProjectStructure, create_example_config
from docsible.utils.special_tasks_keys import process_special_task_keys
from docsible.utils.yaml import (
    get_task_comments,
    get_task_line_numbers,
    load_yaml_files_from_dir_custom,
    load_yaml_generic,
)

DOCSIBLE_START_TAG = "<!-- DOCSIBLE START -->"
DOCSIBLE_END_TAG = "<!-- DOCSIBLE END -->"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")


def get_version():
    return "0.8.0"


def extract_playbook_role_dependencies(playbook_content, current_role_name):
    """
    Extract role names from playbook that differ from the current role name.

    Searches for roles in:
    - roles: section
    - include_role/import_role tasks in pre_tasks, tasks, post_tasks

    Args:
        playbook_content: YAML content of the playbook as string
        current_role_name: Name of the current role being documented

    Returns:
        List of role names (excluding current role)
    """
    if not playbook_content:
        return []

    try:
        playbook_data = yaml.safe_load(playbook_content)
        if not isinstance(playbook_data, list):
            return []

        playbook_roles = []

        for play in playbook_data:
            if not isinstance(play, dict):
                continue

            # Extract roles from 'roles' key
            roles = play.get("roles", [])
            for role in roles:
                if isinstance(role, dict):
                    # Role as dict: {role: name, vars: {...}}
                    role_name = role.get("role", role.get("name"))
                else:
                    # Role as string: "role_name"
                    role_name = str(role)

                # Only add if different from current role and not already in list
                if (
                    role_name
                    and role_name != current_role_name
                    and role_name not in playbook_roles
                ):
                    playbook_roles.append(role_name)

            # Extract roles from include_role/import_role in task sections
            for task_section in ["pre_tasks", "tasks", "post_tasks"]:
                tasks = play.get(task_section, [])
                if not isinstance(tasks, list):
                    continue

                for task in tasks:
                    if not isinstance(task, dict):
                        continue

                    # Check for include_role or import_role
                    for role_action in ["include_role", "import_role"]:
                        if role_action in task:
                            role_spec = task[role_action]

                            # Role can be specified as string or dict with 'name' key
                            if isinstance(role_spec, str):
                                role_name = role_spec
                            elif isinstance(role_spec, dict):
                                role_name = role_spec.get("name")
                            else:
                                continue

                            # Add if different from current role and not already in list
                            if (
                                role_name
                                and role_name != current_role_name
                                and role_name not in playbook_roles
                            ):
                                playbook_roles.append(role_name)

        return playbook_roles
    except Exception as e:
        print(f"[WARN] Could not extract playbook role dependencies: {e}")
        return []


def manage_docsible_file_keys(docsible_path):
    default_data = {
        "description": None,
        "requester": None,
        "users": None,
        "dt_dev": None,
        "dt_prod": None,
        "dt_update": datetime.now().strftime("%Y/%m/%d"),
        "version": None,
        "time_saving": None,
        "category": None,
        "subCategory": None,
        "aap_hub": None,
        "critical": None,
        "automation_kind": None,
    }
    if os.path.exists(docsible_path):
        with open(docsible_path, "r") as f:
            existing_data = yaml.safe_load(f) or {}

        updated_data = {**default_data, **existing_data}
        if updated_data != existing_data:
            # Update dt_update field if docsible keys added
            existing_data["dt_update"] = datetime.now().strftime("%Y/%m/%d")
            with open(docsible_path, "w", encoding="utf-8") as f:
                yaml.dump(updated_data, f, default_flow_style=False)
            print(f"Updated {docsible_path} with new keys.")
    else:
        with open(docsible_path, "w", encoding="utf-8") as f:
            yaml.dump(default_data, f, default_flow_style=False)
        print(f"Initialized {docsible_path} with default keys.")


def manage_docsible_tags(content):
    return f"{DOCSIBLE_START_TAG}\n{content}\n{DOCSIBLE_END_TAG}\n"


def replace_between_tags(existing_content, new_content):
    start_index = existing_content.find(DOCSIBLE_START_TAG)
    end_index = existing_content.find(DOCSIBLE_END_TAG) + len(DOCSIBLE_END_TAG)

    if start_index != -1 and end_index != -1:
        before = existing_content[:start_index].rstrip()
        after = existing_content[end_index:].lstrip()
        return f"{before}\n{new_content}\n{after}".strip()
    else:
        return existing_content + "\n" + new_content.strip()


def render_readme_template(
    collection_metadata, md_collection_template, roles_info, output_path, append
):
    """
    Render the collection README.md using an embedded Jinja template.
    """
    # Render the static template
    if md_collection_template:
        template_dir = os.path.dirname(md_collection_template)
        template_file = os.path.basename(md_collection_template)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
    else:
        env = Environment(loader=BaseLoader)
        template = env.from_string(collection_template)
    data = {"collection": collection_metadata, "roles": roles_info}
    new_content = template.render(data)
    new_content = manage_docsible_tags(new_content)

    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_readme = f.read()
        if append:
            if (
                DOCSIBLE_START_TAG in existing_readme
                and DOCSIBLE_END_TAG in existing_readme
            ):
                final_content = replace_between_tags(existing_readme, new_content)
            else:
                final_content = f"{existing_readme}\n{new_content}"
        else:
            final_content = new_content
    else:
        final_content = new_content

    with open(output_path, "w", encoding="utf-8") as readme_file:
        readme_file.write(final_content)
    print(f"Collection README.md written at: {output_path}")


def document_collection_roles(
    collection_path,
    playbook,
    graph,
    no_backup,
    no_docsible,
    comments,
    task_line,
    md_collection_template,
    md_role_template,
    hybrid,
    no_vars,
    append,
    output,
    repository_url,
    repo_type,
    repo_branch,
):
    """
    Document all roles in a collection, extracting metadata from galaxy.yml or galaxy.yaml.
    """
    # Initialize project structure
    project_structure = ProjectStructure(collection_path)

    try:
        git_info = get_repo_info(collection_path) or {}
    except Exception as e:
        print(f"[WARN] Could not get Git info: {e}")
        git_info = {}
    repository_url = git_info.get("repository") if git_info else None
    repo_branch = repo_branch or (git_info.get("branch") if git_info else "main")
    repo_type = repo_type or (git_info.get("repository_type") if git_info else None)

    # Find all collection markers in the directory tree
    collection_markers = project_structure.find_collection_markers()

    if not collection_markers:
        print(
            f"[WARN] No collection marker files (galaxy.yml/yaml) found in {collection_path}"
        )
        return

    for galaxy_path in collection_markers:
        collection_root = galaxy_path.parent

        with open(galaxy_path, "r") as f:
            collection_metadata = yaml.safe_load(f)
            if output == "README.md":
                readme_path = os.path.join(
                    str(collection_root), collection_metadata.get("readme", output)
                )
            else:
                readme_path = os.path.join(str(collection_root), output)

        collection_metadata["repository_type"] = repo_type
        collection_metadata["repository_branch"] = repo_branch

        if os.path.exists(readme_path) and not no_backup:
            backup_path = f"{readme_path[: readme_path.lower().rfind('.md')]}_backup_{timestamp}.md"
            copyfile(readme_path, backup_path)
            print(f"Backup of existing {output} created at: {backup_path}")

        # Use ProjectStructure to find roles directory
        collection_structure = ProjectStructure(str(collection_root))
        roles_dir = collection_structure.get_roles_dir()

        roles_info = []
        if roles_dir.exists() and roles_dir.is_dir():
            for role in os.listdir(str(roles_dir)):
                role_path = roles_dir / role
                if role_path.is_dir():
                    if playbook:
                        playbook_content = None
                        role_playbook_path = role_path / playbook
                        try:
                            with open(role_playbook_path, "r") as f:
                                playbook_content = f.read()
                        except FileNotFoundError:
                            print(f"{role} playbook not found:", role_playbook_path)
                        except Exception as e:
                            print(f"{playbook} import for {role} error:", e)
                    role_info = document_role(
                        str(role_path),
                        playbook_content,
                        graph,
                        no_backup,
                        no_docsible,
                        comments,
                        task_line,
                        md_role_template,
                        hybrid,
                        no_vars,
                        belongs_to_collection=collection_metadata,
                        append=append,
                        output=output,
                        repository_url=repository_url,
                        repo_type=repo_type,
                        repo_branch=repo_branch,
                    )
                    roles_info.append(role_info)

        render_readme_template(
            collection_metadata, md_collection_template, roles_info, readme_path, append
        )


@click.command()
@click.option("--role", "-r", default=None, help="Path to the Ansible role directory.")
@click.option(
    "--collection", "-c", default=None, help="Path to the Ansible collection directory."
)
@click.option(
    "--playbook", "-p", default="tests/test.yml", help="Path to the playbook file."
)
@click.option("--graph", "-g", is_flag=True, help="Generate Mermaid graph for tasks.")
@click.option(
    "--no-backup", "-nob", is_flag=True, help="Do not backup the readme before remove."
)
@click.option(
    "--no-docsible",
    "-nod",
    is_flag=True,
    help="Do not generate .docsible file and do not include it in README.md.",
)
@click.option("--comments", "-com", is_flag=True, help="Read comments from tasks files")
@click.option("--task-line", "-tl", is_flag=True, help="Read line numbers from tasks")
@click.option(
    "--md-collection-template",
    "-ctpl",
    default=None,
    help="Path to the collection markdown template file.",
)
@click.option(
    "--md-role-template",
    "-rtpl",
    "--md-template",
    "-tpl",
    default=None,
    help="Path to the role markdown template file.",
)
@click.option(
    "--hybrid",
    is_flag=True,
    help="Use hybrid template (combines manual sections with auto-generated content).",
)
@click.option(
    "--no-vars", is_flag=True, help="Skip variable documentation generation."
)
@click.option(
    "--append",
    "-a",
    is_flag=True,
    help="Append to the existing README.md instead of replacing it.",
)
@click.option("--output", "-o", default="README.md", help="Output readme file name.")
@click.option(
    "--repository-url",
    "-ru",
    default=None,
    help="Repository base URL (used for standalone roles)",
)
@click.option(
    "--repo-type",
    "-rt",
    default=None,
    help="Repository type: github, gitlab, gitea, etc.",
)
@click.option(
    "--repo-branch",
    "-rb",
    default=None,
    help="Repository branch name (e.g., main or master)",
)
@click.version_option(
    version=get_version(), help=f"Show the module version. Actual is {get_version()}"
)
def doc_the_role(
    role,
    collection,
    playbook,
    graph,
    no_backup,
    no_docsible,
    comments,
    task_line,
    md_collection_template,
    md_role_template,
    hybrid,
    no_vars,
    append,
    output,
    repository_url,
    repo_type,
    repo_branch,
):
    if collection:
        collection_path = os.path.abspath(collection)
        if not os.path.exists(collection_path) or not os.path.isdir(collection_path):
            print(f"Folder {collection_path} does not exist.")
            return
        document_collection_roles(
            collection_path,
            playbook,
            graph,
            no_backup,
            no_docsible,
            comments,
            task_line,
            md_collection_template,
            md_role_template,
            hybrid,
            no_vars,
            append,
            output,
            repository_url,
            repo_type,
            repo_branch,
        )
    elif role:
        role_path = os.path.abspath(role)
        if not os.path.exists(role_path) or not os.path.isdir(role_path):
            print(f"Folder {role_path} does not exist.")
            return

        if playbook == "tests/test.yml":
            playbook = os.path.join(role_path, playbook)

        playbook_content = None
        if playbook:
            try:
                with open(playbook, "r") as f:
                    playbook_content = f.read()
            except FileNotFoundError:
                print("playbook not found:", playbook)
            except Exception as e:
                print("playbook import error:", e)
        document_role(
            role_path,
            playbook_content,
            graph,
            no_backup,
            no_docsible,
            comments,
            task_line,
            md_role_template,
            hybrid,
            no_vars,
            belongs_to_collection=False,
            append=append,
            output=output,
            repository_url=repository_url,
            repo_type=repo_type,
            repo_branch=repo_branch,
        )
    else:
        print("Please specify either a role or a collection path.")


def document_role(
    role_path,
    playbook_content,
    generate_graph,
    no_backup,
    no_docsible,
    comments,
    task_line,
    md_role_template,
    hybrid,
    no_vars,
    belongs_to_collection,
    append,
    output,
    repository_url,
    repo_type,
    repo_branch,
):
    # Initialize project structure for this role
    project_structure = ProjectStructure(role_path)

    role_name = os.path.basename(role_path)
    readme_path = os.path.join(role_path, output)
    docsible_path = os.path.join(role_path, ".docsible")

    if not no_docsible:
        manage_docsible_file_keys(docsible_path)

    # Use ProjectStructure to get meta file path
    meta_path = project_structure.get_meta_file(Path(role_path))
    if meta_path is None:
        print(f"[WARN] No meta file found for role {role_name}")
        meta_path = (
            Path(role_path) / "meta" / "main.yml"
        )  # Fallback for load_yaml_generic

    # Use ProjectStructure to get argument specs file
    argument_specs_path = project_structure.get_argument_specs_file(Path(role_path))

    if argument_specs_path and argument_specs_path.exists():
        argument_specs = load_yaml_generic(str(argument_specs_path))
    else:
        argument_specs = None

    # Use ProjectStructure to get defaults and vars directories
    defaults_dir = project_structure.get_defaults_dir(Path(role_path))
    vars_dir = project_structure.get_vars_dir(Path(role_path))

    defaults_data = load_yaml_files_from_dir_custom(str(defaults_dir)) or []
    vars_data = load_yaml_files_from_dir_custom(str(vars_dir)) or []

    if repository_url == "detect":
        try:
            git_info = get_repo_info(role_path) or {}
        except Exception as e:
            print(f"[WARN] Could not get Git info: {e}")
            git_info = {}
        repository_url = git_info.get("repository") if git_info else None
        repo_branch = repo_branch or (git_info.get("branch") if git_info else "main")
        repo_type = repo_type or (git_info.get("repository_type") if git_info else None)

    # Extract playbook role dependencies (roles different from current role)
    playbook_dependencies = extract_playbook_role_dependencies(
        playbook_content, role_name
    )

    role_info = {
        "name": role_name,
        "defaults": defaults_data,
        "vars": vars_data,
        "tasks": [],
        "handlers": [],
        "meta": load_yaml_generic(str(meta_path)) or {},
        "playbook": {
            "content": playbook_content,
            "graph": generate_mermaid_playbook(yaml.safe_load(playbook_content))
            if generate_graph and playbook_content
            else None,
            "dependencies": playbook_dependencies,
        },
        "docsible": load_yaml_generic(docsible_path) if not no_docsible else None,
        "belongs_to_collection": belongs_to_collection,
        "repository": repository_url,
        "repository_type": repo_type,
        "repository_branch": repo_branch,
        "argument_specs": argument_specs,
    }

    # Use ProjectStructure to get tasks directory
    tasks_dir = project_structure.get_tasks_dir(Path(role_path))
    role_info["tasks"] = []

    if tasks_dir.exists() and tasks_dir.is_dir():
        # Get supported YAML extensions from project structure
        yaml_extensions = project_structure.get_yaml_extensions()

        for dirpath, dirnames, filenames in os.walk(str(tasks_dir)):
            for task_file in filenames:
                # Check if file has a supported YAML extension
                if any(task_file.endswith(ext) for ext in yaml_extensions):
                    file_path = os.path.join(dirpath, task_file)
                    tasks_data = load_yaml_generic(file_path)
                    if tasks_data:
                        relative_path = os.path.relpath(file_path, str(tasks_dir))
                        task_info = {
                            "file": relative_path,
                            "tasks": [],
                            "mermaid": [],
                            "comments": [],
                            "lines": [],
                        }
                        if comments:
                            task_info["comments"] = get_task_comments(file_path)
                        if task_line:
                            task_info["lines"] = get_task_line_numbers(file_path)
                        if not isinstance(tasks_data, list):
                            print(
                                f"Unexpected data type for tasks in {task_file}. Skipping."
                            )
                            continue
                        for task in tasks_data:
                            if not isinstance(task, dict):
                                print(
                                    f"Skipping unexpected data in {task_file}: {task}"
                                )
                                continue
                            if task and len(task.keys()) > 0:
                                processed_tasks = process_special_task_keys(task)
                                task_info["tasks"].extend(processed_tasks)
                                task_info["mermaid"].extend([task])

                        role_info["tasks"].append(task_info)

    # Scan handlers directory (similar to tasks)
    handlers_dir = Path(role_path) / "handlers"
    role_info["handlers"] = []

    if handlers_dir.exists() and handlers_dir.is_dir():
        yaml_extensions = project_structure.get_yaml_extensions()

        for dirpath, dirnames, filenames in os.walk(str(handlers_dir)):
            for handler_file in filenames:
                if any(handler_file.endswith(ext) for ext in yaml_extensions):
                    file_path = os.path.join(dirpath, handler_file)
                    handlers_data = load_yaml_generic(file_path)
                    if handlers_data and isinstance(handlers_data, list):
                        for handler in handlers_data:
                            if isinstance(handler, dict) and "name" in handler:
                                # Extract handler info
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
                                    "file": os.path.relpath(
                                        file_path, str(handlers_dir)
                                    ),
                                }
                                role_info["handlers"].append(handler_info)

    if os.path.exists(readme_path):
        if not no_backup:
            backup_readme_path = os.path.join(
                role_path,
                f"{output[: output.lower().rfind('.md')]}_backup_{timestamp}.md",
            )
            copyfile(readme_path, backup_readme_path)
            print(f"Readme file backed up as: {backup_readme_path}")
        if not append:
            os.remove(readme_path)

    mermaid_code_per_file = {}
    sequence_diagram_high_level = None
    sequence_diagram_detailed = None

    if generate_graph:
        mermaid_code_per_file = generate_mermaid_role_tasks_per_file(role_info["tasks"])

        # Generate sequence diagrams
        # High-level: playbook → roles (for Architecture Overview)
        if playbook_content:
            try:
                playbook_parsed = yaml.safe_load(playbook_content)
                sequence_diagram_high_level = (
                    generate_mermaid_sequence_playbook_high_level(
                        playbook_parsed, role_meta=role_info.get("meta")
                    )
                )
            except Exception as e:
                print(f"[WARN] Could not generate high-level sequence diagram: {e}")

        # Detailed: role → tasks → handlers (for Task Execution Flow)
        try:
            sequence_diagram_detailed = generate_mermaid_sequence_role_detailed(
                role_info, include_handlers=len(role_info.get("handlers", [])) > 0
            )
        except Exception as e:
            print(f"[WARN] Could not generate detailed sequence diagram: {e}")

    # Render the template
    if md_role_template:
        # Custom template provided
        template_dir = os.path.dirname(md_role_template)
        template_file = os.path.basename(md_role_template)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_file)
    elif hybrid:
        # Use hybrid template
        env = Environment(loader=BaseLoader)
        template = env.from_string(hybrid_role_template)
        print("[INFO] Using hybrid template (manual + auto-generated sections)")
    else:
        # Use standard template
        env = Environment(loader=BaseLoader)
        template = env.from_string(static_template)
    new_content = template.render(
        role=role_info,
        mermaid_code_per_file=mermaid_code_per_file,
        sequence_diagram_high_level=sequence_diagram_high_level,
        sequence_diagram_detailed=sequence_diagram_detailed,
        no_vars=no_vars,
    )
    new_content = manage_docsible_tags(new_content)

    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            existing_readme = f.read()
        if append:
            if (
                DOCSIBLE_START_TAG in existing_readme
                and DOCSIBLE_END_TAG in existing_readme
            ):
                final_content = replace_between_tags(existing_readme, new_content)
            else:
                final_content = f"{existing_readme}\n{new_content}"
        else:
            final_content = new_content
    else:
        final_content = new_content

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print("Documentation generated at:", readme_path)
    return role_info


@click.command()
@click.option("--path", "-p", default=".", help="Path where to create .docsible.yml")
@click.option(
    "--force", "-f", is_flag=True, help="Overwrite existing .docsible.yml file"
)
def init_config(path, force):
    """
    Generate an example .docsible.yml configuration file.
    This file allows you to customize how docsible interprets your Ansible project structure.
    """
    config_path = Path(path) / ".docsible.yml"

    if config_path.exists() and not force:
        print(f"[ERROR] Configuration file already exists at {config_path}")
        print("Use --force to overwrite it.")
        return

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(create_example_config())
        print(f"[SUCCESS] Example configuration created at: {config_path}")
        print("\nYou can now customize this file to match your project structure.")
    except Exception as e:
        print(f"[ERROR] Failed to create configuration file: {e}")


if __name__ == "__main__":
    doc_the_role()
