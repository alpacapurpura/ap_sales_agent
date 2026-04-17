"""Backfill DRAFT placeholder editions for legacy offers (Phase 3.7).

Before Phase 2 shipped, offers of edition-supporting archetypes
(EXPERIENCIA, PROGRAMA, SERVICIO) were allowed to exist without a single
``launch_editions`` row. Phase 2 made placeholder creation part of
``OfferService.create``, but existing production data predates that
guarantee. This script closes the gap.

Usage (inside the FastAPI container so settings/env load identically):

    docker exec -t visionarias_brain_dev bash -c \\
        "cd /app && python scripts/backfill_edition_placeholders.py"

Flags:

- ``--dry-run``  : print what would be inserted, don't write.
- ``--tenant``   : restrict to a single tenant UUID.

The script is idempotent — re-running it after a partial failure skips
offers that already gained an edition.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

# Repo root on sys.path so ``src.*`` imports work when invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session  # noqa: TC002 — needed at runtime for type annotation

from src.core.database import SessionLocal
from src.modules.offer.domain.archetype_catalog import get_capabilities
from src.modules.offer.domain.enums import OfferArchetype


def _archetypes_supporting_editions() -> set[str]:
    return {archetype.value for archetype in OfferArchetype if get_capabilities(archetype).supports_editions}


def _find_offers_without_edition(
    db: Session,
    *,
    tenant_filter: uuid.UUID | None,
) -> list[tuple[uuid.UUID, uuid.UUID, str]]:
    """Return ``(offer_id, tenant_id, archetype)`` for orphan offers."""
    sql = """
        SELECT p.id, p.tenant_id, p.archetype
        FROM products p
        LEFT JOIN launch_editions le ON le.offer_id = p.id
        WHERE p.deleted_at IS NULL
          AND p.archetype = ANY(:supported)
          AND le.id IS NULL
    """
    params: dict[str, object] = {
        "supported": sorted(_archetypes_supporting_editions()),
    }
    if tenant_filter is not None:
        sql += " AND p.tenant_id = :tenant_id"
        params["tenant_id"] = tenant_filter
    return list(db.execute(text(sql), params).all())


def _insert_placeholder(
    db: Session,
    *,
    offer_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> None:
    """Insert a DRAFT + PRIVATE placeholder edition #1 with no dates."""
    db.execute(
        text(
            """
            INSERT INTO launch_editions (
                id, offer_id, tenant_id,
                edition_name, edition_number,
                status, visibility, timezone, enrollment_count
            )
            VALUES (
                gen_random_uuid(), :offer_id, :tenant_id,
                'Edición #1', 1,
                'draft', 'private', 'UTC', 0
            )
            """,
        ),
        {"offer_id": offer_id, "tenant_id": tenant_id},
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tenant", type=str, default=None)
    args = parser.parse_args(argv)

    tenant_filter: uuid.UUID | None = None
    if args.tenant:
        tenant_filter = uuid.UUID(args.tenant)

    db = SessionLocal()
    try:
        orphans = _find_offers_without_edition(db, tenant_filter=tenant_filter)
        print(f"Found {len(orphans)} edition-supporting offer(s) without a placeholder.")
        if not orphans:
            return 0

        for offer_id, tenant_id, archetype in orphans:
            print(f"  tenant={tenant_id}  offer={offer_id}  archetype={archetype}")
            if args.dry_run:
                continue
            _insert_placeholder(db, offer_id=offer_id, tenant_id=tenant_id)

        if args.dry_run:
            print("Dry run — no changes committed.")
            db.rollback()
        else:
            db.commit()
            print(f"Committed {len(orphans)} placeholder edition(s).")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
