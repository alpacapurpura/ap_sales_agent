"""Tests for CRMInternalProvider — Cold Contact from journey_events.

Mocks SQLAlchemy database session.
"""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_analytics_engine.infrastructure.providers.crm_internal_provider import (
    CRMInternalProvider,
)

TENANT_ID = uuid4()


class TestCRMInternalProviderBasics:
    def test_provider_name(self):
        assert CRMInternalProvider().provider_name() == "crm_internal"

    def test_rate_limit_config(self):
        cfg = CRMInternalProvider().rate_limit_config()
        assert "requests_per_minute" in cfg


class TestColdContactMetrics:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        mock_db = MagicMock()

        # Mock count queries: contacts=25, responses=8
        mock_contacts_result = MagicMock()
        mock_contacts_result.scalar.return_value = 25

        mock_responses_result = MagicMock()
        mock_responses_result.scalar.return_value = 8

        mock_db.execute.side_effect = [mock_contacts_result, mock_responses_result]

        provider = CRMInternalProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {"db_session": mock_db},
            date(2026, 3, 1),
            date(2026, 3, 15),
        )

        cold = [m for m in result.metrics if m.channel_slug == "cold-contact"]
        assert len(cold) == 2

        contacts = next(m for m in cold if m.metric_name == "contacts")
        assert contacts.value == 25.0

        responses = next(m for m in cold if m.metric_name == "responses")
        assert responses.value == 8.0


class TestCRMInternalErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_db_session(self):
        provider = CRMInternalProvider()
        result = await provider.extract_metrics(
            TENANT_ID,
            {},
            date(2026, 3, 1),
            date(2026, 3, 15),
        )
        assert result.metrics == []

    @pytest.mark.asyncio
    async def test_db_exception(self):
        """DB exceptions propagate to the pipeline, which handles them as FAILED runs."""
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB connection lost")

        provider = CRMInternalProvider()
        with pytest.raises(Exception, match="DB connection lost"):
            await provider.extract_metrics(
                TENANT_ID,
                {"db_session": mock_db},
                date(2026, 3, 1),
                date(2026, 3, 15),
            )
