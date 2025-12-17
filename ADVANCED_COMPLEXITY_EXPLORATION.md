# Advanced Complexity Analysis Features - Exploration

## Overview

This document explores four advanced features for complexity analysis that could help users identify refactoring opportunities, optimization potential, and anti-patterns in Ansible roles:

1. **Task Similarity Scoring** - Detect near-duplicate tasks
2. **Variable Extraction** - Suggest extracting repeated values into variables
3. **Missing Tags Detection** - Identify tasks lacking tags for selective execution
4. **Task Parallelization Opportunities** - Detect independent tasks that could run in parallel

---

## 1. Task Similarity Scoring (Detect Near-Duplicates)

### Motivation

Ansible roles often contain near-duplicate tasks that differ only in minor details (e.g., installing different packages with the same module). These duplicates suggest refactoring opportunities using loops, includes, or role parameters.

### Examples of Duplicate Tasks

```yaml
# Bad: Repetitive tasks
- name: Install nginx
  apt:
    name: nginx
    state: present

- name: Install apache2
  apt:
    name: apache2
    state: present

- name: Install postgresql
  apt:
    name: postgresql
    state: present

# Good: Use a loop
- name: Install packages
  apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - apache2
    - postgresql
```

### Implementation Approach

#### 1.1 Similarity Metrics

**Structural Similarity** (using module + parameters):
```python
from difflib import SequenceMatcher

def calculate_task_similarity(task1: dict, task2: dict) -> float:
    """Calculate similarity between two tasks (0.0 - 1.0).

    Returns:
        0.0 - completely different
        1.0 - identical
        0.5-0.9 - similar (candidates for refactoring)
    """
    # Compare modules
    if task1.get("module") != task2.get("module"):
        return 0.0  # Different modules = not similar

    # Extract parameters (excluding 'name')
    params1 = {k: v for k, v in task1.items()
              if k not in ["name", "module"]}
    params2 = {k: v for k, v in task2.items()
              if k not in ["name", "module"]}

    # Compare parameter keys
    keys1 = set(params1.keys())
    keys2 = set(params2.keys())
    key_similarity = len(keys1 & keys2) / len(keys1 | keys2) if keys1 | keys2 else 0

    # Compare parameter values
    common_keys = keys1 & keys2
    if not common_keys:
        return key_similarity * 0.5

    value_matches = sum(1 for k in common_keys if params1[k] == params2[k])
    value_similarity = value_matches / len(common_keys)

    # Weighted average
    return (key_similarity * 0.4) + (value_similarity * 0.6)
```

**Text Similarity** (using task names):
```python
def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between task names using Levenshtein distance."""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
```

#### 1.2 Similarity Detection Algorithm

```python
from typing import Any
from dataclasses import dataclass

@dataclass
class SimilarTaskGroup:
    """Group of similar tasks that could be refactored."""

    tasks: list[dict[str, Any]]
    similarity_score: float
    common_module: str
    common_params: dict[str, Any]
    varying_params: dict[str, list[Any]]
    suggestion: str

def detect_similar_tasks(
    tasks: list[dict],
    threshold: float = 0.7
) -> list[SimilarTaskGroup]:
    """Detect groups of similar tasks.

    Args:
        tasks: List of task dictionaries
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of similar task groups with refactoring suggestions
    """
    similar_groups = []

    # Group tasks by module first
    by_module: dict[str, list[dict]] = {}
    for task in tasks:
        module = task.get("module", "")
        if module:
            by_module.setdefault(module, []).append(task)

    # Within each module, find similar tasks
    for module, module_tasks in by_module.items():
        if len(module_tasks) < 2:
            continue

        # Compare all pairs
        for i in range(len(module_tasks)):
            for j in range(i + 1, len(module_tasks)):
                similarity = calculate_task_similarity(
                    module_tasks[i],
                    module_tasks[j]
                )

                if similarity >= threshold:
                    # Found similar pair - analyze differences
                    common, varying = _extract_params(
                        module_tasks[i],
                        module_tasks[j]
                    )

                    suggestion = _generate_loop_suggestion(
                        module,
                        common,
                        varying
                    )

                    similar_groups.append(SimilarTaskGroup(
                        tasks=[module_tasks[i], module_tasks[j]],
                        similarity_score=similarity,
                        common_module=module,
                        common_params=common,
                        varying_params=varying,
                        suggestion=suggestion
                    ))

    return similar_groups

def _extract_params(task1: dict, task2: dict) -> tuple[dict, dict]:
    """Extract common and varying parameters."""
    common = {}
    varying = {}

    all_keys = set(task1.keys()) | set(task2.keys())
    for key in all_keys:
        if key in ["name", "module"]:
            continue

        val1 = task1.get(key)
        val2 = task2.get(key)

        if val1 == val2:
            common[key] = val1
        else:
            varying[key] = [val1, val2]

    return common, varying

def _generate_loop_suggestion(
    module: str,
    common: dict,
    varying: dict
) -> str:
    """Generate refactoring suggestion."""
    # Detect if varying params follow a pattern
    if len(varying) == 1:
        param_name = list(varying.keys())[0]
        return (
            f"Refactor using a loop over '{param_name}' parameter:\n"
            f"  - name: Task with loop\n"
            f"    {module}:\n"
            f"      {param_name}: \"{{{{ item }}}}\"\n"
            + "".join(f"      {k}: {v}\n" for k, v in common.items()) +
            f"    loop: {varying[param_name]}"
        )
    else:
        return (
            f"Refactor using a loop with complex items:\n"
            f"  - name: Task with loop\n"
            f"    {module}:\n"
            + "".join(f"      {k}: \"{{{{ item.{k} }}}}\"\n" for k in varying.keys()) +
            "      loop:\n"
            + "".join(f"        - {k}: {v[0]}\n" for k, v in varying.items())
        )
```

