"""Configuration models for smart defaults."""

from pydantic import BaseModel, Field

from docsible.defaults.decisions.base import Decision


class DocumentationConfig(BaseModel):
    """Complete configuration for documentation generation.

    This is the output of the smart defaults engine.
    Combines decisions into a cohesive configuration object.
    """

    # Graph options
    generate_graph: bool = Field(
        default=False,
        description="Generate a dependency or include graph for the role."
    )
    simplify_diagrams: bool = Field(
        default=False,
        description="Simplify generated diagrams to reduce visual complexity."
    )
    no_diagrams: bool = Field(
        default=False,
        description="Disable diagram generation entirely."
    )

    # Content options
    no_vars: bool = Field(
        default=False,
        description="Exclude variables documentation."
    )
    no_tasks: bool = Field(
        default=False,
        description="Exclude tasks documentation."
    )
    no_metadata: bool = Field(
        default=False,
        description="Exclude metadata documentation."
    )
    no_examples: bool = Field(
        default=False,
        description="Exclude examples documentation."
    )
    no_handlers: bool = Field(
        default=False,
        description="Exclude handlers documentation."
    )
    minimal: bool = Field(
        default=False,
        description="Generate minimal documentation with only essential sections."
    )

    # Output options
    output: str = Field(
        default="README.md",
        description="Output file path for the generated documentation."
    )
    no_backup: bool = Field(
        default=False,
        description="Do not create a backup of an existing output file."
    )
    append: bool = Field(
        default=False,
        description="Append documentation to an existing output file instead of overwriting."
    )

    # Reporting options
    complexity_report: bool = Field(
        default=False,
        description="Include a complexity analysis report."
    )
    simplification_report: bool = Field(
        default=False,
        description="Include a report explaining simplification decisions."
    )
    show_dependencies: bool = Field(
        default=False,
        description="Show role dependencies in the generated documentation."
    )

    # Metadata
    decisions: list[Decision] = Field(
    default_factory=list,
    description="List of Decision objects that led to this configuration."
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence score for this configuration (0.0-1.0)."
    )

    def to_cli_args(self) -> list[str]:
        """Convert configuration to CLI arguments.

        Useful for:
        - Testing: compare CLI args vs smart defaults
        - Logging: show what would have been typed
        - Migration: help users understand what's happening
        """
        args: list[str] = []

        if self.generate_graph:
            args.append("--graph")
        if self.no_diagrams:
            args.append("--no-diagrams")
        if self.simplify_diagrams:
            args.append("--simplify-diagrams")

        if self.no_vars:
            args.append("--no-vars")
        if self.no_tasks:
            args.append("--no-tasks")
        if self.no_metadata:
            args.append("--no-metadata")
        if self.no_examples:
            args.append("--no-examples")
        if self.no_handlers:
            args.append("--no-handlers")
        if self.minimal:
            args.append("--minimal")

        if self.complexity_report:
            args.append("--complexity-report")
        if self.simplification_report:
            args.append("--simplification-report")
        if self.show_dependencies:
            args.append("--show-dependencies")

        if self.output != "README.md":
            args.extend(["--output", self.output])

        if self.no_backup:
            args.append("--no-backup")
        if self.append:
            args.append("--append")

        return args

    def get_decision_summary(self) -> str:
        """Human-readable summary of decisions made.

        Useful for:
        - --dry-run output
        - Verbose logging
        - User education ("here's what I decided and why")
        """
        lines = ["Smart Defaults Applied:"]

        for decision in self.decisions:
            lines.append(
                f"  • {decision.option_name} = {decision.value} "
                f"({decision.confidence:.0%} confident: {decision.rationale})"
            )

        return "\n".join(lines)
