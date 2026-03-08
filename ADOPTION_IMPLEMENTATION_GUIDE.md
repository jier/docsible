# Adoption Implementation Guide

> Derived from `SMART_PRESETS_CICD_FRIENDLY.md` · Current state: structural reorganization complete (995 tests, 0 mypy errors) · Next: user-facing adoption features

---

## Phase 1 — Immediate wins (1–2 weeks)

### 1.1 Essential 5 Default Patterns

**Goal:** Reduce cognitive load for first-time users. Five high-impact, low-false-positive patterns run by default; all others require explicit opt-in.

**Where:**
- `docsible/analyzers/patterns/analyzer.py` — `PatternAnalyzer.__init__`
- `docsible/commands/document_role/options/recommendations.py` — add `--advanced-patterns` flag

**What to build:**

1. In `docsible/analyzers/patterns/analyzer.py`, add a module-level constant and wire it into `PatternAnalyzer`:

```python
# Essential patterns — run by default (high impact, low false-positive rate)
ESSENTIAL_PATTERN_NAMES: frozenset[str] = frozenset({
    "exposed_secrets",
    "missing_no_log",
    "monolithic_main_file",
    "shell_injection_risk",
    "missing_idempotency",
})

class PatternAnalyzer:
    def __init__(
        self,
        enabled_detectors: list[type[BasePatternDetector]] | None = None,
        min_confidence: float = 0.0,
        essential_only: bool = True,   # NEW — True by default
    ):
        self.essential_only = essential_only
        ...
```

2. In `PatternAnalyzer.analyze()`, after collecting `all_suggestions`, filter when `essential_only=True`:

```python
if self.essential_only:
    all_suggestions = [
        s for s in all_suggestions
        if s.pattern in ESSENTIAL_PATTERN_NAMES
    ]
```

3. In `docsible/commands/document_role/options/recommendations.py`, add the flag alongside `--show-info` and `--recommendations-only`:

```python
f = click.option(
    "--advanced-patterns",
    "advanced_patterns",
    is_flag=True,
    default=False,
    help="Enable all 17+ pattern detectors. Default runs Essential 5 only.",
)(f)
```

4. Thread `advanced_patterns` through `RoleCommandContext` → `AnalysisConfig` (`docsible/commands/document_role/models/`) and pass `essential_only=not advanced_patterns` when constructing `PatternAnalyzer` in `docsible/analyzers/recommendations.py` (or wherever `PatternAnalyzer` is instantiated for the main flow — trace from `generate_all_recommendations` called in `role_orchestrator.py` line 73).

**Acceptance criteria:**
- `docsible document role --role ./my-role` surfaces at most 5 pattern findings covering the Essential 5 only.
- `docsible document role --role ./my-role --advanced-patterns` enables all detectors (`DuplicationDetector`, `ComplexityDetector`, `SecurityDetector`, `MaintainabilityDetector`) without filtering.
- Existing tests for `PatternAnalyzer` pass when `essential_only=False` is passed explicitly.
- New unit tests: `tests/analyzers/patterns/test_essential_filter.py` — verify filtered vs unfiltered result sets.

---

### 1.2 `--advanced-patterns` Output Label

**Goal:** Make the mode visible so users know they are in Essential-only mode and how to get more.

**Where:** `docsible/formatters/text/` — whichever formatter renders the pattern/recommendation section (the `PositiveFormatter` or `RecommendationFormatter`).

**What to build:**

When `essential_only=True`, append a footer line to the recommendations block:

```
-- Essential patterns only (5/17+). Run with --advanced-patterns for full analysis.
```

When `essential_only=False`, show:

```
-- Full pattern analysis enabled (17+ patterns).
```

Pass the mode flag from `RoleCommandContext` down to the formatter. The simplest path is a boolean field `analysis.essential_only` on `AnalysisConfig` (already a Pydantic model in `docsible/commands/document_role/models/`).

**Acceptance criteria:**
- The footer appears in both `--positive` (default) and `--neutral` output modes.
- The footer is absent when `--recommendations-only` is not requested (i.e., patterns were not run at all).

---

### 1.3 Discovery-Based Command Suggestions

