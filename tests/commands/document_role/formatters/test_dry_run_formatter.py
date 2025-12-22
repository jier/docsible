"""Tests for DryRunFormatter class."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from docsible.commands.document_role.formatters.dry_run_formatter import DryRunFormatter


class TestDryRunFormatter:
    """Test DryRunFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create DryRunFormatter instance."""
        return DryRunFormatter(width=70)

    @pytest.fixture
    def mock_analysis_report(self):
        """Create mock analysis report."""
        report = Mock()
        report.category.value = "simple"
        report.metrics.total_tasks = 10
        report.metrics.task_files = 2
        report.integration_points = []
        return report

    @pytest.fixture
    def minimal_role_info(self):
        """Create minimal role info."""
        return {
            "name": "test_role",
            "defaults": [],
            "vars": [],
            "handlers": [],
            "tasks": [],
        }

    @pytest.fixture
    def role_info_with_vars(self):
        """Create role info with variables."""
        return {
            "name": "test_role",
            "defaults": [
                {
                    "file": "main.yml",
                    "data": {
                        "var1": {"value": "value1"},
                        "var2": {"value": "value2"},
                    },
                }
            ],
            "vars": [
                {
                    "file": "main.yml",
                    "data": {
                        "var3": {"value": "value3"},
                    },
                }
            ],
            "handlers": [
                {"name": "Restart service", "module": "service"},
            ],
            "tasks": [],
        }

    @pytest.fixture
    def temp_role_dir(self):
        """Create temporary role directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            role_path = Path(tmpdir) / "test_role"
            role_path.mkdir()
            yield role_path

    def test_formatter_initialization(self):
        """Test DryRunFormatter initialization."""
        formatter = DryRunFormatter(width=80)
        assert formatter.width == 80

    def test_formatter_default_width(self):
        """Test DryRunFormatter default width."""
        formatter = DryRunFormatter()
        assert formatter.width == 70

    def test_format_header(self, formatter):
        """Test header formatting."""
        header = formatter._format_header()
        assert "DRY RUN MODE" in header
        assert "=" * 70 in header
        assert "🔍" in header

    def test_format_role_info(self, formatter, minimal_role_info, temp_role_dir):
        """Test role info formatting."""
        output = formatter._format_role_info(minimal_role_info, temp_role_dir)
        assert "Analysis Complete" in output
        assert "test_role" in output
        assert str(temp_role_dir) in output

    def test_format_complexity_minimal(self, formatter, mock_analysis_report, minimal_role_info):
        """Test complexity formatting with minimal role."""
        output = formatter._format_complexity(mock_analysis_report, minimal_role_info)
        assert "Complexity Analysis" in output
        assert "SIMPLE" in output
        assert "Total Tasks: 10" in output
        assert "Task Files: 2" in output
        assert "Variables: 0" in output

    def test_format_complexity_with_vars(self, formatter, mock_analysis_report, role_info_with_vars):
        """Test complexity formatting with variables."""
        output = formatter._format_complexity(mock_analysis_report, role_info_with_vars)
        assert "Variables: 3 (2 defaults, 1 vars)" in output

    def test_format_complexity_with_handlers(
        self, formatter, mock_analysis_report, role_info_with_vars
    ):
        """Test complexity formatting with handlers."""
        output = formatter._format_complexity(mock_analysis_report, role_info_with_vars)
        assert "Handlers: 1" in output

    def test_format_diagrams_none_generated(self, formatter, mock_analysis_report):
        """Test diagrams formatting when none generated."""
        diagrams = {"generate_graph": False}
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "Would Generate" in output
        assert "No diagrams or matrices" in output

    def test_format_diagrams_with_flowcharts(self, formatter, mock_analysis_report):
        """Test diagrams formatting with task flowcharts."""
        diagrams = {
            "generate_graph": True,
            "mermaid_code_per_file": {"main.yml": "graph TD", "setup.yml": "graph TD"},
        }
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "Task flowcharts (2 files)" in output

    def test_format_diagrams_with_sequence(self, formatter, mock_analysis_report):
        """Test diagrams formatting with sequence diagrams."""
        diagrams = {
            "generate_graph": True,
            "sequence_diagram_high_level": "sequenceDiagram",
            "sequence_diagram_detailed": "sequenceDiagram",
        }
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "Sequence diagram (high-level)" in output
        assert "Sequence diagram (detailed)" in output

    def test_format_diagrams_with_state(self, formatter, mock_analysis_report):
        """Test diagrams formatting with state diagram."""
        diagrams = {
            "generate_graph": True,
            "state_diagram": "stateDiagram",
        }
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "State transition diagram" in output

    def test_format_diagrams_with_integration(self, formatter, mock_analysis_report):
        """Test diagrams formatting with integration boundary diagram."""
        mock_analysis_report.integration_points = ["API", "Database", "Redis"]
        diagrams = {
            "generate_graph": True,
            "integration_boundary_diagram": "graph LR",
        }
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "Integration boundary diagram (3 external systems)" in output

    def test_format_diagrams_with_architecture(self, formatter, mock_analysis_report):
        """Test diagrams formatting with architecture diagram."""
        diagrams = {
            "generate_graph": True,
            "architecture_diagram": "graph TB",
        }
        output = formatter._format_diagrams(diagrams, None, mock_analysis_report)
        assert "Component architecture diagram" in output

    def test_format_diagrams_with_dependency_matrix(self, formatter, mock_analysis_report):
        """Test diagrams formatting with dependency matrix."""
        diagrams = {"generate_graph": False}
        dependency_matrix = "| Role | Dependencies |\n|------|--------------|"
        output = formatter._format_diagrams(diagrams, dependency_matrix, mock_analysis_report)
        assert "Dependency matrix" in output

    def test_format_files_new_readme(self, formatter, temp_role_dir):
        """Test files formatting for new README."""
        flags = {"no_backup": False, "no_docsible": False}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert "Files That Would Be Created/Modified" in output
        assert "README.md (new file)" in output

    def test_format_files_existing_readme(self, formatter, temp_role_dir):
        """Test files formatting for existing README."""
        readme_path = temp_role_dir / "README.md"
        readme_path.write_text("# Existing content")

        flags = {"no_backup": False, "no_docsible": False}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert "existing file would be updated" in output
        assert "backup" in output

    def test_format_files_no_backup_flag(self, formatter, temp_role_dir):
        """Test files formatting with no-backup flag."""
        readme_path = temp_role_dir / "README.md"
        readme_path.write_text("# Existing content")

        flags = {"no_backup": True, "no_docsible": False}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert "backup" not in output

    def test_format_files_with_docsible(self, formatter, temp_role_dir):
        """Test files formatting with .docsible file."""
        flags = {"no_backup": False, "no_docsible": False}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert ".docsible" in output
        assert "metadata file - new" in output

    def test_format_files_existing_docsible(self, formatter, temp_role_dir):
        """Test files formatting with existing .docsible."""
        docsible_path = temp_role_dir / ".docsible"
        docsible_path.write_text("---\nkey: value")

        flags = {"no_backup": False, "no_docsible": False}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert ".docsible" in output
        assert "would be updated" in output

    def test_format_files_no_docsible_flag(self, formatter, temp_role_dir):
        """Test files formatting with no-docsible flag."""
        flags = {"no_backup": False, "no_docsible": True}
        output = formatter._format_files(temp_role_dir, "README.md", flags)
        assert ".docsible" not in output

    def test_format_flags_all_disabled(self, formatter):
        """Test flags formatting with all disabled."""
        flags = {
            "generate_graph": False,
            "hybrid": False,
            "no_backup": False,
            "minimal": False,
        }
        output = formatter._format_flags(flags)
        assert "Active Flags" in output
        assert "--graph: ✗" in output
        assert "--hybrid: ✗" in output
        assert "--no-backup: ✗" in output
        assert "--minimal: ✗" in output

    def test_format_flags_all_enabled(self, formatter):
        """Test flags formatting with all enabled."""
        flags = {
            "generate_graph": True,
            "hybrid": True,
            "no_backup": True,
            "minimal": True,
        }
        output = formatter._format_flags(flags)
        assert "--graph: ✓" in output
        assert "--hybrid: ✓" in output
        assert "--no-backup: ✓" in output
        assert "--minimal: ✓" in output

    def test_format_footer(self, formatter):
        """Test footer formatting."""
        footer = formatter._format_footer()
        assert "without --dry-run" in footer
        assert "=" * 70 in footer

    def test_format_summary_minimal(
        self, formatter, minimal_role_info, temp_role_dir, mock_analysis_report
    ):
        """Test complete summary formatting with minimal role."""
        diagrams = {"generate_graph": False}
        flags = {
            "generate_graph": False,
            "hybrid": False,
            "no_backup": False,
            "no_docsible": False,
            "minimal": False,
        }

        summary = formatter.format_summary(
            role_info=minimal_role_info,
            role_path=temp_role_dir,
            output="README.md",
            analysis_report=mock_analysis_report,
            diagrams=diagrams,
            dependency_matrix=None,
            flags=flags,
        )

        assert "DRY RUN MODE" in summary
        assert "test_role" in summary
        assert "Complexity Analysis" in summary
        assert "Would Generate" in summary
        assert "Files That Would Be Created/Modified" in summary
        assert "Active Flags" in summary
        assert "without --dry-run" in summary

    def test_format_summary_full_featured(
        self, formatter, role_info_with_vars, temp_role_dir, mock_analysis_report
    ):
        """Test complete summary formatting with full features."""
        diagrams = {
            "generate_graph": True,
            "mermaid_code_per_file": {"main.yml": "graph TD"},
            "sequence_diagram_high_level": "sequenceDiagram",
            "state_diagram": "stateDiagram",
        }
        flags = {
            "generate_graph": True,
            "hybrid": True,
            "no_backup": False,
            "no_docsible": False,
            "minimal": False,
        }

        summary = formatter.format_summary(
            role_info=role_info_with_vars,
            role_path=temp_role_dir,
            output="README.md",
            analysis_report=mock_analysis_report,
            diagrams=diagrams,
            dependency_matrix="matrix",
            flags=flags,
        )

        assert "Variables: 3 (2 defaults, 1 vars)" in summary
        assert "Handlers: 1" in summary
        assert "Task flowcharts (1 files)" in summary
        assert "Sequence diagram (high-level)" in summary
        assert "State transition diagram" in summary
        assert "Dependency matrix" in summary
        assert "--graph: ✓" in summary
        assert "--hybrid: ✓" in summary

    def test_custom_width(self, minimal_role_info, temp_role_dir, mock_analysis_report):
        """Test formatter with custom width."""
        formatter = DryRunFormatter(width=50)
        diagrams = {"generate_graph": False}
        flags = {
            "generate_graph": False,
            "hybrid": False,
            "no_backup": False,
            "no_docsible": False,
            "minimal": False,
        }

        summary = formatter.format_summary(
            role_info=minimal_role_info,
            role_path=temp_role_dir,
            output="README.md",
            analysis_report=mock_analysis_report,
            diagrams=diagrams,
            dependency_matrix=None,
            flags=flags,
        )

        assert "=" * 50 in summary
