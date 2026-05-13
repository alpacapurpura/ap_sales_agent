"""Architecture fitness: ExpertBusinessType enum <-> catalog invariants.

Mirrors ``test_archetype_catalog_completeness.py``. Adding a new
``ExpertBusinessType`` without a matching catalog entry (or leaving an
orphan entry) fails CI.
"""

from __future__ import annotations

from luana_core_platform.domain.expert_business_type import (
    EXPERT_BUSINESS_TYPE_CATALOG,
    ExpertBusinessType,
)


def test_every_expert_business_type_has_a_catalog_entry() -> None:
    missing = [t for t in ExpertBusinessType if t not in EXPERT_BUSINESS_TYPE_CATALOG]
    assert missing == [], (
        "Every ExpertBusinessType must have an EXPERT_BUSINESS_TYPE_CATALOG entry. "
        f"Missing: {missing}. Add a record to shared/domain/expert_business_type.py."
    )


def test_catalog_has_no_orphan_entries() -> None:
    enum_values = set(ExpertBusinessType)
    catalog_values = set(EXPERT_BUSINESS_TYPE_CATALOG.keys())
    orphans = catalog_values - enum_values
    assert orphans == set(), f"Catalog has entries for business types that no longer exist in the enum: {orphans}"


def test_catalog_records_self_reference_their_type() -> None:
    for business_type, metadata in EXPERT_BUSINESS_TYPE_CATALOG.items():
        assert metadata.business_type is business_type, (
            f"Catalog entry for {business_type} declares business_type={metadata.business_type}"
        )
