# FIXME Analysis and Fix Plan

This document analyzes all #FIXME comments in the codebase, explains why they should be fixed, and shows how to fix them.

## Summary

| File | Line | Severity | Status |
|------|------|----------|--------|
| security.py | 19 | Low | Design question |
| file_analyzer.py | 91 | Low | Missing detail |
| file_analyzer.py | 110 | **High** | Dead code |
| role_analyzer.py | 17 | **High** | Dead code |
| role_analyzer.py | 284 | **High** | Broken function |
| recommendations.py | 15 | **High** | Maintainability |
| models.py | 46 | Medium | Design question |
| loader.py | 41 | **High** | Maintainability |

---

## 1. security.py:19 - Secret Indicators Pluggability

**Location:** `docsible/analyzers/patterns/detectors/security.py:19`

**Current Code:**
```python
#FIXME Should secret indicators not be pluggable?
SECRET_INDICATORS = [
    "password", "secret", "token", "api_key", ...
]
```

**Why Fix:**
- **Extensibility**: Users may need custom secret patterns
- **Flexibility**: Different projects have different secret naming conventions
- **Best Practice**: Hard-coded patterns limit usefulness

**Severity:** Low (works fine, just not extensible)

**How to Fix:**
```python
# Option 1: Load from config file
def load_secret_indicators(config_path: Path | None = None) -> list[str]:
    """Load secret indicators from config, with fallback to defaults."""
    default_indicators = [
        "password", "secret", "token", "api_key", ...
    ]

    if config_path and config_path.exists():
        with open(config_path) as f:
            custom = yaml.safe_load(f).get("secret_indicators", [])
            return default_indicators + custom

    return default_indicators

SECRET_INDICATORS = load_secret_indicators()

# Option 2: Plugin system (more complex)
class SecretDetectorPlugin:
    def get_indicators(self) -> list[str]:
        raise NotImplementedError

# Then register plugins...
```

**Recommendation:** Low priority. Current implementation works well. Only implement if users request custom patterns.

---

## 2. file_analyzer.py:91 - Missing Detailed Concern

**Location:** `docsible/analyzers/complexity_analyzer/analyzers/file_analyzer.py:91`

**Current Code:**
```python
#FIXME Missing detailed concern
concern = "High complexity file"
```

**Why Fix:**
- **User Experience**: Vague message doesn't help users understand the problem
- **Actionability**: Users need specific guidance on what to refactor

**Severity:** Low (works, just not helpful)

**How to Fix:**
```python
# Provide specific metrics that triggered the concern
metrics = []
if conditional_tasks > 5:
    metrics.append(f"{conditional_tasks} conditional tasks")
if nested_loops > 2:
    metrics.append(f"{nested_loops} nested loops")
if error_handling_blocks > 3:
    metrics.append(f"{error_handling_blocks} error handling blocks")

concern = f"High complexity file: {', '.join(metrics)}. Consider splitting into smaller files."
```

**Recommendation:** Medium priority. Improves user experience.

---

## 3. file_analyzer.py:110 - Unused Function ⚠️ CRITICAL

**Location:** `docsible/analyzers/complexity_analyzer/analyzers/file_analyzer.py:110`

**Current Code:**
```python
#FIXME Unused function
def _calculate_something(...):
    # ... implementation
```

**Why Fix:**
- **Code Smell**: Dead code clutters the codebase
- **Maintenance**: Unused code needs to be maintained but provides no value
- **Confusion**: Future developers waste time understanding unused code
- **Testing**: Dead code may not be tested, causing false confidence

**Severity:** **HIGH** - Dead code should be removed

**How to Fix:**
```python
# Simply delete the function
# If there's any chance it might be needed:
# 1. Check git history to see when it was last used
# 2. If needed in future, restore from git
# 3. Otherwise, delete it
```

**Recommendation:** **Delete immediately**. Dead code has no place in production.

---

## 4. role_analyzer.py:17 - Unused Pattern Analysis Import ⚠️ CRITICAL

**Location:** `docsible/analyzers/complexity_analyzer/analyzers/role_analyzer.py:17`

**Current Code:**
```python
try:
    #FIXME Not used  PatternAnalysisReport and analyze_role_patterns unbound warning
    from docsible.analyzers.patterns import (
        PatternAnalysisReport,
        analyze_role_patterns,
    )
    PATTERN_ANALYSIS_AVAILABLE = True
except ImportError:
    logger.debug("Pattern analysis not available")
    PATTERN_ANALYSIS_AVAILABLE = False
    PatternAnalysisReport = None  # type: ignore
```

