# Pattern Analyzer Usage Guide

The Pattern Analyzer provides comprehensive detection of anti-patterns and code smells in Ansible roles, offering actionable suggestions for improvement.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Output](#understanding-the-output)
3. [Advanced Usage](#advanced-usage)
4. [Creating Custom Detectors](#creating-custom-detectors)
5. [Integration with Complexity Analyzer](#integration-with-complexity-analyzer)

---

## Quick Start

### Basic Analysis

```python
from docsible.analyzers.patterns import analyze_role_patterns
from docsible.parsers.role_parser import parse_role

# Parse role
role_info = parse_role('/path/to/ansible/role')

# Analyze patterns
report = analyze_role_patterns(role_info)

# Print summary
print(f"Overall Health Score: {report.overall_health_score}/100")
print(f"Total Issues Found: {report.total_patterns}")
print(f"  Critical: {report.by_severity['critical']}")
print(f"  Warnings: {report.by_severity['warning']}")
print(f"  Info: {report.by_severity['info']}")

# Show all suggestions
for suggestion in report.suggestions:
    print(f"\n{suggestion.severity.upper()}: {suggestion.description}")
    print(f"Pattern: {suggestion.pattern}")
    print(f"Files: {', '.join(suggestion.affected_files)}")
    print(f"Impact: {suggestion.impact}")
```

### Filter by Severity

```python
# Show only critical issues
critical_issues = [
    s for s in report.suggestions
    if s.severity == 'critical'
]

for issue in critical_issues:
    print(f"CRITICAL: {issue.description}")
    print(f"Example:\n{issue.example}")
    print(f"How to fix:\n{issue.suggestion}\n")
```

### Filter by Category

```python
# Show only security issues
security_issues = [
    s for s in report.suggestions
    if s.category == 'security'
]

for issue in security_issues:
    print(f"Security Issue: {issue.description}")
    print(f"Confidence: {issue.confidence * 100}%")
```

---

## Understanding the Output

### SimplificationSuggestion Model

Each detected pattern returns a `SimplificationSuggestion` with:

| Field | Type | Description |
|-------|------|-------------|
| `pattern` | str | Unique identifier (e.g., `"repeated_package_install"`) |
| `category` | enum | High-level category (`duplication`, `security`, etc.) |
| `severity` | enum | Importance level (`info`, `warning`, `critical`) |
| `description` | str | What was found |
| `example` | str | Code snippet showing the issue |
| `suggestion` | str | How to fix it (with code examples) |
| `affected_files` | list | Files where pattern appears |
| `impact` | str | Expected benefit of fixing |
| `confidence` | float | How certain we are (0.0-1.0) |

### Pattern Categories

- **`duplication`**: Repeated code/tasks
- **`complexity`**: Overly complex logic
- **`security`**: Security vulnerabilities
- **`maintainability`**: Hard to maintain code
- **`idempotency`**: Non-idempotent operations
- **`organization`**: Poor file structure
- **`performance`**: Performance issues
- **`error_handling`**: Missing error handling

### Severity Levels

- **`info`**: Minor improvements, nice-to-have
- **`warning`**: Should be addressed, impacts quality
- **`critical`**: Must be fixed, security/reliability risk

---

## Advanced Usage

### Customize Detector Selection

```python
from docsible.analyzers.patterns import PatternAnalyzer
from docsible.analyzers.patterns.detectors import (
    SecurityDetector,
    DuplicationDetector
)

# Only run security and duplication checks
analyzer = PatternAnalyzer(
    enabled_detectors=[SecurityDetector, DuplicationDetector]
)

report = analyzer.analyze(role_info)
```

### Set Confidence Threshold

```python
# Only show high-confidence patterns (≥80%)
analyzer = PatternAnalyzer(min_confidence=0.8)
report = analyzer.analyze(role_info)

# Lower threshold for exploratory analysis
analyzer = PatternAnalyzer(min_confidence=0.5)
report = analyzer.analyze(role_info)
```

### Programmatic Filtering

```python
# Get critical security issues only
critical_security = [
    s for s in report.suggestions
    if s.severity == 'critical' and s.category == 'security'
]

# Get high-confidence warnings
high_confidence_warnings = [
    s for s in report.suggestions
    if s.severity == 'warning' and s.confidence >= 0.9
]

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for suggestion in report.suggestions:
    by_category[suggestion.category].append(suggestion)
```

### Export Results

```python
import json

# Export to JSON
report_dict = report.model_dump()
with open('pattern_analysis.json', 'w') as f:
    json.dump(report_dict, f, indent=2)

# Export critical issues to CSV
import csv
with open('critical_issues.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Pattern', 'Severity', 'Description', 'Files'])

    for s in report.suggestions:
        if s.severity == 'critical':
            writer.writerow([
                s.pattern,
                s.severity,
                s.description,
                '; '.join(s.affected_files)
            ])
```

---

## Creating Custom Detectors

### Step 1: Create Detector Class

```python
# my_detector.py
from typing import List, Dict, Any
from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.models import (
    SimplificationSuggestion,
    SeverityLevel,
    PatternCategory
)

class MyCustomDetector(BasePatternDetector):
    """Detects custom anti-patterns."""

    @property
    def pattern_category(self) -> PatternCategory:
        """Return the category this detector handles."""
        return PatternCategory.MAINTAINABILITY

    def detect(self, role_info: Dict[str, Any]) -> List[SimplificationSuggestion]:
        """Main detection logic."""
        suggestions = []

        # Use helper methods from base class
        tasks = self._flatten_tasks(role_info)

        # Example: Detect tasks with TODO comments
        for task in tasks:
            task_name = task.get('name', '').lower()

            if 'todo' in task_name or 'fixme' in task_name:
                suggestions.append(SimplificationSuggestion(
                    pattern="unfinished_task",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description=f"Task '{task.get('name')}' has TODO/FIXME marker",
                    example=self._show_task(task),
                    suggestion=(
                        "Complete the task or create a GitHub issue:\n\n"
                        "1. Finish the implementation\n"
                        "2. Remove the TODO marker\n"
                        "3. Or create a tracking issue and reference it"
                    ),
                    affected_files=[task.get('file')],
                    impact="Ensures all tasks are complete",
                    confidence=1.0
                ))

        return suggestions
```

### Step 2: Use Custom Detector

```python
from docsible.analyzers.patterns import PatternAnalyzer
from my_detector import MyCustomDetector

analyzer = PatternAnalyzer(
    enabled_detectors=[MyCustomDetector]
)

report = analyzer.analyze(role_info)
```

### Available Helper Methods

The `BasePatternDetector` provides these utilities:

```python
# Get all tasks as flat list
tasks = self._flatten_tasks(role_info)

# Get list of task files
task_files = self._get_task_files(role_info)

# Count tasks by module
counts = self._count_tasks_by_module(role_info)
# {'apt': 12, 'service': 5, 'template': 8}

# Get tasks using specific module
apt_tasks = self._get_tasks_by_module(role_info, 'apt')

# Check if task has attributes
has_when = self._has_attribute(task, 'when', 'condition')

# Get unique file names from tasks
files = self._get_unique_files(tasks)

# Generate example snippets
snippet = self._show_task_snippet(tasks, limit=3)
single = self._show_task(task, include_module_args=True)
```

---

## Integration with Complexity Analyzer

### Combine Pattern Analysis with Complexity Report

```python
from docsible.analyzers.complexity_analyzer import analyze_role
from docsible.analyzers.patterns import analyze_role_patterns

# Get complexity report
complexity = analyze_role(role_info)

# Get pattern analysis
patterns = analyze_role_patterns(role_info)

# Combine insights
print(f"Complexity: {complexity.category}")
print(f"Task Files: {complexity.metrics.task_file_count}")
print(f"Total Tasks: {complexity.metrics.total_tasks}")
print(f"\nPattern Analysis:")
print(f"Health Score: {patterns.overall_health_score}/100")
print(f"Issues Found: {patterns.total_patterns}")

# Show patterns relevant to complexity
if complexity.category == "complex":
    # Show organization and complexity patterns
    relevant = [
        s for s in patterns.suggestions
        if s.category in ['organization', 'complexity']
    ]
    for s in relevant:
        print(f"- {s.description}")
```

### Add Patterns to ComplexityReport

```python
# Extend ComplexityReport to include patterns
from dataclasses import dataclass

@dataclass
class EnhancedComplexityReport:
    """Complexity report with pattern analysis."""
    complexity_report: ComplexityReport
    pattern_report: PatternAnalysisReport

    @property
    def actionable_suggestions(self) -> List[SimplificationSuggestion]:
        """Get most important suggestions based on complexity."""
        if self.complexity_report.category == "complex":
            # Prioritize critical and warning level
            return [
                s for s in self.pattern_report.suggestions
                if s.severity in ['critical', 'warning']
            ]
        else:
            # Only show critical for simple roles
            return [
                s for s in self.pattern_report.suggestions
                if s.severity == 'critical'
            ]

# Usage
complexity = analyze_role(role_info)
patterns = analyze_role_patterns(role_info)
enhanced = EnhancedComplexityReport(complexity, patterns)

for suggestion in enhanced.actionable_suggestions:
    print(f"{suggestion.severity}: {suggestion.description}")
```

---

## Best Practices

### 1. Start with Critical Issues

```python
# Fix critical issues first
critical = analyzer.analyze_critical_only(role_info)
for issue in critical:
    print(f"Must fix: {issue.description}")
```

### 2. Use Confidence Thresholds

```python
# High confidence for production
prod_analyzer = PatternAnalyzer(min_confidence=0.85)

# Lower confidence for exploration
dev_analyzer = PatternAnalyzer(min_confidence=0.6)
```

### 3. Focus on High-Impact Patterns

```python
# Prioritize by impact
high_impact_patterns = [
    'exposed_secrets',          # Security
    'shell_injection_risk',     # Security
    'missing_idempotency',      # Reliability
    'repeated_package_install', # Performance
    'monolithic_main_file',     # Maintainability
]

priority_issues = [
    s for s in report.suggestions
    if s.pattern in high_impact_patterns
]
```

### 4. Integrate into CI/CD

```python
#!/usr/bin/env python3
"""CI check for role quality."""

import sys
from docsible.analyzers.patterns import analyze_role_patterns
from docsible.parsers.role_parser import parse_role

def check_role_quality(role_path: str) -> int:
    """Return 0 if quality acceptable, 1 otherwise."""
    role_info = parse_role(role_path)
    report = analyze_role_patterns(role_info, min_confidence=0.8)

    # Fail if critical issues found
    if report.by_severity['critical'] > 0:
        print(f"FAILED: {report.by_severity['critical']} critical issues")
        return 1

    # Fail if health score too low
    if report.overall_health_score < 70:
        print(f"FAILED: Health score {report.overall_health_score} < 70")
        return 1

    print(f"PASSED: Health score {report.overall_health_score}/100")
    return 0

if __name__ == '__main__':
    sys.exit(check_role_quality('.'))
```

---

## Pattern Detection Reference

### Duplication Patterns
- `repeated_package_install` - Multiple package tasks
- `repeated_service_operations` - Multiple service tasks
- `repeated_directory_creation` - Multiple directory tasks
- `similar_task_names` - Tasks with similar naming patterns

### Complexity Patterns
- `complex_conditional` - Overly complex when conditions
- `deep_include_chain` - Too many levels of includes
- `excessive_set_fact` - Overuse of set_fact tasks

### Security Patterns
- `exposed_secrets` - Plain-text secrets
- `missing_no_log` - Secrets without no_log
- `insecure_file_permissions` - Overly permissive file modes
- `shell_injection_risk` - Unsafe shell commands

### Maintainability Patterns
- `missing_idempotency` - Non-idempotent operations
- `monolithic_main_file` - Too many tasks in main.yml
- `magic_values` - Hard-coded literals
- `missing_check_mode` - No check mode support
- `missing_failed_when` - Pipelines without error handling
- `variable_shadowing` - Variables defined in multiple places

---

For more information, see the inline documentation in each detector module.
