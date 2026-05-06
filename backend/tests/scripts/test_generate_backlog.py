"""Tests for ``scripts/generate_backlog.py`` (R33 backlog auto-gen).

Each test builds a throwaway ``docs/product/`` tree under ``tmp_path`` and
invokes the script via subprocess with ``--repo tmp_path``. Asserts on
exit code + generated files.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "generate_backlog.py"


def _setup_minimal(repo: Path) -> None:
    """Create minimal docs/product/ tree under repo."""
    (repo / "docs" / "product" / "outcomes").mkdir(parents=True)
    (repo / "docs" / "product" / "stories").mkdir()
    (repo / "docs" / "product" / "capabilities").mkdir()
    (repo / "docs" / "product" / "modules").mkdir()


def _write_ideas_pool(repo: Path, entries: list[dict]) -> None:
    path = repo / "docs" / "product" / "ideas-pool.yaml"
    path.write_text(yaml.safe_dump({"ideas": entries}), encoding="utf-8")


def _write_outcome(repo: Path, slug: str, frontmatter: dict, body: str = "") -> Path:
    path = repo / "docs" / "product" / "outcomes" / f"{slug}.md"
    fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    path.write_text(f"---\n{fm_yaml}\n---\n\n{body}\n")
    return path


def _write_story_checkpoint(repo: Path, story_id: str, state: str, **extra: str) -> Path:
    folder = repo / "docs" / "product" / "stories" / story_id
    folder.mkdir(parents=True)
    cp = folder / "checkpoint.md"
    fm = {"id": story_id, "state": state, **extra}
    fm_yaml = yaml.safe_dump(fm, sort_keys=False).strip()
    cp.write_text(f"---\n{fm_yaml}\n---\n")
    return cp


def _write_capability(repo: Path, module: str, cap_id: str, status: str, story_ids: list[str] | None = None) -> Path:
    folder = repo / "docs" / "product" / "capabilities" / module
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{cap_id}.yaml"
    fm = {"id": cap_id, "module": module, "status": status, "story_ids": story_ids or []}
    fm_yaml = yaml.safe_dump(fm, sort_keys=False).strip()
    path.write_text(f"---\n{fm_yaml}\n---\n\nbody\n")
    return path


def _run(repo: Path, *, check: bool = False) -> subprocess.CompletedProcess:
    args = [sys.executable, str(SCRIPT), "--repo", str(repo)]
    if check:
        args.append("--check")
    return subprocess.run(args, capture_output=True, text=True, check=False)  # noqa: S603


def test_empty_repo_generates_minimal_backlog(tmp_path: Path) -> None:
    """Empty docs/product/ structure should still produce valid BACKLOG files."""
    _setup_minimal(tmp_path)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr

    backlog_yaml = tmp_path / "docs" / "product" / "BACKLOG.yaml"
    backlog_md = tmp_path / "docs" / "product" / "BACKLOG.md"
    assert backlog_yaml.exists()
    assert backlog_md.exists()

    data = yaml.safe_load(backlog_yaml.read_text())
    assert data["caps"]["validated_max"] == 10
    assert data["buckets"]["idea"] == []
    assert data["buckets"]["building"] == []


def test_idea_in_pool_appears_in_idea_bucket(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_ideas_pool(
        tmp_path,
        [
            {
                "id": "test-idea-1",
                "one_liner": "test idea",
                "state": "idea",
                "tags": ["module:test"],
                "created": "2026-05-01",
            }
        ],
    )
    _run(tmp_path)

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    assert len(data["buckets"]["idea"]) == 1
    assert data["buckets"]["idea"][0]["id"] == "test-idea-1"


def test_validated_idea_appears_in_validated_bucket(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_ideas_pool(
        tmp_path,
        [
            {
                "id": "v1",
                "one_liner": "validated thing",
                "state": "validated",
                "created": "2026-05-01",
                "ost": {"outcome": "test", "opportunities": [], "solutions": [], "tests": []},
            }
        ],
    )
    _run(tmp_path)

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    assert len(data["buckets"]["validated"]) == 1
    assert data["buckets"]["validated"][0]["id"] == "v1"


def test_active_story_with_state_ready_appears_in_ready_bucket(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_story_checkpoint(tmp_path, "my-story", "ready", outcome="my-outcome")
    _run(tmp_path)

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    assert len(data["buckets"]["ready"]) == 1
    assert data["buckets"]["ready"][0]["id"] == "my-story"


def test_outcome_with_metadata_appears(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_outcome(
        tmp_path,
        "test-outcome",
        {
            "id": "test-outcome",
            "state": "validated",
            "title": "Test Outcome",
            "story_ids": ["s1", "s2"],
            "why_now": "because",
            "priority": 1,
        },
    )
    _run(tmp_path)

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    outcomes = [it for it in data["buckets"]["validated"] if it["kind"] == "outcome"]
    assert len(outcomes) == 1
    assert outcomes[0]["extra"]["why_now"] == "because"


def test_capability_rollup_aggregates_per_module(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_capability(tmp_path, "modA", "cap1", "live", ["s1"])
    _write_capability(tmp_path, "modA", "cap2", "in-progress", ["s2"])
    _write_capability(tmp_path, "modB", "cap3", "live", ["s3"])
    _run(tmp_path)

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    rollup_a = next(c for c in data["capabilities"] if c["module"] == "modA")
    assert rollup_a["live"] == 1
    assert rollup_a["in_progress"] == 1
    assert rollup_a["total"] == 2


def test_validated_cap_warning_when_exceeded(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    entries = [{"id": f"v-{i}", "one_liner": f"v{i}", "state": "validated", "created": "2026-05-01"} for i in range(11)]
    _write_ideas_pool(tmp_path, entries)
    result = _run(tmp_path)
    assert result.returncode == 0

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    assert any("validated cap exceeded" in w for w in data["warnings"])
    assert "validated cap exceeded" in result.stdout or "validated cap exceeded" in result.stderr


def test_building_cap_warning_when_exceeded(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    for i in range(4):
        _write_story_checkpoint(tmp_path, f"build-{i}", "building")
    result = _run(tmp_path)
    assert result.returncode == 0

    data = yaml.safe_load((tmp_path / "docs" / "product" / "BACKLOG.yaml").read_text())
    assert any("building cap exceeded" in w for w in data["warnings"])


def test_check_mode_returns_0_when_fresh(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _run(tmp_path)  # generate first
    result = _run(tmp_path, check=True)
    assert result.returncode == 0
    assert "fresh" in result.stdout.lower() or "OK" in result.stdout


def test_check_mode_returns_1_when_drift(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _run(tmp_path)
    # introduce drift — add idea after generation
    _write_ideas_pool(tmp_path, [{"id": "new", "one_liner": "x", "state": "idea", "created": "2026-05-01"}])
    result = _run(tmp_path, check=True)
    assert result.returncode == 1
    assert "DRIFT" in result.stdout


def test_mermaid_kanban_block_present_in_md(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_ideas_pool(tmp_path, [{"id": "x", "one_liner": "x", "state": "idea", "created": "2026-05-01"}])
    _run(tmp_path)

    md = (tmp_path / "docs" / "product" / "BACKLOG.md").read_text()
    assert "```mermaid" in md
    assert "kanban" in md
    assert "💡 Ideas" in md
    assert "🔨 Building" in md


def test_roadmap_section_present_in_md(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _run(tmp_path)
    md = (tmp_path / "docs" / "product" / "BACKLOG.md").read_text()
    assert "Roadmap view" in md
    assert "Now (state=building" in md
    assert "Next (state=ready" in md


def test_capabilities_snapshot_present_in_md(tmp_path: Path) -> None:
    _setup_minimal(tmp_path)
    _write_capability(tmp_path, "mod1", "cap1", "live")
    _run(tmp_path)
    md = (tmp_path / "docs" / "product" / "BACKLOG.md").read_text()
    assert "Capabilities snapshot" in md
    assert "mod1" in md


@pytest.mark.parametrize(
    ("phase", "status", "expected_state"),
    [
        ("PM_DRAFT", "pending", "validated"),
        ("PO_SPEC", "in-progress", "validated"),
        ("ARCH_DONE", "in-progress", "ready"),
        ("BUILD_T1", "in-progress", "building"),
        ("AUDIT_T1_APPROVED", "in-progress", "review"),
        ("DONE", "done", "done"),
        ("BUILD_T2", "blocked", "parked"),
    ],
)
def test_legacy_phase_mapping_to_macro_state(phase: str, status: str, expected_state: str) -> None:
    """Direct unit test of legacy phase → macro state mapping."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from generate_backlog import _map_legacy_phase_to_state
    finally:
        sys.path.pop(0)
    assert _map_legacy_phase_to_state(phase, status) == expected_state


def test_idempotent_regeneration(tmp_path: Path) -> None:
    """Running twice should produce identical output."""
    _setup_minimal(tmp_path)
    _write_ideas_pool(tmp_path, [{"id": "x", "one_liner": "x", "state": "idea", "created": "2026-05-01"}])
    _write_capability(tmp_path, "modA", "cap1", "live", ["s1"])
    _run(tmp_path)
    md_first = (tmp_path / "docs" / "product" / "BACKLOG.md").read_text()
    _run(tmp_path)
    md_second = (tmp_path / "docs" / "product" / "BACKLOG.md").read_text()
    # Note: generated_at timestamp will differ, but content structure should be identical
    # Strip timestamps to compare structure
    assert md_first.split("Generated at")[1].split("\n", 2)[2] == md_second.split("Generated at")[1].split("\n", 2)[2]
