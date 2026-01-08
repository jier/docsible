from pathlib import Path

from docsible.models.recommendation import Recommendation
from docsible.models.severity import Severity


class SecurityRecommendationGenerator:
    """Generate security-focused recommendations."""

    def analyze_role(self, role_path: Path) -> list[Recommendation]:
        """Analyze role for security issues."""
        recommendations = []

        # Check for unencrypted vault files
        recommendations.extend(self._check_vault_encryption(role_path))

        # Check for exposed secrets
        recommendations.extend(self._check_exposed_secrets(role_path))

        # Check for unsafe permissions
        recommendations.extend(self._check_unsafe_permissions(role_path))

        return recommendations

    def _check_vault_encryption(self, role_path: Path) -> list[Recommendation]:
        """Check vault files are encrypted."""
        recommendations = []

        vault_files = [
            role_path / "vars" / "vault.yml",
            role_path / "vars" / "secrets.yml",
        ]

        for vault_file in vault_files:
            if vault_file.exists():
                content = vault_file.read_text()
                # Check only the first line - encrypted vaults start with $ANSIBLE_VAULT
                if content and not content.startswith("$ANSIBLE_VAULT"):
                    recommendations.append(Recommendation(
                        category="security",
                        message=f"Vault file not encrypted: {vault_file.name}",
                        rationale="Unencrypted vault files expose secrets in version control",
                        severity=Severity.CRITICAL,
                        file_path=str(vault_file.relative_to(role_path)),
                        line_number=1,
                        remediation=f"Run: ansible-vault encrypt {vault_file.name}",
                        confidence=1.0,
                        auto_fixable=False,
                    ))

        return recommendations

    def _check_exposed_secrets(self, role_path: Path) -> list[Recommendation]:
        """Check for secrets in logs or debug output."""
        recommendations = []

        tasks_dir = role_path / "tasks"
        if not tasks_dir.exists():
            return recommendations

        import yaml

        for task_file in tasks_dir.glob("**/*.yml"):
            try:
                with open(task_file) as f:
                    tasks = yaml.safe_load(f) or []

                for idx, task in enumerate(tasks):
                    if not isinstance(task, dict):
                        continue

                    # Check debug module for sensitive vars
                    if task.get("debug"):
                        var = task["debug"].get("var", "")
                        msg = task["debug"].get("msg", "")

                        # Pattern matching for sensitive variable names
                        sensitive_patterns = [
                            "password", "secret", "key", "token",
                            "credential", "api_key", "private"
                        ]

                        # Check if sensitive pattern appears in var or msg
                        var_match = any(pattern in var.lower() for pattern in sensitive_patterns) if var else False
                        msg_match = any(pattern in str(msg).lower() for pattern in sensitive_patterns) if msg else False

                        if var_match or msg_match:
                            # Build detailed message showing what was exposed
                            exposed_parts = []
                            if var_match:
                                exposed_parts.append(f"var: {var}")
                            if msg_match:
                                exposed_parts.append(f"msg: {msg}")

                            exposed = " and ".join(exposed_parts)

                            recommendations.append(Recommendation(
                                category="security",
                                message=f"Potentially sensitive data exposed in debug: {exposed}",
                                rationale="Debug output may expose secrets in logs",
                                severity=Severity.CRITICAL,
                                file_path=str(task_file.relative_to(role_path)),
                                line_number=idx + 1,
                                remediation="Use no_log: true or remove debug statement",
                                confidence=0.8,
                                auto_fixable=False,
                            ))
            except Exception:
                # Skip files that can't be parsed
                continue

        return recommendations
    
    def _check_unsafe_permissions(self, role_path: Path) -> list[Recommendation]:
        """Check for unsafe file permissions in tasks."""
        recommendations = []
        
        tasks_dir = role_path / "tasks"
        if not tasks_dir.exists():
            return recommendations
        
        import yaml
        
        # Unsafe permission patterns (world-writable, etc.)
        unsafe_modes = ["0777", "777", "0666", "666", "0o777", "0o666"]
        
        for task_file in tasks_dir.glob("**/*.yml"):
            try:
                with open(task_file) as f:
                    tasks = yaml.safe_load(f) or []
                
                for idx, task in enumerate(tasks, 1):
                    if not isinstance(task, dict):
                        continue
                    
                    # Check file/directory modules for unsafe permissions
                    module_name = None
                    module_params = {}
                    
                    # Extract module name and params
                    if "file" in task:
                        module_name = "file"
                        module_params = task["file"] if isinstance(task["file"], dict) else {}
                    elif "copy" in task:
                        module_name = "copy"
                        module_params = task["copy"] if isinstance(task["copy"], dict) else {}
                    elif "template" in task:
                        module_name = "template"
                        module_params = task["template"] if isinstance(task["template"], dict) else {}
                    
                    if module_name and module_params:
                        # Check mode parameter
                        mode = module_params.get("mode", "")
                        if isinstance(mode, (str, int)):
                            mode_str = str(mode)
                            if mode_str in unsafe_modes:
                                recommendations.append(Recommendation(
                                    category="security",
                                    message=f"Unsafe file permissions detected: mode={mode}",
                                    rationale="World-writable permissions (777/666) are a security risk",
                                    severity=Severity.CRITICAL,
                                    file_path=str(task_file.relative_to(role_path)),
                                    line_number=idx,
                                    remediation="Use restrictive permissions like 0644 or 0755",
                                    confidence=0.95,
                                    auto_fixable=False,
                                ))
            except Exception:
                # Skip files that can't be parsed
                continue
        
        return recommendations