#### 1.3 Example Output

```python
# For the nginx/apache/postgresql example:
SimilarTaskGroup(
    tasks=[
        {"name": "Install nginx", "module": "apt", "name": "nginx", "state": "present"},
        {"name": "Install apache2", "module": "apt", "name": "apache2", "state": "present"},
    ],
    similarity_score=0.9,
    common_module="apt",
    common_params={"state": "present"},
    varying_params={"name": ["nginx", "apache2"]},
    suggestion="""
Refactor using a loop over 'name' parameter:
  - name: Install packages
    apt:
      name: "{{ item }}"
      state: present
    loop:
      - nginx
      - apache2
"""
)
```

### Integration with Complexity Analyzer

```python
# In docsible/analyzers/complexity_analyzer/similarity.py

class TaskSimilarityAnalyzer:
    """Detect and analyze task similarity for refactoring opportunities."""

    def analyze(
        self,
        role_info: dict,
        threshold: float = 0.7
    ) -> list[SimilarTaskGroup]:
        """Analyze role for similar tasks."""
        all_similar_groups = []

        for task_file_info in role_info.get("tasks", []):
            tasks = task_file_info.get("tasks", [])
            file_path = task_file_info.get("file")

            # Detect similar tasks in this file
            groups = detect_similar_tasks(tasks, threshold)

            # Add file path context
            for group in groups:
                group.file_path = file_path

            all_similar_groups.extend(groups)

        return all_similar_groups
```

### Benefits

- **Reduced Code Duplication**: Identify 80% of duplicate patterns
- **Better Maintainability**: Fewer lines, less repetition
- **Improved Readability**: Loop-based tasks are more concise

### Challenges

- **False Positives**: Some similar tasks are intentionally separate
- **Complex Patterns**: Harder to detect similarity with nested structures
- **Performance**: O(n²) comparison for large task files

---

## 2. Variable Extraction from Repeated Values

### Motivation

Hard-coded values repeated across tasks should be extracted into variables for:
- Easier configuration management
- Better reusability
- Clearer intent

### Examples

```yaml
# Bad: Hard-coded repeated values
- name: Create app directory
  file:
    path: /opt/myapp
    state: directory

- name: Copy config
  copy:
    src: config.yml
    dest: /opt/myapp/config.yml

- name: Set permissions
  file:
    path: /opt/myapp
    mode: '0755'

# Good: Use variables
- name: Create app directory
  file:
    path: "{{ app_install_dir }}"
    state: directory

- name: Copy config
  copy:
    src: config.yml
    dest: "{{ app_install_dir }}/config.yml"

- name: Set permissions
  file:
    path: "{{ app_install_dir }}"
    mode: '0755'

# In defaults/main.yml:
app_install_dir: /opt/myapp
```

### Implementation Approach

#### 2.1 Value Frequency Analysis

