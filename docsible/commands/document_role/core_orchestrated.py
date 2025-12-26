"""Orchestrated version of doc_the_role using RoleOrchestrator.

This module provides a feature-flagged alternative implementation of doc_the_role
that uses the new orchestrator pattern. Enable via environment variable:
    DOCSIBLE_USE_ORCHESTRATOR=true
"""

import logging
import os
from pathlib import Path
from typing import Any

import click

from docsible.commands.document_role.helpers import apply_minimal_flag
from docsible.commands.document_role.models import (
    AnalysisConfig,
    ContentFlags,
    DiagramConfig,
    PathConfig,
    ProcessingConfig,
    RepositoryConfig,
    RoleCommandContext,
    TemplateConfig,
    ValidationConfig,
)
from docsible.commands.document_role.orchestrators import RoleOrchestrator
from docsible.exceptions import CollectionNotFoundError

logger = logging.getLogger(__name__)

def _optional_path(value: str | None) -> Path | None:
    return Path(value) if value else None

def _ensure_str(value: Path | str | None, default: str = "") -> str:
    """Convert Path | str | None to str, with default for None.

    Args:
        value: The value to convert (Path, str, or None)
        default: Default value to return if value is None

    Returns:
        String representation of value, or default if value is None
    """
    if value is None:
        return default
    return str(value)

