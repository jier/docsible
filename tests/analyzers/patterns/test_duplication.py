"""Tests for the DuplicationDetector pattern detector.

Covers FQCN matching, args-based state extraction, and threshold behaviour.
"""

from docsible.analyzers.patterns.detectors.duplication import DuplicationDetector


def make_role_info(tasks):
    """Wrap a flat list of task dicts into the role_info structure expected by detectors."""
    return {
        "tasks": [{"file": "tasks/main.yml", "tasks": tasks}],
        "defaults": [],
        "vars": [],
        "handlers": [],
        "meta": {},
    }


def make_task(task_name, module, **args):
    """Create a task dict in docsible's internal format."""
    return {"name": task_name, "module": module, "args": args, "file": "tasks/main.yml"}


def test_service_state_grouping_uses_args():
    """Detector groups service tasks by state read from task['args']['state'],
    not task['state'], so the suggestion description must contain the actual
    state value ('started') rather than the old fallback 'unknown'.
    """
    tasks = [
        make_task(f"Start svc{i}", "service", state="started", name=f"svc{i}")
        for i in range(4)
    ] + [
        make_task("Stop other1", "service", state="stopped", name="other1"),
        make_task("Stop other2", "service", state="stopped", name="other2"),
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    patterns = [s.pattern for s in suggestions]
    assert "repeated_service_operations" in patterns, (
        f"Expected 'repeated_service_operations' in {patterns}"
    )

    service_suggestions = [s for s in suggestions if s.pattern == "repeated_service_operations"]
    descriptions = [s.description for s in service_suggestions]
    assert any("started" in d for d in descriptions), (
        f"Expected 'started' in at least one description, got: {descriptions}"
    )
    assert not any("unknown" in d for d in descriptions), (
        f"'unknown' should not appear in descriptions; got: {descriptions}"
    )


def test_directory_detection_works():
    """Detector identifies repeated directory creation tasks (5 with state=directory)."""
    tasks = [
        make_task(f"Create dir{i}", "file", state="directory", path=f"/dir{i}")
        for i in range(5)
    ] + [
        make_task("Remove old", "file", state="absent", path="/old"),
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    patterns = [s.pattern for s in suggestions]
    assert "repeated_directory_creation" in patterns, (
        f"Expected 'repeated_directory_creation' in {patterns}"
    )


def test_fqcn_package_detection():
    """Detector recognises ansible.builtin.apt as an apt-family module."""
    tasks = [
        make_task(f"Install pkg{i}", "ansible.builtin.apt", name=f"pkg{i}")
        for i in range(6)
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    patterns = [s.pattern for s in suggestions]
    assert "repeated_package_install" in patterns, (
        f"Expected 'repeated_package_install' in {patterns}"
    )


def test_fqcn_service_detection():
    """Detector recognises ansible.builtin.service as a service-family module."""
    tasks = [
        make_task(f"Start svc{i}", "ansible.builtin.service", state="started", name=f"svc{i}")
        for i in range(6)
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    patterns = [s.pattern for s in suggestions]
    assert "repeated_service_operations" in patterns, (
        f"Expected 'repeated_service_operations' in {patterns}"
    )


def test_short_name_still_works():
    """Detector still matches the short module name 'apt' (no FQCN)."""
    tasks = [
        make_task(f"Install pkg{i}", "apt", name=f"pkg{i}")
        for i in range(6)
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    patterns = [s.pattern for s in suggestions]
    assert "repeated_package_install" in patterns, (
        f"Expected 'repeated_package_install' in {patterns}"
    )


def test_below_threshold_no_suggestion():
    """Fewer than 6 tasks of the same module must NOT produce a package suggestion."""
    tasks = [
        make_task(f"Install pkg{i}", "apt", name=f"pkg{i}")
        for i in range(3)
    ]
    role_info = make_role_info(tasks)

    suggestions = DuplicationDetector().detect(role_info)

    package_suggestions = [s for s in suggestions if s.pattern == "repeated_package_install"]
    assert len(package_suggestions) == 0, (
        f"Expected no package suggestions for 3 tasks, got: {package_suggestions}"
    )