**Goal:** After every zero-config run, suggest the next step the user can take. Converts a single-use tool interaction into a learning journey.

**Where:** `docsible/formatters/text/positive_formatter.py` — `PositiveFormatter` (or a new `DiscoverySuggester` class in `docsible/formatters/text/discovery.py`).

**What to build:**

Create `docsible/formatters/text/discovery.py`:

```python
class DiscoverySuggester:
    """Generates context-aware next-step suggestions after analysis."""

    def suggest(
        self,
        pattern_count: int,
        essential_only: bool,
        has_security_findings: bool,
        has_maintainability_findings: bool,
    ) -> list[str]:
        """Return 1–3 command suggestions based on analysis results."""
        suggestions: list[str] = []

        if essential_only and pattern_count > 0:
            suggestions.append(
                "docsible document role --role . --advanced-patterns"
                "  # see all patterns"
            )
        if has_security_findings:
            suggestions.append(
                "docsible analyze role --role .  # security-focused analysis"
            )
        if has_maintainability_findings:
            suggestions.append(
                "docsible init --preset=team  # configure team-wide defaults"
            )
        return suggestions[:3]  # cap at 3
```

Render in the output block under a "Next steps" heading. Hook into `RoleOrchestrator.execute()` after recommendations are displayed (around the existing recommendation rendering call).

**Acceptance criteria:**
- At least one suggestion is shown for any role that has Essential 5 findings.
- No suggestions are shown when the role is clean (no findings).
- Suggestions are suppressed when `--recommendations-only` is not the intent (i.e., do not show for documentation-only runs where pattern analysis is not the focus).

---

### 1.4 Progressive Disclosure in Markdown Output

**Goal:** Reduce visual overwhelm in generated `README.md` by collapsing the full recommendation detail under `<details>` blocks. The summary line (count + severity) is always visible.

**Where:** Jinja2 templates consumed by the readme renderer (`docsible/renderers/readme_renderer.py` and `docsible/formatters/templates/`).

**What to build:**

In the template that renders the recommendations/analysis section, wrap the detail body:

```jinja2
<details>
<summary>{{ severity_icon }} {{ severity_label }} ({{ count }})</summary>

{% for item in recommendations_by_severity %}
### {{ item.title }}
**File:** `{{ item.file }}`
**Fix:** {{ item.suggestion }}
{% endfor %}

</details>
```

Keep the health score and finding count outside the `<details>` block — always visible.

Add a `--no-collapse` CLI flag in `docsible/commands/document_role/options/output.py` for users who want flat output (e.g. CI that parses the markdown).

**Acceptance criteria:**
- Generated `README.md` for any role with findings contains `<details>` wrapping the recommendation body.
- `docsible document role --role . --no-collapse` produces flat markdown without `<details>` tags.
- Health score summary line is always outside the collapsible section.

---

### 1.5 Time-to-Value Guardrail: Cap Tier 1 Recommendations at 5

**Goal:** Enforce the Tier 1 constraint: `<5 recommendations` surfaced to the user. Prevents first-time users from being overwhelmed even if Essential 5 patterns each fire multiple findings.

**Where:** `docsible/formatters/text/recommendation_formatter.py` — `RecommendationFormatter`.

**What to build:**

Add a `max_recommendations: int | None` parameter to `RecommendationFormatter`. Default to `5` when `essential_only=True`, `None` (unlimited) when `essential_only=False`.

```python
class RecommendationFormatter:
    def format(
        self,
        recommendations: list[Recommendation],
        max_recommendations: int | None = 5,
    ) -> str:
        if max_recommendations is not None:
            recommendations = recommendations[:max_recommendations]
        ...
```

When the cap truncates results, append:

```
(Showing 5 of N findings. Run with --advanced-patterns or --show-info to see all.)
```

**Acceptance criteria:**
- A role with 12 findings shows exactly 5 in default mode with the truncation note.
- `--advanced-patterns` removes the cap.
- `--show-info` does not remove the cap on its own (it only adds INFO-level; cap is about pattern count, not severity level).

---

## Phase 2 — Interactive setup (3–8 weeks)

### 2.1 Extend `docsible init` with Security/Focus-Area Questions