```python
from collections import Counter
from typing import Any
import re

@dataclass
class RepeatedValue:
    """Represents a value that appears multiple times."""

    value: Any
    count: int
    locations: list[tuple[str, str, int]]  # (file, param, task_index)
    suggested_var_name: str
    suggestion: str

def extract_repeated_values(
    role_info: dict,
    min_count: int = 3,
    ignore_patterns: list[str] | None = None
) -> list[RepeatedValue]:
    """Find repeated values across tasks.

    Args:
        role_info: Role information dictionary
        min_count: Minimum repetitions to report
        ignore_patterns: Patterns to ignore (e.g., ["yes", "no", "present", "absent"])

    Returns:
        List of repeated values with extraction suggestions
    """
    ignore_patterns = ignore_patterns or [
        "yes", "no", "true", "false",
        "present", "absent", "started", "stopped",
        "latest", "installed"
    ]

    # Track all values and their locations
    value_tracker: dict[str, list[tuple[str, str, int]]] = {}

    for task_file_info in role_info.get("tasks", []):
        file_path = task_file_info.get("file", "unknown")
        tasks = task_file_info.get("tasks", [])

        for idx, task in enumerate(tasks):
            # Scan all task parameters
            for key, value in task.items():
                if key in ["name", "module", "when", "loop", "with_items"]:
                    continue  # Skip metadata

                # Extract string values
                str_value = str(value) if value else None
                if not str_value or str_value in ignore_patterns:
                    continue

                # Track this value
                location = (file_path, key, idx)
                value_tracker.setdefault(str_value, []).append(location)

    # Find repeated values
    repeated = []
    for value, locations in value_tracker.items():
        if len(locations) >= min_count:
            var_name = _suggest_variable_name(value, locations)
            suggestion = _generate_extraction_suggestion(value, var_name, locations)

            repeated.append(RepeatedValue(
                value=value,
                count=len(locations),
                locations=locations,
                suggested_var_name=var_name,
                suggestion=suggestion
            ))

    # Sort by frequency (most repeated first)
    return sorted(repeated, key=lambda r: r.count, reverse=True)

def _suggest_variable_name(value: str, locations: list) -> str:
    """Suggest a variable name based on context."""
    # Analyze common patterns
    if value.startswith("/"):
        # Looks like a path
        path_parts = Path(value).parts
        return f"{path_parts[-1]}_path"

    if re.match(r"\d+", value):
        # Numeric value
        param_names = [loc[1] for loc in locations]
        most_common_param = Counter(param_names).most_common(1)[0][0]
        return f"{most_common_param}_value"

    if ":" in value or "@" in value:
        # Looks like a URL or email
        return "service_endpoint" if "://" in value else "contact_email"

    # Generic: use value as hint
    safe_name = re.sub(r"[^a-z0-9_]", "_", value.lower())
    return f"{safe_name[:20]}_var"

def _generate_extraction_suggestion(
    value: str,
    var_name: str,
    locations: list
) -> str:
    """Generate suggestion for variable extraction."""
    files = set(loc[0] for loc in locations)
    params = set(loc[1] for loc in locations)

    suggestion = f"""
Extract repeated value '{value}' into variable:

1. Add to defaults/main.yml:
   {var_name}: {value}

2. Replace in tasks ({len(locations)} occurrences across {len(files)} file(s)):
"""

    for file_path, param_name, task_idx in locations[:5]:  # Show first 5
        suggestion += f"   - {file_path}:{task_idx} ({param_name})\n"

    if len(locations) > 5:
        suggestion += f"   ... and {len(locations) - 5} more\n"

    suggestion += f"\n3. Update task parameters:\n"
    suggestion += f"   {list(params)[0]}: \"{{{{ {var_name} }}}}\""

    return suggestion
```

#### 2.2 Example Output

```python
RepeatedValue(
    value="/opt/myapp",
    count=15,
    locations=[
        ("tasks/main.yml", "path", 5),
        ("tasks/main.yml", "dest", 12),
        ("tasks/config.yml", "path", 3),
        # ...
    ],
    suggested_var_name="myapp_path",
    suggestion="""
Extract repeated value '/opt/myapp' into variable:

1. Add to defaults/main.yml:
   myapp_path: /opt/myapp

2. Replace in tasks (15 occurrences across 3 file(s)):
   - tasks/main.yml:5 (path)
   - tasks/main.yml:12 (dest)
   - tasks/config.yml:3 (path)
   ...

3. Update task parameters:
   path: "{{ myapp_path }}"
"""
)
```

### Benefits

- **Configuration Management**: Easy to change values in one place
- **Reduced Errors**: Less chance of typos or inconsistencies
- **Better Documentation**: Variable names provide semantic meaning

### Challenges

- **Context Sensitivity**: Not all repeated values should be variables
- **Scoping**: Determining if a value should be in defaults/ or vars/
- **Type Detection**: Distinguishing paths, URLs, port numbers, etc.

