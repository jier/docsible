# Strategic Planning: Docsible Future Features

This document analyzes four strategic questions about Docsible's future direction, with feasibility assessments based on the current codebase architecture.

---

## Question 1: Documentation Drift Prevention

### Problem Statement
**Question:** How do we keep the README generated up to date to avoid documentation drift besides backup? Is it even valuable?

### Current State Analysis

**What We Have:**
- `--no-backup` flag to skip README backup (default: creates backup)
- `--append` flag to append instead of replace
- One-time generation model: run docsible → generates README
- No tracking of when documentation was last generated
- No detection of role/playbook changes since last generation

**Documentation Drift Scenarios:**
1. **New tasks added** → README still shows old task count/diagrams
2. **Variables changed** → README variable table outdated
3. **Dependencies updated** → Meta information stale
4. **Handlers modified** → Handler documentation incorrect

### Value Assessment: **HIGH VALUE** ✅

**Why it matters:**
- Outdated docs are worse than no docs (misleading)
- Teams rely on README for onboarding/reference
- Stale complexity analysis gives wrong architectural guidance
- Incorrect variable documentation causes deployment failures

### Proposed Solutions

#### **Solution 1A: Git Hook Integration** (Recommended - Short Term)
**Feasibility:** ⭐⭐⭐⭐⭐ Very High

**Implementation:**
```bash
# .git/hooks/pre-commit
#!/bin/bash
# Auto-regenerate docs when role files change

CHANGED_FILES=$(git diff --cached --name-only)

if echo "$CHANGED_FILES" | grep -qE "(defaults|vars|tasks|handlers|meta)/.*\.ya?ml$"; then
    echo "📝 Ansible files changed - regenerating documentation..."
    docsible role --role . --no-backup --graph --complexity-report
    git add README.md
fi
```

**Advantages:**
- ✅ Automatic updates on commit
- ✅ No code changes needed in Docsible
- ✅ User can customize when to trigger
- ✅ Works with existing workflow

**Disadvantages:**
- ❌ Requires user setup (not automatic)
- ❌ Can slow down commits for large roles
- ❌ Skipped if using `--no-verify`

**Docsible Enhancement:**
Add `docsible init-hook` command to install git hooks automatically:

```python
# New command: docsible/commands/init_hook.py
@click.command()
@click.option("--hook-type", type=click.Choice(["pre-commit", "post-commit"]))
def init_hook(hook_type):
    """Install git hooks to auto-regenerate documentation."""
    # Generate hook script
    # Install to .git/hooks/
    # Make executable
```

---

#### **Solution 1B: CI/CD Integration** (Recommended - Medium Term)
**Feasibility:** ⭐⭐⭐⭐⭐ Very High

**GitHub Actions Example:**
```yaml
# .github/workflows/update-docs.yml
name: Update Documentation
on:
  push:
    paths:
      - 'defaults/**'
      - 'vars/**'
      - 'tasks/**'
      - 'handlers/**'
      - 'meta/**'

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Docsible
        run: pip install docsible
      - name: Regenerate Documentation
        run: docsible role --role . --graph --complexity-report --no-backup
      - name: Check for changes
        id: verify-changed-files
        run: |
          git diff --quiet README.md || echo "changed=true" >> $GITHUB_OUTPUT
      - name: Commit updated docs
        if: steps.verify-changed-files.outputs.changed == 'true'
        run: |
          git config user.name "docsible-bot"
          git config user.email "bot@docsible.io"
          git add README.md
          git commit -m "docs: auto-update README from role changes"
          git push
```

**Advantages:**
- ✅ Fully automated
- ✅ Runs in CI environment
- ✅ Creates audit trail (git commits)
- ✅ Can run comprehensive checks/tests

**Disadvantages:**
- ❌ Requires CI/CD setup
- ❌ Extra commit in git history
- ❌ Delay between change and doc update

---

#### **Solution 1C: Watch Mode** (Future - Long Term)
**Feasibility:** ⭐⭐⭐ Medium (Requires new code)

**Implementation:**
```bash
# New feature: watch mode
docsible role --role . --watch --graph

# Output:
# 🔍 Watching /path/to/role for changes...
# ✓ Documentation up to date
#
# [File changed: tasks/main.yml]
# ⚡ Regenerating documentation...
# ✓ Updated README.md
```

**Technical Approach:**
```python
# docsible/commands/watch.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RoleFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(('.yml', '.yaml')):
            if any(dir in event.src_path for dir in ['tasks', 'defaults', 'vars', 'handlers', 'meta']):
                regenerate_documentation()
```

