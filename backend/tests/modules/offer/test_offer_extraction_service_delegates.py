"""Tests — OfferExtractionService.extract_all delegates to OfferExtractionOrchestrator.

Verifies that:
1. extract_all instantiates and calls OfferExtractionOrchestrator.run()
2. The public signature of extract_all is preserved (callers don't break)
3. user_id is forwarded to the orchestrator
4. progress_callback is forwarded to the orchestrator
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OFFER_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

# The orchestrator is lazily imported inside extract_all — patch at module level.
_ORCHESTRATOR_CLASS_PATH = (
    "luana_core_offer_studio.application.offer_extraction_orchestrator.OfferExtractionOrchestrator"
)


class TestExtractAllDelegatesToOrchestrator:
    """extract_all must delegate to OfferExtractionOrchestrator.run()."""

    @pytest.mark.asyncio
    async def test_extract_all_calls_orchestrator_run(self) -> None:
        """extract_all should instantiate orchestrator and call run()."""
        db = MagicMock()
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run = AsyncMock(return_value=None)

        with patch(_ORCHESTRATOR_CLASS_PATH, return_value=mock_orchestrator_instance) as MockOrch:
            from luana_core_offer_studio.application.offer_extraction_service import (
                OfferExtractionService,
            )

            service = OfferExtractionService(db, TENANT_ID, OFFER_ID)
            await service.extract_all(
                url="https://example.com",
                text=None,
                mode="initial",
                update_instructions=None,
                progress_callback=None,
            )

        # Orchestrator was instantiated with the service itself
        MockOrch.assert_called_once_with(service)
        # run() was called
        mock_orchestrator_instance.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_all_forwards_url(self) -> None:
        """extract_all forwards url to orchestrator.run()."""
        db = MagicMock()
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run = AsyncMock(return_value=None)

        with patch(_ORCHESTRATOR_CLASS_PATH, return_value=mock_orchestrator_instance):
            from luana_core_offer_studio.application.offer_extraction_service import (
                OfferExtractionService,
            )

            service = OfferExtractionService(db, TENANT_ID, OFFER_ID)
            await service.extract_all(
                url="https://some-offer.com",
                text="extra text",
                mode="update",
                update_instructions="Focus on pricing",
                progress_callback=None,
            )

        call_kwargs = mock_orchestrator_instance.run.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs
        assert kwargs.get("url") == "https://some-offer.com"
        assert kwargs.get("text") == "extra text"
        assert kwargs.get("mode") == "update"
        assert kwargs.get("update_instructions") == "Focus on pricing"

    @pytest.mark.asyncio
    async def test_extract_all_forwards_user_id(self) -> None:
        """extract_all forwards user_id to orchestrator.run()."""
        db = MagicMock()
        user_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run = AsyncMock(return_value=None)

        with patch(_ORCHESTRATOR_CLASS_PATH, return_value=mock_orchestrator_instance):
            from luana_core_offer_studio.application.offer_extraction_service import (
                OfferExtractionService,
            )

            service = OfferExtractionService(db, TENANT_ID, OFFER_ID)
            await service.extract_all(
                url=None,
                text="some text",
                mode="initial",
                update_instructions=None,
                progress_callback=None,
                user_id=user_id,
            )

        call_kwargs = mock_orchestrator_instance.run.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs
        assert kwargs.get("user_id") == user_id

    @pytest.mark.asyncio
    async def test_extract_all_forwards_progress_callback(self) -> None:
        """extract_all forwards progress_callback to orchestrator.run()."""
        db = MagicMock()
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run = AsyncMock(return_value=None)

        def my_callback(pct: int, stage: str) -> None:
            pass

        with patch(_ORCHESTRATOR_CLASS_PATH, return_value=mock_orchestrator_instance):
            from luana_core_offer_studio.application.offer_extraction_service import (
                OfferExtractionService,
            )

            service = OfferExtractionService(db, TENANT_ID, OFFER_ID)
            await service.extract_all(
                url=None,
                text="some text",
                mode="initial",
                update_instructions=None,
                progress_callback=my_callback,
            )

        call_kwargs = mock_orchestrator_instance.run.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs
        assert kwargs.get("progress_callback") is my_callback

    @pytest.mark.asyncio
    async def test_extract_all_no_args_still_delegates(self) -> None:
        """extract_all with no url/text still delegates (orchestrator handles it)."""
        db = MagicMock()
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_instance.run = AsyncMock(return_value=None)

        with patch(_ORCHESTRATOR_CLASS_PATH, return_value=mock_orchestrator_instance):
            from luana_core_offer_studio.application.offer_extraction_service import (
                OfferExtractionService,
            )

            service = OfferExtractionService(db, TENANT_ID, OFFER_ID)
            # Must not raise even with no content
            await service.extract_all()

        mock_orchestrator_instance.run.assert_called_once()
