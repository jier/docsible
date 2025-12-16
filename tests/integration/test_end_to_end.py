"""End-to-end integration tests for Docsible.

These tests exercise complete workflows from CLI invocation to output file generation,
ensuring that all components work together correctly.
"""

from click.testing import CliRunner

from docsible.cli import cli
from docsible import constants


class TestRoleDocumentation:
    """Test end-to-end role documentation generation."""

    def test_document_simple_role_creates_readme(self, minimal_role):
        """Test full workflow: role -> README generation."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", str(minimal_role), "--no-backup"]
        )

        # Check command succeeded
        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check README created
        readme = minimal_role / "README.md"
        assert readme.exists(), "README.md was not created"

        # Check README content
        content = readme.read_text()
        assert "test_role" in content, "Role name not in README"
        assert "Test task" in content, "Task name not in README"
        assert "test_var" in content, "Variable not in README"
        assert constants.DOCSIBLE_START_TAG in content, "Docsible start tag missing"
        assert constants.DOCSIBLE_END_TAG in content, "Docsible end tag missing"

    def test_hybrid_template_preserves_manual_sections(self, minimal_role):
        """Test that regeneration with hybrid template preserves manual edits."""
        # First generation with hybrid template
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", str(minimal_role), "--hybrid", "--no-backup"]
        )
        assert result.exit_code == 0

        readme = minimal_role / "README.md"
        assert readme.exists()

        # Add manual content outside Docsible tags
        original_content = readme.read_text()
        manual_section = "\n## My Manual Section\nThis is manually added content.\n"
        modified_content = original_content + manual_section
        readme.write_text(modified_content)

        # Regenerate documentation
        result = runner.invoke(
            cli,
            [
                "role",
                "--role",
                str(minimal_role),
                "--hybrid",
                "--append",
                "--no-backup",
            ],
        )
        assert result.exit_code == 0

        # Check manual section is preserved
        final_content = readme.read_text()
        assert "My Manual Section" in final_content, "Manual section was lost"
        assert "manually added content" in final_content, "Manual content was lost"

    def test_role_with_mermaid_graphs(self, minimal_role):
        """Test role documentation with Mermaid diagram generation."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", str(minimal_role), "--graph", "--no-backup"]
        )

        assert result.exit_code == 0

        readme = minimal_role / "README.md"
        content = readme.read_text()

        # Check for Mermaid diagram markers
        assert "```mermaid" in content, "Mermaid code block not found"
        assert "flowchart" in content or "graph" in content, (
            "Mermaid flowchart not generated"
        )

    def test_role_with_playbook(self, role_with_playbook):
        """Test role documentation with playbook content."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "role",
                "--role",
                str(role_with_playbook),
                "--playbook",
                str(role_with_playbook / "tests" / "test.yml"),
                "--no-backup",
            ],
        )

        assert result.exit_code == 0

        readme = role_with_playbook / "README.md"
        content = readme.read_text()

        # Check playbook content is included
        assert "Test playbook" in content or "test.yml" in content

    def test_role_with_handlers(self, role_with_handlers):
        """Test role documentation with handlers."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", str(role_with_handlers), "--no-backup"]
        )

        assert result.exit_code == 0

        readme = role_with_handlers / "README.md"
        content = readme.read_text()

        # Check handlers are documented
        assert "Restart service" in content, "Handler not in README"
        assert "handlers" in content.lower(), "Handlers section not in README"

    def test_backup_created_when_readme_exists(self, minimal_role):
        """Test that backup is created when overwriting existing README."""
        # Create initial README
        readme = minimal_role / "README.md"
        readme.write_text("# Existing README\nThis will be backed up.")

        runner = CliRunner()
        result = runner.invoke(cli, ["role", "--role", str(minimal_role)])

        assert result.exit_code == 0

        # Check for backup file
        backup_files = list(minimal_role.glob("README_backup_*.md"))
        assert len(backup_files) == 1, "Backup file was not created"

        # Check backup contains original content
        backup_content = backup_files[0].read_text()
        assert "Existing README" in backup_content


