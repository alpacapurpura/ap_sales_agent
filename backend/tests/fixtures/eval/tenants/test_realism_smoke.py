"""Realism smoke tests — 5 tenants x 6 YAMLs = 30 parametrized combinations.

Status in T-1: RED expected (no seed YAML files yet). Unblocked by T-3.

Each test verifies that a seed YAML has ≥5 non-null top-level fields,
ensuring drafts are realistic and not skeleton placeholders.

Validator coverage: scenario_happy_realism_smoke
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.fixtures.eval.tenants.loader import (
    ARCHETYPE_SLUGS,
    YAML_FILENAMES,
    _THIS_DIR,
)

# ---------------------------------------------------------------------------
# Minimum non-null field count per YAML
# ---------------------------------------------------------------------------

_MIN_NON_NULL_FIELDS = 5


# ---------------------------------------------------------------------------
# Parametrize: 5 x 6 = 30 effective test cases
# conftest.py pytest_generate_tests handles parametrize when BOTH
# archetype_slug AND yaml_filename are in fixturenames.
# ---------------------------------------------------------------------------


def test_yaml_has_min_nonnull_fields(archetype_slug: str, yaml_filename: str) -> None:
    """Each seed YAML must have ≥5 non-null top-level fields.

    This is a realism gate: a YAML with fewer non-null fields is likely
    a skeleton placeholder (not a usable seed tenant).

    RED in T-1 (no YAML files). GREEN after T-3 creates content.
    """
    yaml_path = _THIS_DIR / archetype_slug / f"{yaml_filename}.yaml"

    if not yaml_path.is_file():
        pytest.fail(
            f"Seed YAML not found: {yaml_path}. "
            "Run T-3 to create the seed YAML files. "
            "(This test is expected to be RED in T-1.)"
        )

    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        pytest.fail(f"YAML {yaml_path} did not parse to a dict (got {type(raw).__name__})")

    non_null_fields = [k for k, v in raw.items() if v is not None and v not in ("", [], {})]
    assert len(non_null_fields) >= _MIN_NON_NULL_FIELDS, (
        f"{archetype_slug}/{yaml_filename}.yaml has only {len(non_null_fields)} non-null "
        f"top-level fields (minimum: {_MIN_NON_NULL_FIELDS}). "
        f"Non-null keys found: {non_null_fields}"
    )
