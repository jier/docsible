# CLI UX Redesign - Gap Analysis & Implementation Plan

**Date:** 2025-12-18
**Based on:** PRODUCT_STRATEGY_ANALYSIS.md (Parts 1-3) + Current Codebase Exploration

---

## Executive Summary

### Current State vs. Desired State

| Aspect | Current (Explored) | Desired (Strategy + User Request) | Gap Size |
|--------|-------------------|-----------------------------------|----------|
| **CLI Structure** | `docsible --verbose role --option1 --option2` | `docsible <intent> [scope] [options]` | **LARGE** - Requires restructuring |
| **Entry Point** | 3 commands (role, init, check) | 5+ intents (document, analyze, validate, init, suppress) | **MEDIUM** - Add new commands |
| **Configuration** | Manual .docsible.yml creation | Interactive wizard with profiles | **LARGE** - Build wizard |
| **Defaults** | Requires config for best results | Zero-config with smart detection | **MEDIUM** - Smart defaults logic |
| **Help System** | Grouped options (emoji-based) | Context-aware, progressive disclosure | **SMALL** - Enhance existing |
| **Suppressions** | None | .docsible/suppress.yml with CLI management | **LARGE** - Build from scratch |
| **Presets** | None | 4 presets (learning, team, expert, consultant) | **LARGE** - Build from scratch |

---

## Phase 1: Intent-Based CLI Structure

### What Exists ✅

```python
# Current: docsible/cli.py
@click.group()
@click.option("--verbose", "-v", is_flag=True)
@click.version_option(version=get_version())
def cli(verbose: bool):
    """Main CLI group"""
    setup_logging(verbose)

# Commands registered:
cli.add_command(doc_the_role, name="role")
cli.add_command(init_config, name="init")
cli.add_command(check)
```

**Architecture:**
- Click framework (>=8.1.7) ✅
- Command group pattern ✅
- Modular option decorators ✅
- Custom help formatting (GroupedHelpCommand) ✅

### What's Missing ❌

1. **Intent-based command structure**
   - No `document` intent (currently just `role`)
   - No `analyze` intent
   - No `validate` intent
   - No `suppress` intent

2. **Scope parameters**
   - Currently: `docsible role` (scope is hardcoded)
   - Needed: `docsible document role|playbook|collection`

3. **Global options placement**
   - Currently: `--verbose` before command
   - Desired: Works both before and after intent

### Implementation Requirements

#### 1.1 Restructure CLI to Intent-Based

**File:** `docsible/cli.py`

**Changes Needed:**
```python
# NEW: Intent commands as subgroups
@click.group()
@click.pass_context
def document(ctx):
    """Generate documentation (auto-adapts to complexity)"""
    pass

@document.command("role")
@click.argument("path", default=".")
@add_profile_options  # NEW
@add_output_options
def document_role(path, profile, ...):
    """Document an Ansible role"""
    pass

@document.command("playbook")  # FUTURE
def document_playbook(...):
    pass

# NEW: Analyze intent
@click.group()
def analyze():
    """Show complexity analysis without documentation"""
    pass

@analyze.command("role")
def analyze_role(...):
    pass

# NEW: Validate intent
@click.group()
def validate():
    """Check documentation quality"""
    pass

# NEW: Suppress intent
@click.group()
def suppress():
    """Manage recommendation suppressions"""
    pass

# Register intents
cli.add_command(document)
cli.add_command(analyze)
cli.add_command(validate)
cli.add_command(init_config, name="init")  # Keep existing
cli.add_command(suppress)
```

**Backward Compatibility:**
```python
# Alias old 'role' command to new 'document role'
@cli.command("role", hidden=True)
def role_alias(*args, **kwargs):
    """Deprecated: Use 'docsible document role' instead"""
    click.secho("⚠️  'docsible role' is deprecated. Use 'docsible document role' instead.", fg="yellow")
    return document_role(*args, **kwargs)
```

#### 1.2 Profile/Preset Options

**New File:** `docsible/commands/document_role/options/profiles.py`

```python
from functools import wraps
import click

def add_profile_options(f):
    """Add profile-based configuration options"""
    f = click.option(
        "--profile",
        type=click.Choice(["minimal", "standard", "comprehensive", "dev"]),
        default="standard",
        help="Output profile (standard auto-detects features)"
    )(f)
    f = click.option(
        "--preset",
        type=click.Choice(["learning", "team", "expert", "consultant"]),
        help="Load preset configuration (overrides profile)"
    )(f)
    return f
```