**Dependencies:**
- `watchdog` library for filesystem monitoring
- Debouncing logic (don't regenerate on every keystroke)
- Optional: LiveReload for browser preview

**Advantages:**
- ✅ Real-time updates during development
- ✅ Great developer experience
- ✅ Can integrate with IDE

**Disadvantages:**
- ❌ Requires daemon/background process
- ❌ New dependency (watchdog)
- ❌ Complexity in managing watch state

---

#### **Solution 1D: Metadata Tracking** (Complementary to all solutions)
**Feasibility:** ⭐⭐⭐⭐⭐ Very High

**Track generation metadata in README:**
```markdown
<!-- DOCSIBLE METADATA
generated_at: 2025-12-11T10:30:00Z
docsible_version: 0.8.0
role_hash: a3f5c9d8e1b2...  (hash of all role files)
-->
```

**Add check command:**
```bash
docsible check --role .

# Output:
# ⚠️  Documentation is OUTDATED
#
# Last generated: 2 weeks ago
# Role files modified: 5 files changed since last generation
#
# Run: docsible role --role . --no-backup
```

**Implementation:**
```python
# Add to readme_renderer.py
def add_generation_metadata(role_path: Path) -> str:
    """Generate metadata comment block."""
    role_hash = compute_role_hash(role_path)
    return f"""<!-- DOCSIBLE METADATA
generated_at: {datetime.utcnow().isoformat()}Z
docsible_version: {__version__}
role_hash: {role_hash}
-->"""

def compute_role_hash(role_path: Path) -> str:
    """Hash all role YAML files to detect changes."""
    import hashlib
    hash_obj = hashlib.sha256()
    for pattern in ['defaults/**/*.y*ml', 'vars/**/*.y*ml', 'tasks/**/*.y*ml']:
        for file in sorted(role_path.glob(pattern)):
            hash_obj.update(file.read_bytes())
    return hash_obj.hexdigest()[:16]
```

---

### Recommendation: **Hybrid Approach**

**Phase 1 (Immediate - 1 week):**
1. Add metadata tracking to generated README
2. Implement `docsible check` command
3. Create `docsible init-hook` for git hook installation

**Phase 2 (Short term - 2-4 weeks):**
4. Document CI/CD integration patterns in docs
5. Provide template GitHub Actions/GitLab CI configs
6. Add `--check-drift` flag that exits 1 if docs outdated (for CI)

**Phase 3 (Future - 3+ months):**
7. Consider watch mode for interactive development
8. Explore IDE plugins (VS Code extension)

---

## Question 2: Large Mermaid Diagram Export

### Problem Statement
**Question:** For mermaid diagrams that are too big, should we offer the option to save diagrams as SVG/PNG so the user can view easily?

### Current State Analysis

**What We Have:**
- Mermaid diagrams embedded in markdown as code blocks
- Rendered by GitHub/GitLab when viewing README
- No size limits or diagram complexity checks
- Complex roles (100+ tasks) create huge diagrams

**Problems with Large Diagrams:**
1. **Rendering fails** on GitHub (timeout or too complex)
2. **Hard to read** (zooming doesn't work in markdown)
3. **Slow page load** for large README files
4. **No offline viewing** (requires markdown renderer with Mermaid)

### Value Assessment: **MEDIUM-HIGH VALUE** ✅

**Why it matters:**
- Large diagrams are currently unusable (fail to render)
- Complex roles need visualization the most
- SVG/PNG can be zoomed, panned, and printed
- Portable across all platforms

### Proposed Solutions

#### **Solution 2A: Mermaid CLI Integration** (Recommended)
**Feasibility:** ⭐⭐⭐⭐ High

**Implementation:**
```bash
# Install mermaid CLI (one-time setup)
npm install -g @mermaid-js/mermaid-cli

# New docsible flag
docsible role --role . --export-diagrams --diagram-format svg

# Output:
# ✓ Generated diagrams/sequence_diagram.svg
# ✓ Generated diagrams/architecture_diagram.svg
# ✓ Generated diagrams/state_diagram.svg
# ✓ Updated README.md with diagram references
```

**Technical Approach:**
```python
# docsible/utils/diagram_export.py
import subprocess
from pathlib import Path

def export_mermaid_to_svg(mermaid_code: str, output_path: Path) -> bool:
    """Export Mermaid diagram to SVG using mermaid-cli."""
    try:
        # Write mermaid code to temp file
        temp_mmd = output_path.with_suffix('.mmd')
        temp_mmd.write_text(mermaid_code)

        # Run mermaid-cli
        subprocess.run(
            ['mmdc', '-i', str(temp_mmd), '-o', str(output_path), '-b', 'transparent'],
            check=True,
            timeout=30
        )

        temp_mmd.unlink()  # Clean up
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def should_export_diagram(diagram_code: str) -> bool:
    """Determine if diagram should be exported based on complexity."""
    # Heuristics for "too large"
    line_count = len(diagram_code.split('\n'))
    node_count = diagram_code.count('-->') + diagram_code.count('---')

    return line_count > 100 or node_count > 50
```

**README Template Update:**
```jinja2
{% if export_diagrams and architecture_diagram_svg %}
## Architecture Diagram

![Architecture Diagram](diagrams/architecture.svg)

<details>
<summary>View Mermaid Source</summary>

```mermaid
{{ architecture_diagram }}
```
</details>
{% else %}
```mermaid
{{ architecture_diagram }}
```
{% endif %}
```

**Advantages:**
- ✅ Standard tooling (Mermaid CLI)
- ✅ High quality SVG output
- ✅ Works offline
- ✅ Can fall back to inline Mermaid if export fails

**Disadvantages:**
- ❌ Requires Node.js/npm dependency
- ❌ Additional setup step for users
- ❌ Slower generation (external process)

---

#### **Solution 2B: Cloud Rendering Services** (Alternative)
**Feasibility:** ⭐⭐⭐ Medium

**Use mermaid.ink or kroki.io:**
```markdown
## Architecture Diagram

![Architecture](https://mermaid.ink/img/base64encodeddiagram)
```

**Advantages:**
- ✅ No local dependencies
- ✅ Always available
- ✅ Simple implementation

**Disadvantages:**
- ❌ Requires internet connection
- ❌ Privacy concerns (sends diagram to 3rd party)
- ❌ Link rot if service dies
- ❌ Slower page loads (external image)

---

#### **Solution 2C: Diagram Pagination** (Complementary)
**Feasibility:** ⭐⭐⭐⭐ High

**Split large diagrams into multiple smaller diagrams:**

```python
def split_large_sequence_diagram(tasks: List[Dict], max_tasks_per_diagram: int = 20):
    """Split large sequence diagram into phases."""
    diagrams = []
    for i in range(0, len(tasks), max_tasks_per_diagram):
        chunk = tasks[i:i + max_tasks_per_diagram]
        diagram = generate_sequence_diagram(
            chunk,
            title=f"Task Flow - Part {i//max_tasks_per_diagram + 1}"
        )
        diagrams.append(diagram)
    return diagrams
```

**README Output:**
```markdown
## Task Execution Flow

### Phase 1: Installation (Tasks 1-20)
```mermaid
...
```

### Phase 2: Configuration (Tasks 21-40)
```mermaid
...
```
```

---

### Recommendation: **Multi-Pronged Approach**

**Immediate (Priority 1):**
1. Implement diagram complexity detection
2. Add automatic pagination for large diagrams (>50 nodes)
3. Add warning message for diagrams that may not render

**Short Term (Priority 2):**
4. Add `--export-diagrams` flag with Mermaid CLI integration
5. Make it optional (graceful fallback if CLI not available)
6. Create `diagrams/` directory for exported SVG/PNG files
7. Update README template to use `<img>` tags for exported diagrams

**Long Term (Priority 3):**
8. Consider interactive diagrams (HTML with pan/zoom)
9. Explore mermaid-live integration for editing

**Configuration:**
```yaml
# .docsible.yml
diagram_export:
  enabled: true
  format: svg  # or png
  max_inline_complexity: 50  # nodes
  directory: diagrams
  fallback_to_inline: true
```

---

## Question 3: Simplification Suggestions

### Problem Statement
**Question:** Are we able, after detecting complexity, to provide besides simple feedback how a role/playbook can be simplified to achieve the same result? Or is it with the current codebase a long stretch?

### Current State Analysis

**What We Have:**
- **Complexity Analyzer** (`analyzers/complexity_analyzer.py`)
  - Detects: task count, conditionals, includes, integrations
  - Categories: SIMPLE, MEDIUM, COMPLEX
  - Generic recommendations (e.g., "Consider splitting role")

- **Existing Recommendations** (from `complexity_analyzer.py:266-321`):
  ```python
  if category == ComplexityCategory.COMPLEX:
      recommendations.append("Consider splitting into smaller, focused roles")
  if metrics.conditional_percentage > 50:
      recommendations.append("High conditional complexity - consider using role composition")
  ```

**What We DON'T Have:**
- Specific, actionable refactoring suggestions
- Code smell detection (duplicated tasks, complex conditionals)
- Anti-pattern identification
- Task grouping/factoring analysis

### Value Assessment: **VERY HIGH VALUE** ⭐⭐⭐⭐⭐

**Why it matters:**
- **Educational:** Teaches best practices
- **Maintainability:** Helps teams improve code quality
- **Onboarding:** Shows newcomers "the right way"
- **Refactoring:** Provides concrete action items

### Feasibility Assessment: **MEDIUM** ⭐⭐⭐

**Current Codebase Readiness:**
- ✅ Already parses all role files
- ✅ Has complexity metrics
- ✅ Has task analysis infrastructure
- ✅ Template system for output
- ❌ No pattern recognition engine
- ❌ No task similarity analysis
- ❌ No refactoring suggestion framework

### Proposed Solutions

#### **Solution 3A: Pattern-Based Analysis** (Recommended - Short Term)
**Feasibility:** ⭐⭐⭐⭐ High

**Detect common anti-patterns:**

```python
# docsible/analyzers/pattern_analyzer.py

@dataclass
class SimplificationSuggestion:
    """Suggestion for simplifying a role."""
    pattern: str  # e.g., "duplicated_tasks"
    severity: str  # "info", "warning", "critical"
    description: str
    example: str  # Code example
    suggestion: str  # How to fix
    affected_files: List[str]
    impact: str  # "Reduces X tasks by Y%"

class PatternAnalyzer:
    """Detects anti-patterns and suggests simplifications."""

    def analyze_duplicated_tasks(self, role_info: Dict) -> List[SimplificationSuggestion]:
        """Find duplicated or near-duplicate tasks."""
        suggestions = []
        tasks = self._flatten_tasks(role_info)

        # Group by module
        by_module = defaultdict(list)
        for task in tasks:
            by_module[task.get('module')].append(task)

        # Detect repetitive package installations
        if 'apt' in by_module and len(by_module['apt']) > 5:
            suggestions.append(SimplificationSuggestion(
                pattern="repeated_package_install",
                severity="warning",
                description=f"Found {len(by_module['apt'])} separate apt tasks",
                example=self._show_task_snippet(by_module['apt'][:2]),
                suggestion="Combine into single task with loop:\n"
                           "- name: Install packages\n"
                           "  apt:\n"
                           "    name: '{{ item }}'\n"
                           "  loop:\n"
                           "    - pkg1\n"
                           "    - pkg2",
                affected_files=[task.get('file') for task in by_module['apt']],
                impact=f"Reduces {len(by_module['apt'])} tasks to 1 task (-{len(by_module['apt'])-1} tasks)"
            ))

        return suggestions

    def analyze_complex_conditionals(self, role_info: Dict) -> List[SimplificationSuggestion]:
        """Find overly complex when conditions."""
        suggestions = []

        for task_file in role_info.get('tasks', []):
            for task in task_file.get('tasks', []):
                when = task.get('when')
                if not when:
                    continue

                # Convert to string for analysis
                when_str = str(when) if not isinstance(when, list) else ' and '.join(map(str, when))

                # Detect complex conditionals
                if when_str.count('or') > 2 or when_str.count('and') > 3:
                    suggestions.append(SimplificationSuggestion(
                        pattern="complex_conditional",
                        severity="info",
                        description=f"Complex conditional in task '{task.get('name')}'",
                        example=f"when: {when_str[:100]}...",
                        suggestion="Consider:\n"
                                   "1. Setting intermediate facts\n"
                                   "2. Using role composition (include_role with when)\n"
                                   "3. Creating separate task files per scenario",
                        affected_files=[task_file.get('file')],
                        impact="Improves readability and testability"
                    ))

        return suggestions

    def analyze_missing_idempotency(self, role_info: Dict) -> List[SimplificationSuggestion]:
        """Detect tasks that may not be idempotent."""
        suggestions = []

        # Modules that often lack idempotency
        risky_modules = ['shell', 'command', 'raw']

        for task_file in role_info.get('tasks', []):
            for task in task_file.get('tasks', []):
                module = task.get('module')

                if module in risky_modules:
                    has_creates = 'creates' in task or 'removes' in task
                    has_changed_when = 'changed_when' in task

                    if not has_creates and not has_changed_when:
                        suggestions.append(SimplificationSuggestion(
                            pattern="missing_idempotency",
                            severity="warning",
                            description=f"Task '{task.get('name')}' uses {module} without idempotency checks",
                            example=self._show_task(task),
                            suggestion="Add one of:\n"
                                       "  creates: /path/to/file  # Skip if file exists\n"
                                       "  removes: /path/to/file  # Skip if file missing\n"
                                       "  changed_when: false     # Never report changed",
                            affected_files=[task_file.get('file')],
                            impact="Ensures role can be run multiple times safely"
                        ))

        return suggestions

    def analyze_task_file_organization(self, role_info: Dict) -> List[SimplificationSuggestion]:
        """Suggest better task file organization."""
        suggestions = []

        task_files = role_info.get('tasks', [])

        # Check for monolithic main.yml
        main_file = next((f for f in task_files if f.get('file') == 'main.yml'), None)
        if main_file:
            task_count = len(main_file.get('tasks', []))

            if task_count > 30:
                suggestions.append(SimplificationSuggestion(
                    pattern="monolithic_main_file",
                    severity="warning",
                    description=f"main.yml contains {task_count} tasks (recommended: <30)",
                    example="",
                    suggestion="Split into separate files:\n"
                               "tasks/\n"
                               "  main.yml         # Orchestration only\n"
                               "  install.yml      # Package installation\n"
                               "  configure.yml    # Configuration files\n"
                               "  service.yml      # Service management\n"
                               "\n"
                               "In main.yml:\n"
                               "  - import_tasks: install.yml\n"
                               "  - import_tasks: configure.yml\n"
                               "  - import_tasks: service.yml",
                    affected_files=['tasks/main.yml'],
                    impact=f"Improves maintainability and reusability"
                ))

        return suggestions
```

**Integration with Complexity Analyzer:**

```python
# In complexity_analyzer.py
def analyze_role(role_info: Dict[str, Any]) -> ComplexityReport:
    # ... existing code ...

    # NEW: Add simplification suggestions
    from docsible.analyzers.pattern_analyzer import PatternAnalyzer

    pattern_analyzer = PatternAnalyzer()
    simplification_suggestions = []

    simplification_suggestions.extend(pattern_analyzer.analyze_duplicated_tasks(role_info))
    simplification_suggestions.extend(pattern_analyzer.analyze_complex_conditionals(role_info))
    simplification_suggestions.extend(pattern_analyzer.analyze_missing_idempotency(role_info))
    simplification_suggestions.extend(pattern_analyzer.analyze_task_file_organization(role_info))

    return ComplexityReport(
        # ... existing fields ...
        simplification_suggestions=simplification_suggestions
    )
```

**Output in README:**

```markdown
## Simplification Opportunities

Based on analysis, here are suggestions to improve this role:

### ⚠️  Warning: Repeated Package Installation
**Pattern:** `repeated_package_install`
**Impact:** Reduces 12 tasks to 1 task (-11 tasks)

**Current approach:**
```yaml
- name: Install nginx
  apt: name=nginx
- name: Install php-fpm
  apt: name=php-fpm
# ... 10 more similar tasks
```

**Suggested refactoring:**
```yaml
- name: Install packages
  apt:
    name: "{{ item }}"
  loop:
    - nginx
    - php-fpm
    - php-mysql
    # ... all packages
```

**Affected files:** `tasks/install.yml`

---

### ℹ️ Info: Complex Conditional Logic
**Pattern:** `complex_conditional`
**Impact:** Improves readability and testability

**Current approach:**
```yaml
when: (ansible_os_family == "Debian" and ansible_distribution_major_version >= "10") or
      (ansible_os_family == "RedHat" and ansible_distribution_major_version >= "8" and not is_container)
```

**Suggested refactoring:**
```yaml
# Set intermediate fact
- set_fact:
    is_supported_os: "{{ (ansible_os_family == 'Debian' and ansible_distribution_major_version >= '10') or
                          (ansible_os_family == 'RedHat' and ansible_distribution_major_version >= '8' and not is_container) }}"

