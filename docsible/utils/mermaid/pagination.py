"""Paginate large Mermaid diagrams for better rendering."""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def should_paginate_diagram(mermaid_code: str, max_nodes: int = 50) -> bool:
    """
    Determine if a Mermaid diagram should be paginated.

    Args:
        mermaid_code: Complete Mermaid diagram code
        max_nodes: Maximum nodes before pagination (default: 50)

    Returns:
        True if diagram should be split into pages

    Example:
        >>> diagram = "flowchart TD\\nA-->B\\nB-->C"
        >>> should_paginate_diagram(diagram, max_nodes=2)
        True
    """
    # Count node connections (arrows)
    arrow_count = mermaid_code.count("-->") + mermaid_code.count("---")

    # Count total lines (rough complexity metric)
    line_count = len(mermaid_code.strip().split("\n"))

    # Paginate if too many nodes or lines
    should_split = arrow_count > max_nodes or line_count > 100

    if should_split:
        logger.debug(
            f"Diagram complexity: {arrow_count} arrows, {line_count} lines - "
            f"will paginate (threshold: {max_nodes} arrows)"
        )

    return should_split


def paginate_tasks(
    tasks: List[Dict], tasks_per_page: int = 20
) -> List[Tuple[str, List[Dict]]]:
    """
    Split task list into pages for multiple diagrams.

    Args:
        tasks: List of task dictionaries
        tasks_per_page: Number of tasks per diagram page

    Returns:
        List of (page_title, task_chunk) tuples

    Example:
        >>> tasks = [{'name': f'Task {i}'} for i in range(45)]
        >>> pages = paginate_tasks(tasks, tasks_per_page=20)
        >>> len(pages)
        3
        >>> pages[0][0]
        'Tasks 1-20 (Page 1/3)'
    """
    if not tasks:
        return []

    pages = []
    total_tasks = len(tasks)
    total_pages = (total_tasks + tasks_per_page - 1) // tasks_per_page

    for page_num in range(total_pages):
        start_idx = page_num * tasks_per_page
        end_idx = min(start_idx + tasks_per_page, total_tasks)
        chunk = tasks[start_idx:end_idx]

        title = f"Tasks {start_idx + 1}-{end_idx} (Page {page_num + 1}/{total_pages})"
        pages.append((title, chunk))

    return pages


def get_diagram_complexity_warning(mermaid_code: str) -> str:
    """
    Generate a warning message for complex diagrams.

    Args:
        mermaid_code: Mermaid diagram code

    Returns:
        Warning message if diagram is complex, empty string otherwise
    """
    arrow_count = mermaid_code.count("-->") + mermaid_code.count("---")

    if arrow_count > 100:
        return (
            f"> ⚠️ **Note**: This diagram has {arrow_count} nodes and may not render "
            "on some platforms. Consider using `--export-diagrams` to generate SVG/PNG."
        )
    elif arrow_count > 50:
        return (
            f"> **Note**: This diagram has {arrow_count} nodes. "
            "If it doesn't render, the diagram has been split into smaller sections below."
        )

    return ""
