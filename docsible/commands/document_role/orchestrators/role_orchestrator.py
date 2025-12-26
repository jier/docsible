"""Role documentation generation orchestrator.

Coordinates the workflow for generating role documentation by orchestrating
builders, formatters, and renderers.
"""

import logging
from pathlib import Path

import click

from docsible.commands.document_role.builders.role_info_builder import RoleInfoBuilder
from docsible.commands.document_role.formatters.dry_run_formatter import DryRunFormatter
from docsible.commands.document_role.models import RoleCommandContext

logger = logging.getLogger(__name__)


class RoleOrchestrator:
    """Orchestrates role documentation generation process.

    This class coordinates the entire workflow:
    1. Validate paths
    2. Load playbook content
    3. Build role information
    4. Analyze complexity
    5. Generate diagrams
    6. Handle dry-run or generate documentation
    """

    def __init__(self, context: RoleCommandContext):
        """Initialize RoleOrchestrator.

        Args:
            context: Complete role command context with all configuration
        """
        self.context = context
        self.role_info_builder = RoleInfoBuilder()
        self.dry_run_formatter = DryRunFormatter()

    def execute(self) -> None:
        """Execute the documentation generation workflow.

        This is the main entry point that coordinates all steps.
        Designed to eventually replace the main function logic in core.py.
        """
        # Step 1: Validate paths
        role_path = self._validate_paths()

        # Step 2: Load playbook content
        playbook_content = self._load_playbook()

        # Step 3: Build role info
        role_info = self._build_role_info(role_path, playbook_content)

        # Step 4: Analyze complexity
        analysis_report = self._analyze_complexity(role_info)

        # Step 5: Handle analyze-only mode
        if self.context.analysis.analyze_only:
            self._display_analysis_and_exit(analysis_report, role_info)
            return

        # Step 6: Generate diagrams
        diagrams = self._generate_diagrams(role_info, analysis_report, playbook_content)

        # Step 7: Generate dependency matrix
        dependency_data = self._generate_dependencies(role_info, analysis_report)

        # Step 8: Handle dry-run mode
        if self.context.processing.dry_run:
            self._display_dry_run(
                role_info, role_path, analysis_report, diagrams, dependency_data
            )
            return

        # Step 9: Render documentation
        self._render_documentation(
            role_info, role_path, analysis_report, diagrams, dependency_data
        )

    def _validate_paths(self) -> Path:
        """Validate and return role path.

        Returns:
            Validated role path

        Raises:
            click.ClickException: If role path is invalid
        """
        from docsible.commands.document_role.helpers import validate_role_path

        if self.context.paths.role_path is None:
            raise click.ClickException("Role path is required")

        # Convert Path to str for validate_role_path
        role_path_str = str(self.context.paths.role_path)
        return validate_role_path(role_path_str)

    def _load_playbook(self) -> str | None:
        """Load playbook content if provided.

        Returns:
            Playbook content or None
        """
        from docsible.commands.document_role.helpers import load_playbook_content

        # Convert Path to str for load_playbook_content
        playbook_path = self.context.paths.playbook
        if playbook_path is None:
            return None
        return load_playbook_content(str(playbook_path))

    def _build_role_info(self, role_path: Path, playbook_content: str | None) -> dict:
        """Build comprehensive role information.

        Args:
            role_path: Path to role directory
            playbook_content: Optional playbook YAML content

        Returns:
            Role information dictionary
        """
        return self.role_info_builder.build(
            role_path=role_path,
            playbook_content=playbook_content,
            processing=self.context.processing,
            repository=self.context.repository,
        )

    def _analyze_complexity(self, role_info: dict):
        """Analyze role complexity.

        Reuses cached analysis from smart defaults if available to avoid
        duplicate analysis.

        Args:
            role_info: Role information dictionary

        Returns:
            Complexity analysis report
        """
        # Check if we have a cached report from smart defaults
        if self.context.analysis.cached_complexity_report:
            logger.debug("Reusing complexity analysis from smart defaults (avoiding duplicate)")
            return self.context.analysis.cached_complexity_report

        # No cached report available, perform fresh analysis
        from docsible.analyzers import analyze_role_complexity

        logger.debug("Performing fresh complexity analysis")
        return analyze_role_complexity(
            role_info,
            include_patterns=self.context.analysis.simplification_report,
            min_confidence=0.7,
        )

    def _display_analysis_and_exit(self, analysis_report, role_info: dict) -> None:
        """Display analysis report and exit.

        Args:
            analysis_report: Complexity analysis report
            role_info: Role information dictionary
        """
        from docsible.commands.document_role.helpers import handle_analyze_only_mode
        from docsible.utils.console import display_complexity_report

        if self.context.analysis.complexity_report:
            display_complexity_report(analysis_report, role_name=role_info.get("name"))

        handle_analyze_only_mode(role_info, role_info.get("name", "unknown"))

    def _generate_diagrams(
        self, role_info: dict, analysis_report, playbook_content: str | None
    ) -> dict:
        """Generate all Mermaid diagrams.

        Args:
            role_info: Role information dictionary
            analysis_report: Complexity analysis report
            playbook_content: Optional playbook content

        Returns:
            Dictionary of generated diagrams
        """
        from docsible.commands.document_role.helpers import (
            generate_integration_and_architecture_diagrams,
            generate_mermaid_diagrams,
        )

        # Generate task diagrams
        diagrams = generate_mermaid_diagrams(
            generate_graph=self.context.diagrams.generate_graph,
            role_info=role_info,
            playbook_content=playbook_content,
            analysis_report=analysis_report,
            minimal=self.context.content.minimal,
            simplify_diagrams=self.context.content.simplify_diagrams,
        )

        # Add generate_graph flag for formatter
        diagrams["generate_graph"] = self.context.diagrams.generate_graph

        # Generate integration and architecture diagrams
        integration_boundary, architecture = generate_integration_and_architecture_diagrams(
            generate_graph=self.context.diagrams.generate_graph,
            role_info=role_info,
            analysis_report=analysis_report,
        )

        diagrams["integration_boundary_diagram"] = integration_boundary
        diagrams["architecture_diagram"] = architecture

        return diagrams

    def _generate_dependencies(self, role_info: dict, analysis_report) -> dict:
        """Generate dependency matrix and summary.

        Args:
            role_info: Role information dictionary
            analysis_report: Complexity analysis report

        Returns:
            Dictionary with dependency_matrix, dependency_summary, show_matrix
        """
        from docsible.commands.document_role.helpers import generate_dependency_matrix

        dependency_matrix, dependency_summary, show_dependency_matrix = (
            generate_dependency_matrix(
                show_dependencies=self.context.diagrams.show_dependencies,
                role_info=role_info,
                analysis_report=analysis_report,
            )
        )

        return {
            "dependency_matrix": dependency_matrix,
            "dependency_summary": dependency_summary,
            "show_matrix": show_dependency_matrix,
        }

    def _display_dry_run(
        self, role_info: dict, role_path: Path, analysis_report, diagrams: dict, dependency_data: dict
    ) -> None:
        """Display dry-run summary.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory
            analysis_report: Complexity analysis report
            diagrams: Generated diagrams dictionary
            dependency_data: Dependency matrix data
        """
        flags = {
            "generate_graph": self.context.diagrams.generate_graph,
            "hybrid": self.context.template.hybrid,
            "no_backup": self.context.processing.no_backup,
            "no_docsible": self.context.processing.no_docsible,
            "minimal": self.context.content.minimal,
        }

        summary = self.dry_run_formatter.format_summary(
            role_info=role_info,
            role_path=role_path,
            output=self.context.paths.output,
            analysis_report=analysis_report,
            diagrams=diagrams,
            dependency_matrix=dependency_data["dependency_matrix"],
            flags=flags,
        )

        click.echo(summary)

    def _render_documentation(
        self, role_info: dict, role_path: Path, analysis_report, diagrams: dict, dependency_data: dict
    ) -> None:
        """Render final documentation.

        Args:
            role_info: Role information dictionary
            role_path: Path to role directory
            analysis_report: Complexity analysis report
            diagrams: Generated diagrams dictionary
            dependency_data: Dependency matrix data
        """
        from docsible.renderers.readme_renderer import ReadmeRenderer

        # Determine template type
        template_type = "hybrid" if self.context.template.hybrid else "standard_modular"

        # Auto-enable complexity for hybrid mode
        include_complexity = self.context.analysis.include_complexity
        if self.context.template.hybrid and not include_complexity:
            include_complexity = True

        # Create renderer
        renderer = ReadmeRenderer(
            backup=not self.context.processing.no_backup,
            validate=self.context.validation.validate_markdown,
            auto_fix=self.context.validation.auto_fix,
            strict_validation=self.context.validation.strict_validation,
        )

        # Render documentation
        readme_path = role_path / self.context.paths.output

        # Convert Path to str for custom_template_path
        custom_template = self.context.template.md_role_template
        custom_template_str = str(custom_template) if custom_template else None

        renderer.render_role(
            role_info=role_info,
            output_path=readme_path,
            template_type=template_type,
            custom_template_path=custom_template_str,
            mermaid_code_per_file=diagrams.get("mermaid_code_per_file", {}),
            sequence_diagram_high_level=diagrams.get("sequence_diagram_high_level"),
            sequence_diagram_detailed=diagrams.get("sequence_diagram_detailed"),
            state_diagram=diagrams.get("state_diagram"),
            integration_boundary_diagram=diagrams.get("integration_boundary_diagram"),
            architecture_diagram=diagrams.get("architecture_diagram"),
            complexity_report=analysis_report,
            include_complexity=include_complexity,
            dependency_matrix=dependency_data["dependency_matrix"],
            dependency_summary=dependency_data["dependency_summary"],
            show_dependency_matrix=dependency_data["show_matrix"],
            no_vars=self.context.content.no_vars,
            no_tasks=self.context.content.no_tasks,
            no_diagrams=self.context.content.no_diagrams,
            simplify_diagrams=self.context.content.simplify_diagrams,
            no_examples=self.context.content.no_examples,
            no_metadata=self.context.content.no_metadata,
            no_handlers=self.context.content.no_handlers,
            append=self.context.processing.append,
        )

        click.echo(f"✓ Role documentation generated: {readme_path}")