**Estimated Effort:** 2-3 days
**Files to Create:** 1 new
**Files to Modify:** `docsible/cli.py` (major refactor)
**Tests Needed:** CLI routing, backward compatibility

---

## Phase 2: Interactive Init Wizard

### What Exists ✅

```python
# Current: docsible/commands/init_config.py
@click.command(name="init")
@click.option("--path", "-p", default=".")
@click.option("--force", "-f", is_flag=True)
def init_config(path: str, force: bool):
    """Generate example .docsible.yml configuration file"""
    config_content = create_example_config()
    # Writes static YAML template
```

**Capabilities:**
- Creates .docsible.yml with example content ✅
- Has `create_example_config()` helper ✅
- File handling with force flag ✅

### What's Missing ❌

1. **Interactive prompts** - Currently non-interactive
2. **Profile selection** - No concept of profiles
3. **Smart questions** - No adaptation to user responses
4. **suppress.yml creation** - Doesn't create suppression file
5. **Multi-file setup** - Only creates config.yml
6. **Progress indication** - No visual feedback
7. **Follow-up guidance** - No next steps shown

### Implementation Requirements

#### 2.1 Interactive Wizard with Click

**File:** `docsible/commands/init_config.py` (major refactor)

**New Dependencies:**
```toml
# pyproject.toml - Already have Click >=8.1.7
# No new deps needed - Click has built-in prompts
```

**Implementation:**
```python
from typing import Literal
import click

ProfileType = Literal["learning", "team", "expert", "consultant"]

def interactive_init(path: str) -> None:
    """Interactive setup wizard"""

    click.secho("\n┌─────────────────────────────────────────────┐", fg="cyan")
    click.secho("│  🚀 Welcome to Docsible Setup               │", fg="cyan")
    click.secho("└─────────────────────────────────────────────┘\n", fg="cyan")

    # Question 1: Profile selection
    profile = click.prompt(
        "❓ What best describes your use case?\n\n"
        "  1. 🎓 Learning       - I'm learning Ansible, need maximum guidance\n"
        "  2. 👥 Team           - Working with a team, need consistent docs\n"
        "  3. 🔧 Expert         - Experienced user, want minimal noise\n"
        "  4. 💼 Consultant     - Creating client deliverables, need polish\n\n"
        "Your choice",
        type=click.IntRange(1, 4),
        default=2
    )

    profile_map: dict[int, ProfileType] = {
        1: "learning",
        2: "team",
        3: "expert",
        4: "consultant"
    }
    selected_profile = profile_map[profile]

    # Question 2: Complexity levels
    complexity = click.prompt(
        "\n❓ What complexity levels do you typically work with?\n\n"
        "  1. Simple roles (< 20 tasks)\n"
        "  2. Medium roles (20-50 tasks)\n"
        "  3. Complex roles (50+ tasks)\n"
        "  4. Mix of all levels\n\n"
        "Your choice",
        type=click.IntRange(1, 4),
        default=4
    )

    # Question 3: Auto-detection
    auto_detect = click.confirm(
        "\n❓ Do you want Docsible to auto-detect and adapt output?",
        default=True
    )

    # Question 4: Recommendations handling
    rec_mode = click.prompt(
        "\n❓ What should happen with recommendations?\n\n"
        "  1. Show all recommendations (may include false positives)\n"
        "  2. Show recommendations, let me suppress false positives\n"
        "  3. Minimal recommendations only\n\n"
        "Your choice",
        type=click.IntRange(1, 3),
        default=2
    )

    # Generate configuration
    config = generate_profile_config(
        profile=selected_profile,
        complexity=complexity,
        auto_detect=auto_detect,
        rec_mode=rec_mode
    )

    # Create files
    config_path = Path(path) / ".docsible"
    config_path.mkdir(exist_ok=True)

    (config_path / "config.yml").write_text(config)

    if rec_mode == 2:
        (config_path / "suppress.yml").write_text(create_empty_suppress_file())

    # Success message
    click.secho("\n✅ Configuration created: .docsible/config.yml", fg="green")
    if rec_mode == 2:
        click.secho("✅ Suppression file created: .docsible/suppress.yml (empty)", fg="green")

    click.secho(f"\n📝 Your profile: {selected_profile.upper()} with AUTO-DETECTION\n", fg="cyan")

    # Next steps
    click.secho("Next steps:", fg="bright_white")
    click.echo("  • Run: docsible document role ./your-role")
    click.echo("  • Edit: .docsible/config.yml to customize")
    click.echo("  • Learn: docsible help document")

    click.secho("\n💡 Tip: Run 'docsible init --reset' to reconfigure anytime", fg="yellow")
```

