"""README rendering for roles and collections."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from docsible import constants
from docsible.renderers.tag_manager import manage_docsible_tags, replace_between_tags
from docsible.template_loader import TemplateLoader

logger = logging.getLogger(__name__)


class ReadmeRenderer:
    """Renders README files for roles and collections using templates.

    Handles template loading, content rendering, and file management including
    backups and tag-based content replacement.

    Attributes:
        template_loader: TemplateLoader instance for accessing templates
        backup: Whether to create backups before overwriting
    """

    def __init__(self, backup: bool = True):
        """Initialize ReadmeRenderer.

        Args:
            backup: Create backup files before overwriting (default: True)

        Example:
            >>> renderer = ReadmeRenderer(backup=True)
            >>> renderer.render_role(role_data, output_path)
        """
        self.template_loader = TemplateLoader()
        self.backup = backup

    def render_role(
        self,
        role_info: Dict[str, Any],
        output_path: Path,
        template_type: str = 'standard',
        custom_template_path: Optional[str] = None,
        mermaid_code_per_file: Optional[Dict[str, str]] = None,
        sequence_diagram_high_level: Optional[str] = None,
        sequence_diagram_detailed: Optional[str] = None,
        state_diagram: Optional[str] = None,
        integration_boundary_diagram: Optional[str] = None,
        complexity_report: Optional[Any] = None,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False
    ) -> None:
        """Render role README from template.

        Args:
            role_info: Role information dictionary
            output_path: Path where README will be written
            template_type: 'standard' or 'hybrid' (default: 'standard')
            custom_template_path: Optional custom template file path
            mermaid_code_per_file: Task flow graphs per file
            sequence_diagram_high_level: High-level sequence diagram
            sequence_diagram_detailed: Detailed sequence diagram
            no_vars: Skip variable documentation
            append: Append to existing README instead of replacing

        Example:
            >>> renderer = ReadmeRenderer()
            >>> renderer.render_role(
            ...     role_info={'name': 'my_role', ...},
            ...     output_path=Path('README.md')
            ... )
        """
        # Backup existing file if requested
        if self.backup and output_path.exists():
            self._create_backup(output_path)

        # Load template
        if custom_template_path:
            template = self._load_custom_template(custom_template_path)
        else:
            template = self.template_loader.get_role_template(template_type)
            if template_type == 'hybrid':
                logger.info("Using hybrid template (manual + auto-generated sections)")

        # Render template
        new_content = template.render(
            role=role_info,
            mermaid_code_per_file=mermaid_code_per_file or {},
            sequence_diagram_high_level=sequence_diagram_high_level,
            sequence_diagram_detailed=sequence_diagram_detailed,
            state_diagram=state_diagram,
            integration_boundary_diagram=integration_boundary_diagram,
            complexity_report=complexity_report,
            no_vars=no_vars,
            no_tasks=no_tasks,
            no_diagrams=no_diagrams,
            simplify_diagrams=simplify_diagrams,
            no_examples=no_examples,
            no_metadata=no_metadata,
            no_handlers=no_handlers,
        )
        new_content = manage_docsible_tags(new_content)

        # Handle existing file
        final_content = self._merge_content(output_path, new_content, append)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        logger.info(f"README written at: {output_path}")

    def render_collection(
        self,
        collection_metadata: Dict[str, Any],
        roles_info: list,
        output_path: Path,
        custom_template_path: Optional[str] = None,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False
    ) -> None:
        """Render collection README from template.

        Args:
            collection_metadata: Collection metadata dictionary
            roles_info: List of role information dictionaries
            output_path: Path where README will be written
            custom_template_path: Optional custom template file path
            no_vars: Hide variable documentation
            no_tasks: Hide task lists and task details
            no_diagrams: Hide all Mermaid diagrams
            simplify_diagrams: Show only high-level diagrams
            no_examples: Hide example playbook sections
            no_metadata: Hide role metadata
            no_handlers: Hide handlers section
            append: Append to existing README instead of replacing

        Example:
            >>> renderer = ReadmeRenderer()
            >>> renderer.render_collection(
            ...     collection_metadata={'namespace': 'my', 'name': 'collection'},
            ...     roles_info=[...],
            ...     output_path=Path('README.md')
            ... )
        """
        # Backup existing file if requested
        if self.backup and output_path.exists():
            self._create_backup(output_path)

        # Load template
        if custom_template_path:
            template = self._load_custom_template(custom_template_path)
        else:
            template = self.template_loader.get_collection_template()

        # Render template
        data = {
            "collection": collection_metadata,
            "roles": roles_info,
            "no_vars": no_vars,
            "no_tasks": no_tasks,
            "no_diagrams": no_diagrams,
            "simplify_diagrams": simplify_diagrams,
            "no_examples": no_examples,
            "no_metadata": no_metadata,
            "no_handlers": no_handlers,
        }
        new_content = template.render(data)
        new_content = manage_docsible_tags(new_content)

        # Handle existing file
        final_content = self._merge_content(output_path, new_content, append)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        logger.info(f"Collection README written at: {output_path}")

    def _create_backup(self, file_path: Path) -> None:
        """Create timestamped backup of existing file.

        Args:
            file_path: Path to file to backup
        """
        timestamp = datetime.now().strftime(constants.BACKUP_TIMESTAMP_FORMAT)
        stem = file_path.stem  
        suffix = file_path.suffix 
        backup_path = file_path.with_name(f"{stem}_backup_{timestamp}{suffix}")

        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _load_custom_template(self, template_path: str):
        """Load custom template from file path.

        Args:
            template_path: Path to custom template file

        Returns:
            Loaded Jinja2 template
        """
        template_dir = os.path.dirname(template_path)
        template_file = os.path.basename(template_path)
        env = Environment(loader=FileSystemLoader(template_dir))
        return env.get_template(template_file)

    def _merge_content(self, output_path: Path, new_content: str, append: bool) -> str:
        """Merge new content with existing file based on append mode.

        Args:
            output_path: Path to output file
            new_content: New generated content
            append: Whether to append or replace

        Returns:
            Final merged content
        """
        if not output_path.exists():
            return new_content

        with open(output_path, "r", encoding="utf-8") as f:
            existing_content = f.read()

        if not append:
            return new_content

        # Append mode: replace between tags or append to end
        if (constants.DOCSIBLE_START_TAG in existing_content
                and constants.DOCSIBLE_END_TAG in existing_content):
            return replace_between_tags(existing_content, new_content)
        else:
            return f"{existing_content}\n{new_content}"
