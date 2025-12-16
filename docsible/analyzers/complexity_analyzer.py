"""
Complexity analyzer for Ansible roles.

Analyzes role complexity by counting tasks, conditionals, role composition,
and external integrations to determine appropriate documentation strategy.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import concern detection system
from docsible.analyzers.concerns.registry import ConcernRegistry

# Import phase detection system
from docsible.analyzers.phase_detector import PhaseDetector


# Import pattern analysis (optional dependency)
try:
    from docsible.analyzers.patterns import (
        analyze_role_patterns,
        PatternAnalysisReport,
    )
    PATTERN_ANALYSIS_AVAILABLE = True
except ImportError:
    logger.debug("Pattern analysis not available")
    PATTERN_ANALYSIS_AVAILABLE = False
    PatternAnalysisReport = None  # type: ignore


class ComplexityCategory(str, Enum):
    """Role complexity categories based on task count."""

    SIMPLE = "simple"  # 1-10 tasks
    MEDIUM = "medium"  # 11-25 tasks
    COMPLEX = "complex"  # 25+ tasks


class IntegrationType(str, Enum):
    """Types of external system integrations."""

    API = "api"
    DATABASE = "database"
    VAULT = "vault"
    CLOUD = "cloud"
    NETWORK = "network"
    CONTAINER = "container"
    MONITORING = "monitoring"


class IntegrationPoint(BaseModel):
    """Represents a detected external system integration."""

    type: IntegrationType
    system_name: str
    modules_used: List[str]
    task_count: int
    uses_credentials: bool = False
    # Type-specific details
    endpoints: List[str] = Field(
        default_factory=list, description="API endpoints or URLs"
    )
    ports: List[int] = Field(default_factory=list, description="Network ports used")
    services: List[str] = Field(
        default_factory=list, description="Cloud services or container images"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional type-specific details"
    )


class ComplexityMetrics(BaseModel):
    """Detailed metrics for role complexity analysis."""

    # Task metrics
    total_tasks: int = Field(description="Total number of tasks across all files")
    task_files: int = Field(description="Number of task files")
    handlers: int = Field(description="Number of handlers")
    conditional_tasks: int = Field(description="Tasks with 'when' conditions")
    error_handlers: int = Field(
        default=0, description="Tasks with error handling (rescue/always blocks)"
    )

    # Internal composition (role orchestration)
    role_dependencies: int = Field(
        default=0, description="Role dependencies from meta/main.yml"
    )
    role_includes: int = Field(default=0, description="include_role/import_role count")
    task_includes: int = Field(
        default=0, description="include_tasks/import_tasks count"
    )

    # External integrations
    external_integrations: int = Field(
        default=0, description="Count of external system connections"
    )

    # Calculated metrics
    max_tasks_per_file: int = Field(description="Maximum tasks in a single file")
    avg_tasks_per_file: float = Field(description="Average tasks per file")

    @property
    def composition_score(self) -> int:
        """
        Calculate composition complexity score.

        Higher score = more complex orchestration.
        """
        return (
            self.role_dependencies * 2  # Meta deps are important
            + self.role_includes
            + self.task_includes
        )

    @property
    def conditional_percentage(self) -> float:
        """Percentage of tasks that are conditional."""
        if self.total_tasks == 0:
            return 0.0
        return (self.conditional_tasks / self.total_tasks) * 100

class FileComplexityDetail(BaseModel):
    """Detailed complexity metrics for a single task file."""

    file_path: str = Field(description="Relative path to task file")
    task_count: int = Field(description="Number of tasks in this file")
    conditional_count: int = Field(description="Number of conditional tasks")
    conditional_percentage: float = Field(description="Percentage of conditional tasks")
    has_integrations: bool = Field(default=False, description="File uses external integrations")
    integration_types: List[str] = Field(default_factory=list, description="Types of integrations used")
    module_diversity: int = Field(description="Number of unique modules used")
    primary_concern: Optional[str] = Field(default=None, description="Detected primary concern")
    phase_detection: Optional[Dict[str, Any]] = Field(default=None, description="Phase detection results")
    line_ranges: Optional[List[tuple]] = Field(default=None, description="Line ranges for each task")

    @property
    def is_god_file(self) -> bool:
        """Check if this is a 'god file' (too many responsibilities)."""
        return self.task_count > 15 or self.module_diversity > 10

    @property
    def is_conditional_heavy(self) -> bool:
        """Check if this file has high conditional complexity."""
        return self.conditional_percentage > 50.0 and self.conditional_count > 5

class ComplexityReport(BaseModel):
    """Complete complexity analysis report."""

    metrics: ComplexityMetrics
    category: ComplexityCategory
    integration_points: List[IntegrationPoint] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    task_files_detail: List[Dict[str, Any]] = Field(default_factory=list)

    # Pattern analysis (optional, only included when --simplification-report flag is used)
    pattern_analysis: Optional[Any] = Field(
        default=None,
        description="Detailed pattern analysis report with simplification suggestions"
    )

def analyze_file_complexity(
    role_info: Dict[str, Any],
    integration_points: List[IntegrationPoint]
) -> List[FileComplexityDetail]:
    """
    Analyze complexity metrics for each task file.

    Args:
        role_info: Role information dictionary
        integration_points: Detected integration points

    Returns:
        List of FileComplexityDetail objects, sorted by task count (descending)

    Example:
        >>> files = analyze_file_complexity(role_info, integrations)
        >>> largest = files[0]
        >>> print(f"{largest.file_path}: {largest.task_count} tasks")
    """
    file_details = []
    phase_detector = PhaseDetector(min_confidence=0.8)  # Conservative threshold

    for task_file_info in role_info.get("tasks", []):
        file_path = task_file_info.get("file", "unknown")
        tasks = task_file_info.get("tasks", [])

        if not tasks:
            continue

        # Count conditionals
        conditional_tasks = [t for t in tasks if t.get("when")]
        conditional_count = len(conditional_tasks)
        conditional_percentage = (conditional_count / len(tasks)) * 100 if tasks else 0.0

        # Detect integrations in this file
        has_integrations = False
        integration_types = []
        for integration in integration_points:
            # Check if any integration modules are used in this file
            file_modules = set(t.get("module", "") for t in tasks)
            if any(mod in file_modules for mod in integration.modules_used):
                has_integrations = True
                integration_types.append(integration.type.value)

        # Count unique modules (diversity indicator)
        unique_modules = len(set(t.get("module", "") for t in tasks if t.get("module")))

        # Detect primary concern (simple heuristic based on modules)
        primary_concern = _detect_file_concern(tasks)

        # Get line ranges if available
        line_ranges = task_file_info.get("line_ranges")

        # Perform phase detection
        phase_detection_result = None
        try:
            result = phase_detector.detect_phases(tasks, line_ranges)
            if result.detected_phases or result.is_coherent_pipeline:
                # Serialize phase detection result for storage
                phase_detection_result = {
                    "is_coherent_pipeline": result.is_coherent_pipeline,
                    "confidence": result.confidence,
                    "recommendation": result.recommendation,
                    "reasoning": result.reasoning,
                    "phases": [
                        {
                            "phase": phase.phase.value,
                            "start_line": phase.start_line,
                            "end_line": phase.end_line,
                            "task_count": phase.task_count,
                            "confidence": phase.confidence,
                        }
                        for phase in result.detected_phases
                    ]
                }
        except Exception as e:
            logger.debug(f"Phase detection failed for {file_path}: {e}")

        file_details.append(
            FileComplexityDetail(
                file_path=file_path,
                task_count=len(tasks),
                conditional_count=conditional_count,
                conditional_percentage=conditional_percentage,
                has_integrations=has_integrations,
                integration_types=list(set(integration_types)),
                module_diversity=unique_modules,
                primary_concern=primary_concern,
                phase_detection=phase_detection_result,
                line_ranges=line_ranges,
            )
        )

    # Sort by task count (largest first)
    return sorted(file_details, key=lambda f: f.task_count, reverse=True)

def _detect_file_concerns(
    tasks: List[Dict[str, Any]]
) -> tuple[Optional[str], List[tuple[str, str, int]]]:
    """
    Detect all concerns in a task file and return primary + detailed breakdown.

    Args:
        tasks: List of tasks in the file

    Returns:
        Tuple of (primary_concern, [(concern_name, display_name, count)])

    Example:
        >>> primary, concerns = _detect_file_concerns(tasks)
        >>> print(primary)  # 'package_installation'
        >>> print(concerns)  # [('package_installation', 'Package Installation', 5), ...]
    """
    from docsible.analyzers.concerns.registry import ConcernRegistry

    # Get all concerns
    all_matches = ConcernRegistry.detect_all(tasks)

    # Primary concern
    primary = ConcernRegistry.detect_primary_concern(tasks, min_confidence=0.6)
    primary_name = primary.concern_name if primary else None

    # Detailed breakdown (only concerns with >0 tasks)
    concerns_breakdown = [
        (match.concern_name, match.display_name, match.task_count)
        for match in all_matches
        if match.task_count > 0
    ]

    return primary_name, concerns_breakdown


def _detect_file_concern(tasks: List[Dict[str, Any]]) -> Optional[str]:
    """
    Detect the primary concern/responsibility of a task file.

    Uses pluggable concern detection system for extensibility.

    Args:
        tasks: List of tasks in the file

    Returns:
        String describing primary concern, or None if mixed

    Example:
        >>> tasks = [{"module": "apt"}, {"module": "yum"}]
        >>> _detect_file_concern(tasks)
        'package_installation'
    """
    # Use pluggable concern registry
    primary = ConcernRegistry.detect_primary_concern(tasks, min_confidence=0.6)
    return primary.concern_name if primary else None

class ConditionalHotspot(BaseModel):
    """Represents a file with high conditional complexity."""
    
    file_path: str
    conditional_variable: str = Field(description="Main variable driving conditionals")
    usage_count: int = Field(description="How many times this variable appears in conditions")
    affected_tasks: int = Field(description="Number of tasks using this condition")
    suggestion: str = Field(description="Recommended action")

def detect_conditional_hotspots(
    role_info: Dict[str, Any],
    file_details: List[FileComplexityDetail]
) -> List[ConditionalHotspot]:
    """
    Identify files with concentrated conditional logic and the variables driving it.
    
    Args:
        role_info: Role information dictionary
        file_details: File complexity analysis results
    
    Returns:
        List of ConditionalHotspot objects
    
    Example:
        >>> hotspots = detect_conditional_hotspots(role_info, file_details)
        >>> for hotspot in hotspots:
        ...     print(f"{hotspot.file_path}: {hotspot.conditional_variable}")
    """
    hotspots = []
    
    # Focus on files with high conditional percentage
    conditional_files = [f for f in file_details if f.is_conditional_heavy]
    
    for file_detail in conditional_files:
        # Find the corresponding task file data
        task_file_info = next(
            (tf for tf in role_info.get("tasks", []) if tf.get("file") == file_detail.file_path),
            None
        )
        
        if not task_file_info:
            continue
        
        tasks = task_file_info.get("tasks", [])
        
        # Analyze conditional variables
        conditional_vars = _extract_conditional_variables(tasks)
        
        if conditional_vars:
            # Find most common conditional variable
            most_common = max(conditional_vars.items(), key=lambda x: x[1])
            var_name, usage_count = most_common
            
            # Count tasks affected by this variable
            affected_tasks = sum(
                1 for t in tasks
                if t.get("when") and var_name in str(t.get("when"))
            )
            
            # Generate suggestion
            suggestion = _generate_split_suggestion(var_name, file_detail.file_path)
            
            hotspots.append(
                ConditionalHotspot(
                    file_path=file_detail.file_path,
                    conditional_variable=var_name,
                    usage_count=usage_count,
                    affected_tasks=affected_tasks,
                    suggestion=suggestion,
                )
            )
    
    return hotspots


def _extract_conditional_variables(tasks: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Extract variables used in 'when' conditions and count their usage.
    
    Args:
        tasks: List of tasks
    
    Returns:
        Dictionary mapping variable names to usage count
    
    Example:
        >>> tasks = [
        ...     {"when": "ansible_os_family == 'Debian'"},
        ...     {"when": "ansible_os_family == 'RedHat'"}
        ... ]
        >>> _extract_conditional_variables(tasks)
        {'ansible_os_family': 2}
    """
    import re
    
    var_counter = {}
    
    # Common Ansible fact/variable patterns
    VAR_PATTERN = re.compile(r'([a-z_][a-z0-9_]*)')
    
    for task in tasks:
        when_clause = task.get("when")
        if not when_clause:
            continue
        
        # Convert to string (can be list or string)
        when_str = str(when_clause)
        
        # Extract variable names
        matches = VAR_PATTERN.findall(when_str)
        
        for var_name in matches:
            # Filter out common operators and keywords
            if var_name in ["and", "or", "not", "is", "in", "true", "false", "defined"]:
                continue
            
            var_counter[var_name] = var_counter.get(var_name, 0) + 1
    
    return var_counter


