"""docsible analyze role — analyze without generating docs."""
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
def analyze_role_cmd(preset, **kwargs) -> None:
    """Analyze an Ansible role without generating documentation."""
    resolved = resolve_settings(preset_name=preset, cli_overrides=kwargs)
    kwargs.update(resolved)
    # Force analyze intent
    kwargs["analyze_only"] = True
    kwargs.setdefault("complexity_report", True)
    core_doc_the_role(**kwargs)