---

## 3. Missing Tags Detection

### Motivation

Ansible tags enable selective task execution (`ansible-playbook --tags setup`). Roles without consistent tagging make it hard to:
- Run only specific phases (e.g., `--tags install`)
- Skip certain tasks (e.g., `--skip-tags testing`)
- Understand task categorization

### Examples

```yaml
# Bad: Inconsistent or missing tags
- name: Install packages
  apt:
    name: nginx
  # No tags!

- name: Configure nginx
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  tags: [config]  # Only some tasks tagged

- name: Start nginx
  service:
    name: nginx
    state: started
  # No tags!

# Good: Consistent tagging strategy
- name: Install packages
  apt:
    name: nginx
  tags: [install, packages]

- name: Configure nginx
  template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  tags: [config, configuration]

- name: Start nginx
  service:
    name: nginx
    state: started
  tags: [service, startup]
```

### Implementation Approach

#### 3.1 Tag Coverage Analysis

```python
@dataclass
class TagAnalysis:
    """Analysis of tag usage in a role."""

    total_tasks: int
    tagged_tasks: int
    untagged_tasks: int
    coverage_percentage: float
    tag_frequency: dict[str, int]
    suggested_tags: dict[int, list[str]]  # task_index -> suggested tags
    recommendation: str

def analyze_tag_coverage(role_info: dict) -> TagAnalysis:
    """Analyze tag usage and suggest improvements.

    Args:
        role_info: Role information dictionary

    Returns:
        Tag analysis with suggestions
    """
    total_tasks = 0
    tagged_tasks = 0
    untagged_task_indices = []
    tag_counter = Counter()

    all_tasks = []
    for task_file_info in role_info.get("tasks", []):
        tasks = task_file_info.get("tasks", [])
        all_tasks.extend(tasks)

        for idx, task in enumerate(tasks):
            total_tasks += 1

            tags = task.get("tags", [])
            if tags:
                tagged_tasks += 1
                tag_counter.update(tags)
            else:
                untagged_task_indices.append((task_file_info["file"], idx, task))

    coverage = (tagged_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Suggest tags for untagged tasks
    suggested_tags = {}
    for file_path, idx, task in untagged_task_indices:
        tags = _suggest_tags_for_task(task, tag_counter)
        suggested_tags[(file_path, idx)] = tags

    # Generate recommendation
    recommendation = _generate_tag_recommendation(
        coverage,
        len(untagged_task_indices),
        tag_counter
    )

    return TagAnalysis(
        total_tasks=total_tasks,
        tagged_tasks=tagged_tasks,
        untagged_tasks=len(untagged_task_indices),
        coverage_percentage=coverage,
        tag_frequency=dict(tag_counter),
        suggested_tags=suggested_tags,
        recommendation=recommendation
    )

def _suggest_tags_for_task(task: dict, existing_tags: Counter) -> list[str]:
    """Suggest appropriate tags based on task content."""
    suggestions = []

    module = task.get("module", "")
    task_name = task.get("name", "").lower()

    # Module-based tag suggestions
    MODULE_TAG_MAP = {
        "apt": ["install", "packages"],
        "yum": ["install", "packages"],
        "pip": ["install", "python"],
        "npm": ["install", "nodejs"],
        "template": ["config", "configuration"],
        "copy": ["config", "files"],
        "file": ["filesystem", "setup"],
        "service": ["service", "daemon"],
        "systemd": ["service", "systemd"],
        "docker_": ["docker", "container"],
        "git": ["git", "scm"],
    }

    for pattern, tags in MODULE_TAG_MAP.items():
        if module.startswith(pattern) or pattern in module:
            suggestions.extend(tags)

    # Name-based tag suggestions
    NAME_TAG_MAP = {
        "install": ["install"],
        "configure": ["config"],
        "setup": ["setup"],
        "deploy": ["deploy"],
        "start": ["service"],
        "stop": ["service"],
        "restart": ["service"],
        "create": ["setup"],
        "update": ["update"],
        "upgrade": ["upgrade"],
    }

    for keyword, tags in NAME_TAG_MAP.items():
        if keyword in task_name:
            suggestions.extend(tags)

    # Deduplicate and return
    return list(set(suggestions)) or ["uncategorized"]

def _generate_tag_recommendation(
    coverage: float,
    untagged_count: int,
    tag_freq: Counter
) -> str:
    """Generate recommendation based on tag coverage."""
    if coverage >= 90:
        return f"✅ Excellent tag coverage ({coverage:.0f}%). Consider standardizing tag names."

    if coverage >= 70:
        return (
            f"⚠️ Good tag coverage ({coverage:.0f}%), but {untagged_count} tasks lack tags.\n"
            f"   Add tags to enable selective execution (e.g., --tags install)."
        )

    if coverage >= 50:
        return (
            f"⚠️ Moderate tag coverage ({coverage:.0f}%). {untagged_count} tasks lack tags.\n"
            f"   Suggested tag categories based on existing usage:\n"
            + "\n".join(f"      - {tag} (used {count}x)" for tag, count in tag_freq.most_common(5))
        )

    # Poor coverage
    return (
        f"❌ Low tag coverage ({coverage:.0f}%). Only {untagged_count} of tasks are tagged.\n"
        f"   Recommend implementing a tagging strategy:\n"
        f"      - install: Package installation tasks\n"
        f"      - config: Configuration tasks\n"
        f"      - service: Service management tasks\n"
        f"      - deploy: Deployment tasks"
    )
```

