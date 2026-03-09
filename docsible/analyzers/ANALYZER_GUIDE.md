# Analyzer System Guide

This directory contains four analysis subsystems. Use this guide to choose the right one.

## Quick Reference

| Subsystem | Question it answers | Input | Output |
|---|---|---|---|
| `concerns/` | "What is this file **for**?" | Single task file (flat list) | `ConcernMatch` — classification label + confidence |
| `patterns/` | "What is **wrong** with this role?" | Full `role_info` dict | `SimplificationSuggestion` list + health score |
| `complexity_analyzer/phase.py` | "Is this file a **pipeline**?" | Single task file | `PhaseDetectionResult` — ordering analysis |
| `complexity_analyzer/` | "How **complex** is this role?" | Full `role_info` dict | `ComplexityReport` — metrics + category + recommendations |

## When to Use Each

### Use `concerns/` when you need a label
...classifying a task file's domain (package installation, service management, etc.)
to display or use for file naming suggestions.

### Use `patterns/` when you need actionable diagnostics
...finding anti-patterns in a full role to report as recommendations with severity,
impact, and suggested fixes.

The `patterns/detectors/maintainability.py` detector currently implements the following checks:
`missing_idempotency`, `monolithic_main_file`, `magic_values`, `missing_check_mode`,
`missing_failed_when`, `variable_shadowing`, and `unnamed_tasks`.
`unnamed_tasks` flags tasks with no `name:` field (INFO, fires when 3+ unnamed tasks are found);
it skips structural tasks (`include_tasks`, `import_tasks`, `include_role`, `import_role`,
`meta`, `block`/`rescue`/`always`).

### Use `complexity_analyzer/phase.py` when you need pipeline awareness
...detecting whether a task file forms a coherent lifecycle pipeline
(SETUP → INSTALL → CONFIGURE → DEPLOY → VERIFY) to avoid incorrectly flagging it
as a "god file".

### Use `complexity_analyzer/` for the full picture
...running all role-level analysis including metrics, hotspots, inflection points,
and optional pattern analysis.

## Shared Vocabulary

Module name groupings (which modules belong to "package management", "service management", etc.)
are defined once in `shared/module_taxonomy.py` and imported by all subsystems.
If you add support for a new Ansible module, update `module_taxonomy.py` — it propagates everywhere.

## Unified Entry Point

If you need concern + phase + patterns in one call:

```python
from docsible.analyzers.task_analysis_facade import analyze_task_file

analysis = analyze_task_file(tasks, role_info=role_info)
# analysis.concern  → ConcernMatch
# analysis.phase    → PhaseDetectionResult
# analysis.patterns → PatternAnalysisReport (only if role_info provided)
```
