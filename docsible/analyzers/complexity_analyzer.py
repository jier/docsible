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


class ComplexityCategory(str, Enum):
    """Role complexity categories based on task count."""
    SIMPLE = "simple"      # 1-10 tasks
    MEDIUM = "medium"      # 11-25 tasks
    COMPLEX = "complex"    # 25+ tasks


class IntegrationType(str, Enum):
    """Types of external system integrations."""
    API = "api"
    DATABASE = "database"
    VAULT = "vault"
    # Future: CLOUD, CONTAINER, MONITORING, etc.


class IntegrationPoint(BaseModel):
    """Represents a detected external system integration."""
    type: IntegrationType
    system_name: str
    modules_used: List[str]
    task_count: int
    uses_credentials: bool = False


class ComplexityMetrics(BaseModel):
    """Detailed metrics for role complexity analysis."""
    # Task metrics
    total_tasks: int = Field(description="Total number of tasks across all files")
    task_files: int = Field(description="Number of task files")
    handlers: int = Field(description="Number of handlers")
    conditional_tasks: int = Field(description="Tasks with 'when' conditions")

    # Internal composition (role orchestration)
    role_dependencies: int = Field(
        default=0,
        description="Role dependencies from meta/main.yml"
    )
    role_includes: int = Field(
        default=0,
        description="include_role/import_role count"
    )
    task_includes: int = Field(
        default=0,
        description="include_tasks/import_tasks count"
    )

    # External integrations
    external_integrations: int = Field(
        default=0,
        description="Count of external system connections"
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
            self.role_dependencies * 2 +  # Meta deps are important
            self.role_includes +
            self.task_includes
        )

    @property
    def conditional_percentage(self) -> float:
        """Percentage of tasks that are conditional."""
        if self.total_tasks == 0:
            return 0.0
        return (self.conditional_tasks / self.total_tasks) * 100


class ComplexityReport(BaseModel):
    """Complete complexity analysis report."""
    metrics: ComplexityMetrics
    category: ComplexityCategory
    integration_points: List[IntegrationPoint] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    task_files_detail: List[Dict[str, Any]] = Field(default_factory=list)


