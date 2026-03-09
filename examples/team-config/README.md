# Team Configuration Example

This directory contains a sample `.docsible/config.yml` for teams. Copy `.docsible-team.yml` to `.docsible/config.yml` inside your Ansible role repository and adjust as needed.

```bash
mkdir -p .docsible
cp examples/team-config/.docsible-team.yml .docsible/config.yml
```

---

## What the Config Does

```yaml
# .docsible/config.yml (copy of .docsible-team.yml)
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

| Key | Value | Effect |
|---|---|---|
| `preset: team` | Applies the `team` preset | Enables `auto_fix`, `comments`, `validate_markdown`; disables `minimal` and `no_backup` |
| `fail_on: warning` | Exit 1 if WARNING or CRITICAL findings exist | CI pipelines fail when documentation quality is below team standard |
| `essential_only: false` | Show all severity levels | WARNING and INFO findings are both surfaced (not filtered to WARNING/CRITICAL only) |
| `max_recommendations: 10` | Cap at 10 recommendations | Prevents output from being overwhelming on large roles |
| `overrides.graph: true` | Always generate Mermaid diagrams | Overrides the `team` preset's smart-defaults behaviour for graphs |
| `overrides.hybrid: true` | Use hybrid template | Mixes manual narrative sections with auto-generated technical content |
| `ci_cd.strict_validation: true` | Strict markdown validation | `docsible validate role` exits 1 if WARNING/CRITICAL markdown issues are found |

---

## Creating the Config with `docsible init`

Instead of copying this file, you can generate an equivalent config non-interactively:

```bash
docsible init --preset=team
```

This creates `.docsible/config.yml` with just `preset: team`. Then edit it to add `fail_on`, `overrides`, and other fields as needed.

Or use the interactive wizard for guided setup:

```bash
docsible init
# Step 1: choose "Team collaboration"
# Step 2: configure smart defaults
# Step 3: optionally generate a CI/CD workflow file
```

---

## How Presets, Config, and CLI Flags Interact

Settings are resolved in this order (later sources override earlier ones):

```
preset defaults  →  .docsible/config.yml  →  CLI flags
```

**Example:** the `team` preset sets `fail_on: warning`. If you add `fail_on: critical` to `.docsible/config.yml`, the config wins. If you then pass `--fail-on none` on the command line, the CLI flag wins.

```bash
# Uses fail_on from .docsible/config.yml (warning)
docsible validate role --role .

# Overrides config — uses critical
docsible validate role --role . --fail-on critical

# Overrides config — never fails
docsible validate role --role . --fail-on none
```

The same precedence applies to every setting: `generate_graph`, `max_recommendations`, `strict_validation`, etc.

---

## Committing the Config for All Team Members

Once you have a config that works for your team, commit it:

```bash
git add .docsible/config.yml
git commit -m "chore: add docsible team configuration"
```

Every developer and CI runner that clones the repository will automatically use the same preset, `fail_on` threshold, and overrides — no flags required.

---

## Preset Comparison

| Preset | `fail_on` | `essential_only` | `max_recommendations` | Best for |
|---|---|---|---|---|
| `personal` | none | true | 5 | Solo projects, quick docs |
| `team` | warning | false | 10 | Team repos, PR quality gates |
| `enterprise` | critical | false | unlimited | Production, compliance audits |
| `consultant` | warning | false | 15 | Client deliverables, detailed reports |

See [CONFIGURATION.md](../../CONFIGURATION.md) for the full preset settings table and all CLI flag documentation.
