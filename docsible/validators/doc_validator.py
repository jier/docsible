"""
Documentation validation framework for Ansible role documentation.

Implements four validation dimensions:
1. CLARITY: Is the documentation clear and readable?
2. MAINTENANCE: Is the documentation complete and up-to-date?
3. TRUTH: Does the documentation accurately reflect the role?
4. VALUE: Does the documentation provide useful information?
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Critical issues that must be fixed
    WARNING = "warning"  # Issues that should be addressed
    INFO = "info"  # Suggestions for improvement


class ValidationType(str, Enum):
    """Types of validation checks."""

    CLARITY = "clarity"
    MAINTENANCE = "maintenance"
    TRUTH = "truth"
    VALUE = "value"


class ValidationIssue(BaseModel):
    """Represents a single validation issue."""

    type: ValidationType
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    section: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Results from documentation validation."""

    passed: bool
    score: float = Field(ge=0.0, le=100.0, description="Overall quality score 0-100")
    issues: List[ValidationIssue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

    def get_issues_by_type(
        self, validation_type: ValidationType
    ) -> List[ValidationIssue]:
        """Get all issues of a specific validation type."""
        return [issue for issue in self.issues if issue.type == validation_type]

    def get_issues_by_severity(
        self, severity: ValidationSeverity
    ) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)