#### 3.2 Example Output

```python
TagAnalysis(
    total_tasks=50,
    tagged_tasks=15,
    untagged_tasks=35,
    coverage_percentage=30.0,
    tag_frequency={"install": 5, "config": 8, "service": 2},
    suggested_tags={
        ("tasks/main.yml", 0): ["install", "packages"],
        ("tasks/main.yml", 5): ["config", "configuration"],
        # ...
    },
    recommendation="""
❌ Low tag coverage (30.0%). Only 35 of 50 tasks are tagged.
   Recommend implementing a tagging strategy:
      - install: Package installation tasks
      - config: Configuration tasks
      - service: Service management tasks
      - deploy: Deployment tasks
"""
)
```

### Benefits

- **Selective Execution**: Enable `--tags` and `--skip-tags` flags
- **Better Organization**: Tags provide semantic categorization
- **Improved Documentation**: Tags clarify task purposes

### Challenges

- **Tag Standardization**: Different roles use different tag names
- **Over-tagging**: Too many tags can be as bad as no tags
- **Maintenance**: Tags need to be updated as tasks change

---

## 4. Task Dependencies for Parallelization Opportunities

### Motivation

Ansible executes tasks sequentially by default. However, independent tasks could run in parallel using:
- `strategy: free` (all hosts execute independently)
- `async` + `poll` (background tasks)
- `include_tasks` with proper dependencies

Detecting parallelization opportunities can significantly speed up playbook execution.

### Examples

```yaml
# Sequential (slow): All tasks run one after another
- name: Download package A
  get_url:
    url: http://example.com/packageA.tar.gz
    dest: /tmp/packageA.tar.gz

- name: Download package B  # Could run in parallel!
  get_url:
    url: http://example.com/packageB.tar.gz
    dest: /tmp/packageB.tar.gz

- name: Extract package A
  unarchive:
    src: /tmp/packageA.tar.gz
    dest: /opt/packageA

# Optimized (fast): Use async for parallel downloads
- name: Download package A
  get_url:
    url: http://example.com/packageA.tar.gz
    dest: /tmp/packageA.tar.gz
  async: 300
  poll: 0
  register: download_a

- name: Download package B
  get_url:
    url: http://example.com/packageB.tar.gz
    dest: /tmp/packageB.tar.gz
  async: 300
  poll: 0
  register: download_b

- name: Wait for downloads
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  loop:
    - "{{ download_a }}"
    - "{{ download_b }}"

- name: Extract package A
  unarchive:
    src: /tmp/packageA.tar.gz
    dest: /opt/packageA
```

### Implementation Approach

#### 4.1 Dependency Graph Analysis