**Goal:** The existing `docsible init` wizard (`docsible/commands/wizard.py`) already asks 3 questions (use-case, smart defaults, CI/CD). Extend it with focus-area and experience-level questions that map to the Essential 5 vs. full pattern set and preset settings.

**Where:** `docsible/commands/wizard.py` — `_run_wizard()` function.

**What to build:**

After the existing Step 1 (use-case → preset), add Step 2a: focus area:

```
Step 2/4: What is your primary concern?
  1. Security (exposed secrets, missing no_log, injection risks)
  2. Code quality (idempotency, monolithic files, duplication)
  3. Documentation (missing meta, examples, README coverage)
  4. Everything equally
```

And Step 2b: experience level:

```
Step 3/4: Team experience with Ansible?
  1. Beginner    — keep suggestions simple and actionable
  2. Intermediate — standard recommendations
  3. Advanced    — include all patterns and low-confidence findings
```

Map answers to preset `settings` overrides stored in `.docsible/config.yml`:

| Focus + Experience | `essential_only` default | `max_recommendations` | `min_confidence` |
|---|---|---|---|
| Security + Beginner | `True` | 3 | 0.85 |
| Security + Advanced | `False` | unlimited | 0.70 |
| Quality + any | `True` | 5 | 0.75 |
| Everything + Advanced | `False` | unlimited | 0.70 |

Store focus and experience in the generated `.docsible/config.yml` as new fields on `DocsiblePresetConfig` (`docsible/presets/models.py`).

**Acceptance criteria:**
- `docsible init` completes in under 5 minutes (4 questions max).
- Generated `.docsible/config.yml` contains `focus_area` and `experience_level` fields.
- `docsible document role --role .` reads those fields and adjusts `essential_only` and `max_recommendations` accordingly without any extra CLI flags.

---

### 2.2 Smart Context Detection in `SmartDefaultsEngine`

**Goal:** Auto-infer security vs. quality focus from role content. Runs as a third detector in `SmartDefaultsEngine` and adds a `focus` field to `DecisionContext` without requiring any user config.

**Where:**
- `docsible/defaults/engine.py` — `SmartDefaultsEngine.__init__`
- New file: `docsible/defaults/detectors/content.py` — `ContentFocusDetector`

**What to build:**

`ContentFocusDetector` scans role files for signals:

```python
class ContentFocusDetector(Detector):
    """Infers documentation/analysis focus from role content."""

    SECURITY_MODULE_SIGNALS = {"hashivault", "community.hashi_vault", "ansible.builtin.uri"}
    SECURITY_VAR_SIGNALS = {"password", "secret", "token", "api_key", "credential"}
    COMPLEXITY_THRESHOLD = 25  # tasks count above which → refactoring focus

    def detect(self, role_path: Path) -> DetectionResult:
        findings: dict[str, Any] = {"focus": "balanced"}

        has_vault_modules = self._scan_for_modules(role_path, self.SECURITY_MODULE_SIGNALS)
        has_secret_vars = self._scan_vars_for_signals(role_path, self.SECURITY_VAR_SIGNALS)
        task_count = self._count_tasks(role_path)

        if has_vault_modules or has_secret_vars:
            findings["focus"] = "security"
        elif task_count >= self.COMPLEXITY_THRESHOLD:
            findings["focus"] = "refactoring"

        return DetectionResult(
            detector_name="ContentFocusDetector",
            findings=findings,
            confidence=0.8,
        )
```

Add `focus: str = "balanced"` to `DecisionContext` (`docsible/defaults/decisions/base.py`).

Add a new `FocusDecisionRule` in `docsible/defaults/decisions/focus_rule.py` that sets `essential_only=False` and adjusts `min_confidence` when `focus == "security"`.

Register both in `SmartDefaultsEngine.__init__` alongside the existing `ComplexityDetector` and `StructureDetector`.

**Acceptance criteria:**
- A role containing `community.hashi_vault` references produces `focus: security` in `DecisionContext` without any user config.
- A role with 30+ tasks produces `focus: refactoring`.
- A plain role produces `focus: balanced` and runs Essential 5.
- Unit tests in `tests/defaults/detectors/test_content_focus.py`.