# Use simple condition
- name: Configure system
  ...
  when: is_supported_os
```

**Affected files:** `tasks/configure.yml`
```

---

#### **Solution 3B: AI-Powered Suggestions** (Future - Long Term)
**Feasibility:** ⭐⭐ Low-Medium (Requires ML/LLM)

**Use LLM to generate specific refactoring suggestions:**

```python
# Hypothetical: docsible/ai/refactoring.py
import openai  # or anthropic, or local model

def generate_refactoring_suggestion(role_code: str, complexity_metrics: Dict) -> str:
    """Use AI to suggest specific refactorings."""

    prompt = f"""
You are an Ansible expert. Analyze this role and suggest specific refactorings.

Role Statistics:
- Total Tasks: {complexity_metrics['total_tasks']}
- Conditional Tasks: {complexity_metrics['conditional_tasks']}
- Task Files: {complexity_metrics['task_files']}

Code:
{role_code}

Provide specific, actionable suggestions with:
1. What to change
2. Why it should be changed
3. Exact code examples

Format as markdown.
"""

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

**Advantages:**
- ✅ Highly specific suggestions
- ✅ Context-aware refactoring
- ✅ Learns from best practices

**Disadvantages:**
- ❌ Requires API key / internet
- ❌ Costs money per analysis
- ❌ Privacy concerns (sends code to 3rd party)
- ❌ Inconsistent output quality

---

### Recommendation: **Pattern-Based Analysis First**

**Phase 1 (2-4 weeks):**
1. Implement `PatternAnalyzer` with 5-10 common anti-patterns
2. Add `SimplificationSuggestion` data model
3. Integrate with complexity report
4. Add template section for simplification suggestions
5. Add `--simplification-report` flag (opt-in initially)

**Patterns to detect (Priority order):**
1. ✅ Duplicated tasks (same module, similar args)
2. ✅ Complex conditionals (>3 boolean operators)
3. ✅ Missing idempotency (shell/command without creates/removes)
4. ✅ Monolithic main.yml (>30 tasks)
5. ✅ Hardcoded values (should be variables)
6. ✅ Missing error handling (no rescue/always blocks)
7. ✅ Excessive handler triggers (same handler multiple times)
8. ✅ Unused variables (defined but never referenced)

**Phase 2 (1-2 months):**
9. Add task similarity scoring (detect near-duplicates)
10. Suggest variable extraction from repeated values
11. Detect missing tags for selective execution
12. Analyze task dependencies for parallelization opportunities

**Phase 3 (3+ months):**
13. Consider AI-assisted suggestions (optional, opt-in)
14. Interactive refactoring wizard
15. Generate refactored code (not just suggestions)

---

## Question 4: Changelog Automation from Git

### Problem Statement
**Question:** Given we provide a changelog section in templates, should we not be able to retrieve commits from the current repository to update the changelog according to the changelog format?

### Current State Analysis

**What We Have:**
- **Git utilities** (`utils/git.py`):
  - `get_repo_info()` - Gets repo URL, branch, type
  - Repository type detection (GitHub, GitLab, Gitea, Bitbucket)
- **Changelog template** (in `hybrid_modular.jinja2`):
  ```markdown
  ## Changelog
  <!-- MANUALLY MAINTAINED -->
  ### [Version] - Date
  **Added**
  - New feature description

  **Changed**
  - Modified behavior description

  **Fixed**
  - Bug fix description
  ```

**What We DON'T Have:**
- Git commit parsing
- Conventional Commits detection
- Changelog generation logic
- Version tag analysis

### Value Assessment: **MEDIUM-HIGH VALUE** ⭐⭐⭐⭐

**Why it matters:**
- **Time-saving:** Auto-generate from commits
- **Consistency:** Enforce commit message format
- **Traceability:** Link changes to commits
- **Onboarding:** Show evolution of role

**Why NOT highest priority:**
- ❌ Many projects don't use semantic commits
- ❌ Role changes often not versioned
- ❌ Complex to merge manual + auto sections

### Feasibility Assessment: **HIGH** ⭐⭐⭐⭐

**Current Codebase Readiness:**
- ✅ Git integration exists
- ✅ Template system supports dynamic content
- ✅ Jinja2 for formatting
- ❌ No commit parsing
- ❌ No version detection

### Proposed Solutions

#### **Solution 4A: Conventional Commits Parser** (Recommended)
**Feasibility:** ⭐⭐⭐⭐⭐ Very High

**Parse conventional commits and generate changelog:**

```python
# docsible/utils/changelog_generator.py
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class ChangelogEntry:
    """Represents a single changelog entry."""
    type: str  # feat, fix, docs, refactor, etc.
    scope: Optional[str]  # e.g., "tasks", "handlers"
    description: str
    breaking: bool
    commit_hash: str
    date: datetime
    author: str