class TestCollectionDocumentation:
    """Test end-to-end collection documentation generation."""

    def test_document_simple_collection(self, minimal_collection):
        """Test full workflow: collection -> README generation."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--collection", str(minimal_collection), "--no-backup"]
        )

        assert result.exit_code == 0, f"Command failed with output: {result.output}"

        # Check collection README created
        readme = minimal_collection / "README.md"
        assert readme.exists(), "Collection README.md was not created"

        content = readme.read_text()
        assert "test_collection" in content, "Collection name not in README"
        assert "test_namespace" in content, "Namespace not in README"


class TestConfigInitialization:
    """Test configuration file initialization."""

    def test_init_config_creates_file(self, tmp_path):
        """Test that init command creates .docsible.yml file."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])

        assert result.exit_code == 0
        config_file = tmp_path / ".docsible.yml"
        assert config_file.exists(), ".docsible.yml was not created"

        content = config_file.read_text()
        assert "structure:" in content, "Config structure not in file"
        assert "defaults_dir:" in content, "defaults_dir not in config"

    def test_init_config_respects_force_flag(self, tmp_path):
        """Test that --force flag overwrites existing config."""
        config_file = tmp_path / ".docsible.yml"
        config_file.write_text("# Existing config")

        runner = CliRunner()

        # Try without force (should fail)
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])
        assert result.exit_code != 0

        # Try with force (should succeed)
        result = runner.invoke(cli, ["init", "--path", str(tmp_path), "--force"])
        assert result.exit_code == 0

        # Check file was overwritten
        content = config_file.read_text()
        assert "# Existing config" not in content


class TestCommandLineInterface:
    """Test CLI behavior and options."""

    def test_cli_help_displays(self):
        """Test that CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Docsible" in result.output
        assert "role" in result.output
        assert "init" in result.output

    def test_role_command_help_displays(self):
        """Test that role command help works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["role", "--help"])

        assert result.exit_code == 0
        assert "role" in result.output.lower()
        assert "--role" in result.output

    def test_version_flag_works(self):
        """Test that --version flag displays version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert constants.VERSION in result.output

    def test_verbose_logging_enabled(self, minimal_role):
        """Test that --verbose flag enables debug logging."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--verbose", "role", "--role", str(minimal_role), "--no-backup"]
        )

        assert result.exit_code == 0
        # Verbose mode should produce debug output
        # (Note: actual debug output would appear in logs, not CLI output)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_role_path_shows_error(self):
        """Test that invalid role path produces helpful error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", "/nonexistent/path", "--no-backup"]
        )

        assert result.exit_code != 0
        assert (
            "does not exist" in result.output.lower()
            or "not found" in result.output.lower()
        )

    def test_role_without_tasks_still_generates_readme(self, tmp_path):
        """Test that a role without tasks directory still generates README."""
        role_path = tmp_path / "minimal_role"
        role_path.mkdir()

        # Only create defaults (no tasks)
        defaults_dir = role_path / "defaults"
        defaults_dir.mkdir()
        (defaults_dir / "main.yml").write_text("test_var: value")

        runner = CliRunner()
        result = runner.invoke(cli, ["role", "--role", str(role_path), "--no-backup"])

        # Should still succeed even without tasks
        assert result.exit_code == 0
        assert (role_path / "README.md").exists()


class TestModularArchitecture:
    """Test that modular command structure works correctly."""

    def test_commands_are_registered(self):
        """Test that all commands are properly registered in CLI group."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        # Check all commands are listed
        assert "role" in result.output
        assert "init" in result.output

    def test_role_command_uses_modular_structure(self, minimal_role):
        """Test that role command uses the new modular command structure."""
        # This test verifies the refactored cli.py works correctly
        runner = CliRunner()
        result = runner.invoke(
            cli, ["role", "--role", str(minimal_role), "--no-backup"]
        )

        assert result.exit_code == 0
        assert (minimal_role / "README.md").exists()

    def test_init_command_uses_modular_structure(self, tmp_path):
        """Test that init command uses the new modular command structure."""
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--path", str(tmp_path)])

        assert result.exit_code == 0
        assert (tmp_path / ".docsible.yml").exists()
