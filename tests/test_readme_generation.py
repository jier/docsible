"""
Test cases for README generation with various playbook scenarios.
"""

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from docsible.cli import doc_the_role


class TestSimpleRoleGeneration:
    """Test README generation for simple role."""

    @pytest.fixture
    def simple_role_path(self):
        """Path to simple role fixture."""
        return Path(__file__).parent / "fixtures" / "simple_role"

    def test_simple_role_generates_readme(self, simple_role_path, tmp_path):
        """Test that simple role generates README correctly."""
        # Copy fixture to temp directory
        role_path = tmp_path / "simple_role"
        shutil.copytree(simple_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role, ["--role", str(role_path), "--graph", "--no-backup"]
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "simple_role" in content
        assert "Ensure directory exists" in content
        assert "Install package" in content

    def test_simple_role_with_hybrid_template(self, simple_role_path, tmp_path):
        """Test simple role with hybrid template."""
        role_path = tmp_path / "simple_role"
        shutil.copytree(simple_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            ["--role", str(role_path), "--hybrid", "--graph", "--no-backup"],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        assert "## Architecture Overview" in content
        assert "## Task Execution Flow" in content
        assert "MANUALLY MAINTAINED" in content

    def test_simple_role_no_vars_flag(self, simple_role_path, tmp_path):
        """Test simple role with --no-vars flag."""
        role_path = tmp_path / "simple_role"
        shutil.copytree(simple_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            ["--role", str(role_path), "--hybrid", "--no-vars", "--no-backup"],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        # Should not contain variable sections when --no-vars is used
        assert "## Role Variables" not in content
        # Task details and examples should still be present (use --no-tasks to hide)
        # Note: These sections are in the hybrid template by default


class TestComplexRoleGeneration:
    """Test README generation for complex role with state support."""

    @pytest.fixture
    def complex_role_path(self):
        """Path to complex role fixture."""
        return Path(__file__).parent / "fixtures" / "complex_role"

    def test_complex_role_generates_readme(self, complex_role_path, tmp_path):
        """Test that complex role generates README correctly."""
        role_path = tmp_path / "complex_role"
        shutil.copytree(complex_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            ["--role", str(role_path), "--graph", "--comments", "--no-backup"],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "complex_role" in content
        assert "Include prerequisites" in content
        assert "Install application" in content

    def test_complex_role_state_detection(self, complex_role_path, tmp_path):
        """Test that state support is detected in complex role."""
        role_path = tmp_path / "complex_role"
        shutil.copytree(complex_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            ["--role", str(role_path), "--hybrid", "--graph", "--no-backup"],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        # Should detect state support in simplified sequence diagram
        assert "When: **state" in content or "state present" in content

    def test_complex_role_dependencies(self, complex_role_path, tmp_path):
        """Test that role dependencies are extracted correctly."""
        role_path = tmp_path / "complex_role"
        shutil.copytree(complex_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role, ["--role", str(role_path), "--hybrid", "--no-backup"]
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        # Should show dependencies from meta/main.yml
        assert "common" in content
        assert "hashi_vault" in content

        # Should show playbook dependencies
        assert "Playbook Role Dependencies" in content or "Dependencies" in content


class TestPlaybookSequenceDiagram:
    """Test playbook sequence diagram generation."""

    @pytest.fixture
    def complex_role_path(self):
        """Path to complex role with playbook."""
        return Path(__file__).parent / "fixtures" / "complex_role"

    def test_playbook_high_level_diagram(self, complex_role_path, tmp_path):
        """Test that playbook generates high-level sequence diagram."""
        role_path = tmp_path / "complex_role"
        shutil.copytree(complex_role_path, role_path)

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            [
                "--role",
                str(role_path),
                "--playbook",
                str(role_path / "tests" / "test.yml"),
                "--hybrid",
                "--graph",
                "--no-backup",
            ],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        # Should show Architecture Overview
        assert "Architecture Overview" in content or "Execution Sequence" in content

        # Should show include_role calls
        assert "include_role" in content or "hashi_vault" in content

        # Should show task names
        assert "Update apt cache" in content or "Verify installation" in content


class TestMultiRoleProject:
    """Test multi-role project README generation."""

    @pytest.fixture
    def multi_role_path(self):
        """Path to multi-role project fixture."""
        return Path(__file__).parent / "fixtures" / "multi_role_project"

    def test_webserver_role_generation(self, multi_role_path, tmp_path):
        """Test README generation for webserver role in multi-role project."""
        project_path = tmp_path / "multi_role_project"
        shutil.copytree(multi_role_path, project_path)

        role_path = project_path / "roles" / "webserver"

        runner = CliRunner()
        result = runner.invoke(doc_the_role, ["--role", str(role_path), "--no-backup"])

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        assert readme_path.exists()

        content = readme_path.read_text()
        assert "webserver" in content
        assert "Install Apache" in content

    def test_site_playbook_dependencies(self, multi_role_path, tmp_path):
        """Test that site.yml playbook shows all role dependencies."""
        project_path = tmp_path / "multi_role_project"
        shutil.copytree(multi_role_path, project_path)

        role_path = project_path / "roles" / "webserver"

        runner = CliRunner()
        result = runner.invoke(
            doc_the_role,
            [
                "--role",
                str(role_path),
                "--playbook",
                str(project_path / "site.yml"),
                "--hybrid",
                "--graph",
                "--no-backup",
            ],
        )

        assert result.exit_code == 0
        readme_path = role_path / "README.md"
        content = readme_path.read_text()

        # Should show playbook dependencies
        assert "database" in content or "monitoring" in content or "security" in content
