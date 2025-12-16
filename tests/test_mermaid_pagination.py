"""Tests for Mermaid diagram pagination functionality."""

from docsible.utils.mermaid.pagination import (
    get_diagram_complexity_warning,
    paginate_tasks,
    should_paginate_diagram,
)


class TestShouldPaginateDiagram:
    """Test diagram pagination decision logic."""

    def test_small_diagram_no_pagination(self):
        """Small diagrams should not be paginated."""
        diagram = """flowchart TD
Start
Start-->Task1[Task 1]
Task1-->End"""
        assert should_paginate_diagram(diagram, max_nodes=50) is False

    def test_large_diagram_by_arrows(self):
        """Diagrams with many arrows should be paginated."""
        # Create diagram with 51 arrows (exceeds threshold)
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(51)])
        diagram = f"flowchart TD\n{arrows}"
        assert should_paginate_diagram(diagram, max_nodes=50) is True

    def test_large_diagram_by_lines(self):
        """Diagrams with many lines should be paginated."""
        # Create diagram with 101 lines (exceeds threshold)
        lines = "\n".join([f"Node{i}[Task {i}]" for i in range(101)])
        diagram = f"flowchart TD\n{lines}"
        assert should_paginate_diagram(diagram, max_nodes=50) is True

    def test_exact_threshold_no_pagination(self):
        """Diagrams at exact threshold should not be paginated."""
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(50)])
        diagram = f"flowchart TD\n{arrows}"
        assert should_paginate_diagram(diagram, max_nodes=50) is False

    def test_custom_max_nodes(self):
        """Custom max_nodes threshold should be respected."""
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(11)])
        diagram = f"flowchart TD\n{arrows}"
        assert should_paginate_diagram(diagram, max_nodes=10) is True
        assert should_paginate_diagram(diagram, max_nodes=20) is False

    def test_mixed_arrow_types(self):
        """Both --> and --- arrow types should be counted."""
        diagram = """flowchart TD
A-->B
B---C
C-->D"""
        # 3 arrows total
        assert should_paginate_diagram(diagram, max_nodes=2) is True
        assert should_paginate_diagram(diagram, max_nodes=5) is False


class TestPaginateTasks:
    """Test task pagination logic."""

    def test_empty_tasks_list(self):
        """Empty task list should return empty pages."""
        pages = paginate_tasks([], tasks_per_page=20)
        assert pages == []

    def test_single_page(self):
        """Tasks fitting in one page should return single page."""
        tasks = [{"name": f"Task {i}"} for i in range(15)]
        pages = paginate_tasks(tasks, tasks_per_page=20)

        assert len(pages) == 1
        assert pages[0][0] == "Tasks 1-15 (Page 1/1)"
        assert len(pages[0][1]) == 15

    def test_multiple_pages(self):
        """Large task list should be split into multiple pages."""
        tasks = [{"name": f"Task {i}"} for i in range(45)]
        pages = paginate_tasks(tasks, tasks_per_page=20)

        assert len(pages) == 3
        assert pages[0][0] == "Tasks 1-20 (Page 1/3)"
        assert len(pages[0][1]) == 20
        assert pages[1][0] == "Tasks 21-40 (Page 2/3)"
        assert len(pages[1][1]) == 20
        assert pages[2][0] == "Tasks 41-45 (Page 3/3)"
        assert len(pages[2][1]) == 5

    def test_exact_page_boundary(self):
        """Tasks exactly filling pages should not create empty page."""
        tasks = [{"name": f"Task {i}"} for i in range(40)]
        pages = paginate_tasks(tasks, tasks_per_page=20)

        assert len(pages) == 2
        assert pages[0][0] == "Tasks 1-20 (Page 1/2)"
        assert pages[1][0] == "Tasks 21-40 (Page 2/2)"
        assert len(pages[1][1]) == 20

    def test_custom_tasks_per_page(self):
        """Custom tasks_per_page should be respected."""
        tasks = [{"name": f"Task {i}"} for i in range(25)]

        # 10 per page = 3 pages
        pages = paginate_tasks(tasks, tasks_per_page=10)
        assert len(pages) == 3
        assert len(pages[0][1]) == 10
        assert len(pages[1][1]) == 10
        assert len(pages[2][1]) == 5

    def test_single_task(self):
        """Single task should create one page."""
        tasks = [{"name": "Only task"}]
        pages = paginate_tasks(tasks, tasks_per_page=20)

        assert len(pages) == 1
        assert pages[0][0] == "Tasks 1-1 (Page 1/1)"
        assert len(pages[0][1]) == 1

    def test_task_data_preserved(self):
        """Task dictionaries should be preserved unchanged."""
        tasks = [
            {"name": "Task 1", "module": "apt", "when": "True"},
            {"name": "Task 2", "module": "service", "tags": ["prod"]},
        ]
        pages = paginate_tasks(tasks, tasks_per_page=20)

        assert pages[0][1][0] == tasks[0]
        assert pages[0][1][1] == tasks[1]


