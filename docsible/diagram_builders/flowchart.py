"""Flowchart diagram builder for Ansible task flows.

This module provides a builder for creating Mermaid flowchart diagrams
from Ansible task data.
"""

import logging
from typing import Any, Dict, List, Optional

from docsible.diagram_builders.base import DiagramBuilder
from docsible.diagram_builders.formatters import (
    sanitize_for_id,
    sanitize_for_title,
    break_text,
    escape_pipes,
)

logger = logging.getLogger(__name__)


class FlowchartBuilder(DiagramBuilder):
    """Builder for Mermaid flowchart diagrams.

    Creates flowchart diagrams showing task execution flow with
    conditional logic and decision points.

    Example:
        >>> builder = FlowchartBuilder()
        >>> builder.start_diagram("Task Flow")
        >>> builder.add_task("Install nginx", "task_1")
        >>> builder.add_task("Configure nginx", "task_2")
        >>> builder.add_flow("task_1", "task_2")
        >>> diagram = builder.build()
    """

    def __init__(self, direction: str = "TD"):
        """Initialize FlowchartBuilder.

        Args:
            direction: Flow direction (TD=top-down, LR=left-right, default: TD)
        """
        super().__init__()
        self.direction = direction
        self.node_count = 0

    def start_diagram(self, title: Optional[str] = None) -> None:
        """Initialize flowchart diagram with optional title.

        Args:
            title: Optional diagram title

        Example:
            >>> builder.start_diagram("My Task Flow")
        """
        self.clear()
        self.add_line(f"flowchart {self.direction}")

        if title:
            safe_title = sanitize_for_title(title)
            self.add_line(f"    %% {safe_title}")

    def add_task(
        self,
        task_name: str,
        task_id: Optional[str] = None,
        shape: str = "rectangle"
    ) -> str:
        """Add a task node to the flowchart.

        Args:
            task_name: Display name of the task
            task_id: Optional node ID (auto-generated if None)
            shape: Node shape (rectangle, rhombus, circle, etc.)

        Returns:
            ID of the created node

        Example:
            >>> task_id = builder.add_task("Install package", shape="rectangle")
        """
        if task_id is None:
            task_id = f"task_{self.node_count}"
            self.node_count += 1

        safe_id = sanitize_for_id(task_id)
        safe_name = escape_pipes(task_name)
        safe_name = break_text(safe_name, max_length=40)

        # Define node with shape
        if shape == "rectangle":
            node_def = f"    {safe_id}[{safe_name}]"
        elif shape == "rhombus":
            node_def = f"    {safe_id}{{{safe_name}}}"
        elif shape == "circle":
            node_def = f"    {safe_id}(({safe_name}))"
        elif shape == "rounded":
            node_def = f"    {safe_id}({safe_name})"
        else:
            node_def = f"    {safe_id}[{safe_name}]"

        self.add_line(node_def)
        return safe_id

    def add_decision(
        self,
        condition: str,
        decision_id: Optional[str] = None
    ) -> str:
        """Add a decision/conditional node (rhombus shape).

        Args:
            condition: Condition text to display
            decision_id: Optional node ID (auto-generated if None)

        Returns:
            ID of the created decision node

        Example:
            >>> dec_id = builder.add_decision("Is Debian?")
        """
        if decision_id is None:
            decision_id = f"decision_{self.node_count}"
            self.node_count += 1

        return self.add_task(condition, decision_id, shape="rhombus")

    def add_flow(
        self,
        from_id: str,
        to_id: str,
        label: Optional[str] = None,
        style: str = "arrow"
    ) -> None:
        """Add a flow/edge between two nodes.

        Args:
            from_id: Source node ID
            to_id: Target node ID
            label: Optional edge label
            style: Edge style (arrow, dotted, thick, default: arrow)

        Example:
            >>> builder.add_flow("task_1", "task_2", label="success")
        """
        from_safe = sanitize_for_id(from_id)
        to_safe = sanitize_for_id(to_id)

        # Define arrow style
        if style == "dotted":
            arrow = "-.->"
        elif style == "thick":
            arrow = "==>"
        else:
            arrow = "-->"

        # Add label if provided
        if label:
            safe_label = escape_pipes(label)
            flow_line = f"    {from_safe} {arrow}|{safe_label}| {to_safe}"
        else:
            flow_line = f"    {from_safe} {arrow} {to_safe}"

        self.add_line(flow_line)

    def add_start_end(self, node_type: str = "start") -> str:
        """Add start or end node (circle shape).

        Args:
            node_type: Type of node (start or end)

        Returns:
            ID of the created node

        Example:
            >>> start_id = builder.add_start_end("start")
            >>> end_id = builder.add_start_end("end")
        """
        node_id = f"{node_type}_{self.node_count}"
        self.node_count += 1

        return self.add_task(node_type.capitalize(), node_id, shape="circle")

    def add_subgraph(
        self,
        title: str,
        node_ids: List[str]
    ) -> None:
        """Add a subgraph grouping related nodes.

        Args:
            title: Subgraph title
            node_ids: List of node IDs to include in subgraph

        Example:
            >>> builder.add_subgraph("Setup", ["task_1", "task_2"])
        """
        safe_title = escape_pipes(title)
        self.add_line(f"    subgraph {safe_title}")

        for node_id in node_ids:
            safe_id = sanitize_for_id(node_id)
            self.add_line(f"        {safe_id}", indent=1)

        self.add_line("    end")

    def build(self) -> str:
        """Build and return the complete flowchart diagram.

        Returns:
            Complete Mermaid flowchart as string

        Example:
            >>> diagram = builder.build()
            >>> print(diagram)
        """
        if not self.lines:
            logger.warning("Building empty flowchart diagram")
            return ""

        logger.debug(f"Built flowchart with {len(self.lines)} lines")
        return self.get_diagram()
