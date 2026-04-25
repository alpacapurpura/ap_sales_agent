"""F5 — OfferRepository.search (fuzzy match + filters) tests.

pg_trgm `similarity()` lights up only on Postgres; in SQLite tests the repo
falls back to `ILIKE` substring matching. Both paths must respect tenant
isolation, soft-delete exclusion, and limit.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from tests.modules.offer.conftest import TENANT_A, TENANT_B, create_product_model

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


@pytest.fixture
def offers_seed(db: Session) -> dict[str, uuid.UUID]:
    now = datetime.now(timezone.utc)
    proposito = create_product_model(
        TENANT_A,
        name="Programa Propósito y Prosperidad",
        status="active",
        created_at=now - timedelta(days=10),
    )
    mentoria = create_product_model(
        TENANT_A,
        name="Mentoría 1:1",
        status="active",
        created_at=now - timedelta(days=2),
    )
    archived = create_product_model(
        TENANT_A,
        name="Curso archivado",
        status="active",
        archived_at=now - timedelta(days=1),
        created_at=now - timedelta(days=30),
    )
    deleted = create_product_model(
        TENANT_A,
        name="Borrado",
        status="active",
        deleted_at=now - timedelta(days=1),
        created_at=now - timedelta(days=30),
    )
    other_tenant = create_product_model(
        TENANT_B,
        name="Programa Propósito otro tenant",
        status="active",
        created_at=now - timedelta(days=1),
    )
    db.add_all([proposito, mentoria, archived, deleted, other_tenant])
    db.flush()
    return {
        "proposito": proposito.id,
        "mentoria": mentoria.id,
        "archived": archived.id,
        "deleted": deleted.id,
        "other_tenant": other_tenant.id,
    }


def test_search_filters_by_tenant(db: Session, offers_seed: dict[str, uuid.UUID]) -> None:
    # NOTE: query keeps the accent — SQLite ILIKE is accent-sensitive, while
    # pg_trgm in production normalises trigrams (case-insensitive, accent-aware).
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, name_query="Propósito")
    ids = {o.id for o in results}
    assert offers_seed["proposito"] in ids
    assert offers_seed["other_tenant"] not in ids


def test_search_fuzzy_substring_match(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, name_query="prosperidad")
    assert any(o.id == offers_seed["proposito"] for o in results)


def test_search_excludes_soft_deleted(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, name_query="borrado")
    assert all(o.id != offers_seed["deleted"] for o in results)


def test_search_status_active_only(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, status="active")
    ids = {o.id for o in results}
    assert offers_seed["proposito"] in ids
    assert offers_seed["mentoria"] in ids
    assert offers_seed["archived"] not in ids
    assert offers_seed["deleted"] not in ids


def test_search_status_archived_only(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, status="archived")
    ids = {o.id for o in results}
    assert offers_seed["archived"] in ids
    assert offers_seed["proposito"] not in ids


def test_search_status_none_includes_active_and_archived(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, status=None)
    ids = {o.id for o in results}
    assert offers_seed["proposito"] in ids
    assert offers_seed["archived"] in ids
    # soft-deleted always excluded
    assert offers_seed["deleted"] not in ids


def test_search_since_filter(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=5)
    results = repo.search(tenant_id=TENANT_A, since=cutoff)
    ids = {o.id for o in results}
    assert offers_seed["mentoria"] in ids  # 2 days old, within window
    assert offers_seed["proposito"] not in ids  # 10 days old, outside window


def test_search_limit(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, limit=1)
    assert len(results) == 1


def test_search_no_query_returns_all_active_for_tenant(
    db: Session,
    offers_seed: dict[str, uuid.UUID],
) -> None:
    repo = OfferRepository(db)
    results = repo.search(tenant_id=TENANT_A, status="active")
    ids = {o.id for o in results}
    assert offers_seed["proposito"] in ids
    assert offers_seed["mentoria"] in ids
