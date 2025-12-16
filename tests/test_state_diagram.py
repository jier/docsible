"""
Unit tests for state diagram generator.

Tests phase detection, state tracking, and diagram generation.
"""

from docsible.utils.state_diagram import (
    Phase,
    analyze_phases,
    detect_phase_from_task_name,
    extract_condition,
    generate_state_diagram,
    has_state_management,
    infer_transitions,
    should_generate_state_diagram,
)

# Test Phase Detection


def test_detect_install_phase():
    """Test detection of install phase from task names."""
    assert detect_phase_from_task_name("Install nginx package") == Phase.INSTALL
    assert detect_phase_from_task_name("Setup application") == Phase.INSTALL
    assert detect_phase_from_task_name("Create database") == Phase.INSTALL
    assert detect_phase_from_task_name("Download files") == Phase.INSTALL
    assert detect_phase_from_task_name("Fetch dependencies") == Phase.INSTALL


def test_detect_configure_phase():
    """Test detection of configure phase from task names."""
    assert detect_phase_from_task_name("Configure web server") == Phase.CONFIGURE
    assert detect_phase_from_task_name("Set environment variables") == Phase.CONFIGURE
    assert detect_phase_from_task_name("Update configuration") == Phase.CONFIGURE
    assert detect_phase_from_task_name("Copy config file") == Phase.CONFIGURE
    assert detect_phase_from_task_name("Template nginx.conf") == Phase.CONFIGURE
    assert detect_phase_from_task_name("Apply settings") == Phase.CONFIGURE


def test_detect_validate_phase():
    """Test detection of validate phase from task names."""
    assert detect_phase_from_task_name("Check if service is running") == Phase.VALIDATE
    assert detect_phase_from_task_name("Verify service status") == Phase.VALIDATE
    assert detect_phase_from_task_name("Test application") == Phase.VALIDATE
    assert detect_phase_from_task_name("Ensure port is open") == Phase.VALIDATE
    assert detect_phase_from_task_name("Wait for service") == Phase.VALIDATE
    assert detect_phase_from_task_name("Ping server") == Phase.VALIDATE
    assert detect_phase_from_task_name("Validate settings") == Phase.VALIDATE


def test_detect_start_phase():
    """Test detection of start phase from task names."""
    assert detect_phase_from_task_name("Start the service") == Phase.START
    assert detect_phase_from_task_name("Enable nginx") == Phase.START
    assert detect_phase_from_task_name("Launch application") == Phase.START
    assert detect_phase_from_task_name("Run server") == Phase.START
    assert detect_phase_from_task_name("Activate service") == Phase.START


def test_detect_stop_phase():
    """Test detection of stop phase from task names."""
    assert detect_phase_from_task_name("Stop the service") == Phase.STOP
    assert detect_phase_from_task_name("Disable nginx") == Phase.STOP
    assert detect_phase_from_task_name("Shutdown application") == Phase.STOP
    assert detect_phase_from_task_name("Terminate process") == Phase.STOP


def test_detect_cleanup_phase():
    """Test detection of cleanup phase from task names."""
    assert detect_phase_from_task_name("Clean temporary files") == Phase.CLEANUP
    assert detect_phase_from_task_name("Remove old packages") == Phase.CLEANUP
    assert detect_phase_from_task_name("Delete cache") == Phase.CLEANUP
    assert detect_phase_from_task_name("Purge logs") == Phase.CLEANUP
    assert detect_phase_from_task_name("Uninstall software") == Phase.CLEANUP


def test_detect_execute_phase_default():
    """Test default phase detection for generic tasks."""
    assert detect_phase_from_task_name("Do something") == Phase.EXECUTE
    assert detect_phase_from_task_name("Perform action") == Phase.EXECUTE
    assert detect_phase_from_task_name("Execute command") == Phase.EXECUTE


