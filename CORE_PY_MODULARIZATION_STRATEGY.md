# core.py Modularization Strategy

**Date:** 2025-12-21
**File:** `docsible/commands/document_role/core.py`
**Current State:** 666 lines, 30+ parameters in main function
**Risk Level:** 🔴 VERY HIGH (main CLI entry point)

---

## Current State Analysis

### File Metrics
- **Total Lines:** 666 lines
- **Main Function:** `doc_the_role()` - 237 lines (lines 430-666)
- **Helper Function:** `build_role_info()` - 182 lines (lines 122-303)
- **Dry Run Display:** `_display_dry_run_summary()` - 124 lines (lines 306-428)
- **Extract Dependencies:** `extract_playbook_role_dependencies()` - 81 lines (lines 39-119)
- **Parameters in `doc_the_role()`:** 30 parameters (UNMAINTAINABLE!)

### Critical Issues

1. **Parameter Explosion** (🔴 CRITICAL)
   - 30 parameters in `doc_the_role()` function
   - No parameter grouping or context objects
   - Makes function signature impossible to maintain

2. **Mixed Responsibilities** (🔴 CRITICAL)
   - Orchestration + validation + rendering + analysis all in one function
   - No clear separation between CLI handling and business logic

3. **Deep Builder Function** (🟡 HIGH)
   - `build_role_info()` at 182 lines with multiple responsibilities
   - Handles file discovery, YAML loading, task extraction, handler extraction
   - Should be broken into focused builders

4. **Monolithic Dry-Run Display** (🟢 MEDIUM)
   - 124 lines of formatting logic
   - Should use a formatter class

---

## Modularization Strategy

### Phase 1: Parameter Object Pattern (Following RenderContext Pattern)

Create Pydantic models to group related parameters:

```python
# docsible/commands/document_role/models/role_command_context.py
from pydantic import BaseModel, Field
from pathlib import Path

class PathConfig(BaseModel):
    """File and directory paths."""
    role_path: Path = Field(..., description="Path to role directory")
    collection_path: Path | None = Field(None, description="Path to collection")
    playbook: Path | None = Field(None, description="Playbook file path")
    output: str = Field("README.md", description="Output filename")

class TemplateConfig(BaseModel):
    """Template configuration."""
    hybrid: bool = Field(False, description="Use hybrid template")
    md_role_template: Path | None = Field(None, description="Custom role template")
    md_collection_template: Path | None = Field(None, description="Custom collection template")

class ContentFlags(BaseModel):
    """Content inclusion/exclusion flags."""
    no_vars: bool = Field(False, description="Skip variables")
    no_tasks: bool = Field(False, description="Skip tasks")
    no_diagrams: bool = Field(False, description="Skip diagrams")
    simplify_diagrams: bool = Field(False, description="Simplify diagrams")
    no_examples: bool = Field(False, description="Skip examples")
    no_metadata: bool = Field(False, description="Skip metadata")
    no_handlers: bool = Field(False, description="Skip handlers")
    minimal: bool = Field(False, description="Minimal mode")

class DiagramConfig(BaseModel):
    """Diagram generation configuration."""
    generate_graph: bool = Field(False, description="Generate Mermaid diagrams")
    show_dependencies: bool = Field(False, description="Show dependency matrix")

class AnalysisConfig(BaseModel):
    """Analysis and reporting configuration."""
    complexity_report: bool = Field(False, description="Show complexity report")
    include_complexity: bool = Field(False, description="Include in README")
    simplification_report: bool = Field(False, description="Show simplification suggestions")
    analyze_only: bool = Field(False, description="Analyze without generating docs")

class ProcessingConfig(BaseModel):
    """Processing options."""
    comments: bool = Field(False, description="Extract task comments")
    task_line: bool = Field(False, description="Extract line numbers")
    no_backup: bool = Field(False, description="Skip backup creation")
    no_docsible: bool = Field(False, description="Skip .docsible file")
    dry_run: bool = Field(False, description="Preview without writing")
    append: bool = Field(False, description="Append to existing README")

class ValidationConfig(BaseModel):
    """Markdown validation configuration."""
    validate_markdown: bool = Field(False, description="Validate markdown")
    auto_fix: bool = Field(False, description="Auto-fix issues")
    strict_validation: bool = Field(False, description="Fail on validation errors")

class RepositoryConfig(BaseModel):
    """Repository information."""
    repository_url: str | None = Field(None, description="Repository URL or 'detect'")
    repo_type: str | None = Field(None, description="Repository type")
    repo_branch: str | None = Field(None, description="Repository branch")

class RoleCommandContext(BaseModel):
    """Complete context for role documentation command.

    Reduces 30 parameters to 1 structured object.
    """
    paths: PathConfig
    template: TemplateConfig
    content: ContentFlags
    diagrams: DiagramConfig
    analysis: AnalysisConfig
    processing: ProcessingConfig
    validation: ValidationConfig
    repository: RepositoryConfig

    class ConfigDict:
        frozen = False
        validate_assignment = True
```