def doc_the_role_orchestrated(**kwargs: Any) -> None:
    """Generate documentation for an Ansible role using orchestrator pattern.

    This is the new implementation using RoleOrchestrator that can be enabled
    via the DOCSIBLE_USE_ORCHESTRATOR environment variable.

    Args:
        **kwargs: All CLI parameters passed as keyword arguments matching
                  the Click command signature from doc_the_role()

    All parameters are passed via **kwargs to match the Click command signature.
    """
    # Import here to avoid circular imports
    from docsible.commands.document_collection import document_collection_roles
    from docsible.commands.document_role.smart_defaults_integration import (
        apply_smart_defaults,
    )

    # Apply minimal flag settings (keep existing helper)
    minimal = kwargs.get("minimal", False)
    if minimal:
        (
            no_vars,
            no_tasks,
            no_diagrams,
            no_examples,
            no_metadata,
            no_handlers,
            simplify_diagrams,
        ) = apply_minimal_flag(
            minimal,
            kwargs.get("no_vars", False),
            kwargs.get("no_tasks", False),
            kwargs.get("no_diagrams", False),
            kwargs.get("no_examples", False),
            kwargs.get("no_metadata", False),
            kwargs.get("no_handlers", False),
            kwargs.get("simplify_diagrams", False),
        )
        # Update kwargs with minimal flag results
        kwargs["no_vars"] = no_vars
        kwargs["no_tasks"] = no_tasks
        kwargs["no_diagrams"] = no_diagrams
        kwargs["no_examples"] = no_examples
        kwargs["no_metadata"] = no_metadata
        kwargs["no_handlers"] = no_handlers
        kwargs["simplify_diagrams"] = simplify_diagrams

    # SMART DEFAULTS INTEGRATION
    # Apply smart defaults based on role complexity (if enabled)
    enable_smart_defaults = (
        os.getenv("DOCSIBLE_ENABLE_SMART_DEFAULTS", "true").lower() == "true"
    )

    role_path = kwargs.get("role_path")
    collection_path = kwargs.get("collection_path")

    if enable_smart_defaults and role_path and not collection_path:
        try:
            from docsible.commands.document_role.helpers import validate_role_path

            # Validate role path first to ensure it exists
            temp_validated_path = validate_role_path(role_path)

            # Detect which flags user explicitly set
            # For now, assume all flags that differ from Click defaults were user-set
            # This is a simple heuristic - could be improved with Click context
            user_overrides = {}

            # If user set any of these flags, respect them
            # (In future, use Click context to detect commandline vs default)
            # For now, treat any non-default value as user override
            if kwargs.get("generate_graph") is True:  # Click default is False
                user_overrides["generate_graph"] = kwargs["generate_graph"]
            if kwargs.get("minimal") is True:  # Click default is False
                user_overrides["minimal"] = kwargs["minimal"]
            if kwargs.get("show_dependencies") is True:  # Click default is False
                user_overrides["show_dependencies"] = kwargs["show_dependencies"]

            # Apply smart defaults for non-overridden options
            smart_graph, smart_minimal, smart_deps, complexity_report = apply_smart_defaults(
                temp_validated_path, user_overrides
            )

            # Store complexity report for reuse by orchestrator (avoid duplicate analysis)
            if complexity_report:
                kwargs["_complexity_report"] = complexity_report
                logger.debug("Cached complexity analysis for reuse by orchestrator")

            # Use smart defaults only if user didn't override
            if "generate_graph" not in user_overrides:
                kwargs["generate_graph"] = smart_graph
                if smart_graph:
                    logger.info(
                        "Smart default: Enabling graph generation for this role"
                    )

            if "minimal" not in user_overrides:
                kwargs["minimal"] = smart_minimal
                if smart_minimal:
                    logger.info("Smart default: Using minimal documentation mode")

            if "show_dependencies" not in user_overrides:
                kwargs["show_dependencies"] = smart_deps
                if smart_deps:
                    logger.info("Smart default: Including dependency information")

        except Exception as e:
            logger.warning(f"Smart defaults failed: {e}")
            logger.warning("Continuing with manual configuration")
            # Continue with original values

    # Build context from parameters
    context = RoleCommandContext(
        paths=PathConfig(
            role_path=_optional_path(kwargs.get("role_path")),
            collection_path=_optional_path(kwargs.get("collection_path")),
            playbook=_optional_path(kwargs.get("playbook")),
            output=kwargs.get("output", "README.md"),
        ),
        template=TemplateConfig(
            hybrid=kwargs.get("hybrid", False),
            md_role_template=_optional_path(kwargs.get("md_role_template")),
            md_collection_template=_optional_path(kwargs.get("md_collection_template")),
        ),
        content=ContentFlags(
            no_vars=kwargs.get("no_vars", False),
            no_tasks=kwargs.get("no_tasks", False),
            no_diagrams=kwargs.get("no_diagrams", False),
            simplify_diagrams=kwargs.get("simplify_diagrams", False),
            no_examples=kwargs.get("no_examples", False),
            no_metadata=kwargs.get("no_metadata", False),
            no_handlers=kwargs.get("no_handlers", False),
            minimal=minimal,
        ),
        diagrams=DiagramConfig(
            generate_graph=kwargs.get("generate_graph", False),
            show_dependencies=kwargs.get("show_dependencies", False),
        ),
        analysis=AnalysisConfig(
            complexity_report=kwargs.get("complexity_report", False),
            include_complexity=kwargs.get("include_complexity", False),
            simplification_report=kwargs.get("simplification_report", False),
            analyze_only=kwargs.get("analyze_only", False),
            cached_complexity_report=kwargs.get("_complexity_report"),  # From smart defaults
        ),
        processing=ProcessingConfig(
            comments=kwargs.get("comments", False),
            task_line=kwargs.get("task_line", False),
            no_backup=kwargs.get("no_backup", False),
            no_docsible=kwargs.get("no_docsible", False),
            dry_run=kwargs.get("dry_run", False),
            append=kwargs.get("append", False),
        ),
        validation=ValidationConfig(
            validate_markdown=kwargs.get("validate_markdown", False),
            auto_fix=kwargs.get("auto_fix", False),
            strict_validation=kwargs.get("strict_validation", False),
        ),
        repository=RepositoryConfig(
            repository_url=kwargs.get("repository_url"),
            repo_type=kwargs.get("repo_type"),
            repo_branch=kwargs.get("repo_branch"),
        ),
    )

    # Handle collection vs role
    if context.paths.collection_path:
        try:
            # Keep existing collection handling (not yet modularized)
            document_collection_roles(
                collection_path=str(context.paths.collection_path),
                playbook=_ensure_str(context.paths.playbook),
                graph=context.diagrams.generate_graph,
                no_backup=context.processing.no_backup,
                no_docsible=context.processing.no_docsible,
                comments=context.processing.comments,
                task_line=context.processing.task_line,
                md_collection_template=_ensure_str(context.template.md_collection_template),
                md_role_template=_ensure_str(context.template.md_role_template),
                hybrid=context.template.hybrid,
                no_vars=context.content.no_vars,
                no_tasks=context.content.no_tasks,
                no_diagrams=context.content.no_diagrams,
                simplify_diagrams=context.content.simplify_diagrams,
                no_examples=context.content.no_examples,
                no_metadata=context.content.no_metadata,
                no_handlers=context.content.no_handlers,
                minimal=context.content.minimal,
                append=context.processing.append,
                output=context.paths.output,
                repository_url=context.repository.repository_url or "",
                repo_type=context.repository.repo_type or "",
                repo_branch=context.repository.repo_branch or "",
            )
        except CollectionNotFoundError as e:
            raise click.ClickException(str(e)) from e
        return

    # Use orchestrator for role documentation
    orchestrator = RoleOrchestrator(context)

    try:
        orchestrator.execute()
    except CollectionNotFoundError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise


def should_use_orchestrator() -> bool:
    """Check if orchestrator should be used based on environment variable.

    Returns:
        True by default, False if DOCSIBLE_USE_ORCHESTRATOR=false

    Note:
        The orchestrator is now the default implementation. Set
        DOCSIBLE_USE_ORCHESTRATOR=false to use legacy implementation
        (legacy will be removed in v1.0.0).
    """
    return os.environ.get("DOCSIBLE_USE_ORCHESTRATOR", "true").lower() == "true"