**Why Fix:**
- **Confusion**: Comment says "Not used" but code imports them
- **Actually Used**: Later in the file (lines 179-196), these ARE used!
- **False Warning**: The FIXME is incorrect

**Severity:** **HIGH** - Misleading comment

**How to Fix:**
```python
# The FIXME is WRONG - these imports ARE used!
# Just remove the FIXME comment.

try:
    from docsible.analyzers.patterns import (
        PatternAnalysisReport,
        analyze_role_patterns,
    )
    PATTERN_ANALYSIS_AVAILABLE = True
except ImportError:
    logger.debug("Pattern analysis not available")
    PATTERN_ANALYSIS_AVAILABLE = False
    PatternAnalysisReport = None  # type: ignore
```

**Recommendation:** **Remove FIXME comment immediately**. The code is correct.

---

## 5. role_analyzer.py:284 - Broken Function ⚠️ CRITICAL

**Location:** `docsible/analyzers/complexity_analyzer/analyzers/role_analyzer.py:284`

**Current Code:**
```python
#FIXME What happened here?
def _file_has_integrations(
    task_file: dict[str, Any], integration_points: list[IntegrationPoint]
) -> int:
    """Count how many integration points a task file touches."""
    # Simple count for now - can be enhanced
    return 0
```

**Why Fix:**
- **Broken Functionality**: Always returns 0, never actually counts integrations
- **Used in Reports**: This value appears in complexity reports as `has_integrations`
- **Misleading**: Reports show `"has_integrations": 0` even when integrations exist

**Severity:** **HIGH** - Broken functionality

**How to Fix:**
```python
def _file_has_integrations(
    task_file: dict[str, Any], integration_points: list[IntegrationPoint]
) -> int:
    """Count how many integration points a task file touches.

    Args:
        task_file: Task file dict with "file" and "tasks" keys
        integration_points: List of all detected integration points

    Returns:
        Number of integration points this file touches
    """
    file_name = task_file.get("file", "")
    tasks = task_file.get("tasks", [])

    count = 0
    for integration in integration_points:
        # Check if this integration is in this file
        if integration.file == file_name:
            count += 1
        # Alternative: check if any task in this file uses the integration module
        elif any(task.get("module") == integration.module for task in tasks):
            count += 1

    return count
```

**Recommendation:** **Fix immediately**. This is broken functionality.

---

## 6. recommendations.py:15 - Function Too Long ⚠️ CRITICAL

**Location:** `docsible/analyzers/complexity_analyzer/recommendations.py:15`

**Current Code:**
```python
#FIXME Too long, need helper functions to be more readable
def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    ...
) -> list[str]:
    """Generate recommendations..."""
    # 297 lines of code!
    recommendations = []

    # Security recommendations (lines 50-100)
    if has_vault:
        recommendations.append(...)
    if has_secrets:
        recommendations.append(...)

    # Complexity recommendations (lines 101-150)
    if metrics.total_tasks > 100:
        recommendations.append(...)

    # Integration recommendations (lines 151-200)
    ...

    # Documentation recommendations (lines 201-250)
    ...

    # Testing recommendations (lines 251-297)
    ...

    return recommendations
```

**Why Fix:**
- **Maintainability**: 297-line function is impossible to understand
- **Testing**: Can't test individual recommendation types
- **Extensibility**: Adding new recommendations requires editing huge function
- **Readability**: Cognitive load is too high
- **Violation**: Single Responsibility Principle - does too many things

**Severity:** **HIGH** - Serious maintainability issue

