"""Generate actionable recommendations from complexity analysis.

This module has been refactored from a single 297-line function into focused
helper functions for better maintainability and testability.
"""

from typing import Any

from .hotspots import ConditionalHotspot
from .inflections import InflectionPoint
from .models import (
    ComplexityCategory,
    ComplexityMetrics,
    FileComplexityDetail,
    IntegrationPoint,
)


def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    integration_points: list[IntegrationPoint],
    file_details: list[FileComplexityDetail],
    hotspots: list[ConditionalHotspot],
    inflection_points: list[InflectionPoint],
    role_info: dict[str, Any],
    repository_url: str | None = None,
    repo_type: str | None = None,
    repo_branch: str | None = None,
) -> list[str]:
    """Generate specific, actionable recommendations based on comprehensive analysis.

    This is now a clean coordinator that delegates to focused helper functions.
    Each helper function addresses one aspect of complexity analysis.

    Args:
        metrics: Overall complexity metrics
        category: Complexity category
        integration_points: External system integrations
        file_details: Per-file complexity analysis
        hotspots: Conditional complexity hotspots
        inflection_points: Major branching points
        role_info: Role information dictionary
        repository_url: Optional repository URL for linkable recommendations
        repo_type: Optional repository type (github, gitlab, gitea)
        repo_branch: Optional repository branch

    Returns:
        List of specific, actionable recommendation strings

    Example:
        >>> recommendations = generate_recommendations(...)
        >>> for rec in recommendations:
        ...     print(f"- {rec}")
    """
    recommendations = []

    # Delegate to focused helper functions
    recommendations.extend(_generate_file_recommendations(
        metrics, category, file_details, role_info,
        repository_url, repo_type, repo_branch
    ))

    recommendations.extend(_generate_hotspot_recommendations(
        hotspots, repository_url, repo_type, repo_branch
    ))

    recommendations.extend(_generate_inflection_recommendations(
        inflection_points
    ))

    recommendations.extend(_generate_integration_recommendations(
        integration_points, file_details
    ))

    recommendations.extend(_generate_composition_recommendations(
        metrics
    ))

    recommendations.extend(_generate_credential_recommendations(
        integration_points, repository_url, repo_type, repo_branch
    ))

    # Fallback for simple roles (if no other recommendations)
    if not recommendations:
        recommendations.append(
            "✅ Role complexity is well-managed - standard documentation is sufficient"
        )

    return recommendations


# ============================================================================
# Helper Functions - Each focused on one recommendation area
# ============================================================================