class TestGetDiagramComplexityWarning:
    """Test diagram complexity warning generation."""

    def test_no_warning_for_small_diagrams(self):
        """Small diagrams should return empty warning."""
        diagram = """flowchart TD
A-->B
B-->C"""
        warning = get_diagram_complexity_warning(diagram)
        assert warning == ""

    def test_warning_for_medium_complexity(self):
        """Diagrams with 51-100 nodes should get medium warning."""
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(51)])
        diagram = f"flowchart TD\n{arrows}"

        warning = get_diagram_complexity_warning(diagram)
        assert "51 nodes" in warning
        assert "doesn't render" in warning
        assert "split into smaller sections" in warning
        assert "⚠️" not in warning  # No high-severity emoji

    def test_warning_for_high_complexity(self):
        """Diagrams with >100 nodes should get severe warning."""
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(101)])
        diagram = f"flowchart TD\n{arrows}"

        warning = get_diagram_complexity_warning(diagram)
        assert "101 nodes" in warning
        assert "may not render" in warning
        assert "--export-diagrams" in warning
        assert "⚠️" in warning  # High-severity emoji

    def test_exact_threshold_boundaries(self):
        """Test exact threshold values."""
        # Exactly 50 arrows - no warning
        arrows_50 = "\n".join([f"Node{i}-->Node{i+1}" for i in range(50)])
        diagram_50 = f"flowchart TD\n{arrows_50}"
        assert get_diagram_complexity_warning(diagram_50) == ""

        # Exactly 51 arrows - medium warning
        arrows_51 = "\n".join([f"Node{i}-->Node{i+1}" for i in range(51)])
        diagram_51 = f"flowchart TD\n{arrows_51}"
        warning = get_diagram_complexity_warning(diagram_51)
        assert warning != ""
        assert "⚠️" not in warning

        # Exactly 100 arrows - medium warning
        arrows_100 = "\n".join([f"Node{i}-->Node{i+1}" for i in range(100)])
        diagram_100 = f"flowchart TD\n{arrows_100}"
        warning = get_diagram_complexity_warning(diagram_100)
        assert "⚠️" not in warning

        # Exactly 101 arrows - high warning
        arrows_101 = "\n".join([f"Node{i}-->Node{i+1}" for i in range(101)])
        diagram_101 = f"flowchart TD\n{arrows_101}"
        warning = get_diagram_complexity_warning(diagram_101)
        assert "⚠️" in warning

    def test_mixed_arrow_types_counted(self):
        """Both --> and --- arrows should be counted."""
        # Create mix of arrow types totaling 51
        arrows = "\n".join([f"Node{i}-->Node{i+1}" for i in range(30)])
        dashes = "\n".join([f"Node{i}---Node{i+100}" for i in range(21)])
        diagram = f"flowchart TD\n{arrows}\n{dashes}"

        warning = get_diagram_complexity_warning(diagram)
        assert "51 nodes" in warning


class TestPaginationIntegration:
    """Test pagination workflow integration."""

    def test_complete_pagination_workflow(self):
        """Test full workflow from detection to pagination."""
        # Create large task list
        tasks = [{"name": f"Task {i}", "module": "debug"} for i in range(55)]

        # Simulate diagram generation (simplified)
        arrows = "\n".join([f"Task{i}-->Task{i+1}" for i in range(55)])
        diagram = f"flowchart TD\n{arrows}"

        # Check if pagination needed
        should_paginate = should_paginate_diagram(diagram, max_nodes=50)
        assert should_paginate is True

        # Paginate tasks
        pages = paginate_tasks(tasks, tasks_per_page=20)
        assert len(pages) == 3

        # Get warning
        warning = get_diagram_complexity_warning(diagram)
        assert warning != ""

    def test_no_pagination_workflow(self):
        """Test workflow when pagination not needed."""
        # Create small task list
        tasks = [{"name": f"Task {i}", "module": "debug"} for i in range(10)]

        # Simulate diagram generation
        arrows = "\n".join([f"Task{i}-->Task{i+1}" for i in range(10)])
        diagram = f"flowchart TD\n{arrows}"

        # Check if pagination needed
        should_paginate = should_paginate_diagram(diagram, max_nodes=50)
        assert should_paginate is False

        # No pagination needed
        pages = paginate_tasks(tasks, tasks_per_page=20)
        assert len(pages) == 1  # Single page

        # No warning
        warning = get_diagram_complexity_warning(diagram)
        assert warning == ""
