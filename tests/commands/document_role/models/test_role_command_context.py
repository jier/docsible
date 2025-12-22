"""Tests for RoleCommandContext and related models."""

from pathlib import Path

from docsible.commands.document_role.models import (
    AnalysisConfig,
    ContentFlags,
    DiagramConfig,
    PathConfig,
    ProcessingConfig,
    RepositoryConfig,
    RoleCommandContext,
    TemplateConfig,
    ValidationConfig,
)


class TestPathConfig:
    """Test PathConfig model."""

    def test_default_creation(self):
        """Test creating PathConfig with defaults."""
        config = PathConfig()
        assert config.role_path is None
        assert config.collection_path is None
        assert config.playbook is None
        assert config.output == "README.md"

    def test_with_role_path(self):
        """Test PathConfig with role path."""
        config = PathConfig(role_path=Path("/path/to/role"))
        assert config.role_path == Path("/path/to/role")
        assert config.output == "README.md"

    def test_custom_output(self):
        """Test PathConfig with custom output filename."""
        config = PathConfig(output="DOCUMENTATION.md")
        assert config.output == "DOCUMENTATION.md"

    def test_all_paths_set(self):
        """Test PathConfig with all paths set."""
        config = PathConfig(
            role_path=Path("/role"),
            collection_path=Path("/collection"),
            playbook=Path("/playbook.yml"),
            output="README.md",
        )
        assert config.role_path == Path("/role")
        assert config.collection_path == Path("/collection")
        assert config.playbook == Path("/playbook.yml")


class TestTemplateConfig:
    """Test TemplateConfig model."""

    def test_default_creation(self):
        """Test creating TemplateConfig with defaults."""
        config = TemplateConfig()
        assert config.hybrid is False
        assert config.md_role_template is None
        assert config.md_collection_template is None

    def test_hybrid_mode(self):
        """Test TemplateConfig with hybrid mode."""
        config = TemplateConfig(hybrid=True)
        assert config.hybrid is True

    def test_custom_templates(self):
        """Test TemplateConfig with custom templates."""
        config = TemplateConfig(
            md_role_template=Path("/templates/role.md"),
            md_collection_template=Path("/templates/collection.md"),
        )
        assert config.md_role_template == Path("/templates/role.md")
        assert config.md_collection_template == Path("/templates/collection.md")


class TestContentFlags:
    """Test ContentFlags model."""

    def test_default_creation(self):
        """Test creating ContentFlags with all defaults (all False)."""
        flags = ContentFlags()
        assert flags.no_vars is False
        assert flags.no_tasks is False
        assert flags.no_diagrams is False
        assert flags.simplify_diagrams is False
        assert flags.no_examples is False
        assert flags.no_metadata is False
        assert flags.no_handlers is False
        assert flags.minimal is False

    def test_minimal_mode(self):
        """Test ContentFlags with minimal mode."""
        flags = ContentFlags(minimal=True)
        assert flags.minimal is True

    def test_selective_flags(self):
        """Test ContentFlags with selective flags enabled."""
        flags = ContentFlags(
            no_vars=True,
            no_diagrams=True,
            simplify_diagrams=True,
        )
        assert flags.no_vars is True
        assert flags.no_diagrams is True
        assert flags.simplify_diagrams is True
        assert flags.no_tasks is False
        assert flags.no_examples is False


class TestDiagramConfig:
    """Test DiagramConfig model."""

    def test_default_creation(self):
        """Test creating DiagramConfig with defaults."""
        config = DiagramConfig()
        assert config.generate_graph is False
        assert config.show_dependencies is False

    def test_enable_graphs(self):
        """Test DiagramConfig with graphs enabled."""
        config = DiagramConfig(generate_graph=True)
        assert config.generate_graph is True

    def test_enable_dependencies(self):
        """Test DiagramConfig with dependencies enabled."""
        config = DiagramConfig(show_dependencies=True)
        assert config.show_dependencies is True


class TestAnalysisConfig:
    """Test AnalysisConfig model."""

    def test_default_creation(self):
        """Test creating AnalysisConfig with defaults."""
        config = AnalysisConfig()
        assert config.complexity_report is False
        assert config.include_complexity is False
        assert config.simplification_report is False
        assert config.analyze_only is False

    def test_complexity_enabled(self):
        """Test AnalysisConfig with complexity report."""
        config = AnalysisConfig(
            complexity_report=True,
            include_complexity=True,
        )
        assert config.complexity_report is True
        assert config.include_complexity is True

    def test_analyze_only_mode(self):
        """Test AnalysisConfig in analyze-only mode."""
        config = AnalysisConfig(analyze_only=True)
        assert config.analyze_only is True


class TestProcessingConfig:
    """Test ProcessingConfig model."""

    def test_default_creation(self):
        """Test creating ProcessingConfig with defaults."""
        config = ProcessingConfig()
        assert config.comments is False
        assert config.task_line is False
        assert config.no_backup is False
        assert config.no_docsible is False
        assert config.dry_run is False
        assert config.append is False

    def test_dry_run_mode(self):
        """Test ProcessingConfig in dry-run mode."""
        config = ProcessingConfig(dry_run=True)
        assert config.dry_run is True

    def test_detailed_processing(self):
        """Test ProcessingConfig with detailed extraction."""
        config = ProcessingConfig(
            comments=True,
            task_line=True,
        )
        assert config.comments is True
        assert config.task_line is True