def _generate_split_suggestion(var_name: str, file_path: str) -> str:
    """
    Generate a suggestion for splitting based on conditional variable.
    
    Args:
        var_name: Variable name driving conditionals
        file_path: Original file path
    
    Returns:
        Suggested split strategy
    
    Example:
        >>> _generate_split_suggestion("ansible_os_family", "tasks/main.yml")
        'Split into tasks/debian.yml and tasks/redhat.yml based on OS family'
    """
    # Common patterns
    if "os_family" in var_name or "distribution" in var_name:
        return "Split into tasks/debian.yml and tasks/redhat.yml based on OS family"
    elif "environment" in var_name or "env" in var_name:
        return "Split into tasks/production.yml and tasks/staging.yml by environment"
    elif "mode" in var_name or "strategy" in var_name:
        return f"Split by {var_name} into separate task files"
    else:
        base_name = file_path.replace("tasks/", "").replace(".yml", "")
        return f"Extract conditional logic into tasks/{base_name}_{{value}}.yml files"

class InflectionPoint(BaseModel):
    """Represents a major branching point in task execution."""
    
    file_path: str
    task_name: str = Field(description="Task where branching occurs")
    task_index: int = Field(description="Position in file (0-based)")
    variable: str = Field(description="Variable driving the branch")
    branch_count: int = Field(description="Number of execution paths from this point")
    downstream_tasks: int = Field(description="Tasks affected by this branch")

