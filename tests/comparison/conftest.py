"""Fixtures for comparison tests."""

from pathlib import Path

import pytest


@pytest.fixture
def simple_role():
    """Path to simple role fixture."""
    return Path(__file__).parent.parent / "fixtures" / "simple_role"


@pytest.fixture
def complex_role():
    """Path to complex role fixture."""
    return Path(__file__).parent.parent / "fixtures" / "complex_role"


@pytest.fixture
def minimal_role(tmp_path):
    """Create a minimal Ansible role structure for testing.

    Creates a role with:
    - tasks/main.yml with one task
    - defaults/main.yml with one variable
    - meta/main.yml with basic metadata

    Returns:
        Path: Path to the role directory
    """
    role_path = tmp_path / "test_role"
    role_path.mkdir()

    # Create tasks
    tasks_dir = role_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "main.yml").write_text("""---
- name: Test task
  debug:
    msg: "Hello from test role"
""")

    # Create defaults
    defaults_dir = role_path / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "main.yml").write_text("""---
test_var: "test_value"
test_port: 8080
""")

    # Create meta
    meta_dir = role_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "main.yml").write_text("""---
galaxy_info:
  author: Test Author
  description: Test Role Description
  company: Test Company
  license: MIT
  min_ansible_version: "2.9"
  platforms:
    - name: Ubuntu
      versions:
        - focal
        - jammy
  galaxy_tags:
    - test
    - example
dependencies: []
""")

    return role_path