---

### 2.3 `--preview-advanced` Flag

**Goal:** Let users see what additional findings exist beyond the Essential 5, without committing to the full output in every run. Enables the phased onboarding flow from the strategy doc.

**Where:** `docsible/commands/document_role/options/recommendations.py` — add alongside `--advanced-patterns`.

**What to build:**

```python
f = click.option(
    "--preview-advanced",
    "preview_advanced",
    is_flag=True,
    default=False,
    help=(
        "Show a preview of additional findings from all 17+ patterns, "
        "alongside the Essential 5. Does not change default behavior."
    ),
)(f)
```

When `preview_advanced=True`:
1. Run the full pattern set (`essential_only=False`).
2. Split results into Essential 5 findings and "additional" findings.
3. Display Essential 5 findings normally.
4. Display additional findings in a separate collapsed section:

```
--- Advanced Pattern Preview (N additional findings) ---
Run with --advanced-patterns to include these in every analysis.
<details>
<summary>Additional findings</summary>
...
</details>
```

**Acceptance criteria:**
- `--preview-advanced` output contains two distinct sections.
- Running without the flag is unaffected.
- `--preview-advanced` and `--advanced-patterns` together behave identically to `--advanced-patterns` alone (no duplication).

---

### 2.4 `docsible setup --optimize-for <focus>`

**Goal:** Let users who have already run `docsible document role` and seen the discovery suggestions jump directly to a focus-specific config, without answering all wizard questions.

**Where:** `docsible/commands/wizard.py` — new `setup` subcommand, or extend existing `init` with `--optimize-for` option.

**What to build:**

Add `--optimize-for` to `wizard_init`:

```python
@click.option(
    "--optimize-for",
    "optimize_for",
    type=click.Choice(["security", "quality", "documentation", "migration"]),
    default=None,
    help="Skip wizard and generate config optimized for this focus area.",
)
```

When provided, skip all interactive questions and generate `.docsible/config.yml` with the appropriate `focus_area` and preset settings (see mapping table in 2.1).

Register this as the canonical follow-up to discovery suggestions (item 1.3 above suggests `docsible init --preset=team`; this extends that to `docsible init --optimize-for security`).

**Acceptance criteria:**
- `docsible init --optimize-for security` creates `.docsible/config.yml` with `focus_area: security`, `experience_level: intermediate` (default), and appropriate `essential_only`/`min_confidence` values.
- The command completes with zero interactive prompts.

---

### 2.5 Preset Settings: Add `essential_only`, `max_recommendations`, `focus_area`

**Goal:** The existing `PresetRegistry` (`docsible/presets/registry.py`) does not include pattern-filtering settings. Add them so presets carry the full Tier 1/2/3 experience.

**Where:**
- `docsible/presets/models.py` — `Preset.settings` dict (or add typed fields)
- `docsible/presets/registry.py` — update each of the 4 presets

**What to build:**

Add to each preset's `settings`:

| Preset | `essential_only` | `max_recommendations` | `focus_area` |
|---|---|---|---|
| `personal` | `True` | `3` | `"balanced"` |
| `team` | `True` | `5` | `"balanced"` |
| `enterprise` | `False` | `None` | `"quality"` |
| `consultant` | `False` | `None` | `"balanced"` |

Thread `essential_only` and `max_recommendations` from the resolved preset settings into `AnalysisConfig` via `resolve_settings()` in `docsible/presets/config_manager.py`.

**Acceptance criteria:**
- `docsible init --preset=enterprise` followed by `docsible document role --role .` runs all 17+ patterns.
- `docsible init --preset=personal` followed by `docsible document role --role .` runs Essential 5 and caps at 3 recommendations.
- A CLI flag (`--advanced-patterns`) still overrides the preset setting.

---

## Phase 3 — Enterprise (2–6 months)

### 3.1 Custom Pattern Libraries

**Goal:** Allow organizations to ship their own pattern detectors alongside the built-in ones. Enables organizational security standards and bespoke anti-pattern detection.