class ChangelogGenerator:
    """Generate changelog from git commits."""

    # Conventional Commits pattern
    COMMIT_PATTERN = re.compile(
        r'^(?P<type>\w+)'
        r'(?:\((?P<scope>[^\)]+)\))?'
        r'(?P<breaking>!)?'
        r': '
        r'(?P<description>.+)$'
    )

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_commits_since_tag(self, tag: Optional[str] = None) -> List[Dict]:
        """Get commits since last tag (or all commits)."""
        cmd = ['git', '-C', self.repo_path, 'log', '--pretty=format:%H|%an|%ad|%s', '--date=short']

        if tag:
            cmd.append(f'{tag}..HEAD')

        result = subprocess.run(cmd, capture_output=True, text=True)

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue

            hash, author, date, subject = line.split('|', 3)
            commits.append({
                'hash': hash,
                'author': author,
                'date': datetime.strptime(date, '%Y-%m-%d'),
                'subject': subject
            })

        return commits

    def parse_commit(self, commit: Dict) -> Optional[ChangelogEntry]:
        """Parse commit message using Conventional Commits format."""
        match = self.COMMIT_PATTERN.match(commit['subject'])

        if not match:
            # Non-conventional commit - skip or add to "Other" category
            return None

        return ChangelogEntry(
            type=match.group('type'),
            scope=match.group('scope'),
            description=match.group('description'),
            breaking=match.group('breaking') is not None,
            commit_hash=commit['hash'][:7],
            date=commit['date'],
            author=commit['author']
        )

    def generate_changelog(self, since_tag: Optional[str] = None) -> Dict[str, List[ChangelogEntry]]:
        """Generate categorized changelog."""
        commits = self.get_commits_since_tag(since_tag)

        changelog = {
            'feat': [],
            'fix': [],
            'docs': [],
            'refactor': [],
            'test': [],
            'chore': [],
            'breaking': []
        }

        for commit in commits:
            entry = self.parse_commit(commit)
            if entry:
                if entry.breaking:
                    changelog['breaking'].append(entry)
                elif entry.type in changelog:
                    changelog[entry.type].append(entry)

        return changelog

    def format_markdown(self, changelog: Dict[str, List[ChangelogEntry]], version: str = "Unreleased") -> str:
        """Format changelog as markdown."""
        lines = [f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}", ""]

        # Breaking changes first (if any)
        if changelog['breaking']:
            lines.append("### ⚠️ BREAKING CHANGES")
            for entry in changelog['breaking']:
                scope = f"**{entry.scope}**: " if entry.scope else ""
                lines.append(f"- {scope}{entry.description} ([{entry.commit_hash}])")
            lines.append("")

        # Features
        if changelog['feat']:
            lines.append("### Added")
            for entry in changelog['feat']:
                scope = f"**{entry.scope}**: " if entry.scope else ""
                lines.append(f"- {scope}{entry.description} ([{entry.commit_hash}])")
            lines.append("")

        # Fixes
        if changelog['fix']:
            lines.append("### Fixed")
            for entry in changelog['fix']:
                scope = f"**{entry.scope}**: " if entry.scope else ""
                lines.append(f"- {scope}{entry.description} ([{entry.commit_hash}])")
            lines.append("")

        # Other changes
        if changelog['refactor'] or changelog['docs'] or changelog['test']:
            lines.append("### Changed")
            for entry in changelog['refactor'] + changelog['docs']:
                scope = f"**{entry.scope}**: " if entry.scope else ""
                lines.append(f"- {scope}{entry.description} ([{entry.commit_hash}])")
            lines.append("")

        return '\n'.join(lines)
