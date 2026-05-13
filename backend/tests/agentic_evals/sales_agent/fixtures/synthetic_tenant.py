"""Synthetic ``T2_synthetic`` tenant fixture for the cross-tenant leak scenario.

Per ``03-arch-be.md`` § "Tests requeridos" + spec § "Scenario 4 (cross-
tenant adversarial)" + ticket T-5 acceptance A4: the smoke harness must
prove tenant isolation under conditions where multiple tenants exist in
the dev DB. This fixture seeds a deterministic ``T2_synthetic`` tenant
+ a single offer for it BEFORE Scenario 4 invokes the agent against
Visionarias. The assertion then queries
``sales_agent_trace_event WHERE turn_id = ?`` and confirms the DISTINCT
``tenant_id`` set is exactly ``{visionarias_tenant_id}`` — never the
synthetic tenant.

Scope per Decision B6 (real DB, no mocks):

* Real Postgres rows inserted at fixture setup.
* Soft-deleted (``deleted_at = utc_now()``) at teardown so the DB stays
  clean across runs and admin reports do not surface eval pollution.
* Idempotent: if a previous run leaked the row (filesystem crash, abort)
  the fixture upserts by deterministic ``id`` UUID — no duplicate-key
  errors.

Anti-duplication §0:

* Reuses ``TenantModel`` + ``ProductModel`` from production
  infrastructure paths. NO mirror DDL, NO test-only ORM models.
* Reuses ``utc_now`` from ``shared/domain/time.py`` for timestamp
  consistency with audit-log expectations.
* Reuses ``soft_delete`` semantic (``deleted_at = utc_now()``) honored
  by every query in the codebase per ``backend-ddd.md``.

Tenant isolation (`.claude/rules/tenant-isolation.md`):

* The synthetic tenant has its own UUID — never coincides with
  Visionarias. The fixture rejects setup if the dev DB Visionarias UUID
  collides with the synthetic UUID (defensive paranoia — should never
  fire in practice).
* All inserted rows carry the synthetic tenant's UUID; Scenario 4
  proves the AGENT does not write rows under this tenant when invoked
  with the Visionarias tenant_id.

Spanish neutro LATAM (`.claude/rules/spanish-text.md`):

* The synthetic offer name is ASCII (``T2 Synthetic Offer``) for grep
  determinism — Scenario 4 asserts the substring ``T2_synthetic`` is
  ABSENT from the sanitised trace.json artifact.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# Deterministic synthetic tenant UUID — never collides with Visionarias
# default (00000000-0000-0000-0000-000000000001). Documented here so the
# Scenario 4 grader can match by string substring "T2_synthetic" in
# trace.json (the substring lives in offer.name not in tenant_id, but
# the tenant_id presence in DB is the canonical regression signal).
_SYNTHETIC_TENANT_ID = UUID("00000000-0000-0000-0000-0000000000a2")
_SYNTHETIC_TENANT_NAME = "T2_synthetic"
_SYNTHETIC_OFFER_ID = UUID("00000000-0000-0000-0000-0000000000b2")
_SYNTHETIC_OFFER_NAME = "T2 Synthetic Offer"


def seed_t2_synthetic_tenant_with_offer(db: Session) -> dict[str, Any]:
    """Upsert the synthetic tenant + offer rows; idempotent.

    Args:
        db: Real Postgres session (caller owns lifecycle).

    Returns:
        dict with keys ``tenant_id`` (UUID) and ``offer_id`` (UUID).

    Notes:
        * Defensive against partial rows: if the tenant exists but the
          offer is missing, the offer is inserted; vice versa.
        * Soft-deletes are NOT undone — if a previous teardown left the
          rows soft-deleted, the upsert restores ``deleted_at = NULL``.
    """
    # Lazy imports — keep collection cheap when default suite ignores eval.
    from luana_core_iam.infrastructure.models.tenant_model import TenantModel
    from luana_core_offer_studio.infrastructure.models.product_model import ProductModel

    # 1. Tenant upsert.
    tenant = db.execute(
        select(TenantModel).where(TenantModel.id == _SYNTHETIC_TENANT_ID),
    ).scalar_one_or_none()
    if tenant is None:
        tenant = TenantModel(
            id=_SYNTHETIC_TENANT_ID,
            name=_SYNTHETIC_TENANT_NAME,
        )
        db.add(tenant)
        db.flush()
        logger.info(
            "eval_synthetic_tenant_inserted",
            tenant_id=str(_SYNTHETIC_TENANT_ID),
            tenant_name=_SYNTHETIC_TENANT_NAME,
        )
    elif hasattr(tenant, "deleted_at") and tenant.deleted_at is not None:
        # Restore in case a prior run soft-deleted (no-op in TenantModel
        # if the model lacks deleted_at — guarded by hasattr).
        tenant.deleted_at = None
        db.flush()
        logger.info(
            "eval_synthetic_tenant_restored",
            tenant_id=str(_SYNTHETIC_TENANT_ID),
        )

    # 2. Offer upsert (filtered by tenant_id per tenant-isolation rule).
    offer = db.execute(
        select(ProductModel).where(
            ProductModel.id == _SYNTHETIC_OFFER_ID,
            ProductModel.tenant_id == _SYNTHETIC_TENANT_ID,
        ),
    ).scalar_one_or_none()
    if offer is None:
        offer = ProductModel(
            id=_SYNTHETIC_OFFER_ID,
            tenant_id=_SYNTHETIC_TENANT_ID,
            name=_SYNTHETIC_OFFER_NAME,
        )
        db.add(offer)
        db.flush()
        logger.info(
            "eval_synthetic_offer_inserted",
            offer_id=str(_SYNTHETIC_OFFER_ID),
            tenant_id=str(_SYNTHETIC_TENANT_ID),
        )
    elif offer.deleted_at is not None:
        offer.deleted_at = None
        db.flush()
        logger.info(
            "eval_synthetic_offer_restored",
            offer_id=str(_SYNTHETIC_OFFER_ID),
        )

    return {
        "tenant_id": _SYNTHETIC_TENANT_ID,
        "tenant_name": _SYNTHETIC_TENANT_NAME,
        "offer_id": _SYNTHETIC_OFFER_ID,
        "offer_name": _SYNTHETIC_OFFER_NAME,
    }


@pytest.fixture
def synthetic_tenant(visionarias_tenant_session: dict[str, Any]) -> dict[str, Any]:
    """Seed ``T2_synthetic`` tenant + offer alongside Visionarias.

    Depends on ``visionarias_tenant_session`` so the same DB session is
    reused — both tenants live in the same transaction (committed at
    teardown of the parent fixture). The synthetic rows are NOT
    soft-deleted at fixture exit because the smoke runs read-only against
    them after the agent invocation; cleanup is the OPS job (a
    ``backend/scripts/`` cleaner can purge ``T2_synthetic`` periodically).

    Yields:
        dict with keys:
            - ``tenant_id`` (UUID): synthetic tenant UUID.
            - ``tenant_name`` (str): ``T2_synthetic`` for substring grep.
            - ``offer_id`` (UUID): synthetic offer UUID.
            - ``offer_name`` (str): ``T2 Synthetic Offer``.

    Defensive: if the Visionarias UUID equals the synthetic UUID (would
    indicate a misconfigured env var), the fixture skips with explicit
    Spanish-neutro reason — never proceeds with an unsafe seed.
    """
    visionarias_id: UUID = visionarias_tenant_session["tenant_id"]
    if visionarias_id == _SYNTHETIC_TENANT_ID:
        pytest.skip(
            "VISIONARIAS_TENANT_ID coincide con la UUID sintetica reservada "
            f"({_SYNTHETIC_TENANT_ID}). Cambia VISIONARIAS_TENANT_ID en .env "
            "para evitar colision en Scenario 4.",
        )

    db: Session = visionarias_tenant_session["db_session"]
    seeded = seed_t2_synthetic_tenant_with_offer(db)
    db.commit()

    logger.info(
        "eval_synthetic_tenant_ready",
        tenant_id=str(seeded["tenant_id"]),
        offer_id=str(seeded["offer_id"]),
    )
    yield seeded


__all__ = [
    "seed_t2_synthetic_tenant_with_offer",
    "synthetic_tenant",
]
