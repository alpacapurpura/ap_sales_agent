"""Tests for OfferExtractionService — TDD RED→GREEN."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.offer import (
    Offer,
    OfferPromiseUpdate,
)

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OFFER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_offer(**overrides) -> Offer:
    defaults = {
        "id": OFFER_ID,
        "tenant_id": TENANT_ID,
        "internal_sku": "TEST-SKU",
        "public_name": "Test Offer",
        "archetype": OfferArchetype.PROGRAMA,
        "headline_promise": "Transform your life",
        "primary_outcome": "Complete transformation",
        "time_to_value": "8 weeks",
        "target_avatar_match": [],
        "requires_application": False,
        "min_financial_capacity": "LOW_INCOME",
        "pricing_options": [],
        "guarantee_type": "none",
        "guarantee_terms": "",
        "status": "draft",
    }
    defaults.update(overrides)
    return Offer(**defaults)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_offer():
    return _make_offer()


class TestOfferExtractionServiceInit:
    """Test that the service initializes correctly."""

    def test_creates_with_required_params(self, mock_db):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)
        assert service.tenant_id == TENANT_ID
        assert service.offer_id == OFFER_ID

    def test_imports_webcrawler_from_shared(self):
        """Verify WebCrawler is imported from shared, not brand."""
        import inspect

        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        source = inspect.getfile(OfferExtractionService)
        with open(source) as f:
            source_code = f.read()
        assert "from src.shared.infrastructure.web.crawler import" in source_code
        assert "from src.modules.brand" not in source_code


class TestOfferExtractionServicePromptRendering:
    """Test prompt rendering with archetype."""

    @patch("src.modules.offer.application.offer_extraction_service.prompt_loader")
    def test_render_prompt_includes_archetype(self, mock_loader, mock_db):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        mock_loader.render.return_value = "rendered prompt"
        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)

        service._render_prompt(
            "offer_extract_promise",
            "content here",
            "current data",
            "instructions",
            "programa",
        )
        mock_loader.render.assert_called_once()
        call_kwargs = mock_loader.render.call_args[1]
        assert call_kwargs["archetype"] == "programa"

    def test_append_schema_instruction(self, mock_db):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)
        result = service._append_schema_instruction("base prompt", OfferPromiseUpdate)
        assert "SCHEMA:" in result
        assert "headline_promise" in result
        assert "Return a valid JSON" in result


class TestOfferExtractionServiceExtractAll:
    """Test the full extraction orchestration."""

    @pytest.mark.asyncio
    @patch("src.modules.offer.application.offer_extraction_service.OfferService")
    @patch("src.modules.offer.application.offer_extraction_service.WebCrawler")
    async def test_extract_all_calls_crawler_with_url(
        self, mock_crawler_cls, mock_offer_svc_cls, mock_db, mock_offer
    ):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        mock_crawler_instance = AsyncMock()
        mock_crawler_instance.crawl_content.return_value = "crawled content"
        mock_crawler_cls.return_value = mock_crawler_instance

        mock_svc = MagicMock()
        mock_svc.get_offer.return_value = mock_offer
        mock_offer_svc_cls.return_value = mock_svc

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)

        with patch.object(service, "_run_section", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = OfferPromiseUpdate()

            progress_calls = []
            await service.extract_all(
                url="https://example.com/product",
                progress_callback=lambda p, s: progress_calls.append((p, s)),
            )

            mock_crawler_instance.crawl_content.assert_awaited_once_with(
                "https://example.com/product"
            )
            assert mock_run.await_count == 6  # 6 sections
            assert len(progress_calls) > 0

    @pytest.mark.asyncio
    @patch("src.modules.offer.application.offer_extraction_service.OfferService")
    async def test_extract_all_uses_text_when_no_url(
        self, mock_offer_svc_cls, mock_db, mock_offer
    ):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        mock_svc = MagicMock()
        mock_svc.get_offer.return_value = mock_offer
        mock_offer_svc_cls.return_value = mock_svc

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)

        with patch.object(service, "_run_section", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = OfferPromiseUpdate()
            await service.extract_all(text="manual text about the offer")
            assert mock_run.await_count == 6

    @pytest.mark.asyncio
    @patch("src.modules.offer.application.offer_extraction_service.OfferService")
    async def test_extract_all_persists_results_per_wave(
        self, mock_offer_svc_cls, mock_db, mock_offer
    ):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        mock_svc = MagicMock()
        mock_svc.get_offer.return_value = mock_offer
        mock_offer_svc_cls.return_value = mock_svc

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)

        with patch.object(service, "_run_section", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = OfferPromiseUpdate(
                headline_promise="AI extracted promise"
            )
            await service.extract_all(text="some content")

            # patch_offer should be called for each wave's results
            assert mock_svc.patch_offer.call_count >= 2

    @pytest.mark.asyncio
    @patch("src.modules.offer.application.offer_extraction_service.OfferService")
    async def test_extract_all_uses_correct_archetype(
        self, mock_offer_svc_cls, mock_db
    ):
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        offer = _make_offer(archetype=OfferArchetype.SERVICIO)
        mock_svc = MagicMock()
        mock_svc.get_offer.return_value = offer
        mock_offer_svc_cls.return_value = mock_svc

        service = OfferExtractionService(mock_db, TENANT_ID, OFFER_ID)

        with (
            patch.object(service, "_run_section", new_callable=AsyncMock) as mock_run,
            patch.object(service, "_render_prompt") as mock_render,
        ):
            mock_run.return_value = OfferPromiseUpdate()
            mock_render.return_value = "rendered"
            await service.extract_all(text="content")

            # Check archetype was passed to _render_prompt
            for call in mock_render.call_args_list:
                # archetype is the 5th positional arg (index 4)
                assert call[0][4] == "servicio"
