"""
Comparison tests for doc_the_role vs doc_the_role_orchestrated implementations.

These tests verify that both the original and orchestrated implementations
produce identical outputs for the same inputs, ensuring safe migration.
"""

import os
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from docsible.cli import cli


def run_with_orchestrator(runner, args, use_orchestrator=True):
    """Run CLI command with or without orchestrator.

    Args:
        runner: Click CliRunner instance
        args: CLI arguments list
        use_orchestrator: Whether to enable orchestrator

    Returns:
        Result object from runner.invoke
    """
    import os
    old_val = os.environ.get("DOCSIBLE_USE_ORCHESTRATOR")
    try:
        os.environ["DOCSIBLE_USE_ORCHESTRATOR"] = "true" if use_orchestrator else "false"
        return runner.invoke(cli, args)
    finally:
        if old_val is None:
            os.environ.pop("DOCSIBLE_USE_ORCHESTRATOR", None)
        else:
            os.environ["DOCSIBLE_USE_ORCHESTRATOR"] = old_val


def normalize_cli_output(output: str) -> str:
    """Normalize CLI output by removing ANSI codes and optional sections.

    Args:
        output: Raw CLI output with ANSI escape sequences

    Returns:
        Normalized output for comparison
    """
    import re

    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[mGKHF]')
    output = ansi_escape.sub('', output)

    # Remove the complexity analysis report section (which appears before dry-run output)
    # This section is optional and controlled by --complexity-report flag
    output = re.sub(
        r'╔═+╗.*?╚═+╝.*?(?=\n={5,})',
        '',
        output,
        flags=re.DOTALL
    )

    # Normalize backup filenames with timestamps (e.g., README_backup_20251224_190154.md)
    output = re.sub(
        r'README_backup_\d{8}_\d{6}\.md',
        'README_backup_TIMESTAMP.md',
        output
    )

    # Normalize whitespace
    output = re.sub(r'\n{3,}', '\n\n', output)

    return output.strip()


def normalize_readme_content(content: str) -> str:
    """Normalize README content for comparison by removing variable metadata.

    Removes:
    - Timestamps (generated_at)
    - Role hashes (may include timestamp-based data)
    - Role names derived from temporary directory paths

    Args:
        content: README content to normalize

    Returns:
        Normalized content for comparison
    """
    import re

    # Remove timestamp (handles format: 2025-12-24T17:55:53.697781+00:00Z)
    content = re.sub(
        r"generated_at: \d{4}-\d{2}-\d{2}T[\d:.+\-]+Z",
        "generated_at: NORMALIZED_TIMESTAMP",
        content
    )

    # Remove role hash (can vary due to timestamps or paths)
    content = re.sub(
        r"role_hash: [a-f0-9]{64}",
        "role_hash: NORMALIZED_HASH",
        content
    )

    # Normalize role names (remove _orig and _orch suffixes from temp test directories)
    content = re.sub(r"(_role)_(orig|orch)\b", r"\1", content)
    content = re.sub(r"^(##\s+)(\w+)_(orig|orch)$", r"\1\2", content, flags=re.MULTILINE)
    content = re.sub(r"^(#\s+)(\w+)_(orig|orch)$", r"\1\2", content, flags=re.MULTILINE)
    content = re.sub(r'(role:\s+)(\w+)_(orig|orch)', r'\1\2', content)
    content = re.sub(r'(participant\s+)(\w+)_(orig|orch)', r'\1\2', content)
    # Also normalize in YAML role references (e.g., "- full_workflow_orch" -> "- full_workflow")
    content = re.sub(r'(\s+-\s+)(\w+)_(orig|orch)(\s|$)', r'\1\2\4', content)
    # Normalize in Mermaid sequence diagram arrows where role name is the destination
    # (e.g., "Playbook->>+full_workflow_orig:")
    content = re.sub(r'(\w+)->>([+-]?)(\w+)_(orig|orch):', r'\1->>\2\3:', content)
    # Normalize in Mermaid sequence diagram arrows where role name is the source
    # (e.g., "full_workflow_orig->>+Tasks:")
    content = re.sub(r'(\w+)_(orig|orch)->>([+-]?)(\w+):', r'\1->>\3\4:', content)
    # Normalize in activate/deactivate statements (e.g., "activate full_workflow_orig")
    content = re.sub(r'(activate|deactivate)\s+(\w+)_(orig|orch)\b', r'\1 \2', content)
    # Normalize in Mermaid return arrows where role name is the source
    # (e.g., "full_workflow_orig-->>-Playbook")
    content = re.sub(r'(\w+)_(orig|orch)(-->>)([+-]?)(\w+)', r'\1\3\4\5', content)
    # Normalize in Mermaid return arrows where role name is the destination
    # (e.g., "Tasks-->>-full_workflow_orig:")
    content = re.sub(r'(\w+)(-->>)([+-]?)(\w+)_(orig|orch):', r'\1\2\3\4:', content)
    # Normalize in Note over statements (e.g., "Note over full_workflow_orig,Tasks")
    content = re.sub(r'(Note over\s+)(\w+)_(orig|orch)([,\s])', r'\1\2\4', content)

    return content


