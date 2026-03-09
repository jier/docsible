"""docsible validate role — validate without writing files."""

import click

from docsible.commands.document_role.core_orchestrated import doc_the_role as core_doc_the_role
from docsible.commands.document_role.options import (
    add_content_options,
    add_framing_options,
    add_generation_options,
    add_output_options,
    add_path_options,
    add_recommendation_options,
    add_repository_options,
    add_template_options,
)
from docsible.presets.registry import PresetRegistry
from docsible.presets.resolver import resolve_settings


@click.command(name="role")
@add_path_options
@add_output_options
@add_content_options
@add_template_options
@add_generation_options
@add_repository_options
@add_recommendation_options
@add_framing_options
@click.option(
    "--preset",
    type=click.Choice(PresetRegistry.names()),
    default=None,
    help="Apply a built-in preset.",
)
@click.option(
    "--strict/--no-strict",
    "strict_validation",
    default=True,
    help="Fail on validation warnings (default: on for validate intent).",
)
def validate_role_cmd(preset, strict_validation, **kwargs) -> None:
    """Validate documentation for an Ansible role (no files written)."""
    resolved = resolve_settings(preset_name=preset, cli_overrides=kwargs)
    kwargs.update(resolved)
    # Force validate intent
    kwargs["validate_markdown"] = True
    kwargs["strict_validation"] = strict_validation
    kwargs["dry_run"] = True
    kwargs["analyze_only"] = False
    core_doc_the_role(**kwargs)