**Where:**
- `docsible/analyzers/patterns/base.py` — `BasePatternDetector` (already exists, serves as the interface)
- `docsible/analyzers/patterns/analyzer.py` — `PatternAnalyzer` loader
- New: `docsible/analyzers/patterns/loader.py` — `PatternLoader`

**What to build:**

`PatternLoader` discovers external detectors from a configured directory:

```python
class PatternLoader:
    """Loads custom pattern detectors from a user-specified directory."""

    def load_from_directory(self, path: Path) -> list[type[BasePatternDetector]]:
        """Import all *_detector.py files and return classes
        that subclass BasePatternDetector."""
        ...
```

Add a `--custom-patterns` CLI option to `docsible/commands/document_role/options/recommendations.py`:

```python
f = click.option(
    "--custom-patterns",
    "custom_patterns_dir",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Directory of custom pattern detector modules to load.",
)(f)
```

Pass the loaded classes to `PatternAnalyzer(enabled_detectors=builtin + custom)`.

**Acceptance criteria:**
- A user-written `my_pattern_detector.py` in `./security-patterns/` that subclasses `BasePatternDetector` is discovered and run when `--custom-patterns ./security-patterns/` is passed.
- Invalid modules (import errors) log a warning and are skipped; the run does not fail.
- Unit tests in `tests/analyzers/patterns/test_pattern_loader.py`.

---

### 3.2 Multi-Project Governance (`docsible scan collection`)

**Goal:** Enable scanning an entire role library or Ansible collection in one command, producing a unified report. Required for enterprise CI/CD pipelines.

**Where:** New command group `docsible/commands/scan/` following the pattern of `docsible/commands/document/` and `docsible/commands/analyze/`.

**What to build:**

```
docsible scan collection --collection ./roles/ --output report.json
```

- Walk all subdirectories that look like Ansible roles (contain `tasks/` or `meta/`).
- Run `PatternAnalyzer` on each with the configured preset settings.
- Aggregate findings into a unified `CollectionReport` model.
- Output JSON (default) or Markdown summary.

New files:
- `docsible/commands/scan/__init__.py`
- `docsible/commands/scan/collection.py` — Click command
- `docsible/models/collection_report.py` — `CollectionReport` Pydantic model

Register in `docsible/cli.py`.

**Acceptance criteria:**
- `docsible scan collection --collection ./roles/` exits 0 and prints per-role health scores.
- `--output report.json` writes valid JSON.
- Exit code 1 if any CRITICAL finding is found (for CI gating).

---

### 3.3 CI/CD Exit Code Gating

**Goal:** Return a non-zero exit code when findings exceed a configurable severity threshold. Required for blocking merges in CI pipelines.

**Where:** `docsible/commands/document_role/core_orchestrated.py` — end of `doc_the_role()`, and `docsible/commands/document_role/orchestrators/role_orchestrator.py` — after recommendation display.

**What to build:**

Add `--fail-on` CLI option in `docsible/commands/document_role/options/recommendations.py`:

```python
f = click.option(
    "--fail-on",
    "fail_on",
    type=click.Choice(["critical", "warning", "any", "none"]),
    default="none",
    help="Exit with code 1 if findings at or above this severity exist.",
)(f)
```

After recommendations are rendered in `RoleOrchestrator.execute()`:

```python
if context.analysis.fail_on != "none":
    if _should_fail(recommendations, context.analysis.fail_on):
        raise SystemExit(1)
```

**Acceptance criteria:**
- `docsible document role --role . --fail-on critical` exits 1 when a CRITICAL finding exists.
- `--fail-on none` (default) always exits 0 regardless of findings.
- Works with `docsible scan collection` as well (phase 3.2).

---

### 3.4 Enterprise Reporting: Structured JSON Output

**Goal:** Emit machine-readable output alongside (or instead of) human-readable output, for integration with SIEM, dashboards, and audit systems.

**Where:** New `docsible/formatters/json/report_formatter.py` + `--output-format` flag.

**What to build:**

Add to `docsible/commands/document_role/options/output.py`:

```python
f = click.option(
    "--output-format",
    "output_format",
    type=click.Choice(["text", "json", "sarif"]),
    default="text",
    help="Output format for analysis results.",
)(f)
```

`sarif` format enables direct integration with GitHub Advanced Security and similar platforms.

