"""Generate actionable recommendations from complexity analysis."""

from typing import Any

from .models import (
    ComplexityCategory,
    ComplexityMetrics,
    FileComplexityDetail,
    IntegrationPoint,
)
from .inflections import InflectionPoint
from .hotspots import ConditionalHotspot


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
    from .analyzers.file_analyzer import _detect_file_concerns
    from docsible.analyzers.concerns.registry import ConcernRegistry

    recommendations = []

    # 1. FILE-SPECIFIC RECOMMENDATIONS (WHY + HOW format)

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

    # Detailed file-level analysis (when file_details available)
    if file_details:
        largest_file = file_details[0]

        # Generate linkable file path
        file_link = _generate_file_link(
            largest_file.file_path, None, repository_url, repo_type, repo_branch
        )

        # God file detection
        if largest_file.is_god_file:
            # Get task file info to analyze concerns
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

                # Check phase detection results first (determines if we should split at all)
                phase_result = largest_file.phase_detection
                if phase_result and phase_result.get("is_coherent_pipeline"):
                    # Coherent pipeline detected - recommend keeping together
                    confidence = int(phase_result.get("confidence", 0) * 100)
                    phases_info = phase_result.get("phases", [])
                    phase_names = " → ".join([p["phase"].title() for p in phases_info])

                    rec = [
                        f"✅ {file_link} forms a coherent pipeline ({phase_names})",
                        f"   WHY: Sequential workflow is naturally coupled ({confidence}% confidence)",
                        "   RECOMMENDATION: Keep together - splitting would break narrative flow",
                    ]

                    # Show phase breakdown with line numbers
                    if phases_info:
                        rec.append("   PHASE BREAKDOWN:")
                        for phase in phases_info:
                            rec.append(
                                f"      • Lines {phase['start_line']}-{phase['end_line']}: "
                                f"{phase['phase'].title()} ({phase['task_count']} tasks)"
                            )

                    recommendations.append("\n".join(rec))

                # Check if mixing multiple concerns (and no pipeline detected)
                elif len(all_concerns) >= 2:
                    # Mixed concerns - provide detailed WHY + HOW with line numbers
                    concern_names = ", ".join(c[1] for c in all_concerns[:3])

                    rec = [
                        f"🔀 {file_link} mixes {len(all_concerns)} concerns ({concern_names})",
                        "   WHY: Mixed responsibilities reduce maintainability, testability, and reusability",
                        "   HOW: Split by concern:",
                    ]

                    # Get detailed concern matches with line information
                    all_matches = ConcernRegistry.detect_all(tasks)
                    line_ranges = largest_file.line_ranges or []

                    for match in all_matches:
                        if match.task_count > 0:
                            detector = ConcernRegistry.get_detector(match.concern_name)
                            if detector and line_ranges:
                                # Extract line numbers for this concern's tasks
                                concern_lines = []
                                for task_idx in match.task_indices:
                                    if task_idx < len(line_ranges):
                                        start, end = line_ranges[task_idx]
                                        concern_lines.append((start, end))

                                if concern_lines:
                                    # Format line ranges compactly
                                    if len(concern_lines) == 1:
                                        line_info = f"lines {concern_lines[0][0]}-{concern_lines[0][1]}"
                                    elif len(concern_lines) <= 3:
                                        ranges = ", ".join(
                                            f"{s}-{e}" for s, e in concern_lines
                                        )
                                        line_info = f"lines {ranges}"
                                    else:
                                        first_line = concern_lines[0][0]
                                        last_line = concern_lines[-1][1]
                                        line_info = f"lines {first_line}-{last_line} ({len(concern_lines)} blocks)"

                                    rec.append(
                                        f"      • tasks/{detector.suggested_filename}: "
                                        f"{match.display_name} ({match.task_count} tasks, {line_info})"
                                    )
                                else:
                                    rec.append(
                                        f"      • tasks/{detector.suggested_filename}: "
                                        f"{match.display_name} ({match.task_count} tasks)"
                                    )
                            elif detector:
                                # Fallback without line numbers
                                rec.append(
                                    f"      • tasks/{detector.suggested_filename}: "
                                    f"{match.display_name} ({match.task_count} tasks)"
                                )

                    recommendations.append("\n".join(rec))

                elif primary_concern:
                    # Single concern but large file
                    rec = [
                        f"📁 {file_link} has {largest_file.task_count} tasks focused on {primary_concern.replace('_', ' ')}",
                        "   WHY: Large single-purpose files are hard to navigate and review",
                        "   HOW: Split into execution phases:",
                        f"      • tasks/setup_{primary_concern}.yml: Preparation tasks",
                        f"      • tasks/{primary_concern}.yml: Core implementation",
                        f"      • tasks/verify_{primary_concern}.yml: Validation tasks",
                    ]
                    recommendations.append("\n".join(rec))
                else:
                    # No clear concern detected
                    rec = [
                        f"📁 {file_link} has {largest_file.task_count} tasks with no clear single concern",
                        "   WHY: Unclear organization makes the role hard to understand and maintain",
                        "   HOW: Reorganize by execution phase or functional area",
                    ]
                    recommendations.append("\n".join(rec))

    # 2. CONDITIONAL HOTSPOT RECOMMENDATIONS (WHY + HOW format)
    for hotspot in hotspots[:2]:  # Top 2 hotspots
        hotspot_link = _generate_file_link(
            hotspot.file_path, None, repository_url, repo_type, repo_branch
        )
        rec = [
            f"🔀 {hotspot_link}: {hotspot.affected_tasks} tasks depend on '{hotspot.conditional_variable}'",
            "   WHY: OS/environment-specific branching scattered in one file makes platform support hard to test",
            f"   HOW: {hotspot.suggestion}",
        ]
        recommendations.append("\n".join(rec))

    # 3. INFLECTION POINT HINTS (WHY + HOW format)
    if inflection_points:
        main_inflection = inflection_points[0]  # Most significant
        inflection_link = _generate_file_link(
            main_inflection.file_path,
            main_inflection.task_index
            + 1,  # Convert 0-based index to 1-based line (approximate)
            repository_url,
            repo_type,
            repo_branch,
        )
        rec = [
            f"⚡ Major branch point at {inflection_link}",
            f"   WHAT: Task '{main_inflection.task_name}' branches on '{main_inflection.variable}'",
            f"   IMPACT: {main_inflection.downstream_tasks} downstream tasks affected",
            "   WHY: Multiple execution paths in one file reduce clarity and increase cognitive load",
            "   HOW: Extract branches into separate files for each path (e.g., tasks/{value}.yml)",
        ]
        recommendations.append("\n".join(rec))

    # 4. INTEGRATION ISOLATION RECOMMENDATIONS
    # Group integrations by type
    integration_by_file: dict[str, Any] = {}
    for file_detail in file_details:
        if file_detail.has_integrations and file_detail.integration_types:
            for int_type in file_detail.integration_types:
                if int_type not in integration_by_file:
                    integration_by_file[int_type] = []
                integration_by_file[int_type].append(file_detail.file_path)

    # Recommend isolation for scattered integrations
    for int_type, files in integration_by_file.items():
        if len(files) > 1:  # Integration scattered across multiple files
            integration = next(
                (ip for ip in integration_points if ip.type.value == int_type), None
            )
            if integration:
                recommendations.append(
                    f"🔌 {integration.system_name} integration scattered across {len(files)} files - "
                    f"consider consolidating in tasks/{int_type}.yml"
                )

    # 5. COMPOSITION COMPLEXITY (WHY + HOW format)
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

    # 6. INTEGRATION ISOLATION (WHY + HOW format)
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

    # 7. CREDENTIAL WARNINGS (WHY + HOW format)
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

    # 8. FALLBACK FOR SIMPLE ROLES
    if not recommendations:
        recommendations.append(
            "✅ Role complexity is well-managed - standard documentation is sufficient"
        )

    return recommendations


