# Pattern Analyzer Architecture

## Overview

The Pattern Analyzer is a modular, extensible system for detecting anti-patterns in Ansible roles. It uses Pydantic for data validation, implements multiple design patterns, and provides comprehensive pattern detection across security, duplication, complexity, and maintainability categories.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User/Client Code                      │
│  from docsible.analyzers.patterns import analyze_role_patterns │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   PatternAnalyzer                            │
│                   (Facade Pattern)                           │
│  • Coordinates all detectors                                 │
│  • Filters by confidence                                     │
│  • Generates final report                                    │
└────┬────────┬──────────┬──────────┬─────────────────────────┘
     │        │          │          │
     ▼        ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐
│Duplica │ │Complex │ │Security│ │Maintainability│
│tion    │ │  ity   │ │        │ │              │
│Detector│ │Detector│ │Detector│ │  Detector    │
└────┬───┘ └───┬────┘ └───┬────┘ └──────┬───────┘
     │         │           │             │
     └─────────┴───────────┴─────────────┘
                     │
                     │ All extend
                     ▼
         ┌───────────────────────────┐
         │  BasePatternDetector      │
         │  (Template Method Pattern)│
         │  • Common utilities       │
         │  • Helper methods         │
         │  • Abstract interface     │
         └───────────┬───────────────┘
                     │
                     │ Returns
                     ▼
      ┌──────────────────────────────────┐
      │   SimplificationSuggestion       │
      │   (Pydantic BaseModel)           │
      │   • Auto-validation              │
      │   • JSON serialization           │
      │   • Type safety                  │
      └──────────────────────────────────┘
```

## Core Components

### 1. Models (`models.py`)

**Purpose**: Define data structures with automatic validation

**Key Classes**:
- `SimplificationSuggestion`: Individual pattern finding
- `PatternAnalysisReport`: Complete analysis results
- `SeverityLevel`: Enum for severity (info, warning, critical)
- `PatternCategory`: Enum for categories (duplication, security, etc.)

**Why Pydantic**:
```python
class SimplificationSuggestion(BaseModel):
    pattern: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)  # Auto-validates 0-1 range

    @field_validator('affected_files')
    @classmethod
    def validate_files(cls, v: List[str]) -> List[str]:
        return list(set(v))  # Automatic deduplication
```

Benefits:
- ✅ Automatic type checking
- ✅ JSON serialization built-in
- ✅ Field validation (min/max, regex, custom)
- ✅ Clear API documentation
- ✅ IDE autocomplete support

### 2. Base Detector (`base.py`)

**Purpose**: Provide common functionality for all detectors

**Pattern**: Template Method
- Abstract method `detect()` that each detector implements
- Concrete helper methods all detectors can use

**Key Methods**:
```python
class BasePatternDetector(ABC):
    @abstractmethod
    def detect(self, role_info) -> List[SimplificationSuggestion]:
        """Subclasses implement this"""
        pass

    # Helper utilities
    def _flatten_tasks(self, role_info): ...
    def _get_tasks_by_module(self, role_info, module): ...
    def _show_task_snippet(self, tasks, limit): ...
```

**Why This Works**:
- DRY: No code duplication across detectors
- Consistency: All detectors have same utilities
- Easy to extend: New detectors get all helpers for free

### 3. Detectors (`detectors/`)

**Purpose**: Implement specific pattern detection logic

**Pattern**: Strategy Pattern
- Each detector is a separate strategy
- Interchangeable and independent
- Easy to enable/disable

**Current Detectors**:

#### DuplicationDetector
Finds:
- Repeated package installations (apt, yum, dnf)
- Repeated service operations
- Repeated file/directory creation
- Similar task names suggesting patterns

#### ComplexityDetector
Finds:
- Complex conditionals (>3 AND / >2 OR)
- Deep include chains (>3 levels)
- Excessive set_fact usage (>15%)

#### SecurityDetector
Finds:
- Exposed secrets (plain-text passwords)
- Missing no_log directives
- Insecure file permissions (0777)
- Shell injection risks

#### MaintainabilityDetector
Finds:
- Missing idempotency checks
- Monolithic main.yml (>30 tasks)
- Magic values (repeated literals)
- Missing check mode support
- Missing failed_when on pipes
- Variable shadowing (defaults + vars)

### 4. Analyzer (`analyzer.py`)

**Purpose**: Orchestrate all detectors and generate report

**Pattern**: Facade Pattern
- Provides simple interface to complex subsystem
- Hides complexity of multiple detectors
- Handles errors gracefully

**Key Features**:
```python
class PatternAnalyzer:
    def __init__(
        self,
        enabled_detectors: List[Type[BasePatternDetector]] | None = None,
        min_confidence: float = 0.0
    ):
        # Configure which detectors to use
        # Set confidence threshold

    def analyze(self, role_info) -> PatternAnalysisReport:
        # Run all detectors
        # Filter by confidence
        # Generate report with metrics