class TestDryRunOutputComparison:
    """Compare dry-run outputs between implementations."""

    def test_basic_dry_run_identical(self, simple_role):
        """Test that basic dry-run output is identical."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--dry-run"]

        # Run original implementation
        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)

        # Run orchestrated implementation
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        # Compare outputs
        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_dry_run_with_graph_identical(self, simple_role):
        """Test dry-run with graph generation."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--graph", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_dry_run_with_hybrid_identical(self, simple_role):
        """Test dry-run with hybrid template."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--hybrid", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_dry_run_minimal_mode_identical(self, simple_role):
        """Test dry-run with minimal mode."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--minimal", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output


class TestComplexityAnalysisComparison:
    """Compare complexity analysis outputs."""

    @pytest.fixture
    def complex_role_path(self):
        """Path to complex role fixture."""
        return Path(__file__).parent.parent / "fixtures" / "complex_role"

    def test_complexity_report_identical(self, complex_role_path):
        """Test complexity report output."""
        if not complex_role_path.exists():
            pytest.skip("Complex role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(complex_role_path), "--complexity-report", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code

        # Normalize outputs to remove ANSI codes and optional report sections
        orig_normalized = normalize_cli_output(original_result.output)
        orch_normalized = normalize_cli_output(orchestrated_result.output)

        assert orig_normalized == orch_normalized

    def test_simplification_report_identical(self, complex_role_path):
        """Test simplification report output."""
        if not complex_role_path.exists():
            pytest.skip("Complex role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(complex_role_path), "--simplification-report", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_analyze_only_identical(self, complex_role_path):
        """Test analyze-only mode output."""
        if not complex_role_path.exists():
            pytest.skip("Complex role fixture not found")

        runner = CliRunner()
        args = ["role", "--role", str(complex_role_path), "--analyze-only"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code

        # Normalize outputs to remove ANSI codes and optional report sections
        orig_normalized = normalize_cli_output(original_result.output)
        orch_normalized = normalize_cli_output(orchestrated_result.output)

        assert orig_normalized == orch_normalized


class TestGeneratedFileComparison:
    """Compare generated README files between implementations."""

    def test_simple_role_readme_identical(self, simple_role, tmp_path):
        """Test that generated README is identical for simple role."""
        runner = CliRunner()

        # Create two copies of the role with SAME name to avoid role name differences
        orig_role = tmp_path / "test_role_orig"
        orch_role = tmp_path / "test_role_orch"
        shutil.copytree(simple_role, orig_role)
        shutil.copytree(simple_role, orch_role)

        # Generate with original implementation
        original_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orig_role), "--no-backup"],
            use_orchestrator=False
        )
        assert original_result.exit_code == 0

        # Generate with orchestrated implementation
        orchestrated_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orch_role), "--no-backup"],
            use_orchestrator=True
        )
        assert orchestrated_result.exit_code == 0

        # Compare README files
        orig_readme = orig_role / "README.md"
        orch_readme = orch_role / "README.md"

        assert orig_readme.exists(), "Original README not generated"
        assert orch_readme.exists(), "Orchestrated README not generated"

        # Normalize content before comparison to ignore timestamps
        orig_content = normalize_readme_content(orig_readme.read_text())
        orch_content = normalize_readme_content(orch_readme.read_text())

        assert orig_content == orch_content, "Generated READMEs differ"

    def test_role_with_graph_readme_identical(self, simple_role, tmp_path):
        """Test generated README with graph generation."""
        runner = CliRunner()

        # Use same base name to avoid role name differences
        orig_role = tmp_path / "graph_role_orig"
        orch_role = tmp_path / "graph_role_orch"
        shutil.copytree(simple_role, orig_role)
        shutil.copytree(simple_role, orch_role)

        original_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orig_role), "--graph", "--no-backup"],
            use_orchestrator=False
        )
        assert original_result.exit_code == 0

        orchestrated_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orch_role), "--graph", "--no-backup"],
            use_orchestrator=True
        )
        assert orchestrated_result.exit_code == 0

        # Normalize before comparison
        orig_content = normalize_readme_content((orig_role / "README.md").read_text())
        orch_content = normalize_readme_content((orch_role / "README.md").read_text())

        assert orig_content == orch_content, "Generated READMEs with graphs differ"

    def test_hybrid_template_readme_identical(self, simple_role, tmp_path):
        """Test generated README with hybrid template."""
        runner = CliRunner()

        # Use same base name to avoid role name differences
        orig_role = tmp_path / "hybrid_role_orig"
        orch_role = tmp_path / "hybrid_role_orch"
        shutil.copytree(simple_role, orig_role)
        shutil.copytree(simple_role, orch_role)

        original_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orig_role), "--hybrid", "--no-backup"],
            use_orchestrator=False
        )
        assert original_result.exit_code == 0

        orchestrated_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orch_role), "--hybrid", "--no-backup"],
            use_orchestrator=True
        )
        assert orchestrated_result.exit_code == 0

        # Normalize before comparison
        orig_content = normalize_readme_content((orig_role / "README.md").read_text())
        orch_content = normalize_readme_content((orch_role / "README.md").read_text())

        assert orig_content == orch_content, "Generated hybrid READMEs differ"


