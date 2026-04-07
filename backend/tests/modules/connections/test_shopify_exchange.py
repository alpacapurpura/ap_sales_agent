import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.modules.connections.api.shopify import (
    ShopifyExchangeRequest,
    auth_callback,
    exchange_shopify_token,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)


def _build_request(query: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/connections/shopify/auth/callback",
        "query_string": query.encode("utf-8"),
        "headers": [],
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_exchange_resuelve_tenant_por_shop_sin_state():
    tenant_id = uuid.uuid4()
    repo = MagicMock()
    repo.get_active_shopify_by_shop.return_value = SimpleNamespace(tenant_id=tenant_id)
    repo.upsert = MagicMock()

    payload = ShopifyExchangeRequest(
        code="auth_code",
        shop="mi-tienda.myshopify.com",
        hmac="signature",
        state=None,
    )

    with (
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.verify_hmac",
            return_value=True,
        ),
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.exchange_token",
            new=AsyncMock(return_value=("token_permanente", None)),
        ),
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.verify_connection",
            new=AsyncMock(return_value=(True, {"domain": "mi-tienda.myshopify.com"})),
        ),
    ):
        response = await exchange_shopify_token(request=payload, repo=repo)

    assert response.status == "connected"
    repo.get_active_shopify_by_shop.assert_called_once_with("mi-tienda.myshopify.com")
    repo.upsert.assert_called_once()
    assert repo.upsert.call_args.kwargs["tenant_id"] == tenant_id
    assert repo.upsert.call_args.kwargs["channel_type"] == ChannelType.SHOPIFY


@pytest.mark.asyncio
async def test_exchange_falla_si_no_hay_tenant_por_shop():
    repo = MagicMock()
    repo.get_active_shopify_by_shop.return_value = None

    payload = ShopifyExchangeRequest(
        code="auth_code",
        shop="mi-tienda.myshopify.com",
        hmac="signature",
        state=None,
    )

    with (
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.verify_hmac",
            return_value=True,
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        await exchange_shopify_token(request=payload, repo=repo)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Tenant resolution failed for shop"


@pytest.mark.asyncio
async def test_callback_publico_permite_state_ausente():
    tenant_id = uuid.uuid4()
    repo = MagicMock()
    repo.get_active_shopify_by_shop.return_value = SimpleNamespace(tenant_id=tenant_id)
    repo.upsert = MagicMock()

    request = _build_request(
        "shop=mi-tienda.myshopify.com&code=auth_code&hmac=signature"
    )

    with (
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.verify_hmac",
            return_value=True,
        ),
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.exchange_token",
            new=AsyncMock(return_value=("token_permanente", None)),
        ),
        patch(
            "src.modules.connections.api.shopify.ShopifyConnector.verify_connection",
            new=AsyncMock(return_value=(True, {"domain": "mi-tienda.myshopify.com"})),
        ),
        patch("src.modules.connections.api.shopify.settings") as mock_settings,
    ):
        mock_settings.DASHBOARD_DOMAIN = "http://localhost:3000"
        response = await auth_callback(request=request, repo=repo)

    assert response.status_code in (302, 307)
    assert (
        "growth-studio/connections?status=success&channel=shopify"
        in response.headers["location"]
    )
    repo.upsert.assert_called_once()
    assert repo.upsert.call_args.kwargs["tenant_id"] == tenant_id


def test_repo_busca_conexion_activa_por_shop_normalizado():
    target = SimpleNamespace(config={"shop_url": "https://mi-tienda.myshopify.com"})
    other = SimpleNamespace(config={"shop_url": "https://otra-tienda.myshopify.com"})

    scalar_result = MagicMock()
    scalar_result.all.return_value = [other, target]
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalar_result

    db = MagicMock()
    db.execute.return_value = execute_result

    repo = ChannelConnectionRepository(db)
    connection = repo.get_active_shopify_by_shop("mi-tienda")

    assert connection is target