**Impact:** 30 parameters → 1 parameter

---

### Phase 2: Extract Builder Classes

Following the processor pattern from renderers:

```python
# docsible/commands/document_role/builders/role_info_builder.py
class RoleInfoBuilder:
    """Builds role information dictionary from role directory."""

    def __init__(self, project_structure: ProjectStructure):
        self.project_structure = project_structure

    def build(
        self,
        role_path: Path,
        playbook_content: str | None,
        config: ProcessingConfig,
        repository: RepositoryConfig,
    ) -> dict:
        """Build complete role information."""
        role_name = role_path.name

        # Delegate to specialized builders
        meta_info = self._build_meta_info(role_path, config.no_docsible)
        vars_info = self._build_vars_info(role_path)
        tasks_info = self._build_tasks_info(role_path, config)
        handlers_info = self._build_handlers_info(role_path)
        playbook_info = self._build_playbook_info(
            playbook_content, role_name, config.generate_graph
        )
        repo_info = self._build_repository_info(role_path, repository)

        return {
            "name": role_name,
            **meta_info,
            **vars_info,
            **tasks_info,
            **handlers_info,
            **playbook_info,
            **repo_info,
        }

    def _build_meta_info(self, role_path: Path, no_docsible: bool) -> dict:
        """Extract metadata and docsible info."""
        ...

    def _build_vars_info(self, role_path: Path) -> dict:
        """Extract defaults and vars."""
        ...

    def _build_tasks_info(self, role_path: Path, config: ProcessingConfig) -> dict:
        """Extract and process tasks."""
        ...

    def _build_handlers_info(self, role_path: Path) -> dict:
        """Extract handlers."""
        ...

    def _build_playbook_info(
        self, content: str | None, role_name: str, generate_graph: bool
    ) -> dict:
        """Build playbook information."""
        ...

    def _build_repository_info(
        self, role_path: Path, repository: RepositoryConfig
    ) -> dict:
        """Detect or use provided repository information."""
        ...
```

**Files Created:**
- `builders/role_info_builder.py` (~150 lines)
- `builders/task_extractor.py` (~80 lines)
- `builders/handler_extractor.py` (~60 lines)

---

### Phase 3: Extract Orchestrator Classes