**How to Fix:**
```python
# Break into focused helper functions

def _generate_security_recommendations(
    role_info: dict,
    integration_points: list[IntegrationPoint],
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> list[str]:
    """Generate security-related recommendations."""
    recommendations = []

    # Check for vault usage
    has_vault = any(ip.integration_type == IntegrationType.VAULT
                    for ip in integration_points)
    if has_vault:
        recommendations.append(_format_vault_recommendation(repository_url, repo_type, repo_branch))

    # Check for secrets
    if _has_hardcoded_secrets(role_info):
        recommendations.append("⚠️ Hardcoded secrets detected. Use Ansible Vault.")

    return recommendations


def _generate_complexity_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    file_details: list[FileComplexityDetail],
) -> list[str]:
    """Generate complexity-related recommendations."""
    recommendations = []

    if metrics.total_tasks > 100:
        recommendations.append("📚 Large role with 100+ tasks. Consider splitting into sub-roles.")

    if category == ComplexityCategory.COMPLEX:
        recommendations.append("🔧 Complex role detected. Review for simplification opportunities.")

    # Check for complex files
    complex_files = [f for f in file_details if f.complexity_score > 50]
    if complex_files:
        file_list = ", ".join(f.file_path for f in complex_files[:3])
        recommendations.append(f"📁 Complex files detected: {file_list}")

    return recommendations


def _generate_integration_recommendations(
    integration_points: list[IntegrationPoint],
) -> list[str]:
    """Generate integration-related recommendations."""
    recommendations = []

    if len(integration_points) > 5:
        recommendations.append("🔌 Multiple integrations detected. Document integration points.")

    # Check for specific integration types
    has_api = any(ip.integration_type == IntegrationType.API for ip in integration_points)
    if has_api:
        recommendations.append("🌐 API integration detected. Implement retry logic and error handling.")

    return recommendations


def _generate_testing_recommendations(
    metrics: ComplexityMetrics,
    file_details: list[FileComplexityDetail],
) -> list[str]:
    """Generate testing-related recommendations."""
    recommendations = []

    if metrics.conditional_tasks > 10:
        recommendations.append("🧪 Many conditional tasks. Ensure comprehensive testing.")

    if metrics.error_handlers > 5:
        recommendations.append("🛡️ Complex error handling. Test failure scenarios.")

    return recommendations


def _generate_documentation_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    inflection_points: list[InflectionPoint],
) -> list[str]:
    """Generate documentation-related recommendations."""
    recommendations = []

    if category == ComplexityCategory.COMPLEX:
        recommendations.append("📖 Complex role. Add architecture diagrams and workflow documentation.")

    if len(inflection_points) > 3:
        recommendations.append("🔀 Multiple decision points. Document branching logic.")

    return recommendations


# Main function becomes a coordinator
def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    integration_points: list[IntegrationPoint],
    inflection_points: list[InflectionPoint],
    file_details: list[FileComplexityDetail],
    hotspots: list[ConditionalHotspot],
    role_info: dict,
    repository_url: str | None = None,
    repo_type: str | None = None,
    repo_branch: str | None = None,
) -> list[str]:
    """Generate comprehensive recommendations for role improvement.

    Now a clean coordinator that delegates to focused helper functions.
    """
    recommendations = []

    # Delegate to focused functions
    recommendations.extend(_generate_security_recommendations(
        role_info, integration_points, repository_url, repo_type, repo_branch
    ))

    recommendations.extend(_generate_complexity_recommendations(
        metrics, category, file_details
    ))

    recommendations.extend(_generate_integration_recommendations(
        integration_points
    ))

    recommendations.extend(_generate_testing_recommendations(
        metrics, file_details
    ))

    recommendations.extend(_generate_documentation_recommendations(
        metrics, category, inflection_points
    ))

    return recommendations
```

**Benefits:**
- Each function is 15-30 lines (manageable)
- Each function has single responsibility
- Easy to test individually
- Easy to add new recommendation types
- Much more readable

**Recommendation:** **Refactor immediately**. This is a serious maintainability issue.

---

## 7. models.py:46 - TypedDict vs BaseModel

**Location:** `docsible/analyzers/phase_detector/models.py:46`

**Current Code:**
```python
#FIXME Should below model not be based on BaseModel why TypeDict
class PhaseInfo(TypedDict):
    name: str
    tasks: list[dict]
```

**Why Fix:**
- **Consistency**: Other models use Pydantic BaseModel
- **Validation**: TypedDict has no runtime validation
- **Features**: BaseModel provides validation, serialization, defaults

**Severity:** Medium (works, but inconsistent)

**How to Fix:**
```python
from pydantic import BaseModel, Field

class PhaseInfo(BaseModel):
    """Phase information model.

    Uses Pydantic BaseModel for consistency with other models
    and to get validation, serialization, and better IDE support.
    """
    name: str = Field(..., description="Phase name")
    tasks: list[dict] = Field(default_factory=list, description="Tasks in this phase")

    class Config:
        # Allow dict access for backward compatibility
        allow_population_by_field_name = True
```

**Recommendation:** Medium priority. Convert to BaseModel for consistency.

---

## 8. loader.py:41 - Function Too Long ⚠️ CRITICAL

**Location:** `docsible/utils/yaml/loader.py:41`

**Current Code:**
```python
#FIXME too long function not readable nor maintainable.
def load_yaml_file_custom(file_path):
    """Load YAML with metadata extraction..."""
    # 300+ lines of complex logic!
    # - Read file
    # - Parse YAML
    # - Extract comments
    # - Parse metadata
    # - Track line numbers
    # - Handle nested structures
    # - Process special cases
    # ... 300+ lines
```

