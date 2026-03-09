# Docsible Configuration Reference

This document covers all configuration options for Docsible: the `.docsible/config.yml` schema, built-in presets, all CLI flags, CI/CD integration, and team workflows.

## Table of Contents

- [Config File Schema](#config-file-schema)
- [Presets](#presets)
- [CLI Flags](#cli-flags)
  - [Path Flags](#path-flags)
  - [Output Flags](#output-flags)
  - [Content Flags](#content-flags)
  - [Visualization and Generation Flags](#visualization-and-generation-flags)
  - [Analysis and Recommendations Flags](#analysis-and-recommendations-flags)
  - [CI/CD Flags](#cicd-flags)
  - [Template Flags](#template-flags)
  - [Repository Flags](#repository-flags)
  - [Framing Flags](#framing-flags)
- [CI/CD Integration](#cicd-integration)
- [Team Workflow](#team-workflow)

---

## Config File Schema

Docsible reads `.docsible/config.yml` from the working directory (or the directory passed to `--path`). The file is created by `docsible init` and can be edited manually.

```yaml
# .docsible/config.yml

# Built-in preset to apply. One of: personal, team, enterprise, consultant.
# Preset settings are applied first; CLI flags and the fields below override them.
preset: team

# Per-key overrides that supplement or override the chosen preset.
overrides:
  graph: true
  hybrid: true

# CI/CD platform metadata written by `docsible init` when CI/CD setup is requested.
ci_cd:
  platform: github        # github | gitlab | azure
  strict_validation: true

# Analysis behavior — override preset defaults or set standalone values.
fail_on: warning          # none | info | warning | critical (default: none)
essential_only: false     # true = show only WARNING/CRITICAL findings (default varies by preset)
max_recommendations: 10   # integer or null for unlimited (default varies by preset)
```

### Field Descriptions

| Field | Type | Default | Description |
|---|---|---|---|
| `preset` | string \| null | null | Applies a built-in preset before all other settings |
| `overrides` | mapping | `{}` | Key/value pairs that override individual preset settings |
| `ci_cd` | mapping | `{}` | CI/CD metadata; `strict_validation: true` makes validate exit 1 on any WARNING/CRITICAL |
| `fail_on` | string \| null | null (preset default or `none`) | Exit threshold for CI: `none`, `info`, `warning`, or `critical` |
| `essential_only` | bool \| null | null (preset default) | When true, only WARNING and CRITICAL findings are shown |
| `max_recommendations` | int \| null | null (preset default) | Cap on displayed recommendations; null means unlimited |

CLI flags always override values from the config file, which in turn override preset defaults.

---

## Presets

Presets bundle a curated set of settings suited to common use cases. Apply a preset with `--preset` on any command, or set `preset:` in `.docsible/config.yml`.

```bash
docsible document role . --preset=personal
docsible document role . --preset=team
docsible document role . --preset=enterprise
docsible document role . --preset=consultant
```

### Preset Settings Table

| Setting | `personal` | `team` | `enterprise` | `consultant` |
|---|---|---|---|---|
| Description | Solo / learning | Team collaboration | Production / compliance | Client deliverables |
| `generate_graph` | false | smart defaults | true | true |
| `minimal` | true | — | false | false |
| `validate_markdown` | true | true | true | true |
| `strict_validation` | false | false | true | false |
| `auto_fix` | false | true | false | false |
| `no_backup` | true | false | false | false |
| `complexity_report` | false | false | true | true |
| `simplification_report` | false | false | true | true |
| `show_dependencies` | false | smart defaults | true | true |
| `positive_framing` | true | true | true | true |
| `comments` | false | true | true | true |
| `task_line` | false | false | true | true |
| `include_complexity` | false | false | true | true |
| `fail_on` | none | warning | critical | warning |
| `essential_only` | true | false | false | false |
| `max_recommendations` | 5 | 10 | unlimited | 15 |

"smart defaults" means the setting is left unset in the preset and auto-adjusted based on role complexity at runtime.

Individual flags passed on the command line always override preset defaults.

---

## CLI Flags

### Path Flags

| Flag | Short | Description |
|---|---|---|
| `--role TEXT` | `-r` | Path to the Ansible role directory |
| `--collection TEXT` | `-c` | Path to the Ansible collection directory |
| `--playbook TEXT` | `-p` | Path to the playbook file |

### Output Flags

| Flag | Short | Default | Description |
|---|---|---|---|
| `--output TEXT` | `-o` | `README.md` | Output file name |
| `--no-backup` | `-nob` | off | Do not back up the existing README before overwriting |
| `--append` | `-a` | off | Append to the existing README instead of replacing it |
| `--no-docsible` | `-nod` | off | Do not generate `.docsible` metadata file |
| `--dry-run` | — | off | Preview output without writing any files |
| `--validate / --no-validate` | — | on | Validate markdown formatting before writing |
| `--auto-fix` | — | off | Automatically fix common markdown formatting issues |
| `--strict-validation` | — | off | Exit 1 if markdown validation errors are found (fixed — previously a no-op in validate mode) |

### Content Flags

| Flag | Description |
|---|---|
| `--no-vars` | Hide variable documentation (defaults, vars, argument_specs) |
| `--no-tasks` | Hide task lists and task details |
| `--no-diagrams` | Hide all Mermaid diagrams |
| `--no-examples` | Hide example playbook sections |
| `--no-metadata` | Hide role metadata, author, and license |
| `--no-handlers` | Hide handlers section |
| `--minimal` | Enable all `--no-*` flags; generate the smallest possible README |
| `--include-complexity` | Add a complexity analysis section to the README |

### Visualization and Generation Flags

| Flag | Short | Description |
|---|---|---|
| `--graph` | `-g` | Generate Mermaid diagrams for role visualization |
| `--comments` | `-com` | Extract and include inline task comments |
| `--task-line` | `-tl` | Include source file line numbers for each task |
| `--simplify-diagrams` | — | Show only high-level diagrams; hide detailed flowcharts |
| `--complexity-report` | — | Include complexity analysis in documentation |
| `--simplification-report` | — | Include pattern analysis with simplification suggestions |
| `--show-dependencies` | — | Generate task dependency matrix table |
| `--analyze-only` | — | Show complexity analysis without generating documentation |

### Analysis and Recommendations Flags

These flags control how findings (INFO / WARNING / CRITICAL) are collected and displayed.

| Flag | Default | Description |
|---|---|---|
| `--recommendations-only` | off | Show recommendations without generating documentation |
| `--show-info` | off | Show INFO-level recommendations (hidden by default) |
| `--advanced-patterns` | off | Show all findings including INFO-level; removes the default 5-recommendation cap |
| `--output-format [text\|json]` | `text` | Output format for findings; `json` emits machine-readable JSON |

#### `--advanced-patterns` behaviour

Without this flag: only WARNING and CRITICAL findings are shown, capped at 5.

With this flag: all findings including INFO are shown with no cap.

```bash
# Default — at most 5 WARNING/CRITICAL findings
docsible document role --role .

# Advanced — all findings, no cap
docsible document role --role . --advanced-patterns
```

#### `--output-format json` schema

```json
{
  "role": "my-role",
  "findings": [
    {
      "severity": "WARNING",
      "message": "No example playbook found",
      "category": "documentation"
    }
  ],
  "summary": {
    "total": 3,
    "critical": 0,
    "warning": 2,
    "info": 1
  },
  "truncated": false
}
```

```bash
docsible analyze role --role . --output-format json
docsible analyze role --role . --output-format json | jq '.summary'
```

### CI/CD Flags

| Flag | Default | Description |
|---|---|---|
| `--fail-on [none\|info\|warning\|critical]` | `none` | Exit with code 1 if findings at or above this severity exist |

#### `--fail-on` exit codes

| Value | Exit 1 when... |
|---|---|
| `none` | Never (always exits 0) |
| `info` | Any INFO, WARNING, or CRITICAL finding exists |
| `warning` | Any WARNING or CRITICAL finding exists |
| `critical` | Any CRITICAL finding exists |

```bash
# Fail only on critical issues (recommended for most CI pipelines)
docsible validate role --role . --fail-on critical

# Fail on warnings or worse (stricter; recommended for team preset)
docsible validate role --role . --fail-on warning

# Never fail (default; useful for documentation-only jobs)
docsible validate role --role . --fail-on none
```

#### `--strict-validation` (fixed)

`--strict-validation` in `validate` mode now correctly exits 1 when WARNING or CRITICAL findings are present. In previous versions this flag was a no-op when used with `docsible validate role`.

```bash
docsible validate role --role . --strict-validation
```

### Template Flags

| Flag | Short | Description |
|---|---|---|
| `--md-role-template TEXT` | `-rtpl`, `-tpl` | Path to a custom role Markdown template |
| `--md-collection-template TEXT` | `-ctpl` | Path to a custom collection Markdown template |
| `--hybrid` | — | Use hybrid template (manual + auto-generated sections) |

### Repository Flags

| Flag | Short | Default | Description |
|---|---|---|---|
| `--repository-url TEXT` | `-ru` | `detect` | Repository base URL for standalone roles |
| `--repo-type TEXT` | `-rt` | — | Repository type: `github`, `gitlab`, `gitea`, etc. |
| `--repo-branch TEXT` | `-rb` | — | Repository branch name (e.g., `main`) |

### Framing Flags

| Flag | Default | Description |
|---|---|---|
| `--positive / --neutral` | positive | Use positive/actionable output framing |
| `--help-full` | — | Show all available options and advanced settings |
| `--preset [personal\|team\|enterprise\|consultant]` | — | Apply a built-in preset |

---

## CI/CD Integration

### Quick Start

```bash
# Fail the pipeline if CRITICAL findings exist
docsible validate role --role . --fail-on critical

# Fail the pipeline if WARNING or CRITICAL findings exist
docsible validate role --role . --fail-on warning

# Generate machine-readable output for downstream processing
docsible analyze role --role . --output-format json
```

### GitHub Actions

```yaml
- name: Validate role documentation
  run: docsible validate role --role . --fail-on critical

- name: Generate documentation
  run: docsible document role --role . --no-backup
  if: github.ref == 'refs/heads/main'
```

See `examples/ci_pipeline/github-actions.yml` for a complete workflow.

### GitLab CI

```yaml
docsible:check:
  stage: test
  image: python:3.12
  script:
    - pip install docsible
    - docsible validate role --role . --fail-on warning
```

See `examples/ci_pipeline/gitlab-ci.yml` for a complete pipeline.

### Pre-commit Hook

```yaml
- id: docsible-validate
  name: Validate Ansible role documentation
  language: system
  entry: docsible validate role --role . --fail-on critical
  pass_filenames: false
  types: [yaml]
```

See `examples/ci_pipeline/pre-commit-config.yaml` for the full hook configuration.

### Choosing a `--fail-on` Level

| Scenario | Recommended level |
|---|---|
| Catch only blocking errors | `critical` |
| Enforce team quality standards | `warning` |
| Enforce all recommendations | `info` |
| Documentation-only (never fail) | `none` |

---

## Team Workflow

### 1. Initialize the project

```bash
# Interactive wizard — picks a preset, optionally generates CI/CD config
docsible init

# Non-interactive — apply a preset directly
docsible init --preset=team
```

This creates `.docsible/config.yml` in the current directory.

### 2. Edit the config for your team

```yaml
# .docsible/config.yml
preset: team
fail_on: warning
essential_only: false
max_recommendations: 10
overrides:
  graph: true
  hybrid: true
ci_cd:
  strict_validation: true
```

### 3. Commit the config to the repository

```bash
git add .docsible/config.yml
git commit -m "chore: add docsible team configuration"
```

All team members and CI runners will now use the same preset and analysis thresholds automatically, without having to pass flags on every invocation.

### 4. Override per-run as needed

CLI flags always take precedence over the config file:

```bash
# Temporarily use enterprise strictness on this run
docsible document role --role . --preset=enterprise

# Check without failing (ignore fail_on from config)
docsible validate role --role . --fail-on none
```

See `examples/team-config/` for a ready-to-use team configuration example.

---

## Adding a New `scan` Subcommand

The `scan` command group lives in `docsible/commands/scan/` and follows the same pattern used by `analyze` and `document`.

### Module structure

```
docsible/commands/scan/
├── __init__.py            # scan_group (Click group), imports and attaches subcommands
├── collection.py          # `scan collection` subcommand implementation
├── models/
│   └── scan_result.py     # RoleResult, ScanCollectionResult dataclasses
└── formatters/
    ├── text.py            # Human-readable table output
    └── json.py            # Machine-readable JSON output
```

### Steps to add a new subcommand (e.g. `scan role`)

1. **Create the subcommand file** — add `docsible/commands/scan/role.py` with a Click command decorated with `@scan_group.command()`.
2. **Extend the models** if the new subcommand returns a different result shape — add or extend dataclasses in `models/scan_result.py`.
3. **Add formatters** — add `text` and `json` formatter functions in the `formatters/` directory, or extend the existing ones.
4. **Register the subcommand** — import the new command in `docsible/commands/scan/__init__.py` so Click picks it up when `scan_group` is loaded.
5. **Register `scan_group` in the CLI** — `docsible/cli.py` already attaches `scan_group` to the root CLI; no changes needed there for new subcommands.

Follow the same `--fail-on` / `--output-format` / `--preset` / `--dry-run` conventions used by `scan collection` to keep the interface consistent across the command group.