`report_formatter.py` maps `PatternAnalysisReport` → SARIF 2.1.0 JSON.

**Acceptance criteria:**
- `docsible analyze role --role . --output-format json` prints valid JSON to stdout.
- `--output-format sarif` produces SARIF 2.1.0 that GitHub's code scanning can ingest.
- `--output-format text` is unchanged from current behavior.

---

## Implementation order rationale

**Phase 1 first** because it delivers measurable adoption improvement with minimal risk: all changes are additive (new constant, new flag, new formatter parameter). No existing behavior changes unless the user passes new flags. The `PatternAnalyzer` already accepts `enabled_detectors` and `min_confidence` — `essential_only` is a filter on top of the existing pipeline.

**1.1 before 1.3**: The discovery suggestions (1.3) reference the `--advanced-patterns` flag, so that flag must exist first.

**1.5 (cap at 5) before Phase 2**: The Tier 1 experience guarantee must hold before advertising the wizard, otherwise `docsible init` does not deliver a better experience than the baseline.

**Phase 2 order**: 2.1 (extend wizard) depends on 2.5 (preset settings fields) existing first. 2.2 (smart context detection) is independent of the wizard and can be built in parallel. 2.3 (`--preview-advanced`) requires 1.1 and 1.2.

**Phase 3 last**: Custom patterns (3.1), collection scanning (3.2), and SARIF output (3.4) have no Phase 1/2 dependencies but require stable public interfaces — wait until Phase 2 settles.

---

## Success metrics

| Tier | Metric | Target |
|---|---|---|
| Tier 1 (zero-config) | Time from `pip install docsible` to first useful output | < 30 seconds |
| Tier 1 | Config files required | 0 |
| Tier 1 | Recommendations shown per run | <= 5 |
| Tier 1 | Patterns run by default | 5 (Essential 5) |
| Tier 2 (guided) | `docsible init` completion time | < 5 minutes |
| Tier 2 | Value increase vs. Tier 1 | 3x more findings surfaced |
| Tier 2 | False positive rate | < 10% |
| Tier 3 (enterprise) | Patterns available | 17+ built-in + custom |
| Tier 3 | CI/CD integration | Exit code gating + SARIF output |
| Tier 3 | Role library scale | 100+ roles per scan |

---

## Key file reference

| File | Role in adoption work |
|---|---|
| `docsible/analyzers/patterns/analyzer.py` | Add `essential_only`, `ESSENTIAL_PATTERN_NAMES` |
| `docsible/analyzers/patterns/detectors/security.py` | Contains `exposed_secrets`, `missing_no_log`, `shell_injection_risk` |
| `docsible/analyzers/patterns/detectors/maintainability.py` | Contains `missing_idempotency`, `monolithic_main_file` |
| `docsible/commands/document_role/options/recommendations.py` | Add `--advanced-patterns`, `--preview-advanced`, `--fail-on` |
| `docsible/commands/document_role/options/content.py` | Add `--no-collapse` |
| `docsible/commands/document_role/options/output.py` | Add `--output-format` |
| `docsible/commands/document_role/models/` | Add `essential_only`, `max_recommendations` to `AnalysisConfig` |
| `docsible/commands/document_role/orchestrators/role_orchestrator.py` | Wire essential_only into `PatternAnalyzer` construction; add exit code logic |
| `docsible/formatters/text/recommendation_formatter.py` | Add `max_recommendations` cap |
| `docsible/formatters/text/` | Add `discovery.py` (`DiscoverySuggester`) |
| `docsible/defaults/engine.py` | Register `ContentFocusDetector` |
| `docsible/defaults/detectors/` | Add `content.py` (`ContentFocusDetector`) |
| `docsible/defaults/decisions/` | Add `focus_rule.py` (`FocusDecisionRule`) |
| `docsible/presets/registry.py` | Add `essential_only`, `max_recommendations`, `focus_area` to all 4 presets |
| `docsible/presets/models.py` | Add `focus_area`, `experience_level` fields to `DocsiblePresetConfig` |
| `docsible/commands/wizard.py` | Extend `_run_wizard()` with Steps 2a/2b; add `--optimize-for` |
