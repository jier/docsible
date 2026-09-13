"""Suppression must apply uniformly across the three analysis entry points.

Previously only the single-role orchestrator filtered suppressed findings;
`scan collection` and `document role --collection` recomputed recommendations
via analyze_role without suppressing, so a suppressed finding still showed up.
Step 3a moves suppression into the shared analyze_role.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from click.testing import CliRunner

from docsible.cli import cli
from docsible.commands.document_role.role_analysis import analyze_role
from docsible.commands.role_info_loader import RoleInfoLoader

FIXTURES = Path(__file__).parent.parent / "fixtures"
MINIMAL_COLLECTION = FIXTURES / "minimal_collection"

RULE = (
    "rules:\n"
    "  - id: test1\n"
    '    pattern: "examples"\n'
    "    reason: suppressed in test\n"
)


def _write_role(root: Path) -> Path:
    (root / "tasks").mkdir(parents=True)
    (root / "defaults").mkdir()
    (root / "handlers").mkdir()
    (root / "tasks" / "main.yml").write_text("---\n- name: t\n  debug:\n    msg: x\n")
    (root / "defaults" / "main.yml").write_text("---\nk: v\n")
    (root / "handlers" / "main.yml").write_text("---\n")
    return root


def test_analyze_role_applies_suppression_when_enabled(tmp_path):
    role = _write_role(tmp_path / "r")
    (role / ".docsible").mkdir()
    (role / ".docsible" / "suppress.yml").write_text(RULE)

    role_info = RoleInfoLoader().load(role)
    unfiltered = analyze_role(role_info, role)
    filtered = analyze_role(role_info, role, apply_suppressions=True)

    assert any("examples" in r.message for r in unfiltered.recommendations)
    assert not any("examples" in r.message for r in filtered.recommendations)
    assert any("examples" in r.message for r in filtered.suppressed)


def test_scan_collection_honours_suppression(tmp_path):
    collection = tmp_path / "collection"
    shutil.copytree(MINIMAL_COLLECTION, collection)

    def info_count() -> int:
        result = CliRunner().invoke(cli, ["scan", "collection", str(collection), "--output-format", "json"])
        roles = {r["name"]: r for r in json.loads(result.output)["roles"]}
        return roles["web_role"]["info_count"]

    before = info_count()
    assert before >= 1  # the "examples/ directory" info finding exists

    # One project/collection-root store; rules scope per role via `--file`.
    (collection / ".docsible").mkdir()
    (collection / ".docsible" / "suppress.yml").write_text(RULE)

    assert info_count() < before  # scan now reads the collection-root store


def test_suppress_base_path_controls_which_store_is_read(tmp_path):
    role = _write_role(tmp_path / "proj" / "roles" / "r")  # role has no store
    root = tmp_path / "proj"
    (root / ".docsible").mkdir(parents=True)
    (root / ".docsible" / "suppress.yml").write_text(RULE)  # store at project root

    role_info = RoleInfoLoader().load(role)

    # Default base is the role dir -> the project-root store is not read.
    by_role = analyze_role(role_info, role, apply_suppressions=True)
    assert any("examples" in r.message for r in by_role.recommendations)

    # Explicit project root -> suppression applies.
    by_root = analyze_role(
        role_info, role, apply_suppressions=True, suppress_base_path=root
    )
    assert not any("examples" in r.message for r in by_root.recommendations)
    assert any("examples" in r.message for r in by_root.suppressed)