```

**Error Handling**:
- If one detector fails, others continue
- Errors logged but don't crash entire analysis
- Graceful degradation

## Design Patterns Used

### 1. Facade Pattern (PatternAnalyzer)

**Problem**: Too many detectors, complex to use

**Solution**: Single entry point that coordinates everything

```python
# Without facade (hard to use):
d1 = DuplicationDetector()
d2 = SecurityDetector()
suggestions = []
suggestions.extend(d1.detect(role_info))
suggestions.extend(d2.detect(role_info))
# ... filter, aggregate, calculate metrics ...

# With facade (easy to use):
report = analyze_role_patterns(role_info)
```

### 2. Template Method Pattern (BasePatternDetector)

**Problem**: Each detector needs same utilities

**Solution**: Base class with shared methods, abstract interface

```python
class BasePatternDetector(ABC):
    @abstractmethod
    def detect(self):  # Each detector implements
        pass

    def _flatten_tasks(self):  # All can use
        # Implementation once, used everywhere
```

### 3. Strategy Pattern (Individual Detectors)

**Problem**: Different detection algorithms needed

**Solution**: Each detector is independent strategy

```python
# Easy to swap/configure
analyzer = PatternAnalyzer(
    enabled_detectors=[SecurityDetector]  # Only security checks
)
```

### 4. Builder Pattern (SimplificationSuggestion)

**Problem**: Complex object with many fields

**Solution**: Pydantic model with field validation

```python
suggestion = SimplificationSuggestion(
    pattern="exposed_secrets",
    category=PatternCategory.SECURITY,
    severity=SeverityLevel.CRITICAL,
    # ... Pydantic validates everything
)
```

## Extension Points

### Adding a New Detector

**Step 1**: Create detector class

```python
# docsible/analyzers/patterns/detectors/performance.py

from docsible.analyzers.patterns.base import BasePatternDetector
from docsible.analyzers.patterns.models import (
    SimplificationSuggestion,
    SeverityLevel,
    PatternCategory
)

class PerformanceDetector(BasePatternDetector):
    """Detects performance anti-patterns."""

    @property
    def pattern_category(self) -> PatternCategory:
        return PatternCategory.PERFORMANCE

    def detect(self, role_info):
        suggestions = []

        # Detect serial tasks that could be parallel
        suggestions.extend(self._detect_serial_execution(role_info))

        # Detect missing async for long operations
        suggestions.extend(self._detect_missing_async(role_info))

        return suggestions

    def _detect_serial_execution(self, role_info):
        # Implementation using base class helpers
        tasks = self._flatten_tasks(role_info)
        # ... detection logic ...
```

**Step 2**: Register in `detectors/__init__.py`

```python
from docsible.analyzers.patterns.detectors.performance import PerformanceDetector

__all__ = [
    'DuplicationDetector',
    'ComplexityDetector',
    'SecurityDetector',
    'MaintainabilityDetector',
    'PerformanceDetector',  # Add here
]
```

**Step 3**: Use it

```python
from docsible.analyzers.patterns import PatternAnalyzer
from docsible.analyzers.patterns.detectors import PerformanceDetector

