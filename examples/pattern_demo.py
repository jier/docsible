#!/usr/bin/env python3
"""Simple demonstration of the Pattern Analyzer with mock data.

This shows how the pattern analyzer works without requiring a full role.
"""

from docsible.analyzers.patterns import analyze_role_patterns, PatternAnalyzer
from docsible.analyzers.patterns.detectors import SecurityDetector


def create_example_role_with_issues():
    """Create a mock role_info with various anti-patterns."""
    return {
        "tasks": [
            {
                "file": "main.yml",
                "tasks": [
                    # Duplication - many separate package installs
                    {"name": "Install nginx", "module": "apt", "file": "main.yml"},
                    {"name": "Install php", "module": "apt", "file": "main.yml"},
                    {"name": "Install mysql", "module": "apt", "file": "main.yml"},
                    {"name": "Install redis", "module": "apt", "file": "main.yml"},
                    {"name": "Install memcached", "module": "apt", "file": "main.yml"},
                    {"name": "Install supervisor", "module": "apt", "file": "main.yml"},
                    # Missing idempotency
                    {
                        "name": "Download file",
                        "module": "shell",
                        "cmd": "wget https://example.com/file.tar.gz",
                        "file": "main.yml",
                    },
                    # Complex conditional
                    {
                        "name": "Complex task",
                        "module": "debug",
                        "when": 'ansible_os_family == "Debian" and ansible_distribution_major_version >= "18" or ansible_os_family == "RedHat" and ansible_distribution_major_version >= "7" or custom_flag is defined and custom_flag == true',
                        "file": "main.yml",
                    },
                    # Security: missing no_log
                    {
                        "name": "Set database password",
                        "module": "set_fact",
                        "db_password": "secret123",
                        "file": "main.yml",
                    },
                    # Shell with pipe, no failed_when
                    {
                        "name": "Check service",
                        "module": "shell",
                        "cmd": "systemctl status app | grep active",
                        "file": "main.yml",
                    },
                ],
            }
        ],
        "defaults": {"app_port": 8080, "app_user": "www-data"},
        "vars": {
            "app_port": 9000,  # Shadows defaults!
            "db_password": "plain_text_secret",  # Security issue!
        },
        "handlers": [],
        "meta": {},
    }


def main():
    """Run pattern analysis demonstration."""
    print("\n" + "=" * 70)
    print("PATTERN ANALYZER DEMONSTRATION")
    print("=" * 70)

    # Create role with various issues
    role_info = create_example_role_with_issues()

    print("\n📋 Analyzing role with intentional anti-patterns...")
    print(f"   Task count: {len(role_info['tasks'][0]['tasks'])}")
    print(f"   Defaults: {len(role_info['defaults'])} variables")
    print(f"   Vars: {len(role_info['vars'])} variables")

    # Run full analysis
    report = analyze_role_patterns(role_info, min_confidence=0.7)

    # Show summary
    print("\n📊 Analysis Results:")
    print(f"   Overall Health Score: {report.overall_health_score:.1f}/100")
    print(f"   Total Patterns Found: {report.total_patterns}")
    print(f"   - Critical:  {report.by_severity.get('critical', 0)}")
    print(f"   - Warnings:  {report.by_severity.get('warning', 0)}")
    print(f"   - Info:      {report.by_severity.get('info', 0)}")

    # Show breakdown by category
    if report.by_category:
        print("\n📂 Issues by Category:")
        for category, count in sorted(report.by_category.items()):
            print(f"   - {category:15s}: {count}")

    # Show critical issues
    critical = [s for s in report.suggestions if s.severity == "critical"]
    if critical:
        print("\n🚨 Critical Issues:")
        for issue in critical:
            print(f"\n   Pattern: {issue.pattern}")
            print(f"   Description: {issue.description}")
            print(f"   Impact: {issue.impact}")
            print(f"   Confidence: {issue.confidence * 100:.0f}%")

    # Show warnings
    warnings = [s for s in report.suggestions if s.severity == "warning"]
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for issue in warnings:
            print(f"\n   Pattern: {issue.pattern}")
            print(f"   Description: {issue.description}")
            print(f"   Files: {', '.join(issue.affected_files)}")

    # Show info
    info = [s for s in report.suggestions if s.severity == "info"]
    if info:
        print(f"\n💡 Suggestions ({len(info)}):")
        for issue in info:
            print(f"   - {issue.description}")

    # Example: Security-only analysis
    print("\n" + "=" * 70)
    print("SECURITY-FOCUSED ANALYSIS")
    print("=" * 70)

    security_analyzer = PatternAnalyzer(
        enabled_detectors=[SecurityDetector], min_confidence=0.75
    )
    security_report = security_analyzer.analyze(role_info)

    print("\n🔒 Security Analysis:")
    print(f"   Issues Found: {security_report.total_patterns}")

    for issue in security_report.suggestions:
        print(f"\n   {issue.severity.upper()}: {issue.description}")
        print(f"   Impact: {issue.impact}")
        print("   How to fix:")
        print(f"   {issue.suggestion[:200]}...")

    # Example: Export to JSON
    print("\n" + "=" * 70)
    print("JSON EXPORT")
    print("=" * 70)

    import json

    report_dict = report.model_dump()

    # Show compact summary
    summary = {
        "total_patterns": report_dict["total_patterns"],
        "health_score": report_dict["overall_health_score"],
        "by_severity": report_dict["by_severity"],
        "by_category": report_dict["by_category"],
        "sample_pattern": {
            "pattern": report_dict["suggestions"][0]["pattern"],
            "severity": report_dict["suggestions"][0]["severity"],
            "description": report_dict["suggestions"][0]["description"],
        }
        if report_dict["suggestions"]
        else None,
    }

    print("\n📄 JSON Export Sample:")
    print(json.dumps(summary, indent=2))

    print("\n" + "=" * 70)
    print("✅ Demonstration Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