```

**Integration:**

```python
# In document_role/core.py
from docsible.utils.changelog_generator import ChangelogGenerator

def core_doc_the_role(..., generate_changelog=False):
    # ... existing code ...

    changelog_md = None
    if generate_changelog:
        try:
            generator = ChangelogGenerator(role_path)
            changelog_data = generator.generate_changelog()
            changelog_md = generator.format_markdown(changelog_data)
        except Exception as e:
            logger.warning(f"Could not generate changelog: {e}")

    # Pass to template
    readme_renderer.render_role(
        # ... existing params ...
        changelog=changelog_md
    )
```

**CLI Flag:**

```python
# In options/generation.py
f = click.option(
    "--generate-changelog",
    "generate_changelog",
    is_flag=True,
    help="Auto-generate changelog from git commits using Conventional Commits format."
)(f)
```

**Template Update:**

```jinja2
## Changelog
<!-- DOCSIBLE GENERATED -->
{%- if changelog %}
{{ changelog }}
{%- else %}
<!-- MANUALLY MAINTAINED -->
### [Unreleased]
**Added**
- New feature description

**Changed**
- Modified behavior description

**Fixed**
- Bug fix description
{%- endif %}
```

**Example Output:**

```markdown
## Changelog

## [Unreleased] - 2025-12-11