```python
from dataclasses import dataclass
from typing import Set
import re

@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""

    task_index: int
    depends_on: set[int]
    writes_to: set[str]  # Resources written (files, vars)
    reads_from: set[str]  # Resources read

@dataclass
class ParallelizationOpportunity:
    """Represents tasks that could run in parallel."""

    task_indices: list[int]
    estimated_speedup: float
    reason: str
    suggestion: str

def analyze_task_dependencies(
    tasks: list[dict]
) -> tuple[list[TaskDependency], list[ParallelizationOpportunity]]:
    """Analyze task dependencies and find parallelization opportunities.

    Args:
        tasks: List of task dictionaries

    Returns:
        Tuple of (dependencies, parallelization_opportunities)
    """
    dependencies = []

    for idx, task in enumerate(tasks):
        # Extract what this task reads and writes
        reads = _extract_reads(task)
        writes = _extract_writes(task)

        # Determine dependencies
        depends_on = set()
        for prev_idx in range(idx):
            prev_dep = dependencies[prev_idx]

            # Depends if we read something prev task wrote
            if reads & prev_dep.writes_to:
                depends_on.add(prev_idx)

            # Depends if we write something prev task wrote (WAW)
            if writes & prev_dep.writes_to:
                depends_on.add(prev_idx)

            # Depends if we write something prev task read (WAR - rare)
            if writes & prev_dep.reads_from:
                depends_on.add(prev_idx)

        dependencies.append(TaskDependency(
            task_index=idx,
            depends_on=depends_on,
            writes_to=writes,
            reads_from=reads
        ))

    # Find parallelization opportunities
    opportunities = _find_parallel_groups(dependencies, tasks)

    return dependencies, opportunities

def _extract_reads(task: dict) -> set[str]:
    """Extract resources read by a task."""
    reads = set()

    # Files read
    for param in ["src", "template", "source"]:
        if param in task:
            reads.add(f"file:{task[param]}")

    # Variables read (detect {{ var_name }} patterns)
    task_str = str(task)
    var_pattern = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")
    for var_name in var_pattern.findall(task_str):
        reads.add(f"var:{var_name}")

    # Registered variables from previous tasks
    if "when" in task:
        when_str = str(task["when"])
        for var_name in var_pattern.findall(when_str):
            reads.add(f"var:{var_name}")

    return reads

def _extract_writes(task: dict) -> set[str]:
    """Extract resources written by a task."""
    writes = set()

    # Files written
    for param in ["dest", "path", "name"]:
        if param in task:
            value = task[param]
            if isinstance(value, str) and (value.startswith("/") or value.startswith("~/")):
                writes.add(f"file:{value}")

    # Variables registered
    if "register" in task:
        writes.add(f"var:{task['register']}")

    # set_fact writes variables
    if task.get("module") == "set_fact":
        for key in task.keys():
            if key not in ["name", "module", "when", "tags"]:
                writes.add(f"var:{key}")

    return writes

def _find_parallel_groups(
    dependencies: list[TaskDependency],
    tasks: list[dict]
) -> list[ParallelizationOpportunity]:
    """Find groups of independent tasks that could run in parallel."""
    opportunities = []

    # Strategy: Find consecutive tasks with no mutual dependencies
    for i in range(len(dependencies)):
        parallel_group = [i]

        for j in range(i + 1, min(i + 10, len(dependencies))):  # Look ahead max 10 tasks
            # Check if task j is independent of all tasks in current group
            independent = True
            for group_idx in parallel_group:
                # Check if j depends on group_idx or vice versa
                if group_idx in dependencies[j].depends_on:
                    independent = False
                    break

                # Check for resource conflicts
                if dependencies[j].writes_to & dependencies[group_idx].writes_to:
                    independent = False
                    break

                if dependencies[j].writes_to & dependencies[group_idx].reads_from:
                    independent = False
                    break

            if independent:
                parallel_group.append(j)

        # Report if we found 2+ independent tasks
        if len(parallel_group) >= 2:
            speedup = _estimate_speedup(parallel_group, tasks)
            reason = _explain_independence(parallel_group, dependencies)
            suggestion = _generate_async_suggestion(parallel_group, tasks)

            opportunities.append(ParallelizationOpportunity(
                task_indices=parallel_group,
                estimated_speedup=speedup,
                reason=reason,
                suggestion=suggestion
            ))

    return opportunities

def _estimate_speedup(group: list[int], tasks: list[dict]) -> float:
    """Estimate potential speedup from parallelizing this group."""
    # Heuristic: Higher speedup for I/O-bound tasks
    io_modules = ["get_url", "uri", "apt", "yum", "pip", "git", "unarchive"]

    io_tasks = sum(1 for idx in group if tasks[idx].get("module") in io_modules)
    cpu_tasks = len(group) - io_tasks

    # I/O tasks benefit more from parallelization
    if io_tasks >= 2:
        return float(len(group)) * 0.8  # Near-linear speedup
    else:
        return float(len(group)) * 0.5  # CPU-bound tasks have diminishing returns

def _explain_independence(group: list[int], deps: list[TaskDependency]) -> str:
    """Explain why these tasks are independent."""
    if len(group) == 2:
        return (
            f"Tasks {group[0]} and {group[1]} are independent:\n"
            f"  - No shared file or variable dependencies\n"
            f"  - Can execute simultaneously without conflicts"
        )
    else:
        return (
            f"Tasks {group} form an independent group:\n"
            f"  - {len(group)} tasks with no mutual dependencies\n"
            f"  - Safe to parallelize using async execution"
        )

def _generate_async_suggestion(group: list[int], tasks: list[dict]) -> str:
    """Generate suggestion for async execution."""
    if len(group) == 2:
        return f"""
Use async execution for parallel downloads:

# Task {group[0]}
- name: {tasks[group[0]].get('name', 'Task 1')}
  {tasks[group[0]].get('module')}:
    ...
  async: 300
  poll: 0
  register: async_task_{group[0]}

# Task {group[1]}
- name: {tasks[group[1]].get('name', 'Task 2')}
  {tasks[group[1]].get('module')}:
    ...
  async: 300
  poll: 0
  register: async_task_{group[1]}

# Wait for completion
- name: Wait for async tasks
  async_status:
    jid: "{{{{ item.ansible_job_id }}}}"
  register: job_result
  until: job_result.finished
  retries: 30
  loop:
    - "{{{{ async_task_{group[0]} }}}}"
    - "{{{{ async_task_{group[1]} }}}}"
"""
    else:
        task_list = "\n".join(f"    - async_task_{idx}" for idx in group)
        return f"""
Parallelize {len(group)} independent tasks using async:

1. Add async: 300, poll: 0 to each task
2. Register each as async_task_{{index}}
3. Wait for completion:

- name: Wait for all async tasks
  async_status:
    jid: "{{{{ item.ansible_job_id }}}}"
  register: job_result
  until: job_result.finished
  retries: 30
  loop:
{task_list}
"""
```

