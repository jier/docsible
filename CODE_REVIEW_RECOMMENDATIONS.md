# Docsible Codebase Review & Improvement Roadmap

**Review Date**: 2025-12-08
**Reviewer**: Seasoned Python Engineer Perspective
**Codebase Version**: 0.8.0

---

## Executive Summary

Docsible is a functional CLI tool with a clear purpose. The codebase shows signs of organic growth with good intentions but lacks the structural foundation needed for long-term maintainability and collaboration. This document outlines a gradual refactoring roadmap prioritizing small, incremental improvements.

**Overall Assessment**: ⭐⭐⭐ (3/5)
- **Strengths**: Clear purpose, working features, decent test coverage starting
- **Weaknesses**: Large monolithic files, missing type hints, inconsistent patterns, limited separation of concerns

---

## Table of Contents

1. [What's Good](#whats-good)
2. [Critical Issues](#critical-issues)
3. [Improvement Roadmap](#improvement-roadmap)
   - [Phase 1: Quick Wins (1-2 days)](#phase-1-quick-wins-1-2-days)
   - [Phase 2: Code Quality (1 week)](#phase-2-code-quality-1-week)
   - [Phase 3: Refactoring (2-3 weeks)](#phase-3-refactoring-2-3-weeks)
   - [Phase 4: Architecture (1 month)](#phase-4-architecture-1-month)
4. [Detailed Analysis](#detailed-analysis)
5. [Collaboration Guidelines](#collaboration-guidelines)

---

## What's Good

### ✅ Strengths to Preserve

1. **Clear Single Responsibility**
   - Tool has one job: generate Ansible documentation
   - No feature creep or scope confusion

2. **Good Test Foundation**
   - Test fixtures are well-structured
   - Recent improvements to test isolation (tmp_path usage)
   - Good coverage starting with project structure tests

3. **Modern Project Configuration**
   - pyproject.toml with PEP 621 support
   - Multiple build backend compatibility (poetry, hatch, uv)
   - Good CI/CD integration potential

4. **Modular Utils Package**
   - Separate concerns into utils/ directory
   - Git, YAML, Mermaid functionality isolated

5. **Flexible Configuration System**
   - `.docsible.yml` support for custom structures
   - Auto-detection fallback mechanism
   - Priority system (CLI > config > detection > defaults)

6. **Recent Improvements**
   - ProjectStructure class adds abstraction
   - Plugin directory support shows extensibility thinking
   - Fixture test pollution issues being addressed

---

## Critical Issues

### 🚨 High Priority Problems

1. **Massive Monolithic Files**
   - `cli.py`: 758 lines - should be <300
   - `mermaid_sequence.py`: 600 lines - should be <400
   - `markdown_template.py`: 602 lines - mostly template strings
   - **Impact**: Hard to navigate, test, and modify

2. **No Type Hints**
   - Zero type annotations throughout codebase
   - Makes IDEs less helpful
   - Harder to catch bugs
   - Poor self-documentation
   - **Impact**: Higher bug rate, slower onboarding

3. **Inconsistent Error Handling**
   - Mix of `try/except` with print statements
   - No logging framework
   - Silent failures in many places
   - No error recovery strategies
   - **Impact**: Hard to debug production issues

4. **Template Strings in Code**
   - 400+ lines of Jinja templates embedded in Python
   - Should be separate `.jinja2` files
   - Makes editing templates painful
   - **Impact**: Mixing concerns, hard to maintain

5. **God Object Pattern in cli.py**
   - Single file does: CLI parsing, file I/O, template rendering, git operations, README management
   - Violates Single Responsibility Principle
   - **Impact**: Hard to test individual components

6. **Missing Domain Model**
   - No clear data structures (Role, Collection, Playbook classes)
   - Everything is dicts and strings
   - Hard to understand data flow
   - **Impact**: Cognitive overhead, validation scattered

---

## Improvement Roadmap

### Phase 1: Quick Wins (1-2 days)

Small changes with immediate impact, no refactoring needed.

#### 1.1 Add Type Hints to Function Signatures

**Priority**: 🔥 High
**Effort**: Low
**Impact**: High

**Action**: Add type hints to all public functions

**Example - Before**:
```python
def load_yaml_generic(filepath):
    """Function to load YAML in a standard way"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except (FileNotFoundError, yaml.constructor.ConstructorError) as e:
        print(f"Error loading {filepath}: {e}")
        return None
```

**Example - After**:
```python
from typing import Optional, Dict, Any
from pathlib import Path

def load_yaml_generic(filepath: Path | str) -> Optional[Dict[str, Any]]:
    """Load YAML file and return parsed data.

    Args:
        filepath: Path to YAML file

    Returns:
        Parsed YAML data as dictionary, or None if error occurs
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except (FileNotFoundError, yaml.constructor.ConstructorError) as e:
        print(f"Error loading {filepath}: {e}")
        return None
```

**Files to update**:
- `docsible/utils/yaml.py` - 10 functions
- `docsible/utils/git.py` - 3 functions
- `docsible/utils/project_structure.py` - 15 functions
- `docsible/cli.py` - 8 public functions

**Benefits**:
- Better IDE autocomplete
- Catch type errors early
- Self-documenting code
- Easier for new contributors

---

#### 1.2 Replace print() with logging module

**Priority**: 🔥 High
**Effort**: Low
**Impact**: Medium

**Action**: Replace all `print()` statements with proper logging

**Example - Before**:
```python
print(f"[INFO] Loaded configuration from {config_path}")
print(f"[WARN] Error loading config from {config_path}: {e}")
print(f"[ERROR] Failed to create configuration file: {e}")
```

**Example - After**:
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Loaded configuration from {config_path}")
logger.warning(f"Error loading config from {config_path}: {e}")
logger.error(f"Failed to create configuration file: {e}")
```

**Setup in cli.py**:
```python
import logging
import sys

def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def doc_the_role(..., verbose):
    setup_logging(verbose)
    # ... rest of function
```

**Files to update**:
- All files with `print()` statements (grep for "print\(")

**Benefits**:
- Configurable verbosity
- Log levels for filtering
- Better production debugging
- Integration with monitoring tools

---

#### 1.3 Add docstrings to all functions

**Priority**: Medium
**Effort**: Low
**Impact**: High (for collaboration)

**Action**: Add Google-style docstrings to functions missing them

**Example**:
```python
def extract_playbook_role_dependencies(
    playbook_content: str,
    current_role_name: str
) -> list[str]:
    """Extract role dependencies from playbook content.

    Searches for roles in:
    - roles: section in plays
    - include_role/import_role tasks in pre_tasks, tasks, post_tasks

    Args:
        playbook_content: YAML content of playbook as string
        current_role_name: Name of current role being documented

    Returns:
        List of role names (excluding current role)

    Example:
        >>> content = '''
        ... - hosts: all
        ...   roles:
        ...     - common
        ...     - webserver
        ... '''
        >>> extract_playbook_role_dependencies(content, 'webserver')
        ['common']
    """
    # ... implementation
```

**Files to update**:
- Focus on public API functions first
- Then internal utilities

**Benefits**:
- Better IDE hints
- Easier to understand intent
- Examples help users
- Generates better docs

---

#### 1.4 Create constants module

**Priority**: Medium
**Effort**: Low
**Impact**: Medium

**Action**: Extract magic strings and numbers to constants

**Create** `docsible/constants.py`:
```python
"""Application-wide constants."""

# Documentation tags
DOCSIBLE_START_TAG = "<!-- DOCSIBLE START -->"
DOCSIBLE_END_TAG = "<!-- DOCSIBLE END -->"
GENERATED_TAG = "<!-- DOCSIBLE GENERATED -->"
MANUAL_TAG = "<!-- MANUALLY MAINTAINED -->"

# File names
DEFAULT_README = "README.md"
DEFAULT_CONFIG = ".docsible.yml"
DOCSIBLE_FILE = ".docsible"

# YAML extensions
YAML_EXTENSIONS = ['.yml', '.yaml']

# Ansible directory defaults
DEFAULT_DEFAULTS_DIR = "defaults"
DEFAULT_VARS_DIR = "vars"
DEFAULT_TASKS_DIR = "tasks"
DEFAULT_META_DIR = "meta"
DEFAULT_HANDLERS_DIR = "handlers"
DEFAULT_LIBRARY_DIR = "library"
DEFAULT_LOOKUP_PLUGINS_DIR = "lookup_plugins"
DEFAULT_FILTER_PLUGINS_DIR = "filter_plugins"
DEFAULT_MODULE_UTILS_DIR = "module_utils"
DEFAULT_TEMPLATES_DIR = "templates"
DEFAULT_ROLES_DIR = "roles"

# Mermaid diagram limits
MAX_DIAGRAM_LINES = 20
MAX_TASK_NAME_LENGTH = 40

# Version
VERSION = "0.8.0"
```

**Then replace** hardcoded strings throughout codebase:
```python
# Before
DOCSIBLE_START_TAG = "<!-- DOCSIBLE START -->"
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

def get_version():
    return "0.8.0"

# After
from docsible.constants import DOCSIBLE_START_TAG, VERSION

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

def get_version() -> str:
    return VERSION
```

**Benefits**:
- Single source of truth
- Easy to modify values
- Better testability
- Self-documenting

---

#### 1.5 Fix inconsistent naming conventions

**Priority**: Low
**Effort**: Low
**Impact**: Medium (for consistency)

**Issues found**:
- Mix of `snake_case` and `camelCase` in function names
- Inconsistent variable naming (e.g., `filepath` vs `file_path`)

**Action**: Standardize to PEP 8:
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Variables: `snake_case`

**Example fixes**:
```python
# Before
def load_yaml_generic(filepath):
    # ...

def get_TaskComments(file_path):
    # ...

# After
def load_yaml_generic(file_path: Path) -> Optional[Dict]:
    # ...

def get_task_comments(file_path: Path) -> Dict[int, str]:
    # ...
```

**Tool**: Use `ruff` linter (already in dev dependencies):
```bash
ruff check --select N  # Check naming conventions
ruff check --fix --select N  # Auto-fix some issues
```

---

### Phase 2: Code Quality (1 week)

Medium-sized improvements requiring some refactoring.

#### 2.1 Extract templates to separate files

**Priority**: 🔥 High
**Effort**: Medium
**Impact**: High

**Problem**:
- `hybrid_template.py`: 417 lines of template string
- `markdown_template.py`: 602 lines of template strings
- Mixing Python logic with Jinja2 markup

**Action**: Move templates to `docsible/templates/` directory

**File structure**:
```
docsible/
├── templates/
│   ├── role/
│   │   ├── hybrid.jinja2
│   │   ├── standard.jinja2
│   │   └── minimal.jinja2
│   ├── collection/
│   │   ├── main.jinja2
│   │   └── role_list.jinja2
│   └── partials/
│       ├── variables_table.jinja2
│       ├── task_details.jinja2
│       ├── dependencies.jinja2
│       └── metadata.jinja2
```

**Before**:
```python
# hybrid_template.py
hybrid_role_template = """# {{ role.name }}

<!-- MANUALLY MAINTAINED -->
> **Note**: Replace this section...
...
"""
```

**After**:
```python
# docsible/template_loader.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template

class TemplateLoader:
    """Load and cache Jinja2 templates."""

    def __init__(self):
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def get_template(self, name: str) -> Template:
        """Load template by name.

        Args:
            name: Template name (e.g., 'role/hybrid.jinja2')

        Returns:
            Compiled Jinja2 template
        """
        return self.env.get_template(name)
```

**Usage in cli.py**:
```python
from docsible.template_loader import TemplateLoader

loader = TemplateLoader()
template = loader.get_template('role/hybrid.jinja2')
content = template.render(role=role_info, no_vars=no_vars)
```

**Benefits**:
- Easier to edit templates (proper syntax highlighting)
- Separate concerns (logic vs presentation)
- Can hot-reload templates in development
- Template inheritance/includes work better

---

#### 2.2 Split cli.py into modules

**Priority**: 🔥 High
**Effort**: High
**Impact**: High

**Problem**: cli.py is 758 lines doing too many things

**Action**: Create command modules

**New structure**:
```
docsible/
├── cli.py                  # Entry point only (50 lines)
├── commands/
│   ├── __init__.py
│   ├── document_role.py    # Role documentation logic
│   ├── document_collection.py  # Collection documentation
│   ├── init_config.py      # Config initialization
│   └── common.py           # Shared utilities
├── models/
│   ├── __init__.py
│   ├── role.py             # Role data model
│   ├── collection.py       # Collection data model
│   ├── playbook.py         # Playbook data model
│   └── config.py           # Configuration model
└── renderers/
    ├── __init__.py
    ├── readme_renderer.py  # README generation
    └── template_manager.py # Template selection/loading
```

**Example - cli.py (new)**:
```python
"""Docsible CLI entry point."""
import click
from docsible.commands import document_role, document_collection, init_config

@click.group()
@click.version_option()
def cli():
    """Docsible - Generate documentation for Ansible roles and collections."""
    pass

cli.add_command(document_role.doc_the_role)
cli.add_command(document_collection.doc_collection)
cli.add_command(init_config.init_config)

if __name__ == '__main__':
    cli()
```

**Example - commands/document_role.py**:
```python
"""Document a single Ansible role."""
from pathlib import Path
from typing import Optional
import click

from docsible.models.role import Role
from docsible.renderers.readme_renderer import ReadmeRenderer
from docsible.utils.project_structure import ProjectStructure

@click.command('role')
@click.option('--role', '-r', required=True, help='Path to role directory')
@click.option('--output', '-o', default='README.md', help='Output file')
@click.option('--hybrid', is_flag=True, help='Use hybrid template')
@click.option('--no-backup', is_flag=True, help='Skip backup')
def doc_the_role(
    role: str,
    output: str,
    hybrid: bool,
    no_backup: bool
) -> None:
    """Generate documentation for an Ansible role."""
    role_path = Path(role).resolve()

    # Load role
    role_model = Role.from_path(role_path)

    # Render README
    renderer = ReadmeRenderer(
        template_type='hybrid' if hybrid else 'standard',
        backup=not no_backup
    )
    renderer.render(role_model, output_path=role_path / output)

    click.echo(f"✓ Generated {output}")
```

**Benefits**:
- Each file <300 lines
- Clear separation of concerns
- Easier to test individual commands
- Better IDE navigation
- Parallel development possible

---

#### 2.3 Create domain models

**Priority**: High
**Effort**: Medium
**Impact**: High

**Problem**: Everything is `Dict[str, Any]` - no type safety or validation

**Action**: Create dataclasses for core concepts

**Example - models/role.py**:
```python
"""Ansible role domain model."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

@dataclass
class RoleMetadata:
    """Role metadata from meta/main.yml."""
    author: Optional[str] = None
    company: Optional[str] = None
    license: str = "MIT"
    min_ansible_version: str = "2.9"
    platforms: List[Dict[str, Any]] = field(default_factory=list)
    galaxy_tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class RoleTask:
    """Single task in a role."""
    name: str
    module: str
    file: str
    line_number: int
    description: Optional[str] = None
    when: Optional[str] = None
    notify: Optional[List[str]] = None

@dataclass
class Role:
    """Ansible role representation."""
    name: str
    path: Path
    defaults: Dict[str, Any] = field(default_factory=dict)
    vars: Dict[str, Any] = field(default_factory=dict)
    tasks: List[RoleTask] = field(default_factory=list)
    handlers: List[RoleTask] = field(default_factory=list)
    meta: Optional[RoleMetadata] = None

    @classmethod
    def from_path(cls, path: Path) -> 'Role':
        """Load role from filesystem path.

        Args:
            path: Path to role directory

        Returns:
            Role instance populated from disk
        """
        from docsible.loaders.role_loader import RoleLoader
        loader = RoleLoader(path)
        return loader.load()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            'name': self.name,
            'defaults': self.defaults,
            'vars': self.vars,
            'tasks': [task.__dict__ for task in self.tasks],
            'handlers': [h.__dict__ for h in self.handlers],
            'meta': self.meta.__dict__ if self.meta else None,
        }
```

**Benefits**:
- Type safety
- IDE autocomplete
- Validation at construction
- Clear data contracts
- Easier to test
- Self-documenting

---

#### 2.4 Add error handling utilities

**Priority**: Medium
**Effort**: Medium
**Impact**: Medium

**Problem**: Inconsistent error handling, silent failures

**Action**: Create error handling utilities

**Create** `docsible/exceptions.py`:
```python
"""Custom exceptions for docsible."""

class DocsibleError(Exception):
    """Base exception for all docsible errors."""
    pass

class ConfigurationError(DocsibleError):
    """Error in configuration file or structure."""
    pass

class RoleNotFoundError(DocsibleError):
    """Role directory not found or invalid."""
    pass

class TemplateRenderError(DocsibleError):
    """Error rendering Jinja2 template."""
    pass

class YAMLParseError(DocsibleError):
    """Error parsing YAML file."""
    pass
```

**Create** `docsible/utils/error_handler.py`:
```python
"""Error handling utilities."""
import logging
from typing import Callable, TypeVar, ParamSpec
from functools import wraps

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

def handle_errors(default_return: T = None):
    """Decorator to handle and log errors gracefully.

    Args:
        default_return: Value to return on error

    Example:
        @handle_errors(default_return={})
        def load_config(path: Path) -> Dict:
            # ... might raise exception
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

def validate_path(path: Path, must_exist: bool = True) -> None:
    """Validate a filesystem path.

    Args:
        path: Path to validate
        must_exist: Whether path must exist

    Raises:
        ConfigurationError: If validation fails
    """
    from docsible.exceptions import ConfigurationError

    if must_exist and not path.exists():
        raise ConfigurationError(f"Path does not exist: {path}")

    if must_exist and not path.is_dir():
        raise ConfigurationError(f"Path is not a directory: {path}")
```

**Usage**:
```python
from docsible.utils.error_handler import handle_errors, validate_path
from docsible.exceptions import ConfigurationError

@handle_errors(default_return=None)
def load_role_config(path: Path) -> Optional[Dict]:
    """Load role configuration from path."""
    validate_path(path, must_exist=True)
    # ... load logic
```

**Benefits**:
- Consistent error messages
- Better error recovery
- Easier debugging
- User-friendly error reports

---

#### 2.5 Add integration tests

**Priority**: Medium
**Effort**: High
**Impact**: High

**Problem**: Tests focus on units, but no end-to-end validation

**Action**: Add integration tests that exercise full workflows

**Create** `tests/integration/`:
```
tests/
├── integration/
│   ├── test_end_to_end.py
│   ├── test_real_roles.py
│   └── conftest.py
├── unit/
│   ├── test_yaml_parser.py
│   ├── test_mermaid_generator.py
│   └── test_project_structure.py
└── fixtures/
    └── ... (existing)
```

**Example** `tests/integration/test_end_to_end.py`:
```python
"""End-to-end integration tests."""
import pytest
from pathlib import Path
from click.testing import CliRunner

from docsible.cli import doc_the_role

class TestEndToEnd:
    """Test complete workflows."""

    def test_document_simple_role_creates_readme(self, tmp_path):
        """Test full workflow: role -> README generation."""
        # Setup: Create minimal role structure
        role_path = tmp_path / "test_role"
        role_path.mkdir()

        # Create minimal required files
        (role_path / "tasks").mkdir()
        (role_path / "tasks" / "main.yml").write_text("""
---
- name: Test task
  debug:
    msg: "Hello"
""")

        (role_path / "defaults").mkdir()
        (role_path / "defaults" / "main.yml").write_text("""
---
test_var: "value"
""")

        # Execute: Run docsible
        runner = CliRunner()
        result = runner.invoke(doc_the_role, [
            '--role', str(role_path),
            '--no-backup'
        ])

        # Assert: README created with expected content
        assert result.exit_code == 0
        readme = role_path / "README.md"
        assert readme.exists()

        content = readme.read_text()
        assert "test_role" in content
        assert "Test task" in content
        assert "test_var" in content

    def test_hybrid_template_preserves_manual_sections(self, tmp_path):
        """Test that regeneration preserves manual edits."""
        # ... test hybrid template workflow
```

**Benefits**:
- Catch regressions early
- Validate real-world scenarios
- Confidence in releases
- Documentation of expected behavior

---

### Phase 3: Refactoring (2-3 weeks)

Larger structural changes for better architecture.

#### 3.1 Implement Repository pattern for data access

**Priority**: Medium
**Effort**: High
**Impact**: High

**Problem**: File I/O scattered throughout codebase

**Action**: Create repository classes

**Example** `docsible/repositories/role_repository.py`:
```python
"""Repository for loading Ansible roles from disk."""
from pathlib import Path
from typing import Optional
import logging

from docsible.models.role import Role, RoleMetadata, RoleTask
from docsible.utils.yaml import load_yaml_generic
from docsible.utils.project_structure import ProjectStructure

logger = logging.getLogger(__name__)

class RoleRepository:
    """Load and save Role data from/to filesystem."""

    def __init__(self, project_structure: ProjectStructure):
        self.structure = project_structure

    def load(self, path: Path) -> Optional[Role]:
        """Load a role from filesystem.

        Args:
            path: Path to role directory

        Returns:
            Role instance or None if loading fails
        """
        try:
            defaults = self._load_defaults(path)
            vars_data = self._load_vars(path)
            tasks = self._load_tasks(path)
            handlers = self._load_handlers(path)
            meta = self._load_meta(path)

            return Role(
                name=path.name,
                path=path,
                defaults=defaults,
                vars=vars_data,
                tasks=tasks,
                handlers=handlers,
                meta=meta
            )
        except Exception as e:
            logger.error(f"Failed to load role from {path}: {e}")
            return None

    def _load_defaults(self, role_path: Path) -> dict:
        """Load defaults directory."""
        defaults_dir = self.structure.get_defaults_dir(role_path)
        if not defaults_dir.exists():
            return {}

        # ... load YAML files from directory
        return {}

    def _load_tasks(self, role_path: Path) -> list[RoleTask]:
        """Load tasks directory."""
        # ... implementation
        return []

    # ... other private load methods
```

**Benefits**:
- Single place for file I/O
- Easy to mock in tests
- Can swap implementations (DB, API, etc.)
- Clear data access layer

---

#### 3.2 Add configuration validation

**Priority**: Medium
**Effort**: Medium
**Impact**: Medium

**Problem**: Invalid `.docsible.yml` causes cryptic errors

**Action**: Add pydantic for config validation

**Update** `pyproject.toml`:
```toml
dependencies = [
    "click>=8.1.7",
    "PyYAML>=6.0.1",
    "Jinja2>=3.1.2",
    "pydantic>=2.0",  # Add this
]
```

**Create** `docsible/models/config.py`:
```python
"""Configuration models with validation."""
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator

class StructureConfig(BaseModel):
    """Project structure configuration."""

    # Directories
    defaults_dir: str = Field(default="defaults")
    vars_dir: str = Field(default="vars")
    tasks_dir: str = Field(default="tasks")
    meta_dir: str = Field(default="meta")
    handlers_dir: str = Field(default="handlers")
    library_dir: str = Field(default="library")
    lookup_plugins_dir: str = Field(default="lookup_plugins")
    filter_plugins_dir: str = Field(default="filter_plugins")
    module_utils_dir: str = Field(default="module_utils")
    templates_dir: str = Field(default="templates")
    roles_dir: str = Field(default="roles")

    # Files
    meta_file: str = Field(default="main")
    argument_specs_file: str = Field(default="argument_specs")
    test_playbook: str = Field(default="tests/test.yml")

    # Extensions
    yaml_extensions: List[str] = Field(default=['.yml', '.yaml'])

    @validator('*_dir')
    def validate_dir_name(cls, v):
        """Ensure directory names don't start/end with /."""
        if v.startswith('/') or v.endswith('/'):
            raise ValueError("Directory names should not start or end with /")
        return v

    @validator('yaml_extensions')
    def validate_extensions(cls, v):
        """Ensure extensions start with dot."""
        for ext in v:
            if not ext.startswith('.'):
                raise ValueError(f"Extension must start with dot: {ext}")
        return v

class DocsibleConfig(BaseModel):
    """Root configuration model."""

    structure: StructureConfig = Field(default_factory=StructureConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> 'DocsibleConfig':
        """Load and validate config from YAML file.

        Args:
            path: Path to .docsible.yml

        Returns:
            Validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        import yaml
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

**Usage**:
```python
from docsible.models.config import DocsibleConfig
from pydantic import ValidationError

try:
    config = DocsibleConfig.from_yaml(config_path)
except ValidationError as e:
    print(f"Invalid configuration: {e}")
    sys.exit(1)
```

**Benefits**:
- Catch invalid configs early
- Clear error messages
- Type-safe configuration
- Auto-generated JSON schema

---

#### 3.3 Add caching for expensive operations

**Priority**: Low
**Effort**: Medium
**Impact**: Medium (for large projects)

**Problem**: Re-parsing YAML files multiple times

**Action**: Add simple caching layer

**Create** `docsible/utils/cache.py`:
```python
"""Simple caching utilities."""
from functools import lru_cache
from pathlib import Path
from typing import Callable, TypeVar, ParamSpec
import hashlib

P = ParamSpec('P')
T = TypeVar('T')

def cache_by_file_mtime(func: Callable[[Path], T]) -> Callable[[Path], T]:
    """Cache function results by file modification time.

    Args:
        func: Function that takes a Path and returns data

    Returns:
        Cached version of function
    """
    cache = {}

    def wrapper(path: Path) -> T:
        mtime = path.stat().st_mtime
        key = (str(path), mtime)

        if key not in cache:
            cache[key] = func(path)

        return cache[key]

    return wrapper

# Usage example
@cache_by_file_mtime
def load_yaml_cached(path: Path) -> dict:
    """Load YAML with caching."""
    from docsible.utils.yaml import load_yaml_generic
    return load_yaml_generic(path)
```

**Benefits**:
- Faster for large collections
- Reduces I/O
- Better user experience

---

#### 3.4 Refactor mermaid generation

**Priority**: Medium
**Effort**: High
**Impact**: Medium

**Problem**: `mermaid_sequence.py` is 600 lines of complex logic

**Action**: Extract diagram builders

**New structure**:
```
docsible/
└── diagram_builders/
    ├── __init__.py
    ├── base.py              # Base diagram builder
    ├── flowchart.py         # Flowchart diagrams
    ├── sequence.py          # Sequence diagrams
    └── formatters.py        # Mermaid formatting utilities
```

**Example** `diagram_builders/base.py`:
```python
"""Base diagram builder."""
from abc import ABC, abstractmethod
from typing import List

class DiagramBuilder(ABC):
    """Base class for mermaid diagram builders."""

    def __init__(self):
        self.lines: List[str] = []

    @abstractmethod
    def build(self) -> str:
        """Build and return complete diagram."""
        pass

    def add_line(self, line: str, indent: int = 0) -> None:
        """Add line with indentation."""
        self.lines.append("    " * indent + line)

    def clear(self) -> None:
        """Clear current diagram."""
        self.lines = []

    def get_diagram(self) -> str:
        """Get current diagram as string."""
        return "\n".join(self.lines)
```

**Example** `diagram_builders/sequence.py`:
```python
"""Sequence diagram builder."""
from typing import List, Set
from docsible.diagram_builders.base import DiagramBuilder

class SequenceDiagramBuilder(DiagramBuilder):
    """Build mermaid sequence diagrams."""

    def __init__(self):
        super().__init__()
        self.participants: Set[str] = set()

    def start_diagram(self) -> None:
        """Initialize sequence diagram."""
        self.clear()
        self.add_line("sequenceDiagram")

    def add_participant(self, name: str) -> None:
        """Add participant to diagram."""
        if name not in self.participants:
            self.add_line(f"participant {name}", indent=1)
            self.participants.add(name)

    def add_message(
        self,
        from_actor: str,
        to_actor: str,
        message: str,
        arrow_type: str = "->>"
    ) -> None:
        """Add message between actors."""
        self.add_line(
            f"{from_actor}{arrow_type}{to_actor}: {message}",
            indent=1
        )

    def add_activation(self, actor: str) -> None:
        """Activate an actor."""
        self.add_line(f"activate {actor}", indent=1)

    def add_deactivation(self, actor: str) -> None:
        """Deactivate an actor."""
        self.add_line(f"deactivate {actor}", indent=1)

    def build(self) -> str:
        """Build complete diagram."""
        return self.get_diagram()
```

**Benefits**:
- Smaller, focused files
- Easier to test
- Cleaner API
- Can add new diagram types easily

---

### Phase 4: Architecture (1 month)

Long-term architectural improvements.

#### 4.1 Implement plugin system

**Priority**: Low
**Effort**: Very High
**Impact**: High (for extensibility)

**Vision**: Allow users to add custom:
- Template filters
- Diagram types
- Output formats
- Data processors

**Example** plugin interface:
```python
# docsible/plugins/base.py
from abc import ABC, abstractmethod

class DocsiblePlugin(ABC):
    """Base class for docsible plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @abstractmethod
    def initialize(self, config: dict) -> None:
        """Initialize plugin with configuration."""
        pass

class TemplateFilterPlugin(DocsiblePlugin):
    """Plugin providing custom Jinja2 filters."""

    @abstractmethod
    def get_filters(self) -> dict:
        """Return dict of filter_name -> filter_function."""
        pass
```

**Benefits**:
- Extensible without forking
- Community contributions
- Specialized use cases
- Maintainable core

---

#### 4.2 Add CLI test mode

**Priority**: Low
**Effort**: Medium
**Impact**: Low

**Action**: Add `--dry-run` flag

```python
@click.command()
@click.option('--dry-run', is_flag=True, help='Show what would be done')
def doc_the_role(..., dry_run):
    """Generate role documentation."""
    if dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        # ... show what would happen
        return

    # ... actual execution
```

**Benefits**:
- Safe testing
- CI/CD validation
- User confidence

---

#### 4.3 Performance profiling and optimization

**Priority**: Low
**Effort**: Medium
**Impact**: Low (unless performance issues reported)

**Action**: Add profiling tools

```python
# docsible/utils/profiler.py
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def profile(func):
    """Profile function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper
```

---

## Detailed Analysis

### Architecture Patterns

#### Current State: Procedural Script Style
```
cli.py
  ├─ Loads YAML files directly
  ├─ Processes data inline
  ├─ Renders templates
  └─ Writes files
```

**Issues**:
- Hard to test individual steps
- No separation of concerns
- Difficult to extend

#### Recommended: Layered Architecture
```
Presentation Layer (CLI)
  ↓
Application Layer (Commands)
  ↓
Domain Layer (Models)
  ↓
Infrastructure Layer (Repositories, File I/O)
```

**Benefits**:
- Clear boundaries
- Testable layers
- Extensible design

---

### Code Smells Found

1. **God Object**: `cli.py` does everything
2. **Feature Envy**: Functions access too much data from other modules
3. **Long Method**: Several 100+ line functions
4. **Magic Numbers**: Hardcoded values throughout
5. **Duplicated Code**: YAML loading logic repeated
6. **Shotgun Surgery**: Changing one feature requires editing many files
7. **Primitive Obsession**: Using dicts instead of domain models

---

### Testing Strategy

#### Current Coverage (Estimated)
- Unit tests: ~30%
- Integration tests: ~10%
- E2E tests: ~5%

#### Target Coverage
- Unit tests: >80%
- Integration tests: >60%
- E2E tests: >40%

#### Test Pyramid
```
       /\
      /E2E\       <- Few, slow, expensive
     /------\
    /  INT  \     <- Some, medium speed
   /--------\
  /   UNIT   \    <- Many, fast, cheap
 /------------\
```

---

## Collaboration Guidelines

### For New Contributors

1. **Start Small**
   - Pick issues labeled "good first issue"
   - Focus on one module at a time
   - Ask questions early

2. **Follow Conventions**
   - PEP 8 style guide
   - Google-style docstrings
   - Type hints on all public APIs

3. **Write Tests**
   - Every new feature needs tests
   - Bug fixes need regression tests
   - Aim for >80% coverage

4. **Document Changes**
   - Update docstrings
   - Add examples to docs
   - Update CHANGELOG.md

### Code Review Checklist

- [ ] Type hints added
- [ ] Docstrings present
- [ ] Tests included
- [ ] No print() statements (use logging)
- [ ] Error handling added
- [ ] No magic numbers/strings
- [ ] PEP 8 compliant
- [ ] Backwards compatible (or breaking change documented)

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/add-type-hints

# 2. Make small commits
git add docsible/utils/yaml.py
git commit -m "feat(yaml): Add type hints to load functions"

# 3. Keep commits atomic
# One commit = One logical change

# 4. Write good commit messages
# Format: type(scope): description
# Types: feat, fix, docs, refactor, test, chore
```

---

## Priority Matrix

| Change | Priority | Effort | Impact | Phase |
|--------|----------|--------|--------|-------|
| Add type hints | 🔥 High | Low | High | 1 |
| Add logging | 🔥 High | Low | Medium | 1 |
| Extract templates | 🔥 High | Medium | High | 2 |
| Split cli.py | 🔥 High | High | High | 2 |
| Create models | High | Medium | High | 2 |
| Add docstrings | Medium | Low | High | 1 |
| Constants module | Medium | Low | Medium | 1 |
| Error handling | Medium | Medium | Medium | 2 |
| Integration tests | Medium | High | High | 2 |
| Repository pattern | Medium | High | High | 3 |
| Config validation | Medium | Medium | Medium | 3 |
| Caching | Low | Medium | Medium | 3 |
| Refactor mermaid | Medium | High | Medium | 3 |
| Plugin system | Low | Very High | High | 4 |
| Dry-run mode | Low | Medium | Low | 4 |
| Profiling | Low | Medium | Low | 4 |

---

## Immediate Next Steps (This Week)

1. **Day 1-2**: Add type hints to `utils/` modules
2. **Day 3**: Replace print() with logging
3. **Day 4**: Add docstrings to public functions
4. **Day 5**: Create constants module

**Goal**: Improve code quality without breaking changes

---

## Success Metrics

### Code Quality
- [ ] 100% of functions have type hints
- [ ] 100% of public APIs have docstrings
- [ ] 0 print() statements (all use logging)
- [ ] <5 linter warnings

### Testing
- [ ] >80% unit test coverage
- [ ] >60% integration test coverage
- [ ] All tests pass in CI/CD

### Architecture
- [ ] No file >400 lines
- [ ] Clear separation of concerns
- [ ] Domain models implemented
- [ ] Repositories pattern used

### Documentation
- [ ] API docs generated from docstrings
- [ ] Contributing guide updated
- [ ] Architecture documented
- [ ] Examples provided

---

## Questions to Consider

1. **Breaking Changes**: Are we willing to break backwards compatibility for better design?
2. **Release Strategy**: How do we roll out gradual refactoring? Feature flags?
3. **Deprecation Policy**: How long do we support old APIs?
4. **Version Numbers**: Move to 1.0.0 after Phase 2? Or wait for Phase 3?

---

## Resources

### Tools
- `ruff`: Fast Python linter (already in deps)
- `mypy`: Static type checker
- `pytest-cov`: Coverage reporting
- `ruff format`: Code formatter and Import sorter

### References
- [Python Type Hints - PEP 484](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/tags/domain%20driven%20design.html)

---

## Conclusion

Docsible has a solid foundation but needs gradual refactoring to scale. The roadmap prioritizes quick wins (type hints, logging) before larger changes (splitting files, domain models).

**Key Principle**: Make it better gradually. Don't rewrite everything at once.

**Next PR**: Add type hints to `utils/yaml.py` and `utils/git.py` (small, reviewable, immediate value).

---

*This document is a living roadmap. Update it as priorities change and lessons are learned.*
