# Docsible Folder Reorganization Report

**Date:** 2026-03-07
**Branch:** To be implemented on a dedicated branch
**Scope:** Full codebase — 204 Python files across 56 directories

---

## Overview

This report documents structural issues discovered during a full codebase audit and provides concrete reorganization suggestions ranked by priority. The goal is cleaner module boundaries, elimination of duplicate logic, and better discoverability.

---

## Current Structure

| Module | Description |
|--------|-------------|
| `analyzers/` | Complexity analysis, pattern detection, recommendations, concerns, phase detection |
| `commands/` | CLI command implementations (analyze, check, document, document_role, suppress, validate, wizard) |
| `config/` | YAML configuration files (severity_rules.yml) |
| `defaults/` | Smart defaults system (engine, builder, detectors, decisions) |
| `diagram_builders/` | Mermaid diagram generation (flowchart, sequence, formatters) |
| `formatters/` | Output formatting (positive_formatter, recommendation_formatter, message_transformer, templates) |
| `help/` | Progressive help system (formatters, guides, tips) |
| `models/` | Domain models (config, role, severity, recommendation, enhancement, suppression) |
| `presets/` | Configuration presets (registry, resolver, config_manager, models) |
| `renderers/` | Documentation rendering (readme_renderer, processors, models, tag_manager) |
| `repositories/` | Repository abstraction (role_repository) |
| `suppression/` | Suppression system (engine, store, id_gen) |
| `templates/` | Jinja2 templates (role/, collection/) |
| `utils/` | 24+ utility files (cache, git, yaml, mermaid, diagrams, console, validators, etc.) |
| `validators/` | Documentation validation (doc_validator, markdown_validator, clarity, truth, value, maintenance, scoring) |

---

## Issues Found

### A — Duplicate Complexity Analysis Systems (HIGH)

Two separate systems independently measure role complexity (task count, variables, handlers, dependencies) using different categorization schemes:

- `defaults/detectors/complexity.py` — used by SmartDefaultsEngine (Category enum: SIMPLE/MEDIUM/COMPLEX/ENTERPRISE)
- `analyzers/complexity_analyzer/` — detailed role analysis (ComplexityCategory)

Both calculate overlapping metrics. No single source of truth.

**Proposed fix:** Merge both into `analyzers/complexity/`. Update SmartDefaultsEngine imports. Delete `defaults/detectors/`. Bundle with item I (phase_detector).

**Impact:** ~50 imports affected.

---

### B — Diagram Generation Scattered Across 8 Locations (HIGH)

Diagram logic lives in:
- `diagram_builders/` — base, flowchart, sequence
- `utils/mermaid/` — core, formatting, pagination, task_extraction
- `utils/mermaid_sequence/` — playbook, role, sanitization
- `utils/architecture_diagram.py`
- `utils/integration_diagram.py`
- `utils/network_topology.py`
- `utils/dependency_matrix.py`

No clear hierarchy, no single entry point.

**Proposed fix:** Create top-level `diagrams/` module:

```
diagrams/
├── __init__.py
├── base.py
├── types/
│   ├── flowchart.py
│   ├── sequence.py
│   ├── architecture.py
│   ├── integration.py
│   ├── network_topology.py
│   └── dependency_matrix.py
├── mermaid/              (from utils/mermaid/)
│   ├── core.py
│   ├── formatting.py
│   ├── pagination.py
│   └── task_extraction.py
└── sequence/             (from utils/mermaid_sequence/)
    ├── playbook.py
    ├── role.py
    └── sanitization.py
```

Delete `diagram_builders/`, `utils/mermaid/`, `utils/mermaid_sequence/`, and the four `utils/*.py` diagram files.

**Impact:** ~80 imports affected.

---

### C — `document_role/` Has Two Parallel Implementations (HIGH)

`core.py` and `core_orchestrated.py` both implement `doc_the_role()`, toggled via `DOCSIBLE_USE_ORCHESTRATOR` environment variable. `role_info_builder.py` is 15K lines. Options are split across 9 separate files.

**Proposed fix:** Consolidate into concern-based subdirectories, remove the feature flag, make orchestrator the only path:

```
commands/document_role/
├── __init__.py          (CLI entry)
├── execution/           (from core.py + core_orchestrated.py)
├── building/            (refactored from role_info_builder.py)
├── output/              (from formatters/dry_run_formatter.py + rendering)
└── config/              (options consolidated from 9 modules → 1 file, + models)
```

**Impact:** ~100 imports, 1186 lines of core code restructured. Very high effort.

---

### D — `utils/` Is a Dumping Ground (MEDIUM)

24+ files with mixed concerns: YAML handling, mermaid generation, project structure detection, git, error handling, cache, and meta-code checkers (`check_for_error_handling_in_file.py`, `check_for_missing_type_hints_signatures.py`).