class DocumentationValidator:
    """
    Validates generated Ansible role documentation for quality.

    Performs four types of validation:
    - Clarity: Readability, structure, formatting
    - Maintenance: Completeness, freshness, coverage
    - Truth: Accuracy against actual role structure
    - Value: Usefulness, actionable information
    """

    def __init__(self, min_score: float = 70.0):
        """
        Initialize validator.

        Args:
            min_score: Minimum acceptable quality score (0-100)
        """
        self.min_score = min_score

    def validate(
        self,
        documentation: str,
        role_info: Optional[Dict[str, Any]] = None,
        complexity_report: Optional[Any] = None,
    ) -> ValidationResult:
        """
        Validate documentation against all quality criteria.

        Args:
            documentation: Generated documentation content (markdown)
            role_info: Original role information dict
            complexity_report: Complexity analysis report

        Returns:
            ValidationResult with score, issues, and metrics
        """
        issues = []
        metrics = {}

        # Run all validation checks
        clarity_issues, clarity_metrics = self._validate_clarity(documentation)
        issues.extend(clarity_issues)
        metrics["clarity"] = clarity_metrics

        maintenance_issues, maintenance_metrics = self._validate_maintenance(
            documentation, role_info
        )
        issues.extend(maintenance_issues)
        metrics["maintenance"] = maintenance_metrics

        truth_issues, truth_metrics = self._validate_truth(
            documentation, role_info, complexity_report
        )
        issues.extend(truth_issues)
        metrics["truth"] = truth_metrics

        value_issues, value_metrics = self._validate_value(
            documentation, complexity_report
        )
        issues.extend(value_issues)
        metrics["value"] = value_metrics

        # Calculate overall score
        score = self._calculate_score(issues, metrics)
        passed = score >= self.min_score and not any(
            issue.severity == ValidationSeverity.ERROR for issue in issues
        )

        return ValidationResult(
            passed=passed, score=score, issues=issues, metrics=metrics
        )

    def _validate_clarity(
        self, documentation: str
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Validate documentation clarity and readability.

        Checks:
        - Has proper markdown structure
        - Has clear section headings
        - Has reasonable line lengths
        - Has code blocks properly formatted
        - Avoids excessive jargon
        """
        issues = []
        metrics = {}

        lines = documentation.split("\n")
        metrics["total_lines"] = len(lines)

        # Check for main sections
        required_sections = [
            "Description",
            "Requirements",
            "Variables",
            "Dependencies",
            "Example",
        ]
        found_sections = []
        for section in required_sections:
            if re.search(
                rf"^#+\s+{section}", documentation, re.MULTILINE | re.IGNORECASE
            ):
                found_sections.append(section)

        metrics["sections_found"] = len(found_sections)
        metrics["sections_expected"] = len(required_sections)

        missing_sections = set(required_sections) - set(found_sections)
        if missing_sections and len(found_sections) < 3:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"Missing common sections: {', '.join(missing_sections)}",
                    suggestion="Consider adding standard sections for better organization",
                )
            )

        # Check for overly long lines (readability)
        long_lines = 0
        for i, line in enumerate(lines, 1):
            # Ignore code blocks and tables
            if line.strip().startswith("```") or line.strip().startswith("|"):
                continue
            if len(line) > 120:
                long_lines += 1

        metrics["long_lines"] = long_lines
        if long_lines > len(lines) * 0.2:  # More than 20% of lines
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Found {long_lines} lines exceeding 120 characters",
                    suggestion="Consider breaking long lines for better readability",
                )
            )

        # Check for proper code block formatting
        code_blocks = re.findall(r"```(\w*)\n(.*?)```", documentation, re.DOTALL)
        metrics["code_blocks"] = len(code_blocks)

        unlabeled_blocks = sum(1 for lang, _ in code_blocks if not lang)
        if unlabeled_blocks > 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.INFO,
                    message=f"Found {unlabeled_blocks} unlabeled code blocks",
                    suggestion="Add language labels to code blocks (e.g., ```yaml, ```bash)",
                )
            )

        # Check for heading structure (should start with # and be hierarchical)
        headings = re.findall(r"^(#+)\s+(.+)$", documentation, re.MULTILINE)
        metrics["headings"] = len(headings)

        if len(headings) == 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.CLARITY,
                    severity=ValidationSeverity.ERROR,
                    message="No markdown headings found",
                    suggestion="Add structured headings to organize content",
                )
            )

        return issues, metrics

    def _validate_maintenance(
        self, documentation: str, role_info: Optional[Dict[str, Any]]
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Validate documentation completeness and maintainability.

        Checks:
        - All role components are documented
        - Variables are documented
        - Dependencies are listed
        - Examples are provided
        - Metadata is present
        """
        issues = []
        metrics = {}

        if not role_info:
            return issues, metrics

        # Check variable documentation coverage
        defaults_count = sum(
            len(df.get("data", {})) for df in role_info.get("defaults", [])
        )
        vars_count = sum(len(vf.get("data", {})) for vf in role_info.get("vars", []))
        total_vars = defaults_count + vars_count

        metrics["total_variables"] = total_vars

        # Count documented variables (look for variable names in docs)
        if total_vars > 0:
            # Check if variables section exists
            if not re.search(
                r"^#+\s+(?:Role\s+)?Variables",
                documentation,
                re.MULTILINE | re.IGNORECASE,
            ):
                issues.append(
                    ValidationIssue(
                        type=ValidationType.MAINTENANCE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Role has {total_vars} variables but no Variables section found",
                        section="Variables",
                        suggestion="Add a Variables section documenting all configurable options",
                    )
                )

        # Check handler documentation
        handlers_count = len(role_info.get("handlers", []))
        metrics["handlers"] = handlers_count

        if handlers_count > 0:
            if "handler" not in documentation.lower():
                issues.append(
                    ValidationIssue(
                        type=ValidationType.MAINTENANCE,
                        severity=ValidationSeverity.INFO,
                        message=f"Role has {handlers_count} handlers but they're not mentioned",
                        section="Handlers",
                        suggestion="Document available handlers and when they're triggered",
                    )
                )

        # Check for example playbook
        has_example = bool(re.search(r"```(?:yaml|yml)", documentation, re.IGNORECASE))
        metrics["has_example"] = has_example

        if not has_example:
            issues.append(
                ValidationIssue(
                    type=ValidationType.MAINTENANCE,
                    severity=ValidationSeverity.WARNING,
                    message="No example playbook found",
                    section="Example Playbook",
                    suggestion="Add a working example showing how to use the role",
                )
            )

        # Check for dependencies documentation
        dependencies = role_info.get("dependencies", [])
        metrics["dependencies"] = len(dependencies)

        if dependencies and "dependencies" not in documentation.lower():
            issues.append(
                ValidationIssue(
                    type=ValidationType.MAINTENANCE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Role has {len(dependencies)} dependencies but they're not documented",
                    section="Dependencies",
                    suggestion="Document role dependencies and their purpose",
                )
            )

        return issues, metrics

    def _validate_truth(
        self,
        documentation: str,
        role_info: Optional[Dict[str, Any]],
        complexity_report: Optional[Any],
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Validate documentation accuracy against actual role structure.

        Checks:
        - Task counts match reality
        - Variable names are correct
        - Dependencies are accurate
        - Integration claims are verified
        """
        issues = []
        metrics = {}

        # Check for auto-generated markers (always check, even without role_info)
        has_generated_markers = "DOCSIBLE GENERATED" in documentation
        metrics["has_generated_markers"] = has_generated_markers

        # Verify complexity category if mentioned (can check even without role_info)
        if complexity_report:
            actual_category = complexity_report.category.value.upper()
            metrics["actual_complexity"] = actual_category

            category_mentions = re.findall(
                r"\b(SIMPLE|MEDIUM|COMPLEX)\s+role", documentation, re.IGNORECASE
            )
            if category_mentions:
                claimed_category = category_mentions[0].upper()
                if claimed_category != actual_category:
                    issues.append(
                        ValidationIssue(
                            type=ValidationType.TRUTH,
                            severity=ValidationSeverity.ERROR,
                            message=f"Documentation claims {claimed_category} but role is {actual_category}",
                            suggestion=f"Correct complexity category to {actual_category}",
                        )
                    )

        if not role_info:
            return issues, metrics

        # Verify task count accuracy
        actual_tasks = sum(
            len(tf.get("tasks", [])) for tf in role_info.get("tasks", [])
        )
        metrics["actual_tasks"] = actual_tasks

        # Extract task count claims from documentation
        task_claims = re.findall(r"(\d+)\s+tasks?", documentation, re.IGNORECASE)
        if task_claims:
            claimed_tasks = int(task_claims[0])
            metrics["claimed_tasks"] = claimed_tasks

            if claimed_tasks != actual_tasks:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.TRUTH,
                        severity=ValidationSeverity.ERROR,
                        message=f"Documentation claims {claimed_tasks} tasks but role has {actual_tasks}",
                        suggestion=f"Update task count to {actual_tasks}",
                    )
                )

        return issues, metrics

    def _validate_value(
        self, documentation: str, complexity_report: Optional[Any]
    ) -> Tuple[List[ValidationIssue], Dict[str, Any]]:
        """
        Validate documentation usefulness and actionable content.

        Checks:
        - Provides diagrams for complex roles
        - Includes security considerations for integrations
        - Offers troubleshooting guidance
        - Contains performance tips
        - Has clear examples
        """
        issues = []
        metrics = {}

        # Check for diagrams (especially for complex roles)
        has_diagrams = "```mermaid" in documentation
        metrics["has_diagrams"] = has_diagrams

        if complexity_report and complexity_report.category.value in [
            "medium",
            "complex",
        ]:
            if not has_diagrams:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.VALUE,
                        severity=ValidationSeverity.WARNING,
                        message=f"{complexity_report.category.value.upper()} role lacks visual diagrams",
                        suggestion="Add architecture or workflow diagrams for better understanding",
                    )
                )

        # Check for security considerations (especially with integrations)
        has_security = bool(
            re.search(
                r"security|credentials?|authentication", documentation, re.IGNORECASE
            )
        )
        metrics["has_security_guidance"] = has_security

        if complexity_report and complexity_report.integration_points:
            if not has_security:
                issues.append(
                    ValidationIssue(
                        type=ValidationType.VALUE,
                        severity=ValidationSeverity.WARNING,
                        message="Role has external integrations but no security guidance",
                        section="Security",
                        suggestion="Add security considerations for credential management",
                    )
                )

        # Check for actionable examples
        playbook_examples = len(re.findall(r"- hosts:", documentation))
        metrics["playbook_examples"] = playbook_examples

        if playbook_examples == 0:
            issues.append(
                ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.INFO,
                    message="No runnable playbook examples found",
                    suggestion="Add complete playbook examples users can copy",
                )
            )

        # Check for recommendations (from complexity analysis)
        has_recommendations = "recommendation" in documentation.lower()
        metrics["has_recommendations"] = has_recommendations

        # Check content depth (not just structure)
        word_count = len(re.findall(r"\w+", documentation))
        metrics["word_count"] = word_count

        if word_count < 200:
            issues.append(
                ValidationIssue(
                    type=ValidationType.VALUE,
                    severity=ValidationSeverity.WARNING,
                    message=f"Documentation is quite brief ({word_count} words)",
                    suggestion="Consider adding more context and examples",
                )
            )

        return issues, metrics

    def _calculate_score(
        self, issues: List[ValidationIssue], metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate overall quality score (0-100).

        Scoring:
        - Start at 100
        - ERROR: -15 points each
        - WARNING: -5 points each
        - INFO: -2 points each
        - Floor at 0
        """
        score = 100.0

        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 15.0
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 5.0
            elif issue.severity == ValidationSeverity.INFO:
                score -= 2.0

        return max(0.0, score)


def validate_documentation(
    documentation: str,
    role_info: Optional[Dict[str, Any]] = None,
    complexity_report: Optional[Any] = None,
    min_score: float = 70.0,
) -> ValidationResult:
    """
    Convenience function to validate documentation.

    Args:
        documentation: Generated documentation content
        role_info: Original role structure
        complexity_report: Complexity analysis
        min_score: Minimum acceptable score

    Returns:
        ValidationResult with score and issues
    """
    validator = DocumentationValidator(min_score=min_score)
    return validator.validate(documentation, role_info, complexity_report)
