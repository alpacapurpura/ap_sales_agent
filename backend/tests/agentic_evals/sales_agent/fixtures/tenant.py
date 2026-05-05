"""Visionarias tenant session fixture.

Provides a real DB session bound to the Visionarias tenant — the canonical
target of the smoke harness per spec ratification B (Decision B6: real
tenant + real DB, NOT mocked). The fixture **NEVER seeds**: if any
precondition fails (tenant absent, no active offer, no compiled
``PersonalityProfile.system_instruction``), it skips with an explicit
human-readable reason.

Decisión arquitectónica B2 (ratificada Chris 2026-05-04): seed
accountability lives in the dev environment + future ``Story 8`` cron
job, NOT in this fixture. Skip-with-reason is the contract — silent
shifts to a different offer are forbidden.

All queries filter by ``tenant_id == VISIONARIAS_TENANT_ID`` per
``.claude/rules/tenant-isolation.md``. Cross-tenant leak regression is
asserted by Scenario 4 in T-5.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# Default UUID for the Visionarias tenant in dev DB. Override via env var
# ``VISIONARIAS_TENANT_ID`` for CI / staging. Mirrors the convention in
# ``backend/scripts/validate_attraction.py``.
_DEFAULT_VISIONARIAS_TENANT_ID = "00000000-0000-0000-0000-000000000001"


def _resolve_visionarias_tenant_id() -> UUID:
    """Resolve the canonical Visionarias tenant UUID.

    Reads ``VISIONARIAS_TENANT_ID`` env var; falls back to the default
    sentinel UUID. Raises ``ValueError`` (caught by the fixture as a
    skip reason) when the value is not a valid UUID — explicit failure
    mode aligned with B2.
    """
    raw = os.environ.get("VISIONARIAS_TENANT_ID", _DEFAULT_VISIONARIAS_TENANT_ID)
    return UUID(raw)


def _get_real_db_session() -> Session:
    """Open a real Postgres session via the production session factory.

    The eval suite intentionally bypasses the in-memory SQLite session
    fixture from ``backend/tests/conftest.py`` — Decision B6 requires
    real DB writes to ``sales_agent_trace_event`` + ``sales_agent_llm_call``
    so Capa 4 (cost) can be verified.

    Caller closes the session in the fixture teardown.
    """
    from src.core.database import SessionLocal

    return SessionLocal()


@pytest.fixture
def visionarias_tenant_session() -> Any:  # generator yields dict, but mypy gets noisy
    """Bind a real DB session to the Visionarias tenant + verify preconditions.

    Yields:
        dict with keys:
            - ``tenant_id`` (UUID): the resolved Visionarias tenant ID.
            - ``offer`` (ProductModel): top-1 active offer ordered by
              ``created_at desc``. Used by the smoke golden as the
              ``{{offer_name}}`` template variable.
            - ``brand_voice`` (str): rendered ``PersonalityProfile.system_instruction``
              from production compiler v2 path.
            - ``db_session`` (Session): the real DB session (closed in teardown).

    Skips with explicit reason when:
        - Visionarias tenant row absent.
        - Visionarias has 0 active offers (``deleted_at IS NULL``).
        - Visionarias has no compiled ``PersonalityProfile.system_instruction``.
        - DB connection fails (transient — runner re-tries are caller's job).
    """
    tenant_id = _resolve_visionarias_tenant_id()
    db: Session | None = None
    try:
        try:
            db = _get_real_db_session()
        except Exception as exc:  # noqa: BLE001 — fixture is allowed broad except for skip path
            logger.warning(
                "eval_visionarias_db_open_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            pytest.skip(
                f"No se pudo abrir la sesión DB para Visionarias ({tenant_id}). "
                f"Verifica que Postgres esté corriendo. Detalle: {exc}",
            )

        # Lazy imports — keep collection cheap when default suite ignores eval marker.
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel
        from src.modules.offer.infrastructure.models.product_model import ProductModel
        from src.modules.sales_agent.application.services.knowledge_builder import (
            TenantKnowledgeBuilder,
        )

        # 1. Tenant existence (filtered by tenant_id PK — implicit isolation).
        # Lazy connection failure (e.g. unreachable Postgres host) surfaces here
        # at first execute(); wrap in try/except so the fixture can skip with
        # a Spanish-neutro reason instead of erroring out.
        try:
            tenant_row = db.execute(
                select(TenantModel).where(TenantModel.id == tenant_id),
            ).scalar_one_or_none()
        except Exception as exc:  # noqa: BLE001 — broad except for skip path
            logger.warning(
                "eval_visionarias_db_query_failed",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            pytest.skip(
                f"No se pudo consultar la DB para Visionarias ({tenant_id}). "
                f"Verifica que Postgres esté accesible desde WSL nativo. "
                f"Detalle: {exc}",
            )
        if tenant_row is None:
            pytest.skip(
                f"Tenant Visionarias ({tenant_id}) no existe en la DB de dev. "
                f"Corre `make seed-visionarias` o configura VISIONARIAS_TENANT_ID.",
            )

        # 2. Active offer — explicit tenant_id filter per tenant-isolation rule.
        offer_row = db.execute(
            select(ProductModel)
            .where(
                ProductModel.tenant_id == tenant_id,
                ProductModel.deleted_at.is_(None),
            )
            .order_by(ProductModel.created_at.desc())
            .limit(1),
        ).scalar_one_or_none()
        if offer_row is None:
            pytest.skip(
                f"Visionarias ({tenant_id}) no tiene ofertas activas. "
                f"El smoke golden necesita al menos una oferta sin deleted_at.",
            )

        # 3. PersonalityProfile.system_instruction compilado.
        knowledge_builder = TenantKnowledgeBuilder(db)
        brand_voice = knowledge_builder.build_brand_voice(tenant_id)
        if not brand_voice:
            pytest.skip(
                f"Visionarias ({tenant_id}) no tiene PersonalityProfile.system_instruction "
                f"compilado. Configura la voz en /brand-studio/estilo y guarda.",
            )

        # 4. Audit log — Decision B + spec NFR (eval_cross_tenant_check).
        logger.info(
            "eval_cross_tenant_check",
            tenant_id_expected=str(tenant_id),
            tenant_id_observed=str(offer_row.tenant_id),
        )
        # Cross-tenant safeguard: defensive double-check the offer belongs to the tenant.
        if offer_row.tenant_id != tenant_id:
            error_msg = (
                f"Cross-tenant leak detected: golden offer.tenant_id={offer_row.tenant_id} "
                f"does not match harness tenant_id={tenant_id}"
            )
            raise AssertionError(error_msg)

        yield {
            "tenant_id": tenant_id,
            "offer": offer_row,
            "brand_voice": brand_voice,
            "db_session": db,
        }
    finally:
        if db is not None:
            db.close()