def _generate_file_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    file_details: list[FileComplexityDetail],
    role_info: dict[str, Any],
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> list[str]:
    """Generate file-specific recommendations.

    Analyzes individual task files for complexity and suggests splitting
    when appropriate.

    Args:
        metrics: Overall complexity metrics
        category: Complexity category
        file_details: Per-file complexity analysis
        role_info: Role information dictionary
        repository_url: Repository URL for links
        repo_type: Repository type
        repo_branch: Repository branch

    Returns:
        List of file-related recommendations
    """
    from .analyzers.file_analyzer import _detect_file_concerns

    recommendations = []

    # Metrics-based fallback (when file_details not available - primarily for unit tests)
    if not file_details and category == ComplexityCategory.COMPLEX:
        recommendations.append(
            f"📁 Role is complex ({metrics.total_tasks} tasks) - consider splitting by concern"
        )
        if metrics.max_tasks_per_file > 15:
            recommendations.append(
                f"   → Largest task file has {metrics.max_tasks_per_file} tasks - "
                "consider breaking into smaller files"
            )
        return recommendations

    # Detailed file-level analysis (when file_details available)
    if not file_details:
        return recommendations

    largest_file = file_details[0]
    file_link = _generate_file_link(
        largest_file.file_path, None, repository_url, repo_type, repo_branch
    )

    # God file detection
    if largest_file.is_god_file:
        task_file_info = next(
            (
                tf
                for tf in role_info.get("tasks", [])
                if tf.get("file") == largest_file.file_path
            ),
            None,
        )

        if task_file_info:
            tasks = task_file_info.get("tasks", [])
            primary_concern, all_concerns = _detect_file_concerns(tasks)

            # Check phase detection results
            phase_result = largest_file.phase_detection
            if phase_result and phase_result.get("is_coherent_pipeline"):
                confidence = int(phase_result.get("confidence", 0) * 100)
                phases_info = phase_result.get("phases", [])
                phase_names = " → ".join([p["phase"].title() for p in phases_info])

                recommendations.append(
                    f"🔄 {file_link} ({largest_file.task_count} tasks, {confidence}% confidence pipeline)\n"
                    f"   → Detected phases: {phase_names}\n"
                    f"   → Keep together as coherent pipeline\n"
                    f"   → {phase_result.get('reasoning', 'Well-organized pipeline structure')}"
                )
            else:
                # Multiple concerns detected - recommend splitting
                if all_concerns and len(all_concerns) > 1:
                    concern_list = [
                        f"{name.replace('_', ' ').title()} ({count})"
                        for name, _, count in all_concerns
                    ]
                    recommendations.append(
                        f"📁 {file_link} ({largest_file.task_count} tasks, multiple concerns)\n"
                        f"   WHY: Handles multiple distinct concerns: {', '.join(concern_list[:3])}\n"
                        f"   HOW: Split into separate files by concern:\n"
                        + "\n".join(
                            f"      • {name.replace('_', ' ')}.yml ({count} tasks)"
                            for name, _, count in all_concerns[:3]
                        )
                    )
                elif primary_concern:
                    recommendations.append(
                        f"📁 {file_link} ({largest_file.task_count} tasks)\n"
                        f"   WHY: Large file with single concern ({primary_concern})\n"
                        f"   HOW: Break down logically:\n"
                        f"      • {primary_concern}_validate.yml (pre-checks)\n"
                        f"      • {primary_concern}_main.yml (core logic)\n"
                        f"      • {primary_concern}_verify.yml (post-checks)"
                    )
                else:
                    recommendations.append(
                        f"📁 {file_link} ({largest_file.task_count} tasks)\n"
                        f"   WHY: Large monolithic file without clear structure\n"
                        f"   HOW: Consider splitting by:\n"
                        f"      • Execution phases (setup → execute → verify)\n"
                        f"      • Logical groupings of related tasks\n"
                        f"      • Concerns (config, install, deploy, etc.)"
                    )

    return recommendations


