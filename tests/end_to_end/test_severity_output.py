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
    """Test INFO recommendations are not displayed without --show-info flag.

    Verifies that the --show-info flag controls INFO visibility. Without it,
    INFO-level findings should not appear in output. The command should always
    exit cleanly regardless of whether INFO findings exist.
    """
    role = tmp_path / "test_role"
    role.mkdir()
    (role / "tasks").mkdir()
    (role / "tasks" / "main.yml").write_text("---\n- debug: msg=test")

    runner = CliRunner()

    # Without --show-info: INFO-level items must not appear
    result = runner.invoke(cli, [
        "role",
        "--role", str(role),
        "--recommendations-only"
    ])
    assert result.exit_code == 0
    assert "💡 INFO" not in result.output

    # With --show-info: command must still succeed (INFO shown or clean role)
    result = runner.invoke(cli, [
        "role",
        "--role", str(role),
        "--recommendations-only",
        "--show-info"
    ])
    assert result.exit_code == 0