"""Interactive setup wizard — docsible init."""

from pathlib import Path
from typing import Any

import click

from docsible.presets.config_manager import ConfigManager, resolve_config_path
from docsible.presets.models import DocsiblePresetConfig
from docsible.presets.registry import PresetRegistry


@click.command(name="init")
@click.option(
    "--path",
    "-p",
    "base_path",
    default=".",
    help="Base path for .docsible/config.yml (default: current directory)",
)
@click.option(
    "--preset",
    type=click.Choice(["personal", "team", "enterprise", "consultant"]),
    default=None,
    help="Skip wizard and initialize with this preset directly",
)
@click.option("--force", "-f", is_flag=True, default=False, help="Overwrite existing config")
def wizard_init(base_path: str, preset: str | None, force: bool) -> None:
    """Initialize docsible configuration for this project.

    Runs an interactive wizard to choose a preset and optional CI/CD setup.
    Use --preset to skip the wizard and configure directly.

    \f
    # Click \f convention: everything below hidden from --help output.

    Examples:
        docsible init
        docsible init --preset=team
        docsible init --preset=enterprise --force
    """
    resolved_path = Path(base_path).resolve()
    config_path = resolve_config_path(resolved_path)
    manager = ConfigManager()

    if config_path.exists() and not force:
        click.echo(f"Config already exists: {config_path}")
        if not click.confirm("Overwrite?", default=False):
            click.echo("Aborted.")
            return

    if preset:
        # Non-interactive mode
        config = DocsiblePresetConfig(preset=preset)
        manager.save(config, config_path)
        click.echo(f"Initialized with preset '{preset}': {config_path}")
        return

    # Interactive wizard
    config = _run_wizard(resolved_path)
    manager.save(config, config_path)
    click.echo("\nDocsible initialized!")
    click.echo(f"  Config : {config_path}")
    if config.preset:
        click.echo(f"  Preset : {config.preset}")
    if config.ci_cd:
        click.echo(f"  CI/CD  : {config.ci_cd.get('platform', 'configured')}")
    click.echo("\nRun 'docsible document role .' to generate documentation.")


def _run_wizard(base_path: Path) -> DocsiblePresetConfig:
    """Run the interactive 3-step setup wizard."""
    click.echo("\n" + "=" * 70)
    click.echo("  Docsible Setup Wizard")
    click.echo("=" * 70)

    # Step 1: Use case
    click.echo("\nStep 1/3: What is your use case?")
    click.echo("  1. Personal projects  (quick docs, minimal output)")
    click.echo("  2. Team collaboration (comprehensive docs, smart graphs)")
    click.echo("  3. Enterprise/prod    (validation, compliance, all reports)")
    click.echo("  4. Consulting         (maximum detail, all diagrams)")
    choice = click.prompt("\nChoice", type=click.IntRange(1, 4), default=2)
    preset_map = {1: "personal", 2: "team", 3: "enterprise", 4: "consultant"}
    chosen_preset = preset_map[choice]
    preset_obj = PresetRegistry.get(chosen_preset)
    click.echo(f"  -> {preset_obj.description}")

    # Step 2: Smart defaults
    click.echo("\nStep 2/3: Documentation detail level")
    smart = click.confirm(
        "  Enable smart defaults (auto-adjust based on role complexity)?", default=True
    )
    overrides: dict[str, Any] = {}
    if not smart:
        overrides["generate_graph"] = click.confirm("  Always generate diagrams?", default=False)
        overrides["show_dependencies"] = click.confirm(
            "  Always show dependency matrix?", default=False
        )

    # Step 3: CI/CD
    click.echo("\nStep 3/3: CI/CD Integration")
    setup_cicd = click.confirm("  Set up CI/CD integration?", default=False)
    ci_cd: dict[str, Any] = {}
    if setup_cicd:
        click.echo("  Select platform:")
        click.echo("    1. GitHub Actions")
        click.echo("    2. GitLab CI")
        click.echo("    3. Azure DevOps")
        platform_choice = click.prompt("  Choice", type=click.IntRange(1, 3), default=1)
        platform_map = {1: "github", 2: "gitlab", 3: "azure"}
        platform = platform_map[platform_choice]
        ci_cd["platform"] = platform
        _generate_cicd_workflow(base_path, platform, chosen_preset)

    return DocsiblePresetConfig(preset=chosen_preset, overrides=overrides, ci_cd=ci_cd)


def _generate_cicd_workflow(base_path: Path, platform: str, preset: str) -> None:
    """Generate a CI/CD workflow file for the chosen platform."""
    if platform == "github":
        _write_github_actions(base_path, preset)
    elif platform == "gitlab":
        _write_gitlab_ci(base_path, preset)
    elif platform == "azure":
        _write_azure_devops(base_path, preset)


def _write_github_actions(base_path: Path, preset: str) -> None:
    workflow_dir = base_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_path = workflow_dir / "docsible.yml"
    content = f"""\
name: Generate Docsible Documentation
on:
  push:
    paths:
      - 'roles/**'
      - 'tasks/**'
      - 'defaults/**'
      - 'meta/**'
jobs:
  docsible:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install docsible
        run: pip install docsible
      - name: Generate documentation
        run: docsible document role . --preset={preset}
      - uses: actions/upload-artifact@v4
        with:
          name: documentation
          path: README.md
"""
    workflow_path.write_text(content, encoding="utf-8")
    click.echo(f"  GitHub Actions workflow: {workflow_path}")


def _write_gitlab_ci(base_path: Path, preset: str) -> None:
    gitlab_ci_path = base_path / ".gitlab-ci.yml"
    content = f"""\
docsible:
  image: python:3.11
  script:
    - pip install docsible
    - docsible document role . --preset={preset}
  artifacts:
    paths:
      - README.md
  only:
    - main
    - master
"""
    gitlab_ci_path.write_text(content, encoding="utf-8")
    click.echo(f"  GitLab CI config: {gitlab_ci_path}")


def _write_azure_devops(base_path: Path, preset: str) -> None:
    azure_path = base_path / "azure-pipelines.yml"
    content = f"""\
trigger:
  paths:
    include:
      - roles/**
      - tasks/**
      - defaults/**
      - meta/**

pool:
  vmImage: ubuntu-latest

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'
  - script: pip install docsible
    displayName: Install docsible
  - script: docsible document role . --preset={preset}
    displayName: Generate documentation
  - task: PublishPipelineArtifact@1
    inputs:
      targetPath: README.md
      artifact: documentation
"""
    azure_path.write_text(content, encoding="utf-8")
    click.echo(f"  Azure DevOps pipeline: {azure_path}")