```python
# docsible/commands/document_role/orchestrators/role_orchestrator.py
class RoleOrchestrator:
    """Orchestrates role documentation generation process."""

    def __init__(self, context: RoleCommandContext):
        self.context = context
        self.role_info_builder = RoleInfoBuilder(...)
        self.diagram_generator = DiagramGenerator(...)
        self.renderer = ReadmeRenderer(...)

    def execute(self) -> None:
        """Execute the documentation generation workflow."""
        # Step 1: Validate paths
        role_path = self._validate_paths()

        # Step 2: Load playbook
        playbook_content = self._load_playbook()

        # Step 3: Build role info
        role_info = self.role_info_builder.build(
            role_path, playbook_content, self.context.processing, self.context.repository
        )

        # Step 4: Analyze complexity
        analysis_report = self._analyze_complexity(role_info)

        # Step 5: Handle analyze-only mode
        if self.context.analysis.analyze_only:
            self._display_analysis_and_exit(analysis_report, role_info)
            return

        # Step 6: Generate diagrams
        diagrams = self._generate_diagrams(role_info, analysis_report, playbook_content)

        # Step 7: Generate dependency matrix
        dependencies = self._generate_dependencies(role_info, analysis_report)

        # Step 8: Handle dry-run mode
        if self.context.processing.dry_run:
            self._display_dry_run(role_info, analysis_report, diagrams, dependencies)
            return

        # Step 9: Render documentation
        self._render_documentation(role_info, analysis_report, diagrams, dependencies)
```

**Files Created:**
- `orchestrators/role_orchestrator.py` (~120 lines)
- `orchestrators/collection_orchestrator.py` (~100 lines)

---

### Phase 4: Extract Formatters/Displayers

```python
# docsible/commands/document_role/formatters/dry_run_formatter.py
class DryRunFormatter:
    """Formats dry-run output for display."""

    def format_summary(
        self,
        role_info: dict,
        role_path: Path,
        analysis_report,
        diagrams: dict,
        dependencies: dict,
        config: RoleCommandContext,
    ) -> str:
        """Generate formatted dry-run summary."""
        sections = [
            self._format_header(),
            self._format_role_info(role_info, role_path),
            self._format_complexity(analysis_report),
            self._format_variables(role_info),
            self._format_handlers(role_info),
            self._format_diagrams(diagrams),
            self._format_files(role_info, role_path, config),
            self._format_flags(config),
            self._format_footer(),
        ]
        return "\n".join(sections)

    def _format_header(self) -> str: ...
    def _format_role_info(self, role_info: dict, role_path: Path) -> str: ...
    # ... other formatting methods
```

**Files Created:**
- `formatters/dry_run_formatter.py` (~80 lines)
- `formatters/analysis_formatter.py` (~60 lines)

---

### Phase 5: Simplify Main Function

```python
# docsible/commands/document_role/core.py (AFTER refactoring)

def doc_the_role(**kwargs):
    """Generate documentation for an Ansible role.

    This is a thin wrapper that converts Click parameters to RoleCommandContext
    and delegates to the orchestrator.
    """
    # Step 1: Build context from parameters
    context = RoleCommandContext(
        paths=PathConfig(
            role_path=kwargs['role_path'],
            collection_path=kwargs['collection_path'],
            playbook=kwargs['playbook'],
            output=kwargs['output'],
        ),
        template=TemplateConfig(
            hybrid=kwargs['hybrid'],
            md_role_template=kwargs['md_role_template'],
            md_collection_template=kwargs['md_collection_template'],
        ),
        content=ContentFlags(
            no_vars=kwargs['no_vars'],
            no_tasks=kwargs['no_tasks'],
            # ... all content flags
        ),
        # ... all other config groups
    )

    # Step 2: Handle collection vs role
    if context.paths.collection_path:
        orchestrator = CollectionOrchestrator(context)
    else:
        orchestrator = RoleOrchestrator(context)

    # Step 3: Execute
    try:
        orchestrator.execute()
    except CollectionNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise
```

**Result:** Main function reduced from 237 lines to ~50 lines

---

## Proposed File Structure