analyzer = PatternAnalyzer(
    enabled_detectors=[PerformanceDetector]
)
report = analyzer.analyze(role_info)
```

### Adding a New Pattern to Existing Detector

```python
# In existing detector class
class MaintainabilityDetector(BasePatternDetector):
    def detect(self, role_info):
        suggestions = []
        # ... existing detections ...
        suggestions.extend(self._detect_new_pattern(role_info))  # Add
        return suggestions

    def _detect_new_pattern(self, role_info):
        """Detect new anti-pattern."""
        suggestions = []

        for task in self._flatten_tasks(role_info):
            if self._is_problematic(task):
                suggestions.append(SimplificationSuggestion(
                    pattern="new_pattern_name",
                    category=self.pattern_category,
                    severity=SeverityLevel.WARNING,
                    description="What we found",
                    example=self._show_task(task),
                    suggestion="How to fix",
                    affected_files=[task.get('file')],
                    impact="Expected benefit",
                    confidence=0.85
                ))

        return suggestions
```

## Data Flow

```
1. User provides role_info dict
   ↓
2. PatternAnalyzer instantiated with config
   ↓
3. For each enabled detector:
   a. Call detector.detect(role_info)
   b. Detector uses base class helpers
   c. Returns List[SimplificationSuggestion]
   ↓
4. Filter suggestions by confidence
   ↓
5. Aggregate all suggestions
   ↓
6. Calculate metrics (severity counts, health score)
   ↓
7. Return PatternAnalysisReport
   ↓
8. User filters/exports/displays results
```

## Benefits of This Architecture

### 1. Separation of Concerns
- Models: Data structures
- Base: Shared utilities
- Detectors: Specific logic
- Analyzer: Orchestration

### 2. Open/Closed Principle
- Open for extension (add new detectors)
- Closed for modification (don't change existing code)

### 3. Single Responsibility
- Each detector has ONE job
- Each method does ONE thing
- Easy to test in isolation

### 4. Dependency Inversion
- Depend on abstractions (BasePatternDetector)
- Not on concrete implementations

### 5. Testability
```python
# Easy to test individual detectors
def test_security_detector():
    detector = SecurityDetector()
    role_with_secrets = {...}
    suggestions = detector.detect(role_with_secrets)
    assert len(suggestions) > 0
    assert suggestions[0].pattern == "exposed_secrets"
```

### 6. Maintainability
- Clear structure
- Well-documented
- Type hints everywhere
- Consistent patterns

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Only load detectors that are enabled
   - Don't parse data until needed

2. **Caching**
   - `_flatten_tasks()` could cache results
   - Module counts could be memoized

3. **Parallel Execution**
   - Detectors are independent
   - Could run in parallel with ThreadPoolExecutor

4. **Early Exit**
   - If confidence threshold high, skip uncertain patterns
   - If severity filter set, skip low-priority checks

### Future Optimizations

```python
from concurrent.futures import ThreadPoolExecutor

class PatternAnalyzer:
    def analyze_parallel(self, role_info):
        """Run detectors in parallel."""
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(detector.detect, role_info)
                for detector in self.detectors
            ]

            all_suggestions = []
            for future in futures:
                all_suggestions.extend(future.result())

        # ... rest of analysis
```

## Key Learnings

1. **Pydantic > dataclass** for:
   - Validation
   - JSON serialization
   - API schemas
   - Type safety

2. **Composition > Inheritance**:
   - Favor small, focused classes
   - Use base class for utilities, not behavior

3. **Make It Easy to Extend**:
   - New pattern? Add method
   - New detector? Add class
   - No need to modify existing code

4. **Design for Failure**:
   - One detector fails? Others continue
   - Missing data? Graceful handling
   - Invalid input? Clear error messages

5. **Documentation Matters**:
   - Docstrings everywhere
   - Type hints mandatory
   - Examples included
   - Usage guide provided

## Summary

This architecture demonstrates how to build a professional, modular analysis system that is:

- ✅ **Easy to use**: Simple public API
- ✅ **Easy to extend**: Add detectors without changing existing code
- ✅ **Type-safe**: Pydantic validation throughout
- ✅ **Well-tested**: Each component testable in isolation
- ✅ **Production-ready**: Error handling, logging, performance
- ✅ **Maintainable**: Clear structure, documented, consistent patterns

The pattern analyzer serves as a reference implementation for building complex, modular systems in Python.
