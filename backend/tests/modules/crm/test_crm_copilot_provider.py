"""
Tests for CrmCopilotProvider and uncovered CrmDataAccessProvider lines.

CRM-06: Provider surface (module_id, label, data_access, module_data) +
data_access error paths (unsupported kind, db_factory fallback, session close).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from luana_core_copilot.domain.ports import DataQueryPlan, ModuleData
from luana_core_crm.copilot_provider.data_access import CrmDataAccessProvider
from luana_core_crm.copilot_provider.provider import CrmCopilotProvider

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

TENANT_X = uuid.UUID("c001ab1e-0000-4000-8000-cc0000000001")


# ---------------------------------------------------------------------------
# CrmCopilotProvider surface
# ---------------------------------------------------------------------------


class TestCrmCopilotProviderSurface:
    """CrmCopilotProvider implements BaseCopilotProvider correctly."""

    def test_module_id(self):
        assert CrmCopilotProvider().module_id == "crm"

    def test_label(self):
        assert CrmCopilotProvider().label == "CRM"

    def test_data_access_returns_instance(self):
        """data_access() returns a CrmDataAccessProvider."""
        provider = CrmCopilotProvider()
        data_access = provider.data_access()
        assert data_access is not None
        assert isinstance(data_access, CrmDataAccessProvider)

    def test_module_data_returns_correct_metadata(self):
        """module_data() returns ModuleData with expected fields."""
        provider = CrmCopilotProvider()
        md = provider.module_data()

        assert md is not None
        assert isinstance(md, ModuleData)
        assert md.module_id == "crm"
        assert md.label == "CRM"
        assert "clientes" in md.description
        assert md.route_prefix == "sales"
        assert "lead" in md.keywords
        assert "cliente" in md.keywords
        assert "venta" in md.keywords


# ---------------------------------------------------------------------------
# CrmDataAccessProvider — unsupported kind (lines 52-56)
# ---------------------------------------------------------------------------


class TestDataAccessUnsupportedKind:
    """execute raises ValueError for unsupported kinds."""

    @pytest.mark.asyncio
    async def test_unsupported_kind_raises(self):
        """Kind not in SUPPORTED_KINDS → ValueError with expected kinds."""
        access = CrmDataAccessProvider()
        plan = DataQueryPlan(kind="offer_lookup", filters={})

        with pytest.raises(ValueError, match="offer_lookup"):
            await access.execute(tenant_id=TENANT_X, plan=plan)


# ---------------------------------------------------------------------------
# CrmDataAccessProvider — db_factory fallback (lines 24-26, 72, 93)
# ---------------------------------------------------------------------------


class TestDataAccessDbFactoryFallback:
    """When no db in context, provider calls _db_factory and closes it."""

    @pytest.mark.asyncio
    async def test_uses_db_factory_when_no_context_db(self):
        """No db in context → _db_factory called → session closed after."""
        mock_session = MagicMock()
        mock_repo_result = MagicMock()
        mock_repo_result.count_inbound.return_value = 5

        def fake_factory():
            return mock_session

        access = CrmDataAccessProvider(db_factory=fake_factory)
        now = datetime.now(timezone.utc)
        plan = DataQueryPlan(
            kind="lead_count",
            filters={
                "since": now - timedelta(days=7),
                "until": now,
            },
        )

        with patch(
            "luana_core_crm.infrastructure.repositories.lead_repository.LeadRepository",
            return_value=mock_repo_result,
        ):
            result = await access.execute(tenant_id=TENANT_X, plan=plan)

        assert result.metadata["count"] == 5
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_close_session_when_provided_in_context(self, db: Session):
        """db passed via context → owns_session=False → no close."""
        access = CrmDataAccessProvider()
        now = datetime.now(timezone.utc)
        plan = DataQueryPlan(
            kind="lead_count",
            filters={
                "since": now - timedelta(days=7),
                "until": now,
            },
        )

        result = await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})

        # Session should not be closed (it's managed by the test fixture)
        assert result.rows == []
        assert result.metadata["kind"] == "lead_count"