#### 2.2 Profile Config Generator

**New File:** `docsible/config/profiles.py`

```python
def generate_profile_config(
    profile: ProfileType,
    complexity: int,
    auto_detect: bool,
    rec_mode: int
) -> str:
    """Generate YAML config based on wizard choices"""

    templates = {
        "learning": LEARNING_TEMPLATE,
        "team": TEAM_TEMPLATE,
        "expert": EXPERT_TEMPLATE,
        "consultant": CONSULTANT_TEMPLATE,
    }

    template = templates[profile]

    # Customize based on other answers
    if auto_detect:
        template = template.replace("AUTODETECT_PLACEHOLDER", "auto")

    # ... etc

    return template
```

**Estimated Effort:** 3-4 days
**Files to Create:** `docsible/config/profiles.py`, profile YAML templates
**Files to Modify:** `docsible/commands/init_config.py` (major refactor)
**Tests Needed:** Wizard flow, config generation, file creation

---

## Phase 3: Suppression System

### What Exists ✅

**Nothing** - Suppression system doesn't exist at all.

**Related Code:**
- Recommendation generation in `docsible/analyzers/complexity_analyzer/recommendations.py` ✅
- Can be modified to check suppressions before adding recommendations

### What's Missing ❌

1. **suppress.yml schema and parsing**
2. **Suppression matching engine**
3. **CLI commands for suppression management**
4. **Integration with recommendation generation**
5. **Validation and expiry handling**

### Implementation Requirements

#### 3.1 Suppression Schema

**New File:** `docsible/models/suppression.py`

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Literal

class Suppression(BaseModel):
    """Single suppression rule"""

    id: str = Field(description="Unique identifier for this suppression")
    pattern: str = Field(description="Pattern to match in recommendations")
    reason: str = Field(description="Why this is suppressed")
    file: str | None = Field(None, description="Specific file to suppress for")
    expires: date | None = Field(None, description="Expiration date")
    approved_by: str | None = Field(None, description="Who approved this")

class SuppressionConfig(BaseModel):
    """Complete suppression configuration"""

    version: str = "1.0"
    suppressions: list[Suppression] = Field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> "SuppressionConfig":
        """Load from .docsible/suppress.yml"""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def should_suppress(self, recommendation: str, file_path: str | None = None) -> tuple[bool, str | None]:
        """Check if recommendation should be suppressed"""
        for supp in self.suppressions:
            # Check expiry
            if supp.expires and date.today() > supp.expires:
                continue

            # Check pattern match
            if supp.pattern in recommendation:
                # Check file match if specified
                if supp.file and file_path:
                    if supp.file not in file_path:
                        continue

                return True, supp.reason

        return False, None
```

#### 3.2 Suppress CLI Commands

**New File:** `docsible/commands/suppress/__init__.py`

```python
@click.group(name="suppress")
def suppress():
    """Manage recommendation suppressions"""
    pass

@suppress.command("add")
@click.argument("pattern")
@click.option("--reason", "-r", required=True)
@click.option("--file", "-f", help="Specific file to suppress for")
@click.option("--expires", help="Expiration date (YYYY-MM-DD)")
def suppress_add(pattern: str, reason: str, file: str | None, expires: str | None):
    """Add a suppression rule"""

    config = SuppressionConfig.from_file(Path(".docsible/suppress.yml"))

    new_id = f"supp-{len(config.suppressions) + 1}"

    suppression = Suppression(
        id=new_id,
        pattern=pattern,
        reason=reason,
        file=file,
        expires=date.fromisoformat(expires) if expires else None
    )

    config.suppressions.append(suppression)
    config.to_file(Path(".docsible/suppress.yml"))

    click.secho(f"✅ Suppression added: {new_id}", fg="green")

@suppress.command("list")
def suppress_list():
    """List all suppressions"""

    config = SuppressionConfig.from_file(Path(".docsible/suppress.yml"))

    if not config.suppressions:
        click.echo("No suppressions configured")
        return

    for i, supp in enumerate(config.suppressions, 1):
        click.echo(f"{i}. {supp.id}: \"{supp.reason}\"")
        if supp.file:
            click.echo(f"   File: {supp.file}")
        if supp.expires:
            click.echo(f"   Expires: {supp.expires}")