```
docsible/commands/document_role/
├── __init__.py
├── core.py (50 lines - thin CLI wrapper)
│
├── models/
│   ├── __init__.py
│   └── role_command_context.py (200 lines - Pydantic models)
│
├── builders/
│   ├── __init__.py
│   ├── role_info_builder.py (150 lines)
│   ├── task_extractor.py (80 lines)
│   └── handler_extractor.py (60 lines)
│
├── orchestrators/
│   ├── __init__.py
│   ├── role_orchestrator.py (120 lines)
│   └── collection_orchestrator.py (100 lines)
│
├── formatters/
│   ├── __init__.py
│   ├── dry_run_formatter.py (80 lines)
│   └── analysis_formatter.py (60 lines)
│
└── helpers.py (keep existing helper functions)
```

---

## Migration Path

### Step 1: Create Models (Low Risk)
1. Create `models/role_command_context.py`
2. Add comprehensive unit tests
3. **No changes to existing code yet**

### Step 2: Create Builders (Medium Risk)
1. Extract `RoleInfoBuilder` from `build_role_info()`
2. Keep old function as wrapper calling new builder
3. Add tests for builder
4. **Maintains backward compatibility**

### Step 3: Create Formatters (Low Risk)
1. Extract `DryRunFormatter` from `_display_dry_run_summary()`
2. Keep old function as wrapper
3. Add tests
4. **No breaking changes**

### Step 4: Create Orchestrators (Medium Risk)
1. Create `RoleOrchestrator` class
2. Refactor `doc_the_role()` to use orchestrator
3. **This step changes main function**
4. Comprehensive integration tests required

### Step 5: Cleanup (Low Risk)
1. Remove old wrapper functions
2. Update imports
3. Final test verification

---

## Risk Mitigation

### Testing Strategy

**Pre-Refactoring:**
1. Add 50+ integration tests covering all CLI parameter combinations
2. Test all code paths (dry-run, analyze-only, collection, role, etc.)
3. Create fixtures for common role structures

**During Refactoring:**
1. Test each extracted component in isolation
2. Maintain backward compatibility at each step
3. Run full test suite after each commit

**Post-Refactoring:**
1. Verify all 281+ existing tests still pass
2. Verify all new component tests pass
3. Manual testing of CLI commands

### Rollback Plan

Each phase is designed to be independently reversible:
- Phase 1-3: Just delete new files, no existing code changed
- Phase 4: Revert orchestrator changes, restore old main function
- Git history maintains all checkpoints

---

## Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Main function length | 237 lines | <60 lines | 75% reduction |
| Parameter count | 30 params | 1 param | 97% reduction |
| Max function length | 237 lines | <80 lines | 66% reduction |
| Nesting depth | 11 levels | <4 levels | 64% reduction |
| File count | 1 file | 15+ files | Better organization |
| Testability | Low | High | Isolated components |

---

## Estimated Effort

- **Phase 1 (Models):** 1 day
- **Phase 2 (Builders):** 2 days
- **Phase 3 (Formatters):** 1 day
- **Phase 4 (Orchestrators):** 2 days
- **Phase 5 (Cleanup):** 1 day
- **Testing & Documentation:** 1 day

**Total:** 8 days (with buffer for comprehensive testing)

---

## Comparison to Completed Refactorings

This strategy follows proven patterns from completed work:

| Pattern | Source | Applied To core.py |
|---------|--------|-------------------|
| **Parameter Object** | RenderContext (readme_renderer.py) | RoleCommandContext |
| **Processor Pattern** | TemplateProcessor, MetadataProcessor | RoleInfoBuilder, DiagramGenerator |
| **Orchestrator** | ReadmeRenderer delegates to processors | RoleOrchestrator delegates to builders |
| **Pydantic Models** | RenderContext, RenderConfig | All config models |
| **Single Responsibility** | Each validator has one focus | Each builder has one focus |

**Confidence Level:** HIGH - Following established, proven patterns

---

## Next Steps

1. Review and approve this strategy
2. Create feature branch: `refactor/core-py-modularization`
3. Start with Phase 1 (Models) - lowest risk
4. Commit after each phase completion
5. Full test verification between phases

**Ready to proceed?**