def _generate_hotspot_recommendations(
    hotspots: list[ConditionalHotspot],
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> list[str]:
    """Generate conditional hotspot recommendations.

    Identifies areas with high conditional complexity that may be error-prone.

    Args:
        hotspots: Conditional complexity hotspots
        repository_url: Repository URL for links
        repo_type: Repository type
        repo_branch: Repository branch

    Returns:
        List of hotspot-related recommendations
    """
    recommendations = []

    if hotspots:
        for hotspot in hotspots[:2]:  # Top 2 hotspots
            file_link = _generate_file_link(
                hotspot.file_path, None,
                repository_url, repo_type, repo_branch
            )
            rec = [
                f"🔀 {file_link}: {hotspot.affected_tasks} tasks depend on '{hotspot.conditional_variable}'",
                "   WHY: OS/environment-specific branching scattered in one file makes platform support hard to test",
                f"   HOW: {hotspot.suggestion}",
            ]
            recommendations.append("\n".join(rec))

    return recommendations


def _generate_inflection_recommendations(
    inflection_points: list[InflectionPoint],
) -> list[str]:
    """Generate inflection point recommendations.

    Identifies major branching points that control execution flow.

    Args:
        inflection_points: Major branching points

    Returns:
        List of inflection point recommendations
    """
    recommendations = []

    if inflection_points and len(inflection_points) > 2:
        variables = [ip.variable_name for ip in inflection_points[:3]]
        recommendations.append(
            f"🔀 {len(inflection_points)} inflection points detected\n"
            f"   WHY: Key variables control execution: {', '.join(variables)}\n"
            f"   HOW: Document these in README with examples for each path"
        )

    return recommendations


def _generate_integration_recommendations(
    integration_points: list[IntegrationPoint],
    file_details: list[FileComplexityDetail],
) -> list[str]:
    """Generate integration isolation recommendations.

    Suggests isolating external integrations for testability and reliability.

    Args:
        integration_points: External system integrations
        file_details: Per-file complexity analysis

    Returns:
        List of integration-related recommendations
    """
    recommendations = []

    if not integration_points:
        return recommendations

    # Group integrations by type
    from collections import defaultdict
    integrations_by_type = defaultdict(list)
    for ip in integration_points:
        integrations_by_type[ip.type.value].append(ip)

    # Recommend isolation for scattered integrations
    if file_details and len(integration_points) > 1:
        files_with_integrations = [f for f in file_details if f.has_integrations]
        if len(files_with_integrations) > 2:
            recommendations.append(
                f"🔌 {len(integration_points)} integrations scattered across "
                f"{len(files_with_integrations)} files\n"
                f"   WHY: Makes testing and error handling difficult\n"
                f"   HOW: Isolate each integration in dedicated file (e.g., api_calls.yml, db_setup.yml)"
            )

    # Recommend documentation for multiple integrations
    if len(integration_points) >= 3:
        systems = ", ".join(ip.system_name for ip in integration_points[:3])
        rec = [
            f"🔌 Multiple external integrations detected ({len(integration_points)} systems: {systems})",
            "   WHY: External integrations add operational complexity and failure points",
            "   HOW: Document integration architecture:",
            "      • Add architecture diagram showing data flow between systems",
            "      • Document retry/fallback strategies for each integration",
            "      • List external dependencies and their versions",
        ]
        recommendations.append("\n".join(rec))

    return recommendations


def _generate_composition_recommendations(
    metrics: ComplexityMetrics,
) -> list[str]:
    """Generate composition complexity recommendations.

    Addresses high role composition (role dependencies and includes).

    Args:
        metrics: Overall complexity metrics

    Returns:
        List of composition-related recommendations
    """
    recommendations = []

    if metrics.composition_score >= 8:
        rec = [
            f"🔗 High role composition complexity (score: {metrics.composition_score})",
            "   WHY: Complex role dependencies make the execution chain hard to understand and debug",
            "   HOW: Document role dependencies and include chain in README:",
            "      • List all role dependencies from meta/main.yml",
            "      • Show execution order diagram",
            "      • Document required variables passed between roles",
        ]
        recommendations.append("\n".join(rec))

    return recommendations


def _generate_credential_recommendations(
    integration_points: list[IntegrationPoint],
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> list[str]:
    """Generate credential security recommendations.

    Warns about credential management for integrations.

    Args:
        integration_points: External system integrations
        repository_url: Repository URL for links
        repo_type: Repository type
        repo_branch: Repository branch

    Returns:
        List of credential-related recommendations
    """
    recommendations = []

    if any(ip.uses_credentials for ip in integration_points):
        cred_systems = [
            ip.system_name for ip in integration_points if ip.uses_credentials
        ]
        rec = [
            f"🔐 Credentials required for {', '.join(cred_systems)}",
            "   WHY: Hardcoded credentials pose security risks and complicate credential rotation",
            "   HOW: Secure credential management:",
            "      • Use Ansible Vault for sensitive variables",
            "      • Document required credentials in README",
            "      • Consider external secret management (HashiCorp Vault, AWS Secrets Manager)",
        ]
        recommendations.append("\n".join(rec))

    return recommendations


# ============================================================================
# Utility Functions
# ============================================================================

def _generate_file_link(
    file_path: str,
    line_number: int | None,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> str:
    """Generate a linkable file path (or plain path if no repository info).

    Args:
        file_path: Relative file path (e.g., "tasks/main.yml")
        line_number: Optional line number for deep linking
        repository_url: Repository base URL
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Repository branch name

    Returns:
        Markdown link to file or plain file path

    Example:
        >>> _generate_file_link("tasks/main.yml", 42, "https://github.com/user/repo", "github", "main")
        '[tasks/main.yml:42](https://github.com/user/repo/blob/main/tasks/main.yml#L42)'
    """
    # If no repository info, return plain file path
    if not repository_url or not repo_type:
        return f"`{file_path}`" + (f":{line_number}" if line_number else "")

    # Normalize repository URL (remove trailing slashes, .git suffix)
    base_url = repository_url.rstrip("/")
    base_url = base_url.removesuffix(".git")

    # Build URL based on repository type
    if repo_type.lower() == "github":
        path_segment = "blob"
    elif repo_type.lower() in ("gitlab", "gitea"):
        path_segment = "blob"
    else:
        # Unknown type, fallback to plain text
        return f"`{file_path}`" + (f":{line_number}" if line_number else "")

    branch = repo_branch or "main"
    file_url = f"{base_url}/{path_segment}/{branch}/{file_path}"

    if line_number:
        file_url += f"#L{line_number}"
        return f"[`{file_path}:{line_number}`]({file_url})"
    else:
        return f"[`{file_path}`]({file_url})"
