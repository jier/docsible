"""Command for documenting Ansible collections."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

import yaml

from docsible import constants
from docsible.commands.document_role import build_role_info
from docsible.renderers.readme_renderer import ReadmeRenderer
from docsible.utils.git import get_repo_info
from docsible.utils.project_structure import ProjectStructure
from docsible.exceptions import CollectionNotFoundError

logger = logging.getLogger(__name__)


def document_collection_roles(
    collection_path: str,
    playbook: str,
    graph: bool,
    no_backup: bool,
    no_docsible: bool,
    comments: bool,
    task_line: bool,
    md_collection_template: str,
    md_role_template: str,
    hybrid: bool,
    no_vars: bool,
    append: bool,
    output: str,
    repository_url: str,
    repo_type: str,
    repo_branch: str,
):
    """Document all roles in an Ansible collection.

    Extracts metadata from galaxy.yml/yaml and generates documentation
    for the collection and all roles within it.

    Args:
        collection_path: Path to collection directory
        playbook: Path to playbook file (relative to each role)
        graph: Generate Mermaid graphs
        no_backup: Skip backup creation
        no_docsible: Skip .docsible file handling
        comments: Extract task comments
        task_line: Extract task line numbers
        md_collection_template: Custom collection template path
        md_role_template: Custom role template path
        hybrid: Use hybrid template for roles
        no_vars: Skip variable documentation
        append: Append to existing README
        output: Output file name
        repository_url: Repository URL
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name
    """

    collection_path_obj = Path(collection_path)
    if not collection_path_obj.exists():
        raise CollectionNotFoundError(f"Collection directory does not exist: {collection_path}")
    
    if not collection_path_obj.is_dir():
        raise CollectionNotFoundError(f"Path is not a directory: {collection_path}")
    
    # Initialize project structure
    project_structure = ProjectStructure(collection_path)

    # Get repository info
    try:
        git_info = get_repo_info(collection_path) or {}
        repository_url = git_info.get("repository") or repository_url
        repo_branch = repo_branch or git_info.get("branch", "main")
        repo_type = repo_type or git_info.get("repository_type")
    except Exception as e:
        logger.warning(f"Could not get Git info: {e}")
        repository_url = repository_url or None
        repo_branch = repo_branch or "main"
        repo_type = repo_type or "github"

    # Find all collection markers (galaxy.yml/yaml)
    collection_markers = project_structure.find_collection_markers()

    if not collection_markers:
        logger.warning(
            f"No collection marker files (galaxy.yml/yaml) found in {collection_path}"
        )
        return

    # Process each collection found
    for galaxy_path in collection_markers:
        collection_root = galaxy_path.parent

        # Load collection metadata
        with open(galaxy_path, "r", encoding="utf-8") as f:
            collection_metadata = yaml.safe_load(f)

        # Determine README path
        if output == "README.md":
            readme_path = collection_root / collection_metadata.get("readme", output)
        else:
            readme_path = collection_root / output

        # Add repository info to metadata
        collection_metadata["repository"] = repository_url
        collection_metadata["repository_type"] = repo_type
        collection_metadata["repository_branch"] = repo_branch

        # Find and document all roles
        collection_structure = ProjectStructure(str(collection_root))
        roles_dir = collection_structure.get_roles_dir()

        roles_info = []
        if roles_dir.exists() and roles_dir.is_dir():
            for role_name in os.listdir(str(roles_dir)):
                role_path = roles_dir / role_name

                if not role_path.is_dir():
                    continue

                # Load playbook content if specified
                playbook_content = None
                if playbook:
                    role_playbook_path = role_path / playbook
                    try:
                        with open(role_playbook_path, "r", encoding="utf-8") as f:
                            playbook_content = f.read()
                    except FileNotFoundError:
                        logger.warning(f"Playbook not found for {role_name}: {role_playbook_path}")
                    except Exception as e:
                        logger.error(f"Error loading playbook for {role_name}: {e}")

                # Build role info
                role_info = build_role_info(
                    role_path=role_path,
                    playbook_content=playbook_content,
                    generate_graph=graph,
                    no_docsible=no_docsible,
                    comments=comments,
                    task_line=task_line,
                    belongs_to_collection=collection_metadata,
                    repository_url=repository_url,
                    repo_type=repo_type,
                    repo_branch=repo_branch,
                )

                # Generate role README
                renderer = ReadmeRenderer(backup=not no_backup)
                role_readme_path = role_path / output
                template_type = 'hybrid' if hybrid else 'standard'

                renderer.render_role(
                    role_info=role_info,
                    output_path=role_readme_path,
                    template_type=template_type,
                    custom_template_path=md_role_template,
                    no_vars=no_vars,
                    append=append,
                )

                logger.info(f"✓ Documented role: {role_name}")
                roles_info.append(role_info)

        # Generate collection README
        renderer = ReadmeRenderer(backup=not no_backup)
        renderer.render_collection(
            collection_metadata=collection_metadata,
            roles_info=roles_info,
            output_path=readme_path,
            custom_template_path=md_collection_template,
            no_vars=no_vars,
            append=append,
        )

        logger.info(f"✓ Collection documentation generated: {readme_path}")