**Why Fix:**
- **Maintainability**: 300+ line function is unmaintainable
- **Testing**: Impossible to test individual concerns
- **Bugs**: Complex logic increases bug probability
- **Understanding**: Takes hours to understand
- **Modification**: High risk of breaking changes

**Severity:** **HIGH** - Serious maintainability issue

**How to Fix:**
```python
# Break into focused helper functions

def _read_file_lines(file_path: str) -> list[str]:
    """Read file and return lines."""
    with open(file_path, encoding="utf-8") as f:
        return f.readlines()


def _parse_yaml_content(file_path: str) -> dict | list | None:
    """Parse YAML file and return raw content."""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extract_comments_for_key(
    lines: list[str],
    key: str,
    start_line: int,
) -> dict[str, Any]:
    """Extract metadata from comments above a key.

    Returns dict with: title, description, required, choices, etc.
    """
    metadata = {
        "title": None,
        "description": None,
        "required": None,
        "choices": None,
    }

    # Look backwards from key line for comments
    for i in range(start_line - 1, max(0, start_line - 10), -1):
        line = lines[i].strip()
        if not line.startswith("#"):
            break

        # Parse comment metadata
        if "title:" in line:
            metadata["title"] = line.split("title:")[1].strip()
        elif "description:" in line:
            metadata["description"] = line.split("description:")[1].strip()
        # ... parse other metadata

    return metadata


def _find_key_line_number(
    lines: list[str],
    key_path: list[str],
) -> int:
    """Find line number where a key is defined."""
    # ... implementation
    return line_number


def _infer_value_type(value: Any) -> str:
    """Infer type of a value."""
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "str"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, dict):
        return "dict"
    else:
        return "unknown"


def _process_dict_with_metadata(
    data: dict,
    lines: list[str],
    key_path: list[str] = None,
) -> dict:
    """Process dictionary and add metadata for each key."""
    key_path = key_path or []
    result = {}

    for key, value in data.items():
        current_path = key_path + [key]

        # Find line number
        line_num = _find_key_line_number(lines, current_path)

        # Extract metadata from comments
        metadata = _extract_comments_for_key(lines, key, line_num)

        # Build metadata-rich structure
        result[key] = {
            "value": value,
            "line": line_num,
            "type": _infer_value_type(value),
            **metadata,
        }

        # Recursively process nested dicts
        if isinstance(value, dict):
            result[key]["value"] = _process_dict_with_metadata(
                value, lines, current_path
            )

    return result


# Main function becomes a coordinator
def load_yaml_file_custom(file_path: str) -> dict | None:
    """Load YAML file with metadata extraction.

    Now a clean coordinator that delegates to focused helper functions.

    Returns dict with metadata-rich structure where each key has:
    - value: The actual value
    - line: Line number where defined
    - type: Inferred type
    - title, description, required, choices: From comments
    """
    try:
        # Read file
        lines = _read_file_lines(file_path)

        # Parse YAML
        data = _parse_yaml_content(file_path)
        if not data:
            return None

        # Process and add metadata
        if isinstance(data, dict):
            return _process_dict_with_metadata(data, lines)
        else:
            # Handle list case if needed
            return data

    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None
```

**Benefits:**
- Each function is 15-40 lines (manageable)
- Each function has single responsibility
- Easy to test individually
- Much more readable
- Easy to modify

**Recommendation:** **Refactor immediately**. This is critical for maintainability.

---

## Priority Summary

### Immediate (This Session)
1. ✅ **role_analyzer.py:17** - Remove incorrect FIXME comment
2. ✅ **role_analyzer.py:284** - Fix `_file_has_integrations()` to actually count integrations
3. ✅ **file_analyzer.py:110** - Delete unused function

### High Priority (Next)
4. **recommendations.py:15** - Refactor 297-line function into helpers
5. **loader.py:41** - Refactor 300+ line function into helpers

### Medium Priority (Future)
6. **file_analyzer.py:91** - Add detailed concern messages
7. **models.py:46** - Convert TypedDict to BaseModel

### Low Priority (Optional)
8. **security.py:19** - Make secret indicators pluggable (only if requested)

---

## Implementation Plan

1. **Quick Wins** (5 minutes):
   - Remove incorrect FIXME in role_analyzer.py:17
   - Delete unused function in file_analyzer.py:110

2. **Fix Broken Functionality** (15 minutes):
   - Implement `_file_has_integrations()` properly

3. **Major Refactoring** (1-2 hours):
   - Refactor `generate_recommendations()` (297 lines)
   - Refactor `load_yaml_file_custom()` (300+ lines)

4. **Polish** (30 minutes):
   - Add detailed concern messages
   - Convert TypedDict to BaseModel