def test_phase_detection_case_insensitive():
    """Test that phase detection is case insensitive."""
    assert detect_phase_from_task_name("INSTALL PACKAGE") == Phase.INSTALL
    assert detect_phase_from_task_name("Configure Server") == Phase.CONFIGURE
    assert detect_phase_from_task_name("CHECK STATUS") == Phase.VALIDATE


# Test State Management Detection


def test_has_state_management_with_state_modules():
    """Test state management detection for common state modules."""
    assert has_state_management({"module": "package", "name": "nginx"}) is True
    assert has_state_management({"module": "service", "name": "nginx"}) is True
    assert has_state_management({"module": "file", "path": "/tmp/file"}) is True
    assert has_state_management({"module": "ansible.builtin.package"}) is True
    assert has_state_management({"module": "ansible.builtin.service"}) is True


def test_has_state_management_without_state_modules():
    """Test state management detection for non-state modules."""
    assert has_state_management({"module": "debug", "msg": "Hello"}) is False
    assert has_state_management({"module": "command", "cmd": "ls"}) is False
    assert has_state_management({"module": "shell", "cmd": "echo"}) is False


# Test Condition Extraction


def test_extract_condition_string():
    """Test extraction of when condition as string."""
    task = {"name": "Task", "when": "ansible_os_family == 'Debian'"}
    assert extract_condition(task) == "ansible_os_family == 'Debian'"


def test_extract_condition_list():
    """Test extraction of when condition as list."""
    task = {"name": "Task", "when": ["ansible_os_family == 'Debian'", "is_production"]}
    assert extract_condition(task) == "ansible_os_family == 'Debian' and is_production"


def test_extract_condition_none():
    """Test extraction when no condition exists."""
    task = {"name": "Task"}
    assert extract_condition(task) is None


# Test Phase Analysis


def test_analyze_phases_single_phase():
    """Test phase analysis with tasks in single phase."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install nginx", "module": "apt"},
                    {"name": "Install ssl-cert", "module": "apt"},
                ],
            }
        ],
    }

    phases = analyze_phases(role_info)
    assert len(phases) == 1
    assert phases[0].phase == Phase.INSTALL
    assert len(phases[0].tasks) == 2


def test_analyze_phases_multiple_phases():
    """Test phase analysis with tasks in multiple phases."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install nginx", "module": "apt"},
                    {"name": "Configure nginx", "module": "template"},
                    {"name": "Start nginx", "module": "service"},
                ],
            }
        ],
    }

    phases = analyze_phases(role_info)
    assert len(phases) == 3
    phase_types = {p.phase for p in phases}
    assert Phase.INSTALL in phase_types
    assert Phase.CONFIGURE in phase_types
    assert Phase.START in phase_types


def test_analyze_phases_with_state_check():
    """Test phase analysis detects state management."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install nginx", "module": "apt", "state": "present"},
                ],
            }
        ],
    }

    phases = analyze_phases(role_info)
    assert phases[0].has_state_check is True


def test_analyze_phases_with_conditions():
    """Test phase analysis detects conditions."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {
                        "name": "Install nginx",
                        "module": "apt",
                        "when": "ansible_os_family == 'Debian'",
                    },
                ],
            }
        ],
    }

    phases = analyze_phases(role_info)
    assert phases[0].has_conditions is True


# Test Transition Inference


def test_infer_transitions_standard_flow():
    """Test transition inference for standard workflow."""
    from docsible.utils.state_diagram import PhaseInfo

    phases = [
        PhaseInfo(
            phase=Phase.INSTALL,
            tasks=[{"name": "Install"}],
            has_state_check=True,
            has_conditions=False,
        ),
        PhaseInfo(
            phase=Phase.CONFIGURE,
            tasks=[{"name": "Configure"}],
            has_state_check=False,
            has_conditions=False,
        ),
        PhaseInfo(
            phase=Phase.VALIDATE,
            tasks=[{"name": "Validate"}],
            has_state_check=False,
            has_conditions=True,
        ),
        PhaseInfo(
            phase=Phase.START,
            tasks=[{"name": "Start"}],
            has_state_check=True,
            has_conditions=False,
        ),
    ]

    transitions = infer_transitions(phases)

    assert len(transitions) > 0
    # Check standard flow exists
    transition_pairs = [(t.from_phase, t.to_phase) for t in transitions]
    assert (Phase.INSTALL, Phase.CONFIGURE) in transition_pairs
    assert (Phase.CONFIGURE, Phase.VALIDATE) in transition_pairs
    assert (Phase.VALIDATE, Phase.START) in transition_pairs


