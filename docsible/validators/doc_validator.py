import logging
from typing import Any

from .base import BaseValidator
from .clarity import ClarityValidator
from .maintenance import MaintenanceValidator
from .models import ValidationIssue, ValidationResult, ValidationSeverity
from .scoring import calculate_score
from .truth import TruthValidator
from .value import ValueValidator

logger = logging.getLogger(__name__)


class DocumentationValidator:
    """
    Orchestrates all documentation validators.
    
    Follows the Composite pattern - delegates to specialized validators.
    - Clarity: Readability, structure, formatting
    - Maintenance: Completeness, freshness, coverage
    - Truth: Accuracy against actual role structure
    - Value: Usefulness, actionable information
    """
    
    def __init__(
        self, 
        min_score: float = 70.0,
        validators: list[BaseValidator] | None = None
    ):
        """
        Initialize validator with pluggable validators.
        
        Args:
            min_score: Minimum acceptable quality score (0-100)
            validators: Custom validators to use (defaults to all built-in)
        """
        self.min_score = min_score
        
        # Dependency Injection - can inject custom validators!
        if validators is None:
            # Default validators
            self.validators = [
                ClarityValidator(),
                MaintenanceValidator(),
                TruthValidator(),
                ValueValidator(),
            ]
        else:
            self.validators = validators
    
    def validate(
        self,
        documentation: str,
        role_info: dict[str, Any] | None = None,
        complexity_report: Any | None = None,
    ) -> ValidationResult:
        """
        Validate documentation against all quality criteria.
        
        Orchestrates all registered validators.
        """
        all_issues: list[ValidationIssue] = []
        all_metrics: dict[str, Any] = {}
        
        # Run all validators (Open/Closed Principle!)
        for validator in self.validators:
            issues, metrics = validator.validate(
                documentation, role_info, complexity_report
            )
            all_issues.extend(issues)
            
            # Store metrics by validation type
            validator_type = validator.type.value
            all_metrics[validator_type] = metrics
        
        # Calculate score using extracted function
        score = calculate_score(all_issues)
        
        # Check if passed
        passed = score >= self.min_score and not any(
            issue.severity == ValidationSeverity.ERROR for issue in all_issues
        )
        
        return ValidationResult(
            passed=passed,
            score=score,
            issues=all_issues,
            metrics=all_metrics,
        )

def validate_documentation(
    documentation: str,
    role_info: dict[str, Any] | None = None,
    complexity_report: Any | None = None,
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
