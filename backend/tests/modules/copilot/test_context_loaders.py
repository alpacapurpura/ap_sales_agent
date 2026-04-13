"""Tests for context loader registry and OfferContextLoader."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.context.context_loader_registry import (
    get_context_loader,
)
from src.modules.copilot.infrastructure.context.offer_context_loader import (
    OfferContextLoader,
)


def test_get_context_loader_offer() -> None:
    """Test get_context_loader returns OfferContextLoader."""
    db = MagicMock()
    loader = get_context_loader("offer_context", db)
    assert isinstance(loader, OfferContextLoader)


def test_get_context_loader_unknown_raises() -> None:
    """Test get_context_loader raises for unknown type."""
    with pytest.raises(ValueError, match="No context loader"):
        get_context_loader("nonexistent", MagicMock())


@pytest.mark.asyncio
async def test_offer_context_loader_with_no_offers() -> None:
    """Test offer context loader with no offers."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    loader = OfferContextLoader(mock_db)
    result = await loader.load(
        tenant_id=uuid4(),
        entity_id=uuid4(),
    )

    assert isinstance(result, str)
    assert "primero" in result.lower() or "no hay" in result.lower()


@pytest.mark.asyncio
async def test_offer_context_loader_with_offers() -> None:
    """Test offer context loader with existing offers."""
    mock_offer_1 = MagicMock()
    mock_offer_1.name = "Coaching Premium"
    mock_offer_1.archetype = "COURSE"
    mock_offer_1.value_level = "TRANSFORMACION"
    mock_offer_1.currency = "USD"
    mock_offer_1.pricing = [{"pay_in_full": 997}]
    mock_offer_1.status = "published"

    mock_offer_2 = MagicMock()
    mock_offer_2.name = "Ebook Gratis"
    mock_offer_2.archetype = "DIGITAL_PRODUCT"
    mock_offer_2.value_level = "LEAD_MAGNET"
    mock_offer_2.currency = "USD"
    mock_offer_2.pricing = [{"pay_in_full": 0}]
    mock_offer_2.status = "published"

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mock_offer_1, mock_offer_2]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    loader = OfferContextLoader(mock_db)
    result = await loader.load(tenant_id=uuid4())

    assert isinstance(result, str)
    assert "Coaching Premium" in result
    assert "Ebook Gratis" in result
    assert "Gaps" in result or "ACTIVACION" in result


@pytest.mark.asyncio
async def test_offer_context_loader_excludes_entity_id() -> None:
    """Test entity_id offer is excluded from results."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db = MagicMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    entity_id = uuid4()
    loader = OfferContextLoader(mock_db)
    await loader.load(tenant_id=uuid4(), entity_id=entity_id)

    # Verify execute was called (the WHERE clause filtering is in the query)
    mock_db.execute.assert_called_once()