### Added
- **tasks**: Add support for Ubuntu 24.04 ([a3f5c9d])
- **handlers**: Add nginx reload handler ([e1b2c4f])

### Fixed
- **defaults**: Fix database port default value ([9d8e7a1])
- **tasks**: Correct systemd service name ([2c4f6b3])

### Changed
- **docs**: Update installation instructions ([5a1b3c9])
- **refactor**: Simplify task conditionals ([8f2e4d1])
```

---

#### **Solution 4B: Smart Hybrid Changelog** (Recommended Enhancement)
**Feasibility:** ⭐⭐⭐⭐ High

**Merge manual and auto-generated sections:**

```python
def merge_changelog(existing_changelog: str, generated_changelog: str) -> str:
    """Merge manually maintained changelog with auto-generated."""

    # Parse existing changelog to find manual entries
    manual_entries = extract_manual_entries(existing_changelog)

    # Insert auto-generated entries
    merged = []
    merged.append("## Changelog")
    merged.append("")
    merged.append("<!-- AUTO-GENERATED FROM GIT COMMITS -->")
    merged.append(generated_changelog)
    merged.append("")
    merged.append("<!-- MANUALLY MAINTAINED ENTRIES -->")
    merged.extend(manual_entries)

    return '\n'.join(merged)
```

**Template:**

```jinja2
## Changelog