#### 4.2 Example Output

```python
ParallelizationOpportunity(
    task_indices=[3, 4, 5],
    estimated_speedup=2.4,
    reason="""
Tasks [3, 4, 5] form an independent group:
  - 3 tasks with no mutual dependencies
  - Safe to parallelize using async execution
""",
    suggestion="""
Parallelize 3 independent tasks using async:

1. Add async: 300, poll: 0 to each task
2. Register each as async_task_{index}
3. Wait for completion:

- name: Wait for all async tasks
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: job_result
  until: job_result.finished
  retries: 30
  loop:
    - async_task_3
    - async_task_4
    - async_task_5
"""
)
```

### Benefits

- **Faster Execution**: 2-3x speedup for I/O-bound tasks
- **Better Resource Utilization**: Overlap waiting times
- **Clearer Dependencies**: Explicit dependency tracking

### Challenges

- **Complexity**: Dependency analysis is difficult (hidden dependencies)
- **False Positives**: Conservative analysis needed to avoid breaking playbooks
- **Async Limitations**: Not all modules support async execution
- **Error Handling**: Parallel tasks complicate error recovery

---

## 5. Integration into Complexity Analyzer

### 5.1 Proposed Module Structure

```
docsible/analyzers/complexity_analyzer/
├── similarity.py         # Task similarity detection
├── variables.py          # Variable extraction suggestions
├── tags.py               # Tag coverage analysis
├── parallelization.py    # Dependency and parallelization analysis
└── advanced_analyzer.py  # Orchestrator for all advanced features
```

### 5.2 Unified Advanced Analysis Report

