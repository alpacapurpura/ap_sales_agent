"""Backfill ``products.preset_id`` from (tenant.business_types, offer.archetype).

Sprint 14 ships ``OfferTypePreset`` (the 7th SSoT axis) linking each offer
to a preset in its tenant's vocabulary. Legacy offers predate this axis
and therefore have ``preset_id = NULL`` after migration 050 lands. This
script walks every offer and assigns a default preset_id using the pair
(tenant's first declared ``business_type``, offer's ``archetype``).

The mapping is derived from ``OFFER_TYPE_PRESET_CATALOG``: for each
``(business_type, archetype)`` we pick the first preset in the catalog
that matches both axes. That becomes the canonical "default" preset for
that pair — the wizard will let tenants pick a different one later; this
backfill establishes a sane starting state.

Design notes:
- **Idempotent by construction.** Only writes when ``preset_id IS NULL``.
  Rerunning after a partial failure is safe and produces no duplicate
  updates.
- **Conservative on missing data.** If a tenant has no
  ``business_types`` declared, the offer stays ``NULL``. The wizard will
  prompt later. Silent "guess" logic would produce wrong presets and
  break analytics.
- **Archetype-first lookup, business_type-second fallback.** If no preset
  matches the tenant's primary business_type + offer's archetype, we fall
  back to the tenant's secondary business_types (in declared order).
  Still no match → leave NULL.

Usage::

    # Dry run — no writes, prints plan:
    docker exec -t visionarias_brain_dev bash -c \\
        "cd /app && python scripts/backfill_offer_preset_id.py --dry-run"

    # Full run:
    docker exec -t visionarias_brain_dev bash -c \\
        "cd /app && python scripts/backfill_offer_preset_id.py"

    # Single tenant:
    docker exec -t visionarias_brain_dev bash -c \\
        "cd /app && python scripts/backfill_offer_preset_id.py --tenant <UUID>"
"""

from __future__ import annotations

import argparse
import sys
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# Repo root on sys.path so ``src.*`` imports work when invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session  # noqa: TC002

from src.core.database import SessionLocal
from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.offer_type_preset_catalog import (
    OFFER_TYPE_PRESET_CATALOG,
    OfferTypePreset,
)
from src.shared.domain.expert_business_type import ExpertBusinessType


@dataclass(frozen=True, slots=True)
class _OfferRow:
    offer_id: uuid.UUID
    tenant_id: uuid.UUID
    archetype: str


@dataclass(frozen=True, slots=True)
class _TenantContext:
    tenant_id: uuid.UUID
    business_types: tuple[str, ...]  # in declared order


@dataclass
class _BackfillStats:
    offers_scanned: int = 0
    offers_already_tagged: int = 0
    offers_tagged: int = 0
    offers_skipped_no_business_type: int = 0
    offers_skipped_no_match: int = 0
    tenants_touched: set[uuid.UUID] | None = None

    def __post_init__(self) -> None:
        if self.tenants_touched is None:
            self.tenants_touched = set()


def _build_default_preset_mapping() -> dict[tuple[str, str], str]:
    """Derive (business_type, archetype) → preset_id defaults from the catalog.

    For each unique pair, the first preset in the catalog's insertion order
    wins. This is deterministic and reproducible — if the catalog adds a
    new preset later, existing backfilled rows are not affected.
    """
    mapping: dict[tuple[str, str], str] = {}
    for preset in OFFER_TYPE_PRESET_CATALOG.values():
        key = (preset.business_type.value, preset.archetype.value)
        if key not in mapping:
            mapping[key] = preset.preset_id
    return mapping


def _load_tenant_contexts(db: Session) -> dict[uuid.UUID, _TenantContext]:
    """Load tenant_id → declared business_types (in order, deduped)."""
    rows = db.execute(
        text(
            """
            SELECT id,
                   config_json->'brand_settings'->'identity'->'business_types' AS business_types
            FROM tenants
            """
        )
    ).all()
    valid_types = {bt.value for bt in ExpertBusinessType}
    contexts: dict[uuid.UUID, _TenantContext] = {}
    for row in rows:
        tenant_id = uuid.UUID(str(row.id))
        raw = row.business_types
        ordered: list[str] = []
        if isinstance(raw, list):
            for candidate in raw:
                if isinstance(candidate, str) and candidate in valid_types and candidate not in ordered:
                    ordered.append(candidate)
        contexts[tenant_id] = _TenantContext(tenant_id=tenant_id, business_types=tuple(ordered))
    return contexts


def _load_untagged_offers(
    db: Session,
    *,
    tenant_filter: uuid.UUID | None,
) -> list[_OfferRow]:
    """Load offers where ``preset_id IS NULL`` (optionally scoped to one tenant)."""
    sql = """
        SELECT id, tenant_id, archetype
        FROM products
        WHERE preset_id IS NULL
          AND tenant_id IS NOT NULL
          AND deleted_at IS NULL
    """
    params: dict[str, object] = {}
    if tenant_filter is not None:
        sql += " AND tenant_id = :tenant_id"
        params["tenant_id"] = tenant_filter
    rows = db.execute(text(sql), params).all()
    return [
        _OfferRow(
            offer_id=uuid.UUID(str(r.id)),
            tenant_id=uuid.UUID(str(r.tenant_id)),
            archetype=str(r.archetype),
        )
        for r in rows
    ]


