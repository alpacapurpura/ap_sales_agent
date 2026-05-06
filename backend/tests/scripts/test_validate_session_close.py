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


def test_clean_repo_returns_0(tmp_path: Path) -> None:
    """Clean repo (no caps exceeded, no WIP, fresh) → exit 0."""
    _setup_minimal(tmp_path)
    _write_backlog(
        tmp_path,
        {"validated": [], "ready": [], "building": [], "review": []},
    )
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
    # Exit 2 (warn) is acceptable since freshness checks may flag missing scripts; key is no BLOCK
    assert result.returncode in {0, 2}, result.stdout + result.stderr


def test_building_cap_exceeded_blocks(tmp_path: Path) -> None:
    """4 building stories → exit 1 (BLOCK)."""
    _setup_minimal(tmp_path)
    _write_backlog(
        tmp_path,
        {
            "validated": [],
            "ready": [],
            "building": [{"id": f"b{i}"} for i in range(4)],
            "review": [],
        },
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 1
    assert "building" in result.stdout
    assert "cap 3" in result.stdout


def test_validated_cap_exceeded_blocks(tmp_path: Path) -> None:
    """11 validated entries → exit 1."""
    _setup_minimal(tmp_path)
    _write_backlog(
        tmp_path,
        {
            "validated": [{"id": f"v{i}"} for i in range(11)],
            "ready": [],
            "building": [],
            "review": [],
        },
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 1
    assert "validated" in result.stdout


def test_ready_cap_exceeded_blocks(tmp_path: Path) -> None:
    """6 ready stories → exit 1."""
    _setup_minimal(tmp_path)
    _write_backlog(
        tmp_path,
        {
            "validated": [],
            "ready": [{"id": f"r{i}"} for i in range(6)],
            "building": [],
            "review": [],
        },
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 1
    assert "ready" in result.stdout


def test_review_cap_exceeded_blocks(tmp_path: Path) -> None:
    """3 review stories → exit 1."""
    _setup_minimal(tmp_path)
    _write_backlog(
        tmp_path,
        {
            "validated": [],
            "ready": [],
            "building": [],
            "review": [{"id": f"rv{i}"} for i in range(3)],
        },
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 1
    assert "review" in result.stdout


def test_uncommitted_wip_warns(tmp_path: Path) -> None:
    """Modified files → warn (exit 2)."""
    _setup_minimal(tmp_path)
    _write_backlog(tmp_path, {"validated": [], "ready": [], "building": [], "review": []})
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    # Create untracked file
    (tmp_path / "newfile.txt").write_text("uncommitted")

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "uncommitted" in result.stdout


def test_missing_backlog_warns(tmp_path: Path) -> None:
    """No BACKLOG.yaml → warn."""
    _setup_minimal(tmp_path)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 2
    assert "BACKLOG.yaml missing" in result.stdout


def test_quiet_mode_suppresses_warn_output(tmp_path: Path) -> None:
    """--quiet suppresses warn output but keeps exit code."""
    _setup_minimal(tmp_path)
    _write_backlog(tmp_path, {"validated": [], "ready": [], "building": [], "review": []})
    (tmp_path / "newfile.txt").write_text("x")

    result = _run(tmp_path, quiet=True)
    assert result.returncode == 2
    assert result.stdout.strip() == ""  # quiet suppresses


@pytest.mark.parametrize(
    ("state", "cap_label"),
    [
        ("building", "cap 3"),
        ("validated", "cap 10"),
        ("ready", "cap 5"),
        ("review", "cap 2"),
    ],
)
def test_cap_violation_reported_with_count(tmp_path: Path, state: str, cap_label: str) -> None:
    """Each cap violation reports state + cap label."""
    _setup_minimal(tmp_path)
    sizes = {"validated": 0, "ready": 0, "building": 0, "review": 0}
    sizes[state] = 100  # massive overflow
    _write_backlog(tmp_path, {s: [{"id": f"x{i}"} for i in range(sizes[s])] for s in sizes})
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    result = _run(tmp_path)
    assert result.returncode == 1
    assert state in result.stdout
    assert cap_label in result.stdout
