"""Diagram generation for Mermaid diagrams.

This package consolidates all diagram generation utilities for Ansible
role and playbook documentation.

Available builders:
    - DiagramBuilder: Abstract base class for all builders
    - FlowchartBuilder: Build flowchart diagrams for task flows
    - SequenceDiagramBuilder: Build sequence diagrams for playbook execution

Sub-packages:
    - types: Specific diagram type generators
    - mermaid: Core Mermaid flowchart utilities
    - sequence: Mermaid sequence diagram utilities
"""

from docsible.diagrams import types
from docsible.diagrams.base import DiagramBuilder
from docsible.diagrams.types.flowchart import FlowchartBuilder
from docsible.diagrams.types.sequence import SequenceDiagramBuilder

__all__ = [
    "DiagramBuilder",
    "FlowchartBuilder",
    "SequenceDiagramBuilder",
    "types",
]
