from click.testing import CliRunner

from docsible.cli import cli


def test_critical_recommendations_shown(tmp_path):
    """Test critical recommendations displayed."""
    # Create role with unencrypted vault
    role = tmp_path / "test_role"
    role.mkdir()
    (role / "vars").mkdir()
    (role / "vars" / "vault.yml").write_text("secret: password123")

    runner = CliRunner()
    result = runner.invoke(cli, [
        "role",
        "--role", str(role),
        "--recommendations-only"
    ])

    assert result.exit_code == 0
    assert "🔴 CRITICAL" in result.output
    assert "Vault file not encrypted" in result.output

def test_info_hidden_by_default(tmp_path):
    """Test INFO recommendations hidden without --show-info."""
    role = tmp_path / "test_role"
    role.mkdir()
    (role / "tasks").mkdir()
    (role / "tasks" / "main.yml").write_text("---\n- debug: msg=test")

    runner = CliRunner()

    # Without --show-info
    result = runner.invoke(cli, [
        "role",
        "--role", str(role),
        "--recommendations-only"
    ])

    assert "hidden, use --show-info" in result.output

    # With --show-info
    result = runner.invoke(cli, [
        "role",
        "--role", str(role),
        "--recommendations-only",
        "--show-info"
    ])

    assert "💡 INFO" in result.output or "No recommendations" in result.output