def analyze_role_complexity(role_info: Dict[str, Any]) -> ComplexityReport:
    """
    Analyze role complexity and generate comprehensive report.

    Args:
        role_info: Role information dictionary from build_role_info()

    Returns:
        ComplexityReport with metrics, category, and recommendations

    Example:
        >>> report = analyze_role_complexity(role_info)
        >>> print(f"Category: {report.category}")
        >>> print(f"Total tasks: {report.metrics.total_tasks}")
    """
    # Count tasks
    tasks_data = role_info.get('tasks', [])
    total_tasks = sum(len(tf.get('tasks', [])) for tf in tasks_data)
    task_files = len(tasks_data)

    # Count handlers
    handlers = len(role_info.get('handlers', []))

    # Count conditional tasks
    conditional_tasks = sum(
        1 for tf in tasks_data
        for task in tf.get('tasks', [])
        if task.get('when')
    )

    # Count role dependencies (from meta/main.yml)
    role_dependencies = len(role_info.get('meta', {}).get('dependencies', []))

    # Count role includes (include_role, import_role)
    role_includes = sum(
        1 for tf in tasks_data
        for task in tf.get('tasks', [])
        if task.get('module', '') in [
            'include_role', 'import_role',
            'ansible.builtin.include_role', 'ansible.builtin.import_role'
        ]
    )

    # Count task includes (include_tasks, import_tasks)
    task_includes = sum(
        1 for tf in tasks_data
        for task in tf.get('tasks', [])
        if task.get('module', '') in [
            'include_tasks', 'import_tasks',
            'ansible.builtin.include_tasks', 'ansible.builtin.import_tasks'
        ]
    )

    # Calculate max and average tasks per file
    tasks_per_file = [len(tf.get('tasks', [])) for tf in tasks_data]
    max_tasks_per_file = max(tasks_per_file) if tasks_per_file else 0
    avg_tasks_per_file = sum(tasks_per_file) / len(tasks_per_file) if tasks_per_file else 0.0

    # Detect external integrations
    integration_points = detect_integrations(role_info)

    # Create metrics
    metrics = ComplexityMetrics(
        total_tasks=total_tasks,
        task_files=task_files,
        handlers=handlers,
        conditional_tasks=conditional_tasks,
        role_dependencies=role_dependencies,
        role_includes=role_includes,
        task_includes=task_includes,
        external_integrations=len(integration_points),
        max_tasks_per_file=max_tasks_per_file,
        avg_tasks_per_file=avg_tasks_per_file,
    )

    # Classify complexity
    category = classify_complexity(metrics)

    # Generate recommendations
    recommendations = generate_recommendations(metrics, category, integration_points)

    # Task files detail
    task_files_detail = [
        {
            'file': tf.get('file', 'unknown'),
            'task_count': len(tf.get('tasks', [])),
            'has_integrations': _file_has_integrations(tf, integration_points)
        }
        for tf in tasks_data
    ]

    return ComplexityReport(
        metrics=metrics,
        category=category,
        integration_points=integration_points,
        recommendations=recommendations,
        task_files_detail=task_files_detail,
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
    API_MODULES = ['uri', 'get_url', 'ansible.builtin.uri', 'ansible.builtin.get_url']
    DATABASE_MODULES = [
        'mysql', 'mysql_', 'postgresql', 'postgresql_', 'mongodb', 'mongodb_',
        'community.mysql', 'community.postgresql', 'community.mongodb'
    ]
    VAULT_MODULES = ['hashi_vault', 'community.hashi_vault']

    # Ansible composition modules to exclude
    COMPOSITION_MODULES = [
        'include_role', 'import_role', 'include_tasks', 'import_tasks',
        'ansible.builtin.include_role', 'ansible.builtin.import_role',
        'ansible.builtin.include_tasks', 'ansible.builtin.import_tasks'
    ]

    integration_map = {}  # type -> list of tasks

    for task_file_info in role_info.get('tasks', []):
        for task in task_file_info.get('tasks', []):
            module = task.get('module', '')

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

            if int_type:
                if int_type not in integration_map:
                    integration_map[int_type] = []
                integration_map[int_type].append({
                    'module': module,
                    'task': task,
                })

    # Create IntegrationPoint objects
    integration_points = []

    for int_type, tasks in integration_map.items():
        modules_used = list(set(t['module'] for t in tasks))
        task_count = len(tasks)

        # Detect credential usage
        uses_credentials = any(
            _task_uses_credentials(t['task']) for t in tasks
        )

        # Determine system name
        system_name = {
            IntegrationType.API: "REST APIs",
            IntegrationType.DATABASE: _detect_database_type(modules_used),
            IntegrationType.VAULT: "HashiCorp Vault",
        }.get(int_type, str(int_type))

        integration_points.append(IntegrationPoint(
            type=int_type,
            system_name=system_name,
            modules_used=modules_used,
            task_count=task_count,
            uses_credentials=uses_credentials,
        ))

    return integration_points


def _task_uses_credentials(task: Dict[str, Any]) -> bool:
    """Check if task uses credential-related parameters."""
    credential_params = [
        'username', 'password', 'api_key', 'token',
        'url_username', 'url_password', 'vault_token',
        'auth', 'authorization', 'user', 'login_password'
    ]
    return any(param in task for param in credential_params)


def _detect_database_type(modules: List[str]) -> str:
    """Detect specific database type from modules."""
    if any('postgresql' in m for m in modules):
        return "PostgreSQL Database"
    elif any('mysql' in m for m in modules):
        return "MySQL/MariaDB Database"
    elif any('mongodb' in m for m in modules):
        return "MongoDB Database"
    else:
        return "Database"


def _file_has_integrations(
    task_file: Dict[str, Any],
    integration_points: List[IntegrationPoint]
) -> int:
    """Count how many integration points a task file touches."""
    # Simple count for now - can be enhanced
    return 0


def generate_recommendations(
    metrics: ComplexityMetrics,
    category: ComplexityCategory,
    integration_points: List[IntegrationPoint]
) -> List[str]:
    """Generate actionable recommendations based on complexity analysis."""
    recommendations = []

    # Task count recommendations
    if category == ComplexityCategory.COMPLEX:
        recommendations.append(
            f"Role is complex ({metrics.total_tasks} tasks) - consider splitting by concern"
        )

        if metrics.max_tasks_per_file > 15:
            recommendations.append(
                f"Largest task file has {metrics.max_tasks_per_file} tasks - "
                "consider breaking into smaller files"
            )

    # Composition recommendations
    if metrics.composition_score >= 8:
        recommendations.append(
            f"High composition complexity (score: {metrics.composition_score}) - "
            "document role dependencies clearly"
        )

    # Integration recommendations
    if len(integration_points) >= 3:
        recommendations.append(
            f"Multiple external integrations ({len(integration_points)} systems) - "
            "add integration architecture diagram"
        )

    # Conditional logic recommendations
    if metrics.conditional_percentage > 30:
        recommendations.append(
            f"High conditional logic ({metrics.conditional_percentage:.0f}%) - "
            "document decision points in README"
        )

    # Credential usage warnings
    if any(ip.uses_credentials for ip in integration_points):
        recommendations.append(
            "External systems require credentials - document authentication requirements"
        )

    if not recommendations:
        recommendations.append("Role complexity is manageable - standard documentation sufficient")

    return recommendations