```python
@dataclass
class AdvancedComplexityReport:
    """Extended complexity report with advanced analysis."""

    # Existing complexity metrics
    basic_report: ComplexityReport

    # Advanced features
    similar_task_groups: list[SimilarTaskGroup] = field(default_factory=list)
    repeated_values: list[RepeatedValue] = field(default_factory=list)
    tag_analysis: TagAnalysis | None = None
    parallelization_opportunities: list[ParallelizationOpportunity] = field(default_factory=list)

    # Summary statistics
    refactoring_potential: str = ""
    optimization_score: float = 0.0  # 0-100

def analyze_role_advanced(
    role_info: dict,
    enable_similarity: bool = True,
    enable_variables: bool = True,
    enable_tags: bool = True,
    enable_parallelization: bool = False  # Disabled by default (experimental)
) -> AdvancedComplexityReport:
    """Perform advanced complexity analysis.

    Args:
        role_info: Role information dictionary
        enable_similarity: Detect similar tasks
        enable_variables: Suggest variable extraction
        enable_tags: Analyze tag coverage
        enable_parallelization: Find parallelization opportunities (experimental)

    Returns:
        Advanced complexity report with all enabled analyses
    """
    # Start with basic analysis
    basic = analyze_role_complexity(role_info)

    # Run advanced analyses
    similar_groups = []
    if enable_similarity:
        similarity_analyzer = TaskSimilarityAnalyzer()
        similar_groups = similarity_analyzer.analyze(role_info)

    repeated_vals = []
    if enable_variables:
        repeated_vals = extract_repeated_values(role_info, min_count=3)

    tag_info = None
    if enable_tags:
        tag_info = analyze_tag_coverage(role_info)

    parallel_ops = []
    if enable_parallelization:
        for task_file in role_info.get("tasks", []):
            _, ops = analyze_task_dependencies(task_file.get("tasks", []))
            parallel_ops.extend(ops)

    # Calculate optimization score
    opt_score = _calculate_optimization_score(
        similar_groups, repeated_vals, tag_info, parallel_ops
    )

    # Generate summary
    summary = _generate_refactoring_summary(
        similar_groups, repeated_vals, tag_info, parallel_ops
    )

    return AdvancedComplexityReport(
        basic_report=basic,
        similar_task_groups=similar_groups,
        repeated_values=repeated_vals,
        tag_analysis=tag_info,
        parallelization_opportunities=parallel_ops,
        refactoring_potential=summary,
        optimization_score=opt_score
    )
```

### 5.3 CLI Integration

```python
# In docsible/commands/document_role/options/analysis.py

@click.option(
    "--advanced-analysis",
    is_flag=True,
    help="Enable advanced complexity analysis (similarity, variables, tags)"
)
@click.option(
    "--detect-duplicates",
    is_flag=True,
    help="Detect similar tasks that could use loops"
)
@click.option(
    "--suggest-variables",
    is_flag=True,
    help="Suggest variable extraction for repeated values"
)
@click.option(
    "--check-tags",
    is_flag=True,
    help="Analyze tag coverage and suggest improvements"
)
@click.option(
    "--find-parallelization",
    is_flag=True,
    help="Find parallelization opportunities (experimental)"
)
```

---

## 6. Performance Considerations

### Complexity Analysis

| Feature | Time Complexity | Memory | Performance Impact |
|---------|----------------|--------|-------------------|
| Similarity Detection | O(n²) per file | O(n) | Moderate (10-100ms per file) |
| Variable Extraction | O(n×m) | O(n) | Low (5-20ms per role) |
| Tag Analysis | O(n) | O(1) | Negligible (<5ms) |
| Parallelization | O(n²) | O(n) | High (100-500ms per file) |

### Optimization Strategies

1. **Lazy Evaluation**: Only run expensive analyses when requested
2. **Caching**: Cache analysis results (see CACHING_ANALYSIS.md)
3. **Sampling**: For very large files (100+ tasks), sample for similarity
4. **Parallelization**: Run different analyses in parallel (ironically!)

---

## 7. Recommendations

### Implement First (High Value, Low Effort)

1. **Tag Analysis** - Simple, fast, high value for users
   - Effort: 2-3 hours
   - Impact: Improves role usability significantly

2. **Variable Extraction** - Straightforward implementation
   - Effort: 3-4 hours
   - Impact: Identifies clear refactoring opportunities

### Implement Later (High Value, High Effort)

3. **Similarity Detection** - More complex, but very useful
   - Effort: 5-6 hours (including edge cases)
   - Impact: Catches 80% of duplication patterns

### Experimental (High Effort, Uncertain Value)

4. **Parallelization Analysis** - Highly complex, limited applicability
   - Effort: 8-10 hours
   - Impact: Only useful for specific workflows
   - Risk: High false positive rate

### Integration Roadmap

**Phase 1** (Immediate):
- Tag analysis
- Variable extraction
- Basic documentation

**Phase 2** (1-2 weeks):
- Similarity detection
- Integration with complexity report
- CLI flags

**Phase 3** (Future):
- Parallelization analysis (experimental flag)
- Advanced dependency tracking
- Performance profiling tools

---

## 8. Conclusion

These four advanced features would significantly enhance Docsible's ability to identify refactoring opportunities and optimization potential:

1. **Task Similarity** → Reduce duplication via loops
2. **Variable Extraction** → Improve configurability
3. **Tag Analysis** → Enable selective execution
4. **Parallelization** → Speed up playbook runs

**Recommended Priority**: Tag Analysis → Variable Extraction → Similarity Detection → Parallelization

**Total Effort**: 10-15 hours for full implementation of first three features
**Expected Value**: High - would differentiate Docsible from other Ansible documentation tools