def detect_inflection_points(
    role_info: Dict[str, Any],
    hotspots: List[ConditionalHotspot]
) -> List[InflectionPoint]:
    """
    Identify major branching points where execution paths diverge.
    
    An inflection point is a task that:
    1. Uses a conditional variable
    2. Is followed by many tasks using the same variable
    3. Represents a major decision point
    
    Args:
        role_info: Role information dictionary
        hotspots: Conditional hotspot analysis results
    
    Returns:
        List of InflectionPoint objects
    
    Example:
        >>> inflections = detect_inflection_points(role_info, hotspots)
        >>> for point in inflections:
        ...     print(f"{point.file_path}:{point.task_index} - {point.variable}")
    """
    inflection_points = []
    
    for hotspot in hotspots:
        # Find the task file
        task_file_info = next(
            (tf for tf in role_info.get("tasks", []) if tf.get("file") == hotspot.file_path),
            None
        )
        
        if not task_file_info:
            continue
        
        tasks = task_file_info.get("tasks", [])
        var_name = hotspot.conditional_variable
        
        # Find first task using this variable
        for idx, task in enumerate(tasks):
            when_clause = str(task.get("when", ""))
            
            if var_name in when_clause:
                # Count downstream tasks using same variable
                downstream = sum(
                    1 for t in tasks[idx+1:]
                    if var_name in str(t.get("when", ""))
                )
                
                # Only report significant inflection points
                if downstream >= 3:
                    inflection_points.append(
                        InflectionPoint(
                            file_path=hotspot.file_path,
                            task_name=task.get("name", f"Task {idx + 1}"),
                            task_index=idx,
                            variable=var_name,
                            branch_count=2,  # Simplified: assume binary branch
                            downstream_tasks=downstream,
                        )
                    )
                    break  # Only report first major inflection per variable
    
    return inflection_points