{% if changelog %}
<!-- AUTO-GENERATED FROM GIT COMMITS (Since last version tag) -->
{{ changelog }}

{% endif %}
<!-- MANUALLY MAINTAINED -->
<!-- Add manual changelog entries below for non-code changes -->
### [Version] - Date
**Added**
- Manual entry example

---
*Auto-generated entries created from git commits following [Conventional Commits](https://www.conventionalcommits.org/) format.*
```

---

#### **Solution 4C: Version Tag Integration**
**Feasibility:** ⭐⭐⭐⭐ High

**Auto-detect versions from git tags:**

```python
def get_version_tags(repo_path: str) -> List[Dict]:
    """Get all version tags from git repository."""
    result = subprocess.run(
        ['git', '-C', repo_path, 'tag', '-l', 'v*', '--sort=-version:refname'],
        capture_output=True,
        text=True
    )

    tags = []
    for tag in result.stdout.strip().split('\n'):
        if not tag:
            continue

        # Get tag date
        date_result = subprocess.run(
            ['git', '-C', repo_path, 'log', '-1', '--format=%ai', tag],
            capture_output=True,
            text=True
        )

        tags.append({
            'name': tag,
            'date': date_result.stdout.strip()
        })

    return tags

def generate_full_changelog(repo_path: str) -> str:
    """Generate changelog for all versions."""
    tags = get_version_tags(repo_path)
    generator = ChangelogGenerator(repo_path)

    sections = []

    # Unreleased (since last tag)
    if tags:
        unreleased = generator.generate_changelog(since_tag=tags[0]['name'])
        if any(unreleased.values()):
            sections.append(generator.format_markdown(unreleased, "Unreleased"))

    # Each version
    for i, tag in enumerate(tags):
        since = tags[i+1]['name'] if i+1 < len(tags) else None
        changelog = generator.generate_changelog(since_tag=since)
        sections.append(generator.format_markdown(changelog, tag['name']))

    return '\n\n'.join(sections)
```

---

### Recommendation: **Phased Approach**

**Phase 1 (1-2 weeks):**
1. Implement `ChangelogGenerator` with Conventional Commits parsing
2. Add `--generate-changelog` flag
3. Generate changelog for commits since last tag (or all commits)
4. Update template to show auto-generated changelog

**Phase 2 (2-3 weeks):**
5. Add version tag detection
6. Generate full changelog with version history
7. Implement smart merge (manual + auto)
8. Add link generation to commits (GitHub/GitLab URLs)

**Phase 3 (1 month):**
9. Add `--changelog-format` option (conventional, keepachangelog, custom)
10. Support custom commit patterns (regex-based)
11. Interactive changelog editor (review before adding)

**Configuration:**

```yaml
# .docsible.yml
changelog:
  enabled: true
  format: conventional  # or keepachangelog
  include_authors: true
  link_commits: true
  since: last_tag  # or "all", or specific tag "v1.0.0"
  categories:
    feat: "Added"
    fix: "Fixed"
    docs: "Documentation"
    refactor: "Changed"
    breaking: "BREAKING CHANGES"
```

---

## Summary & Prioritization

### Implementation Priority

| Feature | Value | Feasibility | Effort | Priority | Timeline |
|---------|-------|-------------|--------|----------|----------|
| **1. Documentation Drift Prevention** | HIGH | VERY HIGH | Low | **P0** | 1 week |
| - Metadata tracking | HIGH | VERY HIGH | Low | P0 | 3 days |
| - `docsible check` command | HIGH | VERY HIGH | Low | P0 | 2 days |
| - Git hook installer | MEDIUM | VERY HIGH | Low | P1 | 2 days |
| **2. Large Diagram Export** | MEDIUM-HIGH | HIGH | Medium | **P1** | 2 weeks |
| - Diagram pagination | HIGH | HIGH | Low | P0 | 3 days |
| - SVG/PNG export | MEDIUM | HIGH | Medium | P1 | 1 week |
| - Cloud rendering fallback | LOW | MEDIUM | Low | P2 | 2 days |
| **3. Simplification Suggestions** | VERY HIGH | MEDIUM | High | **P1** | 1 month |
| - Pattern analyzer (5-10 patterns) | VERY HIGH | HIGH | Medium | P0 | 2 weeks |
| - Template integration | HIGH | VERY HIGH | Low | P0 | 2 days |
| - Advanced patterns | HIGH | MEDIUM | High | P2 | 2 weeks |
| **4. Changelog Automation** | MEDIUM-HIGH | HIGH | Medium | **P2** | 2 weeks |
| - Conventional Commits parser | HIGH | VERY HIGH | Medium | P1 | 1 week |
| - Version tag integration | MEDIUM | HIGH | Low | P1 | 3 days |
| - Smart merge (manual + auto) | LOW | MEDIUM | Medium | P2 | 4 days |

### Recommended Implementation Order

**Sprint 1 (Week 1-2):**
1. Documentation drift prevention (metadata + check command)
2. Diagram pagination for large diagrams
3. Basic pattern analyzer (3 patterns)

**Sprint 2 (Week 3-4):**
4. Git hook installer
5. Pattern analyzer (7 more patterns)
6. SVG/PNG diagram export

**Sprint 3 (Week 5-6):**
7. Changelog generator (Conventional Commits)
8. Version tag integration
9. Polish and documentation

**Future Enhancements:**
- Watch mode for live updates
- AI-powered refactoring suggestions
- Interactive changelog editor
- IDE plugin integration

---

## Next Steps

To proceed with implementation, let me know which feature you'd like to start with, or if you'd like me to:

1. Create detailed technical specs for any feature
2. Implement a proof-of-concept for validation
3. Discuss alternative approaches
4. Assess impact on existing codebase
5. Create implementation tasks/issues

---

*Document created: 2025-12-11*
*Docsible version: 0.8.0*
*Analysis based on current codebase architecture*
