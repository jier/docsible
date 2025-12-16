"""Sequence diagram builder for Ansible playbook flows.

This module provides a builder for creating Mermaid sequence diagrams
showing playbook-to-role-to-task execution flow.
"""

import logging
from typing import Optional, Set

from docsible.diagram_builders.base import DiagramBuilder
from docsible.diagram_builders.formatters import escape_pipes, break_text

logger = logging.getLogger(__name__)


class SequenceDiagramBuilder(DiagramBuilder):
    """Builder for Mermaid sequence diagrams.

    Creates sequence diagrams showing interaction between playbooks,
    roles, tasks, and handlers over time.

    Example:
        >>> builder = SequenceDiagramBuilder()
        >>> builder.start_diagram()
        >>> builder.add_participant("Playbook")
        >>> builder.add_participant("Role")
        >>> builder.add_message("Playbook", "Role", "Execute role")
        >>> diagram = builder.build()
    """

    def __init__(self):
        """Initialize SequenceDiagramBuilder."""
        super().__init__()
        self.participants: Set[str] = set()

    def start_diagram(self, title: Optional[str] = None) -> None:
        """Initialize sequence diagram with optional title.

        Args:
            title: Optional diagram title

        Example:
            >>> builder.start_diagram("Playbook Execution Flow")
        """
        self.clear()
        self.participants.clear()
        self.add_line("sequenceDiagram")

        if title:
            safe_title = escape_pipes(title)
            self.add_line(f"    %% {safe_title}")

    def add_participant(self, name: str, alias: Optional[str] = None) -> None:
        """Add a participant to the sequence diagram.

        Args:
            name: Participant name
            alias: Optional display alias

        Example:
            >>> builder.add_participant("webserver_role", alias="Web Server")
        """
        if name not in self.participants:
            safe_name = escape_pipes(name)

            if alias:
                safe_alias = escape_pipes(alias)
                self.add_line(f"    participant {safe_name} as {safe_alias}")
            else:
                self.add_line(f"    participant {safe_name}")

            self.participants.add(name)
            logger.debug(f"Added participant: {name}")

    def add_message(
        self, from_actor: str, to_actor: str, message: str, arrow_type: str = "->>"
    ) -> None:
        """Add a message between two actors.

        Args:
            from_actor: Sending participant
            to_actor: Receiving participant
            arrow_type: Arrow style (->>, -->, -x, --x)
            message: Message text

        Example:
            >>> builder.add_message("Playbook", "Role", "Include role")
        """
        # Ensure participants exist
        if from_actor not in self.participants:
            self.add_participant(from_actor)
        if to_actor not in self.participants:
            self.add_participant(to_actor)

        safe_from = escape_pipes(from_actor)
        safe_to = escape_pipes(to_actor)
        safe_message = escape_pipes(message)
        safe_message = break_text(safe_message, max_length=50)

        self.add_line(f"    {safe_from}{arrow_type}{safe_to}: {safe_message}")

    def add_activation(self, actor: str) -> None:
        """Activate an actor (show lifeline).

        Args:
            actor: Participant to activate

        Example:
            >>> builder.add_activation("Role")
        """
        safe_actor = escape_pipes(actor)
        self.add_line(f"    activate {safe_actor}")

    def add_deactivation(self, actor: str) -> None:
        """Deactivate an actor (hide lifeline).

        Args:
            actor: Participant to deactivate

        Example:
            >>> builder.add_deactivation("Role")
        """
        safe_actor = escape_pipes(actor)
        self.add_line(f"    deactivate {safe_actor}")

    def add_note(self, actor: str, note_text: str, position: str = "right") -> None:
        """Add a note next to an actor.

        Args:
            actor: Participant to annotate
            note_text: Note text content
            position: Note position (right, left, over)

        Example:
            >>> builder.add_note("Role", "This role installs nginx")
        """
        safe_actor = escape_pipes(actor)
        safe_text = escape_pipes(note_text)
        safe_text = break_text(safe_text, max_length=40)

        if position == "over":
            self.add_line(f"    Note over {safe_actor}: {safe_text}")
        else:
            self.add_line(f"    Note {position} of {safe_actor}: {safe_text}")

    def add_loop(self, condition: str) -> None:
        """Start a loop block.

        Args:
            condition: Loop condition text

        Example:
            >>> builder.add_loop("for each task")
        """
        safe_condition = escape_pipes(condition)
        self.add_line(f"    loop {safe_condition}")

    def end_loop(self) -> None:
        """End the current loop block.

        Example:
            >>> builder.end_loop()
        """
        self.add_line("    end")

    def add_alt(self, condition: str) -> None:
        """Start an alternative/conditional block.

        Args:
            condition: Condition text

        Example:
            >>> builder.add_alt("when ansible_os_family == 'Debian'")
        """
        safe_condition = escape_pipes(condition)
        self.add_line(f"    alt {safe_condition}")

    def add_else(self, condition: Optional[str] = None) -> None:
        """Add an else branch to current alternative block.

        Args:
            condition: Optional else-if condition

        Example:
            >>> builder.add_else("when ansible_os_family == 'RedHat'")
        """
        if condition:
            safe_condition = escape_pipes(condition)
            self.add_line(f"    else {safe_condition}")
        else:
            self.add_line("    else")

    def end_alt(self) -> None:
        """End the current alternative block.

        Example:
            >>> builder.end_alt()
        """
        self.add_line("    end")

    def add_parallel(self) -> None:
        """Start a parallel execution block.

        Example:
            >>> builder.add_parallel()
        """
        self.add_line("    par")

    def add_and(self) -> None:
        """Add another parallel branch.

        Example:
            >>> builder.add_and()
        """
        self.add_line("    and")

    def end_parallel(self) -> None:
        """End the parallel execution block.

        Example:
            >>> builder.end_parallel()
        """
        self.add_line("    end")

    def build(self) -> str:
        """Build and return the complete sequence diagram.

        Returns:
            Complete Mermaid sequence diagram as string

        Example:
            >>> diagram = builder.build()
            >>> print(diagram)
        """
        if not self.lines:
            logger.warning("Building empty sequence diagram")
            return ""

        logger.debug(
            f"Built sequence diagram with {len(self.participants)} participants "
            f"and {len(self.lines)} lines"
        )
        return self.get_diagram()
