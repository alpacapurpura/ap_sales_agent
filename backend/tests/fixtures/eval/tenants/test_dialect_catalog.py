"""Tests for dialect_catalog.yaml — BCP-47 SSoT.

These tests validate the dialect catalog structure and content.
All 4 tests should be GREEN in T-1 (catalog is created in T-1).

Validator coverage:
  scenario_happy_dialect_catalog (A2 in 06-tickets.yaml)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from tests.fixtures.eval.tenants.loader import (
    ARCHETYPE_DIALECT_MAP,
    _load_dialect_catalog,
    _validate_dialect_code,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = {"code", "display_name", "voseo", "country_code", "description"}
_MIN_ENTRY_COUNT = 13  # must have at least 13 entries; currently 15


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_catalog_has_min_13_entries(dialect_catalog_path: Path) -> None:
    """Dialect catalog must have at least 13 BCP-47 entries."""
    raw = yaml.safe_load(dialect_catalog_path.read_text(encoding="utf-8"))
    entries = raw.get("dialects", [])
    assert len(entries) >= _MIN_ENTRY_COUNT, (
        f"Expected ≥{_MIN_ENTRY_COUNT} entries in dialect_catalog.yaml, got {len(entries)}"
    )


def test_catalog_contains_all_archetype_dialects(dialect_catalog_path: Path) -> None:
    """All 5 archetype dialect codes must be present in the catalog.

    Ratified dialect picks:
      tenant_coach_lat              → es-PE
      tenant_medicina_estetica      → es-MX
      tenant_clinica_dental         → es-CO
      tenant_agencia_growth_video   → es-AR
      tenant_agencia_automatizacion_ia → es-419
    """
    raw = yaml.safe_load(dialect_catalog_path.read_text(encoding="utf-8"))
    catalog_codes = {entry["code"] for entry in raw.get("dialects", [])}

    expected_codes = set(ARCHETYPE_DIALECT_MAP.values())
    missing = expected_codes - catalog_codes
    assert not missing, (
        f"Archetype dialect codes missing from catalog: {sorted(missing)}. Catalog codes: {sorted(catalog_codes)}"
    )


def test_each_entry_has_required_fields(dialect_catalog_path: Path) -> None:
    """Every entry in dialect_catalog.yaml must have all required fields."""
    raw = yaml.safe_load(dialect_catalog_path.read_text(encoding="utf-8"))
    entries = raw.get("dialects", [])

    for i, entry in enumerate(entries):
        missing = _REQUIRED_FIELDS - set(entry.keys())
        assert not missing, f"Entry #{i} (code={entry.get('code', '?')}) missing required fields: {sorted(missing)}"


def test_invalid_dialect_code_raises() -> None:
    """Loading an unknown dialect code must raise ValueError."""
    with pytest.raises(ValueError, match=r"not found in dialect_catalog\.yaml"):
        _validate_dialect_code("xx-UNKNOWN")