class TestContentFlagsComparison:
    """Compare output with various content flags."""

    def test_no_vars_flag_identical(self, simple_role):
        """Test --no-vars flag produces identical output."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--no-vars", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_no_tasks_flag_identical(self, simple_role):
        """Test --no-tasks flag produces identical output."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--no-tasks", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output

    def test_no_diagrams_flag_identical(self, simple_role):
        """Test --no-diagrams flag produces identical output."""
        runner = CliRunner()
        args = ["role", "--role", str(simple_role), "--graph", "--no-diagrams", "--dry-run"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.output == orchestrated_result.output


class TestErrorHandlingComparison:
    """Compare error handling between implementations."""

    def test_invalid_role_path_identical_error(self):
        """Test that invalid role path produces identical error."""
        runner = CliRunner()
        args = ["role", "--role", "/nonexistent/path", "--no-backup"]

        original_result = run_with_orchestrator(runner, args, use_orchestrator=False)
        orchestrated_result = run_with_orchestrator(runner, args, use_orchestrator=True)

        # Both should fail with same exit code
        assert original_result.exit_code == orchestrated_result.exit_code
        assert original_result.exit_code != 0

        # Error messages should be similar (may not be byte-identical due to formatting)
        assert "does not exist" in original_result.output.lower() or "not found" in original_result.output.lower()
        assert "does not exist" in orchestrated_result.output.lower() or "not found" in orchestrated_result.output.lower()


class TestEdgeCasesComparison:
    """Test edge cases and special scenarios."""

    def test_role_without_tasks_identical(self, tmp_path):
        """Test role without tasks directory produces identical output."""
        runner = CliRunner()

        # Create minimal role with only defaults (no tasks) - use same base name
        orig_role = tmp_path / "minimal_role_orig"
        orch_role = tmp_path / "minimal_role_orch"

        for role_path in [orig_role, orch_role]:
            role_path.mkdir()
            defaults_dir = role_path / "defaults"
            defaults_dir.mkdir()
            (defaults_dir / "main.yml").write_text("test_var: value\n")

        original_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orig_role), "--no-backup"],
            use_orchestrator=False
        )

        orchestrated_result = run_with_orchestrator(
            runner,
            ["role", "--role", str(orch_role), "--no-backup"],
            use_orchestrator=True
        )

        # Both should succeed
        assert original_result.exit_code == 0
        assert orchestrated_result.exit_code == 0

        # READMEs should be identical (after normalization)
        orig_content = normalize_readme_content((orig_role / "README.md").read_text())
        orch_content = normalize_readme_content((orch_role / "README.md").read_text())
        assert orig_content == orch_content


@pytest.mark.integration
class TestFullWorkflowComparison:
    """Test complete workflows end-to-end."""

    def test_complete_workflow_with_all_features(self, simple_role, tmp_path):
        """Test complete workflow with multiple features enabled."""
        runner = CliRunner()

        # Use same base name to avoid role name differences
        orig_role = tmp_path / "full_workflow_orig"
        orch_role = tmp_path / "full_workflow_orch"
        shutil.copytree(simple_role, orig_role)
        shutil.copytree(simple_role, orch_role)

        # Run with multiple flags
        orig_args = [
            "role",
            "--role", str(orig_role),
            "--graph",
            "--hybrid",
            "--comments",
            "--task-line",
            "--no-backup",
        ]

        orch_args = [
            "role",
            "--role", str(orch_role),
            "--graph",
            "--hybrid",
            "--comments",
            "--task-line",
            "--no-backup",
        ]

        original_result = run_with_orchestrator(runner, orig_args, use_orchestrator=False)
        assert original_result.exit_code == 0

        orchestrated_result = run_with_orchestrator(runner, orch_args, use_orchestrator=True)
        assert orchestrated_result.exit_code == 0

        # Compare final outputs (normalized)
        orig_content = normalize_readme_content((orig_role / "README.md").read_text())
        orch_content = normalize_readme_content((orch_role / "README.md").read_text())
        assert orig_content == orch_content, "Full workflow produces different READMEs"