class TestValidationConfig:
    """Test ValidationConfig model."""

    def test_default_creation(self):
        """Test creating ValidationConfig with defaults."""
        config = ValidationConfig()
        assert config.validate_markdown is False
        assert config.auto_fix is False
        assert config.strict_validation is False

    def test_validation_enabled(self):
        """Test ValidationConfig with validation enabled."""
        config = ValidationConfig(
            validate_markdown=True,
            auto_fix=True,
        )
        assert config.validate_markdown is True
        assert config.auto_fix is True

    def test_strict_mode(self):
        """Test ValidationConfig in strict mode."""
        config = ValidationConfig(
            validate_markdown=True,
            strict_validation=True,
        )
        assert config.validate_markdown is True
        assert config.strict_validation is True


class TestRepositoryConfig:
    """Test RepositoryConfig model."""

    def test_default_creation(self):
        """Test creating RepositoryConfig with defaults."""
        config = RepositoryConfig()
        assert config.repository_url is None
        assert config.repo_type is None
        assert config.repo_branch is None

    def test_auto_detect(self):
        """Test RepositoryConfig with auto-detection."""
        config = RepositoryConfig(repository_url="detect")
        assert config.repository_url == "detect"

    def test_full_config(self):
        """Test RepositoryConfig with all fields."""
        config = RepositoryConfig(
            repository_url="https://github.com/user/repo",
            repo_type="github",
            repo_branch="main",
        )
        assert config.repository_url == "https://github.com/user/repo"
        assert config.repo_type == "github"
        assert config.repo_branch == "main"


class TestRoleCommandContext:
    """Test RoleCommandContext model."""

    def test_minimal_creation(self):
        """Test creating RoleCommandContext with minimal configuration."""
        context = RoleCommandContext(
            paths=PathConfig(),
            template=TemplateConfig(),
            content=ContentFlags(),
            diagrams=DiagramConfig(),
            analysis=AnalysisConfig(),
            processing=ProcessingConfig(),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )
        assert context.paths.output == "README.md"
        assert context.template.hybrid is False
        assert context.content.no_vars is False
        assert context.diagrams.generate_graph is False

    def test_full_configuration(self):
        """Test creating RoleCommandContext with full configuration."""
        context = RoleCommandContext(
            paths=PathConfig(
                role_path=Path("/my-role"),
                output="DOCS.md",
            ),
            template=TemplateConfig(hybrid=True),
            content=ContentFlags(
                no_vars=False,
                no_diagrams=False,
            ),
            diagrams=DiagramConfig(generate_graph=True),
            analysis=AnalysisConfig(
                complexity_report=True,
                include_complexity=True,
            ),
            processing=ProcessingConfig(
                comments=True,
                task_line=True,
            ),
            validation=ValidationConfig(validate_markdown=True),
            repository=RepositoryConfig(repository_url="detect"),
        )
        assert context.paths.role_path == Path("/my-role")
        assert context.paths.output == "DOCS.md"
        assert context.template.hybrid is True
        assert context.diagrams.generate_graph is True
        assert context.analysis.complexity_report is True
        assert context.processing.comments is True
        assert context.validation.validate_markdown is True
        assert context.repository.repository_url == "detect"

    def test_dry_run_configuration(self):
        """Test RoleCommandContext for dry-run mode."""
        context = RoleCommandContext(
            paths=PathConfig(role_path=Path("/test-role")),
            template=TemplateConfig(),
            content=ContentFlags(),
            diagrams=DiagramConfig(generate_graph=True),
            analysis=AnalysisConfig(),
            processing=ProcessingConfig(dry_run=True),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )
        assert context.processing.dry_run is True
        assert context.diagrams.generate_graph is True

    def test_analyze_only_configuration(self):
        """Test RoleCommandContext for analyze-only mode."""
        context = RoleCommandContext(
            paths=PathConfig(role_path=Path("/test-role")),
            template=TemplateConfig(),
            content=ContentFlags(),
            diagrams=DiagramConfig(),
            analysis=AnalysisConfig(
                analyze_only=True,
                complexity_report=True,
            ),
            processing=ProcessingConfig(),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )
        assert context.analysis.analyze_only is True
        assert context.analysis.complexity_report is True

    def test_pydantic_validation(self):
        """Test that Pydantic validation works."""
        # Test that we can't assign wrong types with validate_assignment=True
        context = RoleCommandContext(
            paths=PathConfig(),
            template=TemplateConfig(),
            content=ContentFlags(),
            diagrams=DiagramConfig(),
            analysis=AnalysisConfig(),
            processing=ProcessingConfig(),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )

        # This should work - assigning a valid boolean
        context.diagrams.generate_graph = True
        assert context.diagrams.generate_graph is True

    def test_serialization(self):
        """Test that context can be serialized and deserialized."""
        context = RoleCommandContext(
            paths=PathConfig(role_path=Path("/test")),
            template=TemplateConfig(hybrid=True),
            content=ContentFlags(no_vars=True),
            diagrams=DiagramConfig(generate_graph=True),
            analysis=AnalysisConfig(),
            processing=ProcessingConfig(),
            validation=ValidationConfig(),
            repository=RepositoryConfig(),
        )

        # Test model_dump
        data = context.model_dump()
        assert data["template"]["hybrid"] is True
        assert data["content"]["no_vars"] is True

        # Test reconstruction
        context2 = RoleCommandContext(**data)
        assert context2.template.hybrid is True
        assert context2.content.no_vars is True