def _generate_file_link(
    file_path: str,
    line_number: int | None,
    repository_url: str | None,
    repo_type: str | None,
    repo_branch: str | None,
) -> str:
    """Generate a markdown link to a file in the repository.

    Args:
        file_path: Relative path to file (e.g., "tasks/main.yml")
        line_number: Optional line number to link to
        repository_url: Repository URL
        repo_type: Repository type (github, gitlab, gitea)
        repo_branch: Branch name

    Returns:
        Markdown link string or plain file path if no repository info

    Example:
        >>> _generate_file_link("tasks/main.yml", 15, "https://github.com/user/repo", "github", "main")
        '[tasks/main.yml:15](https://github.com/user/repo/blob/main/tasks/main.yml#L15)'
    """
    # If no repository info, return plain file path
    if not repository_url or not repo_type:
        if line_number:
            return f"`{file_path}:{line_number}`"
        return f"`{file_path}`"

    # Normalize repository URL (remove trailing slashes, .git suffix)
    base_url = repository_url.rstrip("/").replace(".git", "")
    branch = repo_branch or "main"

    # Build URL based on repository type
    if repo_type == "github":
        url = f"{base_url}/blob/{branch}/{file_path}"
        if line_number:
            url += f"#L{line_number}"
            return f"[{file_path}:{line_number}]({url})"
        return f"[{file_path}]({url})"

    elif repo_type == "gitlab":
        url = f"{base_url}/-/blob/{branch}/{file_path}"
        if line_number:
            url += f"#L{line_number}"
            return f"[{file_path}:{line_number}]({url})"
        return f"[{file_path}]({url})"

    elif repo_type == "gitea":
        url = f"{base_url}/src/branch/{branch}/{file_path}"
        if line_number:
            url += f"#L{line_number}"
            return f"[{file_path}:{line_number}]({url})"
        return f"[{file_path}]({url})"

    else:
        # Unknown repo type, return plain path
        if line_number:
            return f"`{file_path}:{line_number}`"
        return f"`{file_path}`"
