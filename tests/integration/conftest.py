"""Fixtures for integration tests."""

import pytest


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


@pytest.fixture
def role_with_handlers(minimal_role):
    """Create a role with handlers for testing.

    Args:
        minimal_role: Minimal role fixture

    Returns:
        Path: Path to the role directory with handlers
    """
    # Add handlers
    handlers_dir = minimal_role / "handlers"
    handlers_dir.mkdir()
    (handlers_dir / "main.yml").write_text("""---
- name: Restart service
  service:
    name: test-service
    state: restarted
  listen: restart test service
""")

    return minimal_role


@pytest.fixture
def role_with_playbook(minimal_role):
    """Create a role with a test playbook.

    Args:
        minimal_role: Minimal role fixture

    Returns:
        Path: Path to the role directory with playbook
    """
    # Add test playbook
    tests_dir = minimal_role / "tests"
    tests_dir.mkdir()
    (tests_dir / "test.yml").write_text("""---
- name: Test playbook
  hosts: localhost
  gather_facts: false
  roles:
    - test_role
""")

    return minimal_role


@pytest.fixture
def minimal_collection(tmp_path):
    """Create a minimal Ansible collection structure for testing.

    Creates a collection with:
    - galaxy.yml with metadata
    - roles/ directory with one role

    Returns:
        Path: Path to the collection directory
    """
    collection_path = tmp_path / "test_collection"
    collection_path.mkdir()

    # Create galaxy.yml
    (collection_path / "galaxy.yml").write_text("""---
namespace: test_namespace
name: test_collection
version: 1.0.0
readme: README.md
authors:
  - Test Author <test@example.com>
description: Test Collection Description
license:
  - MIT
tags:
  - test
  - example
repository: https://github.com/test/test_collection
""")

    # Create roles directory with a role
    roles_dir = collection_path / "roles"
    roles_dir.mkdir()

    role_dir = roles_dir / "collection_role"
    role_dir.mkdir()

    # Add minimal role structure
    tasks_dir = role_dir / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "main.yml").write_text("""---
- name: Collection role task
  debug:
    msg: "Hello from collection role"
""")

    defaults_dir = role_dir / "defaults"
    defaults_dir.mkdir()
    (defaults_dir / "main.yml").write_text("""---
collection_var: "collection_value"
""")

    return collection_path


@pytest.fixture
def role_with_docsible_config(minimal_role):
    """Create a role with .docsible.yml configuration.

    Args:
        minimal_role: Minimal role fixture

    Returns:
        Path: Path to the role directory with config
    """
    (minimal_role / ".docsible.yml").write_text("""---
structure:
  defaults_dir: 'defaults'
  vars_dir: 'vars'
  tasks_dir: 'tasks'
  meta_dir: 'meta'
""")

    return minimal_role
