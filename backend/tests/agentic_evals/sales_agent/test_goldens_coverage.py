"""Coverage gate tests for golden scenario dataset (Story D -- T-4 -- Scenario 3).

Verifies that the golden dataset covers all 15 cells of the 5-tenant x 3-persona-kind
matrix. Tests use the REAL goldens directory (post Chris curation) when populated,
and fall back to synthetic test fixtures for builder phase validation.

Coverage rules (spec Scenario 3):
  - D11: each (tenant x persona_kind) cell must have >= 1 golden
  - D2: total dataset must not exceed 30 goldens (saturation cap)
  - D-A-11: no early-exit on gap reporting -- ALL gaps must be listed

# voseo-allowed: coverage tests reference persona_kind and tenant slug values
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.no_eval

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[4]

# Real goldens path (populated by Chris after generation + curation)
_GOLDENS_ROOT = _REPO_ROOT / "backend" / "tests" / "agentic_evals" / "sales_agent" / "goldens"

# Synthetic fixtures (builder phase — T-4 deliverable)
_SYNTHETIC_FIXTURES_DIR = _REPO_ROOT / "backend" / "tests" / "_goldens_test_fixtures"

# 15-cell matrix: 5 tenants x 3 persona kinds (D11)
_TENANT_SLUGS: tuple[str, ...] = (
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
)

_PERSONA_KINDS: tuple[str, ...] = ("happy", "nurture", "unqualified")

# Recovery command shown in failure message (D-A-11)
_RECOVERY_CMD = (
    "python backend/scripts/generate_golden_candidates.py \\\n"
    "  --tenant {tenant_slug} --persona-kind {persona_kind} \\\n"
    "  --output-dir backend/tests/agentic_evals/sales_agent/_artifacts/goldens_generation/run-$(date +%Y%m%d)\n"
    "# Then promote via:\n"
    "python backend/scripts/promote_golden.py --simulation-id <uuid> \\\n"
    "  --golden-id {tenant_slug}-{persona_kind}-001 --artifact-dir <dir> \\\n"
    "  --actor-profile-id <story-c-id>"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scan_goldens_dir(directory: Path) -> Generator[dict, None, None]:
    """Yield parsed YAML dicts for all *.yaml files in directory (non-recursive subfolders)."""
    if not directory.exists():
        return
    # Scan both flat (synthetic fixtures) and nested (real goldens: tenant/kind/file.yaml)
    for yaml_file in sorted(directory.rglob("*.yaml")):
        # Skip __pycache__ and hidden dirs
        if any(part.startswith(("__", ".")) for part in yaml_file.parts):
            continue
        try:
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "tenant_slug" in raw and "persona_kind" in raw:
                yield raw
        except yaml.YAMLError:
            continue


def _get_coverage_source() -> tuple[Path, str]:
    """Return (directory, label) for coverage scanning.

    Prefers real goldens dir if it contains GoldenScenarioModel-shaped YAMLs.
    Falls back to synthetic fixtures for builder phase.
    """
    # Check if real goldens dir has any schema-shaped YAMLs
    real_goldens = list(_scan_goldens_dir(_GOLDENS_ROOT))
    if real_goldens:
        return _GOLDENS_ROOT, "real goldens"
    # Fall back to synthetic fixtures
    return _SYNTHETIC_FIXTURES_DIR, "synthetic test fixtures"


# ---------------------------------------------------------------------------
# Coverage gate tests (Scenario 3)
# ---------------------------------------------------------------------------


def test_all_cells_covered() -> None:
    """Each (tenant_slug x persona_kind) cell must have >= 1 golden.

    T-4 deliverable: coverage gate per spec Scenario 3.
    D11: 15-cell minimum coverage invariant.
    Uses real goldens when present (post Chris curation), synthetic fixtures during build.
    """
    source_dir, source_label = _get_coverage_source()

    if not source_dir.exists() or not any(source_dir.rglob("*.yaml")):
        pytest.skip(
            f"No goldens or synthetic fixtures found. "
            f"Real goldens dir: {_GOLDENS_ROOT}, synthetic: {_SYNTHETIC_FIXTURES_DIR}"
        )

    # Build coverage map: {(tenant_slug, persona_kind): count}
    coverage: dict[tuple[str, str], int] = {}
    for golden in _scan_goldens_dir(source_dir):
        key = (golden["tenant_slug"], golden["persona_kind"])
        coverage[key] = coverage.get(key, 0) + 1

    # Check all 15 cells
    missing_cells: list[tuple[str, str]] = []
    for tenant in _TENANT_SLUGS:
        for kind in _PERSONA_KINDS:
            if coverage.get((tenant, kind), 0) == 0:
                missing_cells.append((tenant, kind))

    if missing_cells:
        # Format recovery commands for each missing cell (D-A-11 no early-exit)
        recovery_hints = "\n".join(
            f"  ({tenant}, {kind}):\n    "
            + _RECOVERY_CMD.format(tenant_slug=tenant, persona_kind=kind).replace("\n", "\n    ")
            for tenant, kind in missing_cells
        )
        pytest.fail(
            f"Coverage gap detected in {source_label}: {len(missing_cells)}/15 cells missing.\n\n"
            f"Missing cells:\n"
            + "\n".join(f"  - tenant='{t}', persona_kind='{k}'" for t, k in missing_cells)
            + f"\n\nRecovery commands:\n{recovery_hints}"
        )


def test_reports_all_cells_with_gaps() -> None:
    """When ≥ 2 cells are empty, FAIL message lists ALL violators (no early-exit).

    T-4 deliverable: D-A-11 no-early-exit invariant.
    Verifies that gap reporting is exhaustive — every missing cell is reported
    in a single failure message (not one-at-a-time / short-circuit).

    Strategy: create an in-memory coverage map with exactly 2 missing cells
    and verify the gap detection logic reports both.
    """
    # Build a mock coverage map with 2 deliberate gaps
    mock_coverage: dict[tuple[str, str], int] = {}
    # Fill all cells except the last 2
    all_cells = [(t, k) for t in _TENANT_SLUGS for k in _PERSONA_KINDS]
    gap_cells = [all_cells[-1], all_cells[-2]]  # last 2 cells are gaps

    for tenant, kind in all_cells:
        if (tenant, kind) not in gap_cells:
            mock_coverage[(tenant, kind)] = 1

    # Detect gaps (replicate the logic from test_all_cells_covered)
    missing_cells: list[tuple[str, str]] = []
    for tenant in _TENANT_SLUGS:
        for kind in _PERSONA_KINDS:
            if mock_coverage.get((tenant, kind), 0) == 0:
                missing_cells.append((tenant, kind))

    # D-A-11: all gaps must be reported — check count matches expectation
    assert len(missing_cells) == len(gap_cells), (
        f"Expected {len(gap_cells)} gaps, detected {len(missing_cells)}. "
        "Gap detection logic has early-exit (D-A-11 violation)."
    )

    # Verify both expected gap cells are in the reported missing_cells
    for gap in gap_cells:
        assert gap in missing_cells, (
            f"Gap {gap} not reported in missing_cells. "
            f"Reported: {missing_cells}. "
            "D-A-11: all gaps must be reported, no early-exit."
        )


def test_max_30_per_dataset() -> None:
    """Total golden count must not exceed 30 (saturation cap D2).

    T-4 deliverable: D2 saturation cap enforcement.
    τ-Bench research shows diminishing returns beyond 30 goldens per test suite
    (spec 03-arch.md D2 cement).
    """
    source_dir, source_label = _get_coverage_source()

    if not source_dir.exists() or not any(source_dir.rglob("*.yaml")):
        pytest.skip(
            f"No goldens or synthetic fixtures found. "
            f"Real goldens dir: {_GOLDENS_ROOT}, synthetic: {_SYNTHETIC_FIXTURES_DIR}"
        )

    total_count = sum(1 for _ in _scan_goldens_dir(source_dir))

    assert total_count <= 30, (
        f"Golden dataset exceeds saturation cap: {total_count} goldens in {source_label} "
        f"(D2 max=30). "
        "τ-Bench research shows diminishing eval returns beyond 30 goldens. "
        "Review which goldens add unique coverage before adding more."
    )
