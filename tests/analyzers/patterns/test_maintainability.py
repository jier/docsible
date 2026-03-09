"""Tests for the MaintainabilityDetector._detect_unnamed_tasks check."""

from docsible.analyzers.patterns.detectors.maintainability import MaintainabilityDetector


def make_role_info(task_files):
    """Wrap task file dicts into the role_info structure expected by detectors."""
    return {"tasks": task_files, "vars": {}, "defaults": {}, "handlers": [], "meta": {}}


def make_task_file(tasks, filename="tasks/main.yml"):
    """Wrap a list of task dicts into a task-file dict."""
    return {"file": filename, "tasks": tasks}


def make_named_task(name, module="apt"):
    """Create a task that has a name field."""
    return {"name": name, "module": module, "file": "tasks/main.yml"}


def make_unnamed_task(module="apt"):
    """Create a task that has no name field."""
    return {"module": module, "file": "tasks/main.yml"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_unnamed_tasks_below_threshold_no_suggestion():
    """Role with 2 unnamed real tasks should NOT produce a suggestion (threshold is 3)."""
    tasks = [make_unnamed_task("apt"), make_unnamed_task("copy")]
    role_info = make_role_info([make_task_file(tasks)])

    suggestions = MaintainabilityDetector().detect(role_info)

    unnamed_suggestions = [s for s in suggestions if s.pattern == "unnamed_tasks"]
    assert len(unnamed_suggestions) == 0, (
        f"Expected no suggestion for 2 unnamed tasks, got: {unnamed_suggestions}"
    )


def test_unnamed_tasks_at_threshold_emits_suggestion():
    """Role with exactly 3 unnamed real tasks MUST emit one suggestion."""
    tasks = [make_unnamed_task("apt"), make_unnamed_task("copy"), make_unnamed_task("template")]
    role_info = make_role_info([make_task_file(tasks)])

    suggestions = MaintainabilityDetector().detect(role_info)

    unnamed_suggestions = [s for s in suggestions if s.pattern == "unnamed_tasks"]
    assert len(unnamed_suggestions) == 1, (
        f"Expected exactly one suggestion for 3 unnamed tasks, got: {unnamed_suggestions}"
    )
    suggestion = unnamed_suggestions[0]
    assert suggestion.pattern == "unnamed_tasks"
    from docsible.analyzers.patterns.models import SeverityLevel
    assert suggestion.severity == SeverityLevel.INFO, (
        f"Expected severity INFO, got {suggestion.severity}"
    )


def test_unnamed_tasks_excludes_structural_modules():
    """Role with 5 include_tasks / import_tasks tasks (all unnamed) yields no suggestion.

    Those structural modules are exempt from the unnamed-task check.
    """
    tasks = [
        {"module": "include_tasks", "file": "tasks/main.yml"},
        {"module": "include_tasks", "file": "tasks/main.yml"},
        {"module": "import_tasks", "file": "tasks/main.yml"},
        {"module": "import_tasks", "file": "tasks/main.yml"},
        {"module": "import_tasks", "file": "tasks/main.yml"},
    ]
    role_info = make_role_info([make_task_file(tasks)])

    suggestions = MaintainabilityDetector().detect(role_info)

    unnamed_suggestions = [s for s in suggestions if s.pattern == "unnamed_tasks"]
    assert len(unnamed_suggestions) == 0, (
        "Structural modules should not count as unnamed tasks; "
        f"got: {unnamed_suggestions}"
    )


def test_unnamed_tasks_mixed_excluded_and_real():
    """2 structural unnamed + 3 real unnamed = suggestion fires (3 real unnamed hits threshold)."""
    tasks = [
        # structural (excluded)
        {"module": "include_tasks", "file": "tasks/main.yml"},
        {"module": "import_tasks", "file": "tasks/main.yml"},
        # real unnamed tasks
        make_unnamed_task("apt"),
        make_unnamed_task("copy"),
        make_unnamed_task("template"),
    ]
    role_info = make_role_info([make_task_file(tasks)])

    suggestions = MaintainabilityDetector().detect(role_info)

    unnamed_suggestions = [s for s in suggestions if s.pattern == "unnamed_tasks"]
    assert len(unnamed_suggestions) == 1, (
        "Expected suggestion to fire when 3 real unnamed tasks exist alongside "
        f"excluded structural ones; got: {unnamed_suggestions}"
    )


def test_named_tasks_no_suggestion():
    """Role where all tasks have names should produce no unnamed_tasks suggestion."""
    tasks = [
        make_named_task("Install nginx", "apt"),
        make_named_task("Copy config", "copy"),
        make_named_task("Start service", "service"),
        make_named_task("Verify port", "wait_for"),
    ]
    role_info = make_role_info([make_task_file(tasks)])

    suggestions = MaintainabilityDetector().detect(role_info)

    unnamed_suggestions = [s for s in suggestions if s.pattern == "unnamed_tasks"]
    assert len(unnamed_suggestions) == 0, (
        f"Named tasks must not produce an unnamed_tasks suggestion; got: {unnamed_suggestions}"
    )