def test_infer_transitions_with_cleanup():
    """Test transition inference with cleanup phase."""
    from docsible.utils.state_diagram import PhaseInfo

    phases = [
        PhaseInfo(
            phase=Phase.STOP,
            tasks=[{"name": "Stop"}],
            has_state_check=False,
            has_conditions=False,
        ),
        PhaseInfo(
            phase=Phase.CLEANUP,
            tasks=[{"name": "Clean"}],
            has_state_check=False,
            has_conditions=False,
        ),
    ]

    transitions = infer_transitions(phases)

    # Should have STOP -> CLEANUP transition
    transition_pairs = [(t.from_phase, t.to_phase) for t in transitions]
    assert (Phase.STOP, Phase.CLEANUP) in transition_pairs


# Test Diagram Generation


def test_generate_state_diagram_basic():
    """Test basic state diagram generation."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install nginx", "module": "apt"},
                    {"name": "Configure nginx", "module": "template"},
                    {"name": "Start nginx", "module": "service"},
                    {"name": "Check if running", "module": "command"},
                    {"name": "Validate config", "module": "command"},
                ],
            }
        ],
    }

    diagram = generate_state_diagram(role_info, "webserver")

    assert diagram is not None
    assert "stateDiagram-v2" in diagram
    assert "Install" in diagram or "Configure" in diagram


def test_generate_state_diagram_with_title():
    """Test state diagram generation includes title."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Install package", "module": "apt"},
                    {"name": "Configure service", "module": "template"},
                    {"name": "Start service", "module": "service"},
                    {"name": "Verify service", "module": "command"},
                    {"name": "Check logs", "module": "command"},
                ],
            }
        ],
    }

    diagram = generate_state_diagram(role_info, "my_role")

    assert diagram is not None
    assert "title: my_role - State Transitions" in diagram


def test_generate_state_diagram_insufficient_tasks():
    """Test that diagram is not generated for roles with too few tasks."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    {"name": "Do something", "module": "debug"},
                ],
            }
        ],
    }

    diagram = generate_state_diagram(role_info)
    assert diagram is None


def test_generate_state_diagram_no_tasks():
    """Test diagram generation with no tasks."""
    role_info = {"tasks": []}

    diagram = generate_state_diagram(role_info)
    assert diagram is None


# Test Diagram Generation Decision


def test_should_generate_for_medium_complexity():
    """Test that state diagrams are generated for MEDIUM complexity roles."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(15)],
            }
        ],
    }

    assert should_generate_state_diagram(role_info, "MEDIUM") is True


def test_should_not_generate_for_simple_complexity():
    """Test that state diagrams are not generated for SIMPLE complexity roles."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(8)],
            }
        ],
    }

    assert should_generate_state_diagram(role_info, "SIMPLE") is False


def test_should_not_generate_for_complex_complexity():
    """Test that state diagrams are not generated for COMPLEX complexity roles."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(30)],
            }
        ],
    }

    assert should_generate_state_diagram(role_info, "COMPLEX") is False


def test_should_not_generate_with_too_few_tasks():
    """Test that state diagrams are not generated for roles with < 5 tasks."""
    role_info = {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [{"name": f"Task {i}", "module": "debug"} for i in range(3)],
            }
        ],
    }

    assert should_generate_state_diagram(role_info, "MEDIUM") is False
