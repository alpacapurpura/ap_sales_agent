from fastapi import APIRouter, Depends, HTTPException, Body, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
import structlog
import os
import secrets

from src.core.database import get_db
from src.core.context import set_tenant_id
from src.core.config import settings
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import ChannelConnectionRepository
from src.modules.connections.infrastructure.models import ChannelConnectionModel
from src.modules.connections.infrastructure.channels.meta import MetaAdapter
from src.modules.connections.infrastructure.channels.instagram import InstagramChannel
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator
from src.modules.connections.api.dto.meta import (
    MetaConfigRequest,
    MetaStatusResponse,
    MetaAssetsResponse,
    FacebookPageAsset,
    InstagramAccountAsset,
    MetaAdsAccountAsset,
    ToggleAssetRequest,
)
from src.modules.connections.api.dependencies.webhook_security import verify_meta_signature

router = APIRouter(tags=["meta"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


# ---------------------------------------------------------------------------
# Webhook (no auth — called by Meta)
# ---------------------------------------------------------------------------

@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
):
    verify_token = settings.META_VERIFY_TOKEN if hasattr(settings, "META_VERIFY_TOKEN") else os.getenv("META_VERIFY_TOKEN", "visionarias_secret_token")
    if mode == "subscribe" and token == verify_token:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def webhook_event(
    payload: dict = Body(...),
    verified: bool = Depends(verify_meta_signature),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    try:
        entry = payload.get("entry", [])[0]
        account_id = entry.get("id")
    except (IndexError, AttributeError):
        return {"status": "ignored", "reason": "invalid_payload"}

    # First try to match by specific Facebook Page or Instagram Account asset
    connections = repo.get_all_active_by_type(
        ["facebook_page", "instagram_account", "meta", "instagram"]
    )

    connection = None
    for conn in connections:
        cfg = conn.config or {}
        # Asset-level match: page_id or ig_account_id stored as asset_id
        if cfg.get("asset_id") == account_id:
            connection = conn
            break
        # Legacy match: user_id stored in master META connection
        if cfg.get("user_id") == account_id:
            connection = conn
            break

    if not connection:
        logger.warning("meta_webhook_unknown_account", account_id=account_id)
        return {"status": "ignored", "reason": "unknown_account"}

    set_tenant_id(connection.tenant_id)

    # Use connection credentials (page_access_token for assets, user token for legacy)
    channel = InstagramChannel(
        client_config=connection.config,
        credentials_data=connection.credentials,
    )

    incoming = channel.normalize_payload(payload)
    if not incoming:
        return {"status": "ignored", "reason": "normalization_failed"}

    try:
        await orchestrator.process_chat_flow(channel, incoming)
    except Exception as e:
        logger.error("meta_webhook_process_error", error=str(e))

    return {"status": "processed"}


# ---------------------------------------------------------------------------
# Configuration (app_id / app_secret per-tenant)
# ---------------------------------------------------------------------------

@router.put("/configure")
async def configure(
    data: MetaConfigRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Save Meta app credentials (app_id / app_secret) for this tenant."""
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)

    creds_update = {"app_id": data.app_id, "app_secret": data.app_secret}

    if connection:
        existing = dict(connection.credentials) if connection.credentials else {}
        existing.update(creds_update)
        repo.update_credentials(connection, existing)
    else:
        connection = ChannelConnectionModel(
            tenant_id=user.tenant_id,
            channel_type=ChannelType.META.value,
            credentials=creds_update,
            config={},
            is_active=False,
        )
        repo.db.add(connection)
        repo.db.commit()

    return {"status": "config_saved"}


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------

@router.get("/auth-url")
async def get_auth_url(
    redirect_uri: Optional[str] = None,
    user: User = Depends(get_current_user),
):
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI is required")

    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        raise HTTPException(status_code=500, detail="Meta no configurado en el servidor.")

    adapter = MetaAdapter()
    url, state = adapter.get_authorization_url(redirect_uri)
    return {"url": url, "state": state}


@router.post("/callback")
async def oauth_callback(
    code: str = Body(..., embed=True),
    redirect_uri: str = Body(..., embed=True),
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    adapter = MetaAdapter()

    try:
        creds_data = await adapter.exchange_code(code, redirect_uri)
    except Exception as e:
        logger.error("meta_oauth_exchange_failed", error=str(e))
        raise HTTPException(status_code=400, detail="Error de autenticacion con Meta")

    try:
        adapter_with_token = MetaAdapter(access_token=creds_data.get("access_token"))
        profile = await adapter_with_token.get_user_profile()
        user_id = profile.get("id")
        name = profile.get("name")
        if not user_id:
            raise ValueError("User ID not found in profile")
    except Exception as e:
        logger.error("failed_to_get_meta_profile", error=str(e))
        raise HTTPException(status_code=400, detail="No se pudo obtener el perfil de Meta.")

    repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.META,
        credentials=creds_data,
        config={"user_id": user_id, "name": name},
    )

    return {"status": "connected", "profile": profile}


# ---------------------------------------------------------------------------
# Status / Test / Disconnect
# ---------------------------------------------------------------------------

@router.get("/status", response_model=MetaStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    # Platform credentials from .env — the user never configures these
    is_configured = bool(settings.META_APP_ID and settings.META_APP_SECRET)

    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)

    if not connection or not connection.is_active or not connection.credentials:
        return MetaStatusResponse(is_connected=False, is_configured=is_configured)

    is_connected = bool(connection.credentials.get("access_token"))

    return MetaStatusResponse(
        is_connected=is_connected,
        is_configured=is_configured,
        name=connection.config.get("name") if connection.config else None,
        account_id=connection.config.get("user_id") if connection.config else None,
    )


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
    if connection:
        repo.deactivate(connection)
    return {"status": "disconnected"}


@router.post("/test")
async def test_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Meta no conectado")

    access_token = connection.credentials.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token de acceso no encontrado. Conecta tu cuenta primero.")

    try:
        adapter = MetaAdapter(access_token=access_token)
        profile = await adapter.get_user_profile()
        return {"status": "ok", "message": "Conexion exitosa", "data": profile}
    except Exception as e:
        logger.error("meta_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Business Assets
# ---------------------------------------------------------------------------

_ASSET_CHANNEL_TYPES = [
    ChannelType.FACEBOOK_PAGE,
    ChannelType.INSTAGRAM_ACCOUNT,
    ChannelType.META_ADS_ACCOUNT,
]


@router.get("/assets", response_model=MetaAssetsResponse)
async def get_assets(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Returns the list of Meta business assets stored in the DB for this tenant."""
    existing = repo.get_all_by_tenant_and_types(user.tenant_id, _ASSET_CHANNEL_TYPES)
    by_id: dict[str, ChannelConnectionModel] = {
        conn.config.get("asset_id", ""): conn for conn in existing if conn.config
    }

    pages: list[FacebookPageAsset] = []
    instagram_accounts: list[InstagramAccountAsset] = []
    ads_accounts: list[MetaAdsAccountAsset] = []

    for conn in existing:
        cfg = conn.config or {}
        channel = conn.channel_type

        if channel == ChannelType.FACEBOOK_PAGE.value:
            pages.append(FacebookPageAsset(
                page_id=cfg.get("asset_id", ""),
                page_name=cfg.get("page_name", ""),
                category=cfg.get("category"),
                picture_url=cfg.get("picture_url"),
                fan_count=cfg.get("fan_count"),
                instagram_account_id=cfg.get("instagram_account_id"),
                instagram_username=cfg.get("instagram_username"),
                is_active=conn.is_active,
                has_credentials=bool(conn.credentials),
            ))
        elif channel == ChannelType.INSTAGRAM_ACCOUNT.value:
            instagram_accounts.append(InstagramAccountAsset(
                ig_account_id=cfg.get("asset_id", ""),
                ig_username=cfg.get("ig_username", ""),
                profile_picture_url=cfg.get("profile_picture_url"),
                follower_count=cfg.get("follower_count"),
                linked_page_id=cfg.get("linked_page_id"),
                linked_page_name=cfg.get("linked_page_name"),
                is_active=conn.is_active,
                has_credentials=bool(conn.credentials),
            ))
        elif channel == ChannelType.META_ADS_ACCOUNT.value:
            ads_accounts.append(MetaAdsAccountAsset(
                ad_account_id=cfg.get("asset_id", ""),
                ad_account_name=cfg.get("ad_account_name", ""),
                currency=cfg.get("currency"),
                account_status=cfg.get("account_status"),
                is_active=conn.is_active,
                has_credentials=bool(conn.credentials),
            ))

    return MetaAssetsResponse(
        pages=pages,
        instagram_accounts=instagram_accounts,
        ads_accounts=ads_accounts,
    )


@router.post("/assets/sync", response_model=MetaAssetsResponse)
async def sync_assets(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """
    Pulls business assets from Meta API and upserts them in the DB.
    Preserves is_active state for existing assets.
    Returns the refreshed asset list.
    """
    master = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
    if not master or not master.credentials:
        raise HTTPException(status_code=400, detail="Conecta tu cuenta de Meta primero.")

    access_token = master.credentials.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token de acceso no encontrado.")

    adapter = MetaAdapter(access_token=access_token)
    try:
        raw = await adapter.get_business_assets()
    except Exception as e:
        logger.error("meta_sync_assets_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"Error consultando activos de Meta: {e}")

    # Load existing to preserve is_active
    existing = repo.get_all_by_tenant_and_types(user.tenant_id, _ASSET_CHANNEL_TYPES)
    active_map: dict[str, bool] = {
        conn.config.get("asset_id", ""): conn.is_active
        for conn in existing
        if conn.config
    }

    # Upsert pages
    for page in raw["pages"]:
        page_id = page["page_id"]
        page_token = page.pop("page_access_token", None)
        config = {
            "asset_id": page_id,
            "page_name": page["page_name"],
            "category": page.get("category"),
            "picture_url": page.get("picture_url"),
            "fan_count": page.get("fan_count"),
            "instagram_account_id": page.get("instagram_account_id"),
            "instagram_username": page.get("instagram_username"),
            "parent_connection_id": str(master.id),
        }
        credentials = {"access_token": page_token} if page_token else master.credentials
        conn = repo.get_by_asset_id(user.tenant_id, ChannelType.FACEBOOK_PAGE, page_id)
        if conn:
            conn.credentials = credentials
            conn.config = config
            # Don't flip is_active for existing — preserve user choice
            repo.db.commit()
        else:
            repo.upsert(
                tenant_id=user.tenant_id,
                channel_type=ChannelType.FACEBOOK_PAGE,
                credentials=credentials,
                config=config,
            )

    # Upsert Instagram accounts
    for ig in raw["instagram_accounts"]:
        ig_id = ig["ig_account_id"]
        page_token = ig.pop("page_access_token", None)
        config = {
            "asset_id": ig_id,
            "ig_username": ig["ig_username"],
            "profile_picture_url": ig.get("profile_picture_url"),
            "follower_count": ig.get("follower_count"),
            "linked_page_id": ig.get("linked_page_id"),
            "linked_page_name": ig.get("linked_page_name"),
            "parent_connection_id": str(master.id),
        }
        credentials = {"access_token": page_token} if page_token else master.credentials
        conn = repo.get_by_asset_id(user.tenant_id, ChannelType.INSTAGRAM_ACCOUNT, ig_id)
        if conn:
            conn.credentials = credentials
            conn.config = config
            repo.db.commit()
        else:
            repo.upsert(
                tenant_id=user.tenant_id,
                channel_type=ChannelType.INSTAGRAM_ACCOUNT,
                credentials=credentials,
                config=config,
            )

    # Upsert Ad Accounts (no sensitive credentials — uses master token at query time)
    for ad in raw["ads_accounts"]:
        ad_id = ad["ad_account_id"]
        config = {
            "asset_id": ad_id,
            "ad_account_name": ad["ad_account_name"],
            "currency": ad.get("currency"),
            "account_status": ad.get("account_status"),
            "parent_connection_id": str(master.id),
        }
        conn = repo.get_by_asset_id(user.tenant_id, ChannelType.META_ADS_ACCOUNT, ad_id)
        if conn:
            conn.config = config
            repo.db.commit()
        else:
            repo.upsert(
                tenant_id=user.tenant_id,
                channel_type=ChannelType.META_ADS_ACCOUNT,
                credentials={},
                config=config,
            )

    # Return the refreshed asset list
    return await get_assets(user=user, repo=repo)


@router.patch("/assets/{channel_type}/{asset_id}")
async def toggle_asset(
    channel_type: str,
    asset_id: str,
    body: ToggleAssetRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Activates or deactivates a specific Meta asset without revoking the master OAuth."""
    type_map = {ct.value: ct for ct in _ASSET_CHANNEL_TYPES}
    if channel_type not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de activo inválido: {channel_type}. Válidos: {list(type_map.keys())}",
        )

    conn = repo.get_by_asset_id(user.tenant_id, type_map[channel_type], asset_id)
    if not conn:
        raise HTTPException(status_code=404, detail="Activo no encontrado. Sincroniza primero.")

    if body.is_active:
        repo.activate(conn)
    else:
        repo.deactivate(conn)

    return {"status": "updated", "channel_type": channel_type, "asset_id": asset_id, "is_active": body.is_active}
