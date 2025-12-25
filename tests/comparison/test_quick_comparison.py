"""Quick comparison tests for validating implementation equivalence.

These tests provide a focused set of comparisons to validate that both
implementations produce identical outputs.
"""

import os
import re
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


def normalize_readme_for_comparison(content: str) -> str:
    """Normalize README content by removing timestamp and role name variations.

    This allows comparing READMEs that were generated at different times
    and in different directories by replacing variable elements with fixed placeholders.

    Args:
        content: README content with embedded metadata

    Returns:
        README content with normalized timestamp and role names
    """
    # Replace the timestamp in the DOCSIBLE METADATA comment
    # Pattern matches: 2025-12-25T17:30:45.123456Z or 2025-12-25T17:30:45.123456+00:00Z
    # Replace with: generated_at: TIMESTAMP_NORMALIZED
    timestamp_pattern = r"(generated_at: )\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+\d{2}:\d{2}Z?)"
    normalized = re.sub(timestamp_pattern, r"\1TIMESTAMP_NORMALIZED", content)

    # Normalize role names in headers and mermaid diagrams
    # This handles cases where the role path differs (orig vs orch, orig_graph vs orch_graph)
    # Replace "## orig" or "## orch" with "## ROLE_NAME"
    normalized = re.sub(r"^## (orig|orch)(_graph)?$", r"## ROLE_NAME", normalized, flags=re.MULTILINE)

    # Replace role names in mermaid diagrams
    # participant orig_graph -> participant ROLE_NAME
    normalized = re.sub(r"participant (orig|orch)(_graph)?(\s)", r"participant ROLE_NAME\3", normalized)

    # Replace role names in mermaid diagram interactions
    # Playbook->>+orig_graph -> Playbook->>+ROLE_NAME
    # Tasks_main_yml-->>-orig_graph -> Tasks_main_yml-->>-ROLE_NAME
    normalized = re.sub(r"(Playbook->>[\+\-]?)(orig|orch)(_graph)?(\b)", r"\1ROLE_NAME\4", normalized)
    normalized = re.sub(r"(--?>>[\+\-]?)(orig|orch)(_graph)?(\b)", r"\1ROLE_NAME\4", normalized)
    normalized = re.sub(r"(\b)(orig|orch)(_graph)?(--?>>)", r"ROLE_NAME\4", normalized)

    # Replace in activate/deactivate statements
    normalized = re.sub(r"(activate |deactivate )(orig|orch)(_graph)?(\s|$)", r"\1ROLE_NAME\4", normalized)

    # Replace in Note over statements
    normalized = re.sub(r"(Note over )(orig|orch)(_graph)?(,)", r"\1ROLE_NAME\4", normalized)

    return normalized


def normalize_dry_run_output(output: str) -> str:
    """Normalize dry-run output by removing timestamps from backup filenames.

    Dry-run output includes backup filenames with timestamps that will differ
    between runs. This function replaces those timestamps with a placeholder.

    Args:
        output: CLI dry-run output

    Returns:
        Output with normalized backup filename timestamps
    """
    # Replace backup filename timestamps: README_backup_20251225_180909.md
    # With: README_backup_TIMESTAMP.md
    backup_pattern = r"(README_backup_)\d{8}_\d{6}(\.md)"
    normalized = re.sub(backup_pattern, r"\1TIMESTAMP\2", output)
    return normalized


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
        # Normalize dry-run output to remove timestamp differences in backup filenames
        assert normalize_dry_run_output(orig.output) == normalize_dry_run_output(orch.output)

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

        # Compare README content (normalize timestamps for comparison)
        orig_readme = normalize_readme_for_comparison((orig_role / "README.md").read_text())
        orch_readme = normalize_readme_for_comparison((orch_role / "README.md").read_text())

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

        # Compare README content (normalize timestamps for comparison)
        orig_readme = normalize_readme_for_comparison((orig_role / "README.md").read_text())
        orch_readme = normalize_readme_for_comparison((orch_role / "README.md").read_text())

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
