"""Quick comparison tests for validating implementation equivalence.

These tests provide a focused set of comparisons to validate that both
implementations produce identical outputs.
"""

import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from docsible.cli import cli


def run_with_env(runner, args, orchestrator_enabled):
    """Helper to run CLI with specific orchestrator setting."""
    old_val = os.environ.get("DOCSIBLE_USE_ORCHESTRATOR")
    try:
        os.environ["DOCSIBLE_USE_ORCHESTRATOR"] = "true" if orchestrator_enabled else "false"
        return runner.invoke(cli, args)
    finally:
        if old_val is None:
            os.environ.pop("DOCSIBLE_USE_ORCHESTRATOR", None)
        else:
            os.environ["DOCSIBLE_USE_ORCHESTRATOR"] = old_val


class TestBasicDryRunComparison:
    """Test basic dry-run output comparison."""

    def test_simple_role_dry_run(self, simple_role):
        """Test simple role dry-run produces identical output."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code, f"Exit codes differ: {orig.exit_code} vs {orch.exit_code}"
        assert orig.output == orch.output, "Dry-run outputs differ"

    def test_dry_run_with_graph(self, simple_role):
        """Test dry-run with graph flag."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--graph", "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code
        assert orig.output == orch.output

    def test_dry_run_hybrid_mode(self, simple_role):
        """Test dry-run with hybrid template."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--hybrid", "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code
        assert orig.output == orch.output

    def test_minimal_mode(self, simple_role):
        """Test minimal mode."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--minimal", "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code
        assert orig.output == orch.output


class TestGeneratedFileComparison:
    """Test that generated README files are identical."""

    def test_basic_readme_generation(self, minimal_role, tmp_path):
        """Test basic README generation produces identical files."""
        runner = CliRunner()

        # Create two copies of the role
        orig_role = tmp_path / "orig"
        orch_role = tmp_path / "orch"
        shutil.copytree(minimal_role, orig_role)
        shutil.copytree(minimal_role, orch_role)

        # Generate with both implementations
        orig_result = run_with_env(
            runner,
            ["role", "--role", str(orig_role), "--no-backup"],
            orchestrator_enabled=False
        )
        orch_result = run_with_env(
            runner,
            ["role", "--role", str(orch_role), "--no-backup"],
            orchestrator_enabled=True
        )

        # Both should succeed
        assert orig_result.exit_code == 0, f"Original failed: {orig_result.output}"
        assert orch_result.exit_code == 0, f"Orchestrated failed: {orch_result.output}"

        # Compare README content
        orig_readme = (orig_role / "README.md").read_text()
        orch_readme = (orch_role / "README.md").read_text()

        assert orig_readme == orch_readme, "Generated READMEs differ"

    def test_readme_with_graph(self, minimal_role, tmp_path):
        """Test README generation with graphs."""
        runner = CliRunner()

        orig_role = tmp_path / "orig_graph"
        orch_role = tmp_path / "orch_graph"
        shutil.copytree(minimal_role, orig_role)
        shutil.copytree(minimal_role, orch_role)

        orig_result = run_with_env(
            runner,
            ["role", "--role", str(orig_role), "--graph", "--no-backup"],
            orchestrator_enabled=False
        )
        orch_result = run_with_env(
            runner,
            ["role", "--role", str(orch_role), "--graph", "--no-backup"],
            orchestrator_enabled=True
        )

        assert orig_result.exit_code == 0
        assert orch_result.exit_code == 0

        orig_readme = (orig_role / "README.md").read_text()
        orch_readme = (orch_role / "README.md").read_text()

        assert orig_readme == orch_readme, "Generated READMEs with graphs differ"


class TestContentFlags:
    """Test content flag handling."""

    def test_no_vars_flag(self, simple_role):
        """Test --no-vars flag."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--no-vars", "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code
        assert orig.output == orch.output

    def test_no_tasks_flag(self, simple_role):
        """Test --no-tasks flag."""
        if not simple_role.exists():
            pytest.skip("Simple role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--no-tasks", "--dry-run"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        assert orig.exit_code == orch.exit_code
        assert orig.output == orch.output


class TestErrorHandling:
    """Test error handling is consistent."""

    def test_nonexistent_role_path(self):
        """Test that both implementations handle invalid paths identically."""
        runner = CliRunner()
        args = ["role", "--role", "/nonexistent/path/to/role", "--no-backup"]

        orig = run_with_env(runner, args, orchestrator_enabled=False)
        orch = run_with_env(runner, args, orchestrator_enabled=True)

        # Both should fail with same exit code
        assert orig.exit_code != 0, "Original should fail for invalid path"
        assert orch.exit_code != 0, "Orchestrated should fail for invalid path"
        assert orig.exit_code == orch.exit_code, "Exit codes should match"