def _generate_file_link(
    file_path: str,
    line_number: Optional[int],
    repository_url: Optional[str],
    repo_type: Optional[str],
    repo_branch: Optional[str]
) -> str:
    """
    Generate a markdown link to a file in the repository.

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
    base_url = repository_url.rstrip('/').replace('.git', '')
    branch = repo_branch or 'main'

    # Build URL based on repository type
    if repo_type == 'github':
        url = f"{base_url}/blob/{branch}/{file_path}"
        if line_number:
            url += f"#L{line_number}"
            return f"[{file_path}:{line_number}]({url})"
        return f"[{file_path}]({url})"

    elif repo_type == 'gitlab':
        url = f"{base_url}/-/blob/{branch}/{file_path}"
        if line_number:
            url += f"#L{line_number}"
            return f"[{file_path}:{line_number}]({url})"
        return f"[{file_path}]({url})"

    elif repo_type == 'gitea':
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


def analyze_role_complexity(
    role_info: Dict[str, Any],
    include_patterns: bool = False,
    min_confidence: float = 0.7
) -> ComplexityReport:
    """
    Analyze role complexity and generate comprehensive report.

    Args:
        role_info: Role information dictionary from build_role_info()
        include_patterns: Whether to include pattern analysis (requires --simplification-report flag)
        min_confidence: Minimum confidence threshold for pattern detection (0.0-1.0)

    Returns:
        ComplexityReport with metrics, category, recommendations, and optional pattern analysis

    Example:
        >>> report = analyze_role_complexity(role_info)
        >>> print(f"Category: {report.category}")
        >>> print(f"Total tasks: {report.metrics.total_tasks}")

        >>> # With pattern analysis
        >>> report = analyze_role_complexity(role_info, include_patterns=True)
        >>> if report.pattern_analysis:
        ...     print(f"Health Score: {report.pattern_analysis.overall_health_score}")
    """
    # Count tasks
    tasks_data = role_info.get("tasks", [])
    total_tasks = sum(len(tf.get("tasks", [])) for tf in tasks_data)
    task_files = len(tasks_data)

    # Count handlers
    handlers = len(role_info.get("handlers", []))

    # Count conditional tasks
    conditional_tasks = sum(
        1 for tf in tasks_data for task in tf.get("tasks", []) if task.get("when")
    )

    # Count tasks with error handling (rescue or always blocks)
    error_handlers = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("rescue") or task.get("always")
    )

    # Count role dependencies (from meta/main.yml)
    role_dependencies = len(role_info.get("meta", {}).get("dependencies", []))

    # Count role includes (include_role, import_role)
    role_includes = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("module", "")
        in [
            "include_role",
            "import_role",
            "ansible.builtin.include_role",
            "ansible.builtin.import_role",
        ]
    )

    # Count task includes (include_tasks, import_tasks)
    task_includes = sum(
        1
        for tf in tasks_data
        for task in tf.get("tasks", [])
        if task.get("module", "")
        in [
            "include_tasks",
            "import_tasks",
            "ansible.builtin.include_tasks",
            "ansible.builtin.import_tasks",
        ]
    )

    # Calculate max and average tasks per file
    tasks_per_file = [len(tf.get("tasks", [])) for tf in tasks_data]
    max_tasks_per_file = max(tasks_per_file) if tasks_per_file else 0
    avg_tasks_per_file = (
        sum(tasks_per_file) / len(tasks_per_file) if tasks_per_file else 0.0
    )

    # Detect external integrations
    integration_points = detect_integrations(role_info)

    # Analyze per-file complexity
    file_details = analyze_file_complexity(role_info, integration_points)
    
    # Detect conditional hotspots
    hotspots = detect_conditional_hotspots(role_info, file_details)
    
    # Detect inflection points
    inflection_points = detect_inflection_points(role_info, hotspots)

    # Create metrics
    metrics = ComplexityMetrics(
        total_tasks=total_tasks,
        task_files=task_files,
        handlers=handlers,
        conditional_tasks=conditional_tasks,
        error_handlers=error_handlers,
        role_dependencies=role_dependencies,
        role_includes=role_includes,
        task_includes=task_includes,
        external_integrations=len(integration_points),
        max_tasks_per_file=max_tasks_per_file,
        avg_tasks_per_file=avg_tasks_per_file,
    )

    # Classify complexity
    category = classify_complexity(metrics)

    # Extract repository info for linkable recommendations
    repository_url = role_info.get("repository")
    repo_type = role_info.get("repository_type")
    repo_branch = role_info.get("repository_branch")

    # Generate recommendations
    recommendations = generate_recommendations(
        metrics=metrics,
        category=category,
        integration_points=integration_points,
        inflection_points=inflection_points,
        file_details=file_details,
        hotspots=hotspots,
        role_info=role_info,
        repository_url=repository_url,
        repo_type=repo_type,
        repo_branch=repo_branch
    )

    # Task files detail
    task_files_detail = [
        {
            "file": tf.get("file", "unknown"),
            "task_count": len(tf.get("tasks", [])),
            "has_integrations": _file_has_integrations(tf, integration_points),
        }
        for tf in tasks_data
    ]

    # Run pattern analysis if requested
    pattern_report = None
    if include_patterns and PATTERN_ANALYSIS_AVAILABLE:
        try:
            logger.info("Running pattern analysis...")
            pattern_report = analyze_role_patterns(role_info, min_confidence=min_confidence)
            logger.info(
                f"Pattern analysis complete: {pattern_report.total_patterns} patterns found "
                f"(health score: {pattern_report.overall_health_score:.1f}/100)"
            )
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}", exc_info=True)
            pattern_report = None
    elif include_patterns and not PATTERN_ANALYSIS_AVAILABLE:
        logger.warning(
            "Pattern analysis requested but not available. "
            "Install pattern analyzer dependencies to enable this feature."
        )

    return ComplexityReport(
        metrics=metrics,
        category=category,
        integration_points=integration_points,
        recommendations=recommendations,
        task_files_detail=task_files_detail,
        pattern_analysis=pattern_report,
    )


def classify_complexity(metrics: ComplexityMetrics) -> ComplexityCategory:
    """
    Classify role complexity based on task count.

    Thresholds:
    - Simple: 1-10 tasks
    - Medium: 11-25 tasks
    - Complex: 25+ tasks
    """
    if metrics.total_tasks <= 10:
        return ComplexityCategory.SIMPLE
    elif metrics.total_tasks <= 25:
        return ComplexityCategory.MEDIUM
    else:
        return ComplexityCategory.COMPLEX


def detect_integrations(role_info: Dict[str, Any]) -> List[IntegrationPoint]:
    """
    Detect external system integrations by analyzing task modules.

    Currently detects:
    - API calls (uri, get_url)
    - Database operations (mysql, postgresql, mongodb)
    - Vault operations (hashi_vault)

    Excludes Ansible composition modules (include_role, include_tasks, etc.)
    """
    # Module patterns for detection
    API_MODULES = ["uri", "get_url", "ansible.builtin.uri", "ansible.builtin.get_url"]
    DATABASE_MODULES = [
        "mysql",
        "mysql_",
        "postgresql",
        "postgresql_",
        "mongodb",
        "mongodb_",
        "community.mysql",
        "community.postgresql",
        "community.mongodb",
    ]
    VAULT_MODULES = ["hashi_vault", "community.hashi_vault"]
    CLOUD_MODULES = [
        "aws_",
        "amazon.aws",
        "ec2",
        "s3",
        "rds",
        "lambda",  # AWS
        "azure_",
        "azure.azcollection",  # Azure
        "gcp_",
        "google.cloud",  # GCP
        "openstack",
        "os_",  # OpenStack
    ]
    NETWORK_MODULES = [
        "firewalld",
        "iptables",
        "ufw",  # Firewall
        "nmcli",
        "network",
        "route",  # Network config
        "cisco",
        "junos",
        "vyos",  # Network devices
        "ansible.builtin.iptables",
        "community.general.ufw",
    ]
    CONTAINER_MODULES = [
        "docker",
        "docker_",
        "community.docker",  # Docker
        "podman",
        "containers.podman",  # Podman
        "kubernetes",
        "k8s",
        "community.kubernetes",  # Kubernetes
    ]
    MONITORING_MODULES = [
        "datadog",
        "newrelic",  # APM
        "prometheus",
        "grafana",  # Metrics
        "pagerduty",
        "opsgenie",  # Alerting
        "nagios",
        "zabbix",  # Monitoring
    ]

    # Ansible composition modules to exclude
    COMPOSITION_MODULES = [
        "include_role",
        "import_role",
        "include_tasks",
        "import_tasks",
        "ansible.builtin.include_role",
        "ansible.builtin.import_role",
        "ansible.builtin.include_tasks",
        "ansible.builtin.import_tasks",
    ]

    integration_map = {}  # type -> list of tasks

    for task_file_info in role_info.get("tasks", []):
        for task in task_file_info.get("tasks", []):
            module = task.get("module", "")

            # Skip composition modules
            if module in COMPOSITION_MODULES:
                continue

            # Check for integrations
            int_type = None
            if module in API_MODULES:
                int_type = IntegrationType.API
            elif any(module.startswith(db) for db in DATABASE_MODULES):
                int_type = IntegrationType.DATABASE
            elif any(v in module for v in VAULT_MODULES):
                int_type = IntegrationType.VAULT
            elif any(
                module.startswith(cloud) or cloud in module for cloud in CLOUD_MODULES
            ):
                int_type = IntegrationType.CLOUD
            elif any(
                module.startswith(net) or net in module for net in NETWORK_MODULES
            ):
                int_type = IntegrationType.NETWORK
            elif any(
                module.startswith(cont) or cont in module for cont in CONTAINER_MODULES
            ):
                int_type = IntegrationType.CONTAINER
            elif any(
                module.startswith(mon) or mon in module for mon in MONITORING_MODULES
            ):
                int_type = IntegrationType.MONITORING

            if int_type:
                if int_type not in integration_map:
                    integration_map[int_type] = []
                integration_map[int_type].append(
                    {
                        "module": module,
                        "task": task,
                    }
                )

    # Create IntegrationPoint objects
    integration_points = []

    for int_type, tasks in integration_map.items():
        modules_used = list(set(t["module"] for t in tasks))
        task_count = len(tasks)

        # Detect credential usage
        uses_credentials = any(_task_uses_credentials(t["task"]) for t in tasks)

        # Extract type-specific details
        endpoints = (
            _extract_endpoints([t["task"] for t in tasks])
            if int_type == IntegrationType.API
            else []
        )
        ports = (
            _extract_ports([t["task"] for t in tasks])
            if int_type == IntegrationType.NETWORK
            else []
        )
        services = _extract_services(modules_used, int_type)

        # Determine system name
        system_name = {
            IntegrationType.API: "REST APIs",
            IntegrationType.DATABASE: _detect_database_type(modules_used),
            IntegrationType.VAULT: "HashiCorp Vault",
            IntegrationType.CLOUD: _detect_cloud_provider(modules_used),
            IntegrationType.NETWORK: "Network Infrastructure",
            IntegrationType.CONTAINER: _detect_container_platform(modules_used),
            IntegrationType.MONITORING: _detect_monitoring_platform(modules_used),
        }.get(int_type, str(int_type))

        integration_points.append(
            IntegrationPoint(
                type=int_type,
                system_name=system_name,
                modules_used=modules_used,
                task_count=task_count,
                uses_credentials=uses_credentials,
                endpoints=endpoints,
                ports=ports,
                services=services,
            )
        )

    return integration_points


def _extract_endpoints(tasks: List[Dict[str, Any]]) -> List[str]:
    """Extract API endpoints/URLs from tasks."""
    endpoints = []
    for task in tasks:
        # Check common URL parameters
        for param in ["url", "uri", "dest", "src"]:
            if param in task and isinstance(task[param], str):
                url = task[param]
                # Extract just the base URL/domain
                if url.startswith(("http://", "https://")):
                    # Extract domain from URL
                    from urllib.parse import urlparse

                    parsed = urlparse(url)
                    endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    endpoints.append(endpoint)
    return list(set(endpoints))[:5]  # Limit to first 5 unique endpoints


def _extract_ports(tasks: List[Dict[str, Any]]) -> List[int]:
    """Extract network ports from tasks."""
    ports = []
    for task in tasks:
        # Check common port parameters
        for param in ["port", "ports", "dest_port", "source_port"]:
            if param in task:
                port_val = task[param]
                if isinstance(port_val, int):
                    ports.append(port_val)
                elif isinstance(port_val, str) and port_val.isdigit():
                    ports.append(int(port_val))
    return sorted(list(set(ports)))[:10]  # Limit to first 10 unique ports


def _extract_services(modules: List[str], int_type: IntegrationType) -> List[str]:
    """Extract service names based on integration type and modules used."""
    services = []

    if int_type == IntegrationType.CLOUD:
        # Extract AWS services
        aws_services = {
            "ec2": "EC2",
            "s3": "S3",
            "rds": "RDS",
            "lambda": "Lambda",
            "iam": "IAM",
            "vpc": "VPC",
            "elb": "ELB",
            "cloudformation": "CloudFormation",
        }
        for module in modules:
            for key, service in aws_services.items():
                if key in module.lower():
                    services.append(service)

        # Azure/GCP detection
        if any("azure" in m for m in modules):
            services.append("Azure")
        if any("gcp" in m or "google" in m for m in modules):
            services.append("GCP")

    elif int_type == IntegrationType.CONTAINER:
        if any("docker" in m for m in modules):
            services.append("Docker")
        if any("podman" in m for m in modules):
            services.append("Podman")
        if any("k8s" in m or "kubernetes" in m for m in modules):
            services.append("Kubernetes")

    elif int_type == IntegrationType.MONITORING:
        monitoring_map = {
            "datadog": "Datadog",
            "newrelic": "New Relic",
            "prometheus": "Prometheus",
            "grafana": "Grafana",
            "pagerduty": "PagerDuty",
            "nagios": "Nagios",
        }
        for module in modules:
            for key, service in monitoring_map.items():
                if key in module.lower():
                    services.append(service)

    return list(set(services))


def _detect_cloud_provider(modules: List[str]) -> str:
    """Detect specific cloud provider from modules."""
    if any("aws" in m or "ec2" in m or "s3" in m or "amazon" in m for m in modules):
        return "AWS (Amazon Web Services)"
    elif any("azure" in m for m in modules):
        return "Microsoft Azure"
    elif any("gcp" in m or "google.cloud" in m for m in modules):
        return "Google Cloud Platform"
    elif any("openstack" in m for m in modules):
        return "OpenStack"
    else:
        return "Cloud Provider"


def _detect_container_platform(modules: List[str]) -> str:
    """Detect specific container platform from modules."""
    if any("kubernetes" in m or "k8s" in m for m in modules):
        return "Kubernetes"
    elif any("docker" in m for m in modules):
        return "Docker"
    elif any("podman" in m for m in modules):
        return "Podman"
    else:
        return "Container Platform"


def _detect_monitoring_platform(modules: List[str]) -> str:
    """Detect specific monitoring platform from modules."""
    if any("datadog" in m for m in modules):
        return "Datadog"
    elif any("prometheus" in m for m in modules):
        return "Prometheus"
    elif any("grafana" in m for m in modules):
        return "Grafana"
    elif any("newrelic" in m for m in modules):
        return "New Relic"
    elif any("nagios" in m for m in modules):
        return "Nagios"
    elif any("zabbix" in m for m in modules):
        return "Zabbix"
    else:
        return "Monitoring Platform"


def _task_uses_credentials(task: Dict[str, Any]) -> bool:
    """Check if task uses credential-related parameters."""
    credential_params = [
        "username",
        "password",
        "api_key",
        "token",
        "url_username",
        "url_password",
        "vault_token",
        "auth",
        "authorization",
        "user",
        "login_password",
    ]
    return any(param in task for param in credential_params)


def _detect_database_type(modules: List[str]) -> str:
    """Detect specific database type from modules."""
    if any("postgresql" in m for m in modules):
        return "PostgreSQL Database"
    elif any("mysql" in m for m in modules):
        return "MySQL/MariaDB Database"
    elif any("mongodb" in m for m in modules):
        return "MongoDB Database"
    else:
        return "Database"


def _file_has_integrations(
    task_file: Dict[str, Any], integration_points: List[IntegrationPoint]
) -> int:
    """Count how many integration points a task file touches."""
    # Simple count for now - can be enhanced
    return 0


def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    integration_points: List[IntegrationPoint],
    file_details: List[FileComplexityDetail],
    hotspots: List[ConditionalHotspot],
    inflection_points: List[InflectionPoint],
    role_info: Dict[str, Any],
    repository_url: Optional[str] = None,
    repo_type: Optional[str] = None,
    repo_branch: Optional[str] = None,
) -> List[str]:
    """
    Generate specific, actionable recommendations based on comprehensive analysis.
    
    Args:
        metrics: Overall complexity metrics
        category: Complexity category
        integration_points: External system integrations
        file_details: Per-file complexity analysis
        hotspots: Conditional complexity hotspots
        inflection_points: Major branching points
    
    Returns:
        List of specific, actionable recommendation strings
    
    Example:
        >>> recommendations = generate_recommendations(...)
        >>> for rec in recommendations:
        ...     print(f"- {rec}")
    """
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
            largest_file.file_path,
            None,
            repository_url,
            repo_type,
            repo_branch
        )

        # God file detection
        if largest_file.is_god_file:
            # Get task file info to analyze concerns
            task_file_info = next(
                (tf for tf in role_info.get("tasks", []) if tf.get("file") == largest_file.file_path),
                None
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
                        f"   RECOMMENDATION: Keep together - splitting would break narrative flow"
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
                        f"   WHY: Mixed responsibilities reduce maintainability, testability, and reusability",
                        f"   HOW: Split by concern:"
                    ]

                    # Get detailed concern matches with line information
                    from docsible.analyzers.concerns.registry import ConcernRegistry
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
                                        ranges = ", ".join(f"{s}-{e}" for s, e in concern_lines)
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
                        f"   WHY: Large single-purpose files are hard to navigate and review",
                        f"   HOW: Split into execution phases:",
                        f"      • tasks/setup_{primary_concern}.yml: Preparation tasks",
                        f"      • tasks/{primary_concern}.yml: Core implementation",
                        f"      • tasks/verify_{primary_concern}.yml: Validation tasks"
                    ]
                    recommendations.append("\n".join(rec))
                else:
                    # No clear concern detected
                    rec = [
                        f"📁 {file_link} has {largest_file.task_count} tasks with no clear single concern",
                        f"   WHY: Unclear organization makes the role hard to understand and maintain",
                        f"   HOW: Reorganize by execution phase or functional area"
                    ]
                    recommendations.append("\n".join(rec))
    
    # 2. CONDITIONAL HOTSPOT RECOMMENDATIONS (WHY + HOW format)
    for hotspot in hotspots[:2]:  # Top 2 hotspots
        hotspot_link = _generate_file_link(
            hotspot.file_path,
            None,
            repository_url,
            repo_type,
            repo_branch
        )
        rec = [
            f"🔀 {hotspot_link}: {hotspot.affected_tasks} tasks depend on '{hotspot.conditional_variable}'",
            f"   WHY: OS/environment-specific branching scattered in one file makes platform support hard to test",
            f"   HOW: {hotspot.suggestion}"
        ]
        recommendations.append("\n".join(rec))

    # 3. INFLECTION POINT HINTS (WHY + HOW format)
    if inflection_points:
        main_inflection = inflection_points[0]  # Most significant
        inflection_link = _generate_file_link(
            main_inflection.file_path,
            main_inflection.task_index + 1,  # Convert 0-based index to 1-based line (approximate)
            repository_url,
            repo_type,
            repo_branch
        )
        rec = [
            f"⚡ Major branch point at {inflection_link}",
            f"   WHAT: Task '{main_inflection.task_name}' branches on '{main_inflection.variable}'",
            f"   IMPACT: {main_inflection.downstream_tasks} downstream tasks affected",
            f"   WHY: Multiple execution paths in one file reduce clarity and increase cognitive load",
            f"   HOW: Extract branches into separate files for each path (e.g., tasks/{{value}}.yml)"
        ]
        recommendations.append("\n".join(rec))
    
    # 4. INTEGRATION ISOLATION RECOMMENDATIONS
    # Group integrations by type
    integration_by_file = {}
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
                (ip for ip in integration_points if ip.type.value == int_type),
                None
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
            f"   WHY: Complex role dependencies make the execution chain hard to understand and debug",
            f"   HOW: Document role dependencies and include chain in README:",
            f"      • List all role dependencies from meta/main.yml",
            f"      • Show execution order diagram",
            f"      • Document required variables passed between roles"
        ]
        recommendations.append("\n".join(rec))

    # 6. INTEGRATION ISOLATION (WHY + HOW format)
    if len(integration_points) >= 3:
        systems = ", ".join(ip.system_name for ip in integration_points[:3])
        rec = [
            f"🔌 Multiple external integrations detected ({len(integration_points)} systems: {systems})",
            f"   WHY: External integrations add operational complexity and failure points",
            f"   HOW: Document integration architecture:",
            f"      • Add architecture diagram showing data flow between systems",
            f"      • Document retry/fallback strategies for each integration",
            f"      • List external dependencies and their versions"
        ]
        recommendations.append("\n".join(rec))

    # 7. CREDENTIAL WARNINGS (WHY + HOW format)
    if any(ip.uses_credentials for ip in integration_points):
        cred_systems = [ip.system_name for ip in integration_points if ip.uses_credentials]
        rec = [
            f"🔐 Credentials required for {', '.join(cred_systems)}",
            f"   WHY: Hardcoded credentials pose security risks and complicate credential rotation",
            f"   HOW: Secure credential management:",
            f"      • Use Ansible Vault for sensitive variables",
            f"      • Document required credentials in README",
            f"      • Consider external secret management (HashiCorp Vault, AWS Secrets Manager)"
        ]
        recommendations.append("\n".join(rec))

    # 8. FALLBACK FOR SIMPLE ROLES
    if not recommendations:
        recommendations.append(
            "✅ Role complexity is well-managed - standard documentation is sufficient"
        )
    
    return recommendations
