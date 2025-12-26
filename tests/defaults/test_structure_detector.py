from pathlib import Path

import pytest

from docsible.defaults.detectors.structure import StructureDetector, StructureFindings


class TestStructureDetector:
    """Test structure detection for Ansible roles."""

    def test_detect_simple_role_structure(self, simple_role):
        """Test detection of simple role structure."""
        detector = StructureDetector()
        result = detector.detect(simple_role)

        assert result.detector_name == "StructureDetector"
        assert result.confidence == 1.0  # File checks are always confident

        findings = StructureFindings(**result.findings)
        assert findings.has_tasks is True
        assert findings.task_file_count >= 1

    def test_detect_complex_role_structure(self, complex_role_fixture):
        """Test detection of complex role structure."""
        detector = StructureDetector()
        result = detector.detect(complex_role_fixture)

        findings = StructureFindings(**result.findings)

        # Complex role should have multiple directories
        assert findings.has_tasks is True
        assert findings.has_meta is True
        assert findings.task_file_count > 1

    def test_detect_handlers(self, simple_role):
        """Test handler detection."""
        detector = StructureDetector()
        result = detector.detect(simple_role)

        findings = StructureFindings(**result.findings)

        # Simple role has handlers
        assert findings.has_handlers is True
        assert findings.handler_file_count >= 1

    def test_detect_meta_directory(self, complex_role_fixture):
        """Test meta directory detection."""
        detector = StructureDetector()
        result = detector.detect(complex_role_fixture)

        findings = StructureFindings(**result.findings)
        assert findings.has_meta is True

    def test_detect_defaults_directory(self, medium_role_fixture):
        """Test defaults directory detection."""
        detector = StructureDetector()
        result = detector.detect(medium_role_fixture)

        findings = StructureFindings(**result.findings)
        # Medium role fixture should have defaults
        assert findings.has_defaults is True

    def test_count_task_files(self, complex_role_fixture):
        """Test accurate counting of task files."""
        detector = StructureDetector()
        result = detector.detect(complex_role_fixture)

        findings = StructureFindings(**result.findings)

        # Complex role fixture has multiple task files
        assert findings.task_file_count >= 2

    def test_detect_includes(self, tmp_path):
        """Test detection of include_tasks usage."""
        # Create role with include_tasks
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        main_yml = tasks_dir / "main.yml"
        main_yml.write_text("""
---
- name: Include other tasks
  include_tasks: other.yml
""")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.uses_includes is True

    def test_detect_imports(self, tmp_path):
        """Test detection of import_tasks usage."""
        # Create role with import_tasks
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        main_yml = tasks_dir / "main.yml"
        main_yml.write_text("""
---
- name: Import other tasks
  import_tasks: other.yml
""")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.uses_imports is True

    def test_detect_role_usage(self, tmp_path):
        """Test detection of include_role/import_role usage."""
        # Create role that calls other roles
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        main_yml = tasks_dir / "main.yml"
        main_yml.write_text("""
---
- name: Include another role
  include_role:
    name: common
""")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.uses_roles is True

    def test_detect_blocks(self, tmp_path):
        """Test detection of block/rescue/always usage."""
        # Create role with blocks
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        main_yml = tasks_dir / "main.yml"
        main_yml.write_text("""
---
- name: Block example
  block:
    - name: Task in block
      debug:
        msg: "In block"
  rescue:
    - name: Rescue task
      debug:
        msg: "In rescue"
  always:
    - name: Always task
      debug:
        msg: "Always runs"
""")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.uses_blocks is True

    def test_minimal_role_detection(self, minimal_role):
        """Test detection of truly minimal role."""
        detector = StructureDetector()
        result = detector.detect(minimal_role)

        findings = StructureFindings(**result.findings)

        # Minimal role should have minimal structure
        assert findings.has_tasks is True
        assert findings.has_handlers is False  # No handlers
        assert findings.task_file_count == 1  # Single file
        assert findings.uses_includes is False
        assert findings.uses_imports is False
        assert findings.uses_roles is False

    def test_invalid_role_path_raises_error(self, tmp_path):
        """Test that invalid path raises ValueError."""
        invalid_path = tmp_path / "nonexistent_role"

        detector = StructureDetector()

        # Should raise ValueError for nonexistent path
        with pytest.raises(ValueError, match="Role path does not exist"):
            detector.detect(invalid_path)

    def test_is_well_organized_property(self, complex_role_fixture):
        """Test is_well_organized heuristic."""
        detector = StructureDetector()
        result = detector.detect(complex_role_fixture)

        findings = StructureFindings(**result.findings)

        # Complex role with meta and defaults should be well-organized
        if findings.has_meta and findings.has_defaults and findings.task_file_count <= 10:
            assert findings.is_well_organized is True

    def test_needs_detailed_docs_property(self, complex_role_fixture):
        """Test needs_detailed_docs heuristic."""
        detector = StructureDetector()
        result = detector.detect(complex_role_fixture)

        findings = StructureFindings(**result.findings)

        # Complex role should need detailed docs
        assert findings.needs_detailed_docs is True

    def test_role_with_templates(self, tmp_path):
        """Test detection of templates directory."""
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        templates_dir = role_path / "templates"
        tasks_dir.mkdir(parents=True)
        templates_dir.mkdir(parents=True)

        # Create dummy task file
        (tasks_dir / "main.yml").write_text("---\n- name: Test\n  debug:\n    msg: test\n")
        # Create dummy template
        (templates_dir / "config.j2").write_text("{{ variable }}")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.has_templates is True

    def test_role_with_files(self, tmp_path):
        """Test detection of files directory."""
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        files_dir = role_path / "files"
        tasks_dir.mkdir(parents=True)
        files_dir.mkdir(parents=True)

        # Create dummy task file
        (tasks_dir / "main.yml").write_text("---\n- name: Test\n  debug:\n    msg: test\n")
        # Create dummy file
        (files_dir / "config.conf").write_text("setting=value")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.has_files is True

    def test_role_with_vars(self, tmp_path):
        """Test detection of vars directory."""
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        vars_dir = role_path / "vars"
        tasks_dir.mkdir(parents=True)
        vars_dir.mkdir(parents=True)

        # Create dummy task file
        (tasks_dir / "main.yml").write_text("---\n- name: Test\n  debug:\n    msg: test\n")
        # Create vars file
        (vars_dir / "main.yml").write_text("---\nvar1: value1\n")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.has_vars is True

    def test_count_yaml_files_both_extensions(self, tmp_path):
        """Test that both .yml and .yaml files are counted."""
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        # Create files with both extensions
        (tasks_dir / "task1.yml").write_text("---\n- name: Task 1\n")
        (tasks_dir / "task2.yaml").write_text("---\n- name: Task 2\n")
        (tasks_dir / "task3.yml").write_text("---\n- name: Task 3\n")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        # Should count both .yml and .yaml files
        assert findings.task_file_count == 3

    def test_metadata_includes_scanned_directories(self):
        """Test that metadata includes list of scanned directories."""
        detector = StructureDetector()
        result = detector.detect(Path("tests/fixtures/simple_role"))

        assert "scanned_directories" in result.metadata
        scanned = result.metadata["scanned_directories"]
        assert "tasks" in scanned
        assert "handlers" in scanned
        assert "defaults" in scanned
        assert "vars" in scanned
        assert "meta" in scanned
        assert "templates" in scanned
        assert "files" in scanned

    def test_no_false_positives_for_includes(self, tmp_path):
        """Test that role without includes doesn't trigger include detection."""
        role_path = tmp_path / "test_role"
        tasks_dir = role_path / "tasks"
        tasks_dir.mkdir(parents=True)

        main_yml = tasks_dir / "main.yml"
        main_yml.write_text("""
---
- name: Simple task
  debug:
    msg: "No includes here"
""")

        detector = StructureDetector()
        result = detector.detect(role_path)

        findings = StructureFindings(**result.findings)
        assert findings.uses_includes is False
        assert findings.uses_imports is False
        assert findings.uses_roles is False
        assert findings.uses_blocks is False

    def test_many_files_role(self, many_files_role):
        """Test role with many task files."""
        detector = StructureDetector()
        result = detector.detect(many_files_role)

        findings = StructureFindings(**result.findings)

        # many_files_role has 6 task files
        assert findings.task_file_count == 6
        assert findings.needs_detailed_docs is True
