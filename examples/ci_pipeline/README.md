# CI/CD Pipeline Examples

This directory contains ready-to-use CI/CD configuration files for integrating Docsible into common platforms.

## Files

| File | Platform | Description |
|---|---|---|
| `github-actions.yml` | GitHub Actions | Validate on every PR; generate docs on main |
| `gitlab-ci.yml` | GitLab CI | Two-stage pipeline: test and deploy |
| `azure-devops-pipeline.yml` | Azure DevOps | Two-stage pipeline: validate then generate |
| `pre-commit-config.yaml` | pre-commit | Local hook that runs before every commit |

---

## GitHub Actions (`github-actions.yml`)

The workflow runs on every push to `main` and every pull request:

1. **Validate** — runs `docsible validate role --role . --fail-on critical` on all branches. The job fails (exit 1) only if CRITICAL findings are present, so pull requests with quality warnings are still mergeable but blockers are caught.
2. **Generate** — runs `docsible document role --role . --no-backup` only on the `main` branch, so the README is regenerated after every merge.

**Usage:** copy `github-actions.yml` to `.github/workflows/docsible.yml` in your role repository.

```bash
cp examples/ci_pipeline/github-actions.yml .github/workflows/docsible.yml
```

---

## GitLab CI (`gitlab-ci.yml`)

The pipeline has two jobs:

- `docsible:check` (test stage) — validates documentation on all branches using `--fail-on warning`. This is stricter than the GitHub Actions example: any WARNING or CRITICAL finding fails the pipeline. Suitable for teams enforcing a minimum documentation quality bar.
- `docsible:document` (deploy stage) — regenerates the README on `main` using the `team` preset.

**Usage:** copy to `.gitlab-ci.yml` (or include as a component):

```bash
cp examples/ci_pipeline/gitlab-ci.yml .gitlab-ci.yml
```

If you already have a `.gitlab-ci.yml`, merge the two job blocks into your existing file.

---

## Azure DevOps (`azure-devops-pipeline.yml`)

The pipeline has two stages:

- **Validate** — runs `docsible validate role --role . --fail-on critical` on all branches and pull requests. The stage fails only on CRITICAL findings.
- **Document** — runs `docsible document role --role . --no-backup` on `main` after validation passes and publishes `README.md` as a pipeline artifact.

**Usage:** copy to `azure-pipelines.yml` at your repository root:

```bash
cp examples/ci_pipeline/azure-devops-pipeline.yml azure-pipelines.yml
```

If you already have an `azure-pipelines.yml`, add the two stages (or their jobs) to your existing pipeline. The `dependsOn: Validate` + `condition` guard on the Document stage ensure documentation is only regenerated when the quality gate passes.

---

## Pre-commit Hook (`pre-commit-config.yaml`)

The hook runs `docsible validate role --role . --fail-on critical` before every `git commit` that touches YAML files. This prevents CRITICAL documentation issues from ever being committed.

**Usage:**

```bash
# Install pre-commit if not already installed
pip install pre-commit

# Copy or merge the hook config
cp examples/ci_pipeline/pre-commit-config.yaml .pre-commit-config.yaml

# Install the hook
pre-commit install
```

After installation, the hook runs automatically on `git commit`.

---

## Choosing `--fail-on critical` vs `--fail-on warning`

| Level | Fails when... | Recommended for... |
|---|---|---|
| `--fail-on critical` | CRITICAL findings exist | Most CI pipelines; permissive, catches only blockers |
| `--fail-on warning` | WARNING or CRITICAL findings exist | Teams enforcing quality standards (team/enterprise preset) |
| `--fail-on info` | Any finding exists | Very strict pipelines; not recommended for most teams |
| `--fail-on none` | Never | Documentation-generation-only jobs |

The `team` preset sets `fail_on: warning` by default. The `enterprise` preset sets `fail_on: critical`. Both can be overridden via the `--fail-on` flag or the `fail_on` key in `.docsible/config.yml`.

---

## Committing `.docsible/config.yml` for Team-Wide Settings

Rather than specifying `--fail-on`, `--preset`, or other flags on every CI invocation, commit `.docsible/config.yml` to your repository:

```bash
docsible init --preset=team
git add .docsible/config.yml
git commit -m "chore: add docsible team configuration"
```

Once the config is committed, all CI jobs and team members automatically use the same preset and analysis thresholds. The CI commands in this directory become simpler:

```yaml
# With .docsible/config.yml committed (preset: team, fail_on: warning):
- run: docsible validate role --role .
# No --fail-on needed — picked up from config
```

CLI flags still override the config file when you need a one-off change:

```bash
docsible validate role --role . --fail-on none  # ignore config's fail_on for this run
```

See `examples/team-config/` for a complete example of a team configuration file.