@suppress.command("remove")
@click.argument("suppression_id")
def suppress_remove(suppression_id: str):
    """Remove a suppression"""

    config = SuppressionConfig.from_file(Path(".docsible/suppress.yml"))

    original_count = len(config.suppressions)
    config.suppressions = [s for s in config.suppressions if s.id != suppression_id]

    if len(config.suppressions) == original_count:
        click.secho(f"❌ Suppression not found: {suppression_id}", fg="red")
        return

    config.to_file(Path(".docsible/suppress.yml"))
    click.secho(f"✅ Suppression removed: {suppression_id}", fg="green")

@suppress.command("clean")
def suppress_clean():
    """Remove expired suppressions"""

    config = SuppressionConfig.from_file(Path(".docsible/suppress.yml"))

    original_count = len(config.suppressions)
    config.suppressions = [
        s for s in config.suppressions
        if not s.expires or date.today() <= s.expires
    ]

    removed = original_count - len(config.suppressions)

    if removed > 0:
        config.to_file(Path(".docsible/suppress.yml"))
        click.secho(f"✅ Removed {removed} expired suppression(s)", fg="green")
    else:
        click.echo("No expired suppressions found")
```

#### 3.3 Integration with Recommendations

**File to Modify:** `docsible/analyzers/complexity_analyzer/recommendations.py`

```python
def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    integration_points: list[IntegrationPoint],
    file_details: list[FileComplexityDetail],
    hotspots: list[ConditionalHotspot],
    inflection_points: list[InflectionPoint],
    role_info: dict[str, Any],
    repository_url: str | None = None,
    repo_type: str | None = None,
    repo_branch: str | None = None,
    suppress_config: SuppressionConfig | None = None,  # NEW
) -> list[str]:
    """Generate recommendations with suppression support"""

    recommendations = []
    suppressed = []

    # ... existing logic generates all_recommendations ...

    # NEW: Filter suppressions
    if suppress_config:
        for rec in all_recommendations:
            should_suppress, reason = suppress_config.should_suppress(rec)
            if should_suppress:
                suppressed.append((rec, reason))
            else:
                recommendations.append(rec)
    else:
        recommendations = all_recommendations

    # NEW: Show suppression summary
    if suppressed:
        click.secho(f"\n🔇 Suppressed ({len(suppressed)}):", fg="yellow")
        for rec, reason in suppressed[:3]:
            # Show first 50 chars of recommendation
            rec_preview = rec[:50] + "..." if len(rec) > 50 else rec
            click.echo(f"   • \"{rec_preview}\" - {reason}")

        if len(suppressed) > 3:
            click.echo(f"   ... and {len(suppressed) - 3} more")

    return recommendations
```

**Estimated Effort:** 4-5 days
**Files to Create:**
- `docsible/models/suppression.py`
- `docsible/commands/suppress/__init__.py`
- `docsible/commands/suppress/core.py`

**Files to Modify:**
- `docsible/cli.py` (add suppress command)
- `docsible/analyzers/complexity_analyzer/recommendations.py`
- `docsible/commands/document_role/core.py` (load suppress config)

**Tests Needed:** Suppression matching, expiry, CLI commands, integration

---

## Phase 4: Context-Aware Help

### What Exists ✅

```python
# docsible/utils/cli_helpers.py
class GroupedHelpCommand(click.Command):
    """Custom help formatter with emoji categories"""

    def format_options(self, ctx, formatter):
        # Groups options by category
        # Uses emoji prefixes
```

**Capabilities:**
- Emoji-grouped help ✅
- Custom help formatting ✅
- Category-based organization ✅

### What's Missing ❌

1. **Multi-level help** (docsible help vs docsible help document)
2. **Progressive disclosure** (basic help → detailed help)
3. **Smart typo suggestions**
4. **Examples gallery** (docsible help examples)
5. **Context-specific help** (different help for different scopes)

### Implementation Requirements

#### 4.1 Enhanced Help System

**File to Modify:** `docsible/cli.py`

```python
@cli.command("help")
@click.argument("topic", required=False)
@click.option("--all", "show_all", is_flag=True, help="Show complete reference")
def show_help(topic: str | None, show_all: bool):
    """Context-aware help system"""

    if topic is None:
        # General help - show common commands
        show_general_help(show_all)
    elif topic == "examples":
        show_examples()
    elif topic in ["document", "analyze", "validate", "suppress", "init"]:
        show_intent_help(topic)
    else:
        # Try to find close matches
        suggestions = difflib.get_close_matches(topic, VALID_TOPICS)
        if suggestions:
            click.secho(f"❌ Unknown topic: {topic}", fg="red")
            click.secho(f"\n💡 Did you mean one of these?", fg="yellow")
            for sugg in suggestions:
                click.echo(f"  {sugg}")
        else:
            click.secho(f"❌ Unknown help topic: {topic}", fg="red")
            click.echo("\nAvailable topics: document, analyze, validate, suppress, init, examples")