**Proposed fix:**
- Extract diagram files → `diagrams/` (bundled with B)
- Create `utils/template/` for template filters and loader
- Move meta-code checkers to `utils/validators/`
- Move root-level `template_loader.py` into `utils/template/loader.py`

**Impact:** ~40 imports affected.

---

### E — Formatters Scattered Across 3 Locations (MEDIUM)

- `formatters/` — positive_formatter, recommendation_formatter, message_transformer
- `commands/document_role/formatters/` — dry_run_formatter
- `help/formatters/` — brief_help, contextual_help

**Proposed fix:** Centralize under `formatters/`:

```
formatters/
├── text/
│   ├── positive.py
│   ├── recommendation.py
│   ├── message.py
│   └── dry_run.py        (from commands/document_role/formatters/)
├── help/                 (from help/formatters/)
│   ├── brief.py
│   └── contextual.py
└── templates/            (keep)
```

Delete `commands/document_role/formatters/` and `help/formatters/`.

**Impact:** ~50 imports affected.

---

### F — `validators/` Should Be Renamed `validation/` (MEDIUM)

`validators/` is a validation subsystem, not a collection of individual validator objects. Renaming to `validation/` better reflects its role.

**Impact:** ~20 imports affected. Low effort.

---

### G — `help/` Naming Inconsistency (LOW)

All other modules use plural names (`commands/`, `models/`, `validators/`, `formatters/`). `help/` is singular.

**Proposed fix:** Rename to `helpers/`. Or, since its formatters will move to `formatters/help/` (item E), only `guides/` and `tips/` content remains — consider restructuring as `help/guides/` and `help/tips/` under a renamed module.

**Impact:** Very low effort, ~10 imports.

---

### H — Deprecated `docsible role` Command Has No Clear Home (LOW)

The legacy `docsible role --role PATH` command still exists with deprecation warnings printed to stderr. It's mixed in with `commands/document_role/__init__.py`.

**Proposed fix:** Move to `commands/legacy/` to make the deprecation boundary explicit.

**Impact:** Low effort.

---

### I — `analyzers/phase_detector/` Duplicates Defaults Logic (LOW)

`analyzers/phase_detector/` provides phase detection that overlaps with `defaults/detectors/`. Should be merged into `analyzers/complexity/` as part of item A.

**Impact:** Low effort, bundled with A.

---

### J — Models Defined in 6 Separate Locations (LOW)

Data models are spread across:
- `models/` — core models
- `commands/document_role/models/` — role_command_context
- `defaults/config.py` — DocumentationConfig
- `presets/models.py` — Preset, DocsiblePresetConfig
- `renderers/models/` — render context
- `validators/models.py` — validation models

**Assessment:** Each set is domain-specific enough to stay colocated with its feature. Low priority — mainly needs documentation of the pattern rather than a structural change.

---

## Priority Summary

| Priority | Item | Effort | Imports Affected |
|----------|------|--------|-----------------|
| HIGH | A — Consolidate complexity analysis | High | ~50 |
| HIGH | B — Consolidate diagram generation | High | ~80 |
| HIGH | C — Refactor document_role dual implementation | Very High | ~100 |
| MEDIUM | D — Clean up utils/ | Medium | ~40 |
| MEDIUM | E — Centralize formatters | Medium | ~50 |
| MEDIUM | F — Rename validators/ → validation/ | Low | ~20 |
| LOW | G — Rename help/ → helpers/ | Very Low | ~10 |
| LOW | H — Move deprecated command to commands/legacy/ | Low | ~5 |
| LOW | I — Merge phase_detector/ into complexity/ | Low | bundled with A |
| LOW | J — Document model colocation pattern | Very Low | 0 |

---

## Naming Inconsistencies

| Current | Suggested | Reason |
|---------|-----------|--------|
| `help/` | `helpers/` | Plural consistency with other modules |
| `repositories/` | `repository/` | Only one file — singular fits |
| `suppression/` | `suppressions/` | Plural consistency |
| `validators/` | `validation/` | It's a subsystem, not a collection of objects |
| `diagram_builders/` + `utils/mermaid/` | `diagrams/` | Consolidate into one module |
| `defaults/` | _(delete, merge into `analyzers/complexity/`)_ | Better describes actual purpose |

---

## Recommended Implementation Order

Implement on a dedicated branch (e.g. `jier-folder-reorganisation`):

1. **Phase 1** — B (diagrams) + E (formatters) + F (rename validators): well-bounded, testable, medium effort
2. **Phase 2** — A + I (complexity consolidation): higher effort, requires test updates
3. **Phase 3** — D (utils cleanup): depends on Phase 1 (diagrams already moved)
4. **Phase 4** — C (document_role refactor): largest effort, do last after architecture is stable
5. **Phase 5** — G, H (naming, legacy cleanup): quick wins at the end

After each phase: run full test suite (`python -m pytest -q`) and mypy to verify no regressions.

---

**Total estimated effort:** 80–120 developer-hours over 3–4 weeks for full reorganization.
