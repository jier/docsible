"""README rendering for roles and collections."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from docsible import constants
from docsible.renderers.tag_manager import manage_docsible_tags, replace_between_tags
from docsible.template_loader import TemplateLoader
from docsible.utils.metadata import generate_metadata
from docsible.validators.doc_validator import ValidationSeverity
from docsible.validators.markdown_fixer import MarkdownFixer
from docsible.validators.markdown_validator import MarkdownValidator

logger = logging.getLogger(__name__)


class ReadmeRenderer:
    """Renders README files for roles and collections using templates.

    Handles template loading, content rendering, and file management including
    backups and tag-based content replacement.

    Attributes:
        template_loader: TemplateLoader instance for accessing templates
        backup: Whether to create backups before overwriting
    """

    def __init__(
        self,
        backup: bool = True,
        validate: bool = True,
        auto_fix: bool = False,
        strict_validation: bool = False,
    ):
        """Initialize ReadmeRenderer.

        Args:
            backup: Create backup files before overwriting (default: True)
            validate: Run markdown formatting validation (default: True)
            auto_fix: Automatically fix formatting issues (default: False)
            strict_validation: Fail on validation errors (default: False, warn only)

        Example:
            >>> renderer = ReadmeRenderer(backup=True, validate=True, auto_fix=True)
            >>> renderer.render_role(role_data, output_path)
        """
        self.template_loader = TemplateLoader()
        self.backup = backup
        self.validate = validate
        self.auto_fix = auto_fix
        self.strict_validation = strict_validation
        self.markdown_validator = MarkdownValidator()
        self.markdown_fixer = MarkdownFixer()

    def render_role(
        self,
        role_info: dict[str, Any],
        output_path: Path,
        template_type: str = "standard",
        custom_template_path: str | None = None,
        mermaid_code_per_file: dict[str, str] | None = None,
        sequence_diagram_high_level: str | None = None,
        sequence_diagram_detailed: str | None = None,
        state_diagram: str | None = None,
        integration_boundary_diagram: str | None = None,
        architecture_diagram: str | None = None,
        complexity_report: Any | None = None,
        include_complexity: bool | None = None,
        dependency_matrix: str | None = None,
        dependency_summary: dict[str, Any] | None = None,
        show_dependency_matrix: bool = False,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False,
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
            if template_type in ["hybrid", "hybrid_modular"]:
                logger.info("Using hybrid template (manual + auto-generated sections)")

        # Render template
        new_content = template.render(
            role=role_info,
            mermaid_code_per_file=mermaid_code_per_file or {},
            sequence_diagram_high_level=sequence_diagram_high_level,
            sequence_diagram_detailed=sequence_diagram_detailed,
            state_diagram=state_diagram,
            integration_boundary_diagram=integration_boundary_diagram,
            architecture_diagram=architecture_diagram,
            complexity_report=complexity_report,
            include_complexity=include_complexity,
            dependency_matrix=dependency_matrix,
            dependency_summary=dependency_summary,
            show_dependency_matrix=show_dependency_matrix,
            no_vars=no_vars,
            no_tasks=no_tasks,
            no_diagrams=no_diagrams,
            simplify_diagrams=simplify_diagrams,
            no_examples=no_examples,
            no_metadata=no_metadata,
            no_handlers=no_handlers,
        )

        new_content = manage_docsible_tags(new_content)

        # Validate and auto-fix markdown formatting
        if self.validate or self.auto_fix:
            new_content = self._validate_and_fix_markdown(new_content)
        try:
            metadata = generate_metadata(Path(output_path).parent.resolve())
            new_content = metadata.to_comment() + "\n" + new_content
        except Exception as e:
            # Don't fail if metadata generation fails
            logger.warning(f"Could not generate metadata: {e}")

        # Handle existing file
        final_content = self._merge_content(output_path, new_content, append)

        # Write file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        logger.info(f"✓ README written at: {output_path}")

    def render_collection(
        self,
        collection_metadata: dict[str, Any],
        roles_info: list,
        output_path: Path,
        custom_template_path: str | None = None,
        no_vars: bool = False,
        no_tasks: bool = False,
        no_diagrams: bool = False,
        simplify_diagrams: bool = False,
        no_examples: bool = False,
        no_metadata: bool = False,
        no_handlers: bool = False,
        append: bool = False,
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

        with open(output_path, encoding="utf-8") as f:
            existing_content = f.read()

        if not append:
            return new_content

        # Append mode: replace between tags or append to end
        if (
            constants.DOCSIBLE_START_TAG in existing_content
            and constants.DOCSIBLE_END_TAG in existing_content
        ):
            return replace_between_tags(existing_content, new_content)
        else:
            return f"{existing_content}\n{new_content}"

    def _validate_and_fix_markdown(self, markdown: str) -> str:
        """
        Validate and optionally auto-fix markdown formatting.

        Args:
            markdown: Raw markdown content

        Returns:
            Fixed markdown (if auto_fix=True) or original markdown

        Raises:
            ValueError: If strict_validation=True and errors found
        """
        # Auto-fix if enabled (do this first)
        if self.auto_fix:
            original_markdown = markdown
            markdown = self.markdown_fixer.fix_all(markdown)
            logger.info("🔧 Auto-fixed markdown formatting issues")

        # Validate if enabled
        if self.validate:
            issues = self.markdown_validator.validate(markdown)

            if issues:
                # Categorize issues by severity
                errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
                warnings = [
                    i for i in issues if i.severity == ValidationSeverity.WARNING
                ]
                #FIXME What happened here?
                infos = [i for i in issues if i.severity == ValidationSeverity.INFO]

                # Log errors
                if errors:
                    logger.error(
                        f"❌ Markdown validation found {len(errors)} error(s):"
                    )
                    for error in errors[:5]:  # Show first 5
                        line_info = (
                            f" (line {error.line_number})" if error.line_number else ""
                        )
                        logger.error(f"  {error.message}{line_info}")
                    if len(errors) > 5:
                        logger.error(f"  ... and {len(errors) - 5} more errors")

                # Log warnings
                if warnings:
                    logger.warning(
                        f"⚠️  Markdown validation found {len(warnings)} warning(s):"
                    )
                    for warning in warnings[:3]:  # Show first 3
                        line_info = (
                            f" (line {warning.line_number})"
                            if warning.line_number
                            else ""
                        )
                        logger.warning(f"  {warning.message}{line_info}")
                    if len(warnings) > 3:
                        logger.warning(f"  ... and {len(warnings) - 3} more warnings")

                # Strict mode - fail on errors
                if self.strict_validation and errors:
                    error_summary = "\n".join(
                        [f"Line {e.line_number}: {e.message}" for e in errors[:10]]
                    )
                    raise ValueError(
                        f"Markdown validation failed with {len(errors)} error(s):\n{error_summary}\n\n"
                        f"Fix template issues or use --no-validate to skip validation."
                    )

                # Provide helpful suggestions
                if errors and not self.auto_fix:
                    logger.info(
                        "ℹ️  Run with --auto-fix to automatically correct formatting issues"
                    )
            else:
                logger.info("✓ Markdown validation passed with no issues")

        return markdown