def _choose_preset(
    *,
    offer: _OfferRow,
    tenant_ctx: _TenantContext,
    mapping: dict[tuple[str, str], str],
) -> str | None:
    """Pick the default preset_id for an offer, or ``None`` if no match."""
    for business_type in tenant_ctx.business_types:
        preset_id = mapping.get((business_type, offer.archetype))
        if preset_id is not None:
            return preset_id
    return None


def _apply_updates(
    db: Session,
    *,
    updates: list[tuple[uuid.UUID, str]],
) -> None:
    """Apply ``preset_id`` updates in a single batch."""
    if not updates:
        return
    db.execute(
        text("UPDATE products SET preset_id = :preset_id WHERE id = :offer_id"),
        [{"offer_id": offer_id, "preset_id": preset_id} for offer_id, preset_id in updates],
    )


def run(
    *,
    dry_run: bool = False,
    tenant_filter: uuid.UUID | None = None,
) -> _BackfillStats:
    """Execute the backfill and return aggregated stats."""
    stats = _BackfillStats()
    mapping = _build_default_preset_mapping()

    db: Session = SessionLocal()
    try:
        tenant_contexts = _load_tenant_contexts(db)
        offers = _load_untagged_offers(db, tenant_filter=tenant_filter)
        stats.offers_scanned = len(offers)

        updates: list[tuple[uuid.UUID, str]] = []
        preset_counts: dict[str, int] = defaultdict(int)
        for offer in offers:
            tenant_ctx = tenant_contexts.get(offer.tenant_id)
            if tenant_ctx is None or not tenant_ctx.business_types:
                stats.offers_skipped_no_business_type += 1
                continue
            preset_id = _choose_preset(offer=offer, tenant_ctx=tenant_ctx, mapping=mapping)
            if preset_id is None:
                stats.offers_skipped_no_match += 1
                continue
            updates.append((offer.offer_id, preset_id))
            preset_counts[preset_id] += 1
            stats.tenants_touched.add(offer.tenant_id)  # type: ignore[union-attr]
            stats.offers_tagged += 1

        print(f"[backfill] scanned  : {stats.offers_scanned}")
        print(f"[backfill] tagged   : {stats.offers_tagged}")
        print(f"[backfill] skipped  : no business_type = {stats.offers_skipped_no_business_type}")
        print(f"[backfill] skipped  : no preset match  = {stats.offers_skipped_no_match}")
        print(f"[backfill] tenants  : {len(stats.tenants_touched or set())}")
        if preset_counts:
            print("[backfill] per-preset distribution:")
            for preset_id, n in sorted(preset_counts.items(), key=lambda kv: -kv[1]):
                print(f"  {preset_id}: {n}")

        if dry_run:
            print("[backfill] --dry-run: no writes")
            return stats

        _apply_updates(db, updates=updates)
        db.commit()
        print(f"[backfill] committed {len(updates)} updates.")
    finally:
        db.close()

    return stats


def _valid_archetypes() -> set[str]:
    return {a.value for a in OfferArchetype}


def _validate_mapping_coverage() -> None:
    """Sanity check at script start: every preset in the catalog is valid."""
    valid_archetypes = _valid_archetypes()
    mapping = _build_default_preset_mapping()
    bad = [(bt, arch) for (bt, arch) in mapping if arch not in valid_archetypes]
    if bad:
        msg = f"Invalid archetype values in preset mapping: {bad}"
        raise ValueError(msg)
    # Report coverage so ops can see which (business_type, archetype) pairs
    # would leave offers untagged.
    all_types = {t.value for t in ExpertBusinessType}
    missing_pairs = [(bt, a) for bt in all_types for a in valid_archetypes if (bt, a) not in mapping]
    if missing_pairs:
        print(f"[backfill] NOTE: {len(missing_pairs)} (business_type, archetype) pairs have no default preset.")
        print("[backfill] Offers matching these will stay NULL — wizard will prompt later.")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill Offer.preset_id from catalog defaults.")
    parser.add_argument("--dry-run", action="store_true", help="Print plan, do not write.")
    parser.add_argument("--tenant", type=str, default=None, help="Restrict to a single tenant UUID.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    _validate_mapping_coverage()
    tenant_filter: uuid.UUID | None = None
    if args.tenant:
        tenant_filter = uuid.UUID(args.tenant)
    run(dry_run=args.dry_run, tenant_filter=tenant_filter)


if __name__ == "__main__":
    main()


__all__ = [
    "OfferTypePreset",
    "run",
]
