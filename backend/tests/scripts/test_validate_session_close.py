# ruff: noqa: S607
# Reason: tests invoke `git` via partial path — fixture context, acceptable.
"""Tests for ``scripts/validate_session_close.py`` (R34 Stop hook validator)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "validate_session_close.py"


def _setup_minimal(repo: Path) -> None:
    """Create minimal docs/product/ tree + git repo."""
    (repo / "docs" / "product").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=repo, check=True)


def _write_backlog(repo: Path, buckets: dict[str, list]) -> None:
    """Write a minimal BACKLOG.yaml with given bucket sizes."""
    path = repo / "docs" / "product" / "BACKLOG.yaml"
    content = {
        "generated_at": "2026-05-06T00:00:00+00:00",
        "buckets": buckets,
    }
    path.write_text(yaml.safe_dump(content), encoding="utf-8")


def _run(repo: Path, *, quiet: bool = False) -> subprocess.CompletedProcess:
    args = [sys.executable, str(SCRIPT), "--repo", str(repo)]
    if quiet:
        args.append("--quiet")
    return subprocess.run(args, capture_output=True, text=True, check=False)  # noqa: S603


def _empty_v4_buckets() -> dict[str, list]:
    """Empty buckets for all v4 states."""
    return {
        "idea": [],
        "refining": [],
        "refined": [],
        "ready": [],
        "developing": [],
        "developed": [],
        "reviewing": [],
        "done": [],
        "parked": [],
        "dropped": [],
    }


def _story_items(n: int, prefix: str = "s") -> list[dict]:
    """N story items (kind=story) — eligible for cap counting."""
    return [{"id": f"{prefix}{i}", "kind": "story", "tags": []} for i in range(n)]


def test_clean_repo_returns_0(tmp_path: Path) -> None:
    """Clean repo (no caps exceeded, no WIP, fresh) → exit 0.

    Exit 0 is now the only acceptable outcome for non-blocked repos
    (WARN was reclassified to exit 0 to prevent Claude Code Stop hook loops).
    """
    _setup_minimal(tmp_path)
    _write_backlog(tmp_path, _empty_v4_buckets())
    subprocess.run(
        ["git", "add", "."],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"],
        cwd=tmp_path,
        check=True,
    )
    result = _run(tmp_path, quiet=True)
    # Exit 0 — clean OR warn-only (warn no longer blocks).
    assert result.returncode == 0, result.stdout + result.stderr


def test_developing_cap_exceeded_blocks(tmp_path: Path) -> None:
    """4 developing stories (cap 3) → exit 2 (BLOCK, fed back to model)."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    buckets["developing"] = _story_items(4, "b")
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "developing" in result.stdout
    assert "cap 3" in result.stdout


def test_refining_cap_exceeded_blocks(tmp_path: Path) -> None:
    """4 refining stories (cap 3) → exit 2."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    buckets["refining"] = _story_items(4, "r")
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "refining" in result.stdout


def test_ready_cap_exceeded_blocks(tmp_path: Path) -> None:
    """6 ready stories (cap 5) → exit 2."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    buckets["ready"] = _story_items(6, "r")
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "ready" in result.stdout


def test_reviewing_cap_exceeded_blocks(tmp_path: Path) -> None:
    """3 reviewing stories (cap 2) → exit 2."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    buckets["reviewing"] = _story_items(3, "rv")
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "reviewing" in result.stdout


def test_legacy_exempt_stories_dont_count(tmp_path: Path) -> None:
    """Stories tagged legacy:* are forward-only exempt — no cap violation."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    # 7 legacy stories in refining (would exceed cap=3 if counted)
    buckets["refining"] = [{"id": f"l{i}", "kind": "story", "tags": ["legacy:pi-12"]} for i in range(7)]
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    # Should NOT block (legacy exempt). Exit 0 always now (warn no longer 2).
    assert result.returncode == 0, f"Expected 0, got {result.returncode}: {result.stdout}\n{result.stderr}"


def test_outcomes_dont_count_toward_cap(tmp_path: Path) -> None:
    """kind=outcome items don't count toward story-level WIP cap."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    # 10 outcomes in refining (would exceed cap=3 if counted; outcomes are epics)
    buckets["refining"] = [{"id": f"o{i}", "kind": "outcome", "tags": []} for i in range(10)]
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    # Should NOT block. Exit 0 always.
    assert result.returncode == 0, f"Expected 0, got {result.returncode}"


def test_uncommitted_wip_warns(tmp_path: Path) -> None:
    """Modified files → WARN (exit 0, message on stderr — non-blocking).

    Reclassified from exit 2 to exit 0 to avoid Claude Code Stop hook
    feedback loop on uncommitted WIP.
    """
    _setup_minimal(tmp_path)
    _write_backlog(tmp_path, _empty_v4_buckets())
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    # Create untracked file
    (tmp_path / "newfile.txt").write_text("uncommitted")

    result = _run(tmp_path)
    assert result.returncode == 0
    assert "uncommitted" in result.stderr
    assert result.stdout.strip() == ""


def test_missing_backlog_warns(tmp_path: Path) -> None:
    """No BACKLOG.yaml → WARN (exit 0, message on stderr)."""
    _setup_minimal(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 0
    assert "BACKLOG.yaml missing" in result.stderr


def test_quiet_mode_suppresses_warn_output(tmp_path: Path) -> None:
    """--quiet suppresses WARN output on both streams + exit 0."""
    _setup_minimal(tmp_path)
    _write_backlog(tmp_path, _empty_v4_buckets())
    (tmp_path / "newfile.txt").write_text("x")

    result = _run(tmp_path, quiet=True)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert result.stderr.strip() == ""


@pytest.mark.parametrize(
    ("state", "cap_label"),
    [
        ("refining", "cap 3"),
        ("refined", "cap 5"),
        ("ready", "cap 5"),
        ("developing", "cap 3"),
        ("developed", "cap 10"),
        ("reviewing", "cap 2"),
    ],
)
def test_cap_violation_reported_with_count(tmp_path: Path, state: str, cap_label: str) -> None:
    """Each v4 cap violation reports state + cap label, exits 2 (BLOCK to model)."""
    _setup_minimal(tmp_path)
    buckets = _empty_v4_buckets()
    buckets[state] = _story_items(100, "x")  # massive overflow
    _write_backlog(tmp_path, buckets)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert state in result.stdout
    assert cap_label in result.stdout
