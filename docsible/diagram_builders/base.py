"""Base diagram builder for Mermaid diagrams.

This module provides the abstract base class for all Mermaid diagram builders,
implementing common functionality and defining the interface.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class DiagramBuilder(ABC):
    """Abstract base class for Mermaid diagram builders.

    All diagram builders should inherit from this class and implement
    the build() method to generate their specific diagram type.

    Attributes:
        lines: List of diagram lines being constructed
    """

    def __init__(self):
        """Initialize DiagramBuilder with empty lines list."""
        self.lines: List[str] = []

    @abstractmethod
    def build(self) -> str:
        """Build and return the complete diagram.

        This method must be implemented by subclasses to generate
        the specific diagram type.

        Returns:
            Complete Mermaid diagram as string
        """
        pass

    def add_line(self, line: str, indent: int = 0) -> None:
        """Add a line to the diagram with optional indentation.

        Args:
            line: Line content to add
            indent: Number of indentation levels (default: 0)

        Example:
            >>> builder = ConcreteBuilder()
            >>> builder.add_line("flowchart TD")
            >>> builder.add_line("A --> B", indent=1)
        """
        indentation = "    " * indent
        self.lines.append(f"{indentation}{line}")

    def add_lines(self, lines: List[str], indent: int = 0) -> None:
        """Add multiple lines to the diagram.

        Args:
            lines: List of lines to add
            indent: Number of indentation levels for all lines

        Example:
            >>> builder = ConcreteBuilder()
            >>> builder.add_lines(["A --> B", "B --> C"], indent=1)
        """
        for line in lines:
            self.add_line(line, indent)

    def clear(self) -> None:
        """Clear all diagram lines.

        Example:
            >>> builder.clear()  # Start fresh
        """
        self.lines = []
        logger.debug("Diagram cleared")

    def get_diagram(self) -> str:
        """Get current diagram as string without building.

        Returns:
            Current diagram content as string

        Example:
            >>> diagram = builder.get_diagram()
            >>> print(diagram)
        """
        return "\n".join(self.lines)

    def __str__(self) -> str:
        """String representation of the diagram.

        Returns:
            Current diagram content
        """
        return self.get_diagram()

    def __len__(self) -> int:
        """Get number of lines in the diagram.

        Returns:
            Number of lines in the diagram
        """
        return len(self.lines)