def show_general_help(show_all: bool):
    """Show general help"""

    if show_all:
        # Show complete reference
        # (current --help output)
        pass
    else:
        # Show condensed common commands
        click.echo("""
docsible - Complexity-aware Ansible documentation

USAGE:
  docsible <intent> [scope] [options]

COMMON COMMANDS:
  docsible init                      Interactive setup wizard
  docsible document role .           Generate documentation (auto-detects)
  docsible analyze role .            Show complexity report
  docsible validate role .           Check documentation quality
  docsible suppress add "pattern"    Suppress false positive

GETTING STARTED:
  1. Run: docsible init
  2. Then: docsible document role ./your-role

Learn more: docsible help <intent>
Examples:   docsible help examples
Full docs:  docsible help --all
        """)

def show_examples():
    """Show example gallery"""
    click.echo("""
COMMON EXAMPLES:

Basic Usage:
  docsible document role ./nginx-role
  docsible document role . --preview

Profiles:
  docsible document role . --minimal
  docsible document role . --comprehensive

Analysis:
  docsible analyze role . --json
  docsible analyze role . --format html

Suppressions:
  docsible suppress add "OS-family branching" --reason "Ubuntu-only"
  docsible suppress list
  docsible suppress remove supp-1

CI/CD Integration:
  docsible validate role . --strict
  docsible check . --quiet && echo "Docs up to date"
    """)
```

**Estimated Effort:** 2 days
**Files to Modify:** `docsible/cli.py`
**Tests Needed:** Help output validation

---

## Summary: Implementation Roadmap

### Phase 1: Intent-Based CLI (Week 1-2)
- **Effort:** 5-6 days
- **Priority:** P0 - Foundation for everything else
- **Deliverables:**
  - Restructured CLI with intents
  - Backward compatibility
  - Basic tests

### Phase 2: Interactive Init (Week 2-3)
- **Effort:** 3-4 days
- **Priority:** P0 - Critical for onboarding
- **Deliverables:**
  - Interactive wizard
  - Profile templates
  - Multi-file setup

### Phase 3: Suppression System (Week 3-4)
- **Effort:** 4-5 days
- **Priority:** P1 - High value for adoption
- **Deliverables:**
  - Suppression models
  - CLI commands
  - Integration with recommendations

### Phase 4: Enhanced Help (Week 4)
- **Effort:** 2 days
- **Priority:** P2 - Nice to have
- **Deliverables:**
  - Context-aware help
  - Examples gallery
  - Typo suggestions

---

## Total Effort Estimate

**Total:** 14-17 days (3-4 weeks)

**Recommended Approach:** Implement phases sequentially, releasing each as a minor version:
- v0.9.0: Intent-based CLI + Interactive init
- v0.9.1: Suppression system
- v0.9.2: Enhanced help + polish

---

## Cross-Reference with Strategy Document

### Tier 1 (Zero-Config) - PARTIALLY EXISTS
- ✅ Basic documentation generation exists
- ❌ Smart defaults based on auto-detection - NEEDS IMPLEMENTATION
- ❌ Severity filtering by default - NEEDS IMPLEMENTATION
- ✅ Integration detection exists

### Tier 2 (Guided Config) - MOSTLY MISSING
- ❌ Preset selection - NEEDS IMPLEMENTATION
- ❌ Interactive wizard - NEEDS IMPLEMENTATION
- ❌ Suppression support - NEEDS IMPLEMENTATION
- ✅ Format options exist

### Tier 3 (Expert Config) - FOUNDATION EXISTS
- ✅ Full configuration system exists (.docsible.yml)
- ❌ Custom patterns - FUTURE
- ❌ Advanced suppressions - NEEDS IMPLEMENTATION
- ❌ Integration hooks - FUTURE

---

## Conclusion

The current codebase provides a **solid foundation** with:
- Click framework ✅
- Modular architecture ✅
- Config system ✅
- Help formatting ✅

But requires **significant UX improvements**:
- Intent-based CLI structure (Large gap)
- Interactive wizard (Large gap)
- Suppression system (Large gap)
- Smart defaults (Medium gap)
- Enhanced help (Small gap)

**Recommendation:** Proceed with Phase 1 implementation.
