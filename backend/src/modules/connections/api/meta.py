import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel as PydanticBaseModel
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.context import set_tenant_id
from src.core.database import get_db
from src.modules.connections.api.dependencies.webhook_security import (
    verify_meta_signature,
)
from src.modules.connections.api.dto.common import (
    ConnectionTestResponse,
    SetPrimaryAssetResponse,
    StatusSavedResponse,
    ToggleAssetResponse,
)
from src.modules.connections.api.dto.meta import (
    FacebookPageAsset,
    InstagramAccountAsset,
    MetaAdsAccountAsset,
    MetaAssetsResponse,
    MetaConfigRequest,
    MetaPixelAsset,
    MetaStatusResponse,
    ToggleAssetRequest,
    WhatsAppBusinessAsset,
    WhatsAppPhoneNumber,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.instagram import InstagramChannel
from src.modules.connections.infrastructure.channels.meta import MetaAdapter
from src.modules.connections.infrastructure.models import ChannelConnectionModel
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.sales_agent.application.orchestrator.chat import ChatOrchestrator

router = APIRouter(tags=["meta"])
logger = structlog.get_logger()
orchestrator = ChatOrchestrator()


_ASSET_CHANNEL_TYPES = [
    ChannelType.FACEBOOK_PAGE,
    ChannelType.INSTAGRAM_ACCOUNT,
    ChannelType.META_ADS_ACCOUNT,
    ChannelType.META_PIXEL,
    ChannelType.WHATSAPP_BUSINESS_ACCOUNT,
]


def _upsert_asset(
    repo: ChannelConnectionRepository,
    tenant_id,
    channel_type: ChannelType,
    asset_id: str,
    config: dict,
    credentials: dict,
) -> None:
    """Upsert a single Meta business asset (page, IG, ad account, pixel, WABA)."""
    conn = repo.get_by_asset_id(tenant_id, channel_type, asset_id)
    if conn:
        if credentials:
            conn.credentials = credentials
        conn.config = config
        repo.db.commit()
    else:
        repo.create_asset(
            tenant_id=tenant_id,
            channel_type=channel_type,
            credentials=credentials,
            config=config,
        )


def _sync_pages(repo, tenant_id, raw: dict, master: ChannelConnectionModel) -> None:
    for page in raw.get("pages", []):
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
        _upsert_asset(
            repo,
            tenant_id,
            ChannelType.FACEBOOK_PAGE,
            page_id,
            config,
            credentials,
        )


def _sync_instagram_accounts(
    repo,
    tenant_id,
    raw: dict,
    master: ChannelConnectionModel,
) -> None:
    for ig in raw.get("instagram_accounts", []):
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
        _upsert_asset(
            repo,
            tenant_id,
            ChannelType.INSTAGRAM_ACCOUNT,
            ig_id,
            config,
            credentials,
        )


def _sync_ad_accounts(
    repo,
    tenant_id,
    raw: dict,
    master: ChannelConnectionModel,
) -> None:
    for ad in raw.get("ads_accounts", []):
        ad_id = ad["ad_account_id"]
        config = {
            "asset_id": ad_id,
            "ad_account_name": ad["ad_account_name"],
            "currency": ad.get("currency"),
            "account_status": ad.get("account_status"),
            "parent_connection_id": str(master.id),
        }
        _upsert_asset(repo, tenant_id, ChannelType.META_ADS_ACCOUNT, ad_id, config, {})


def _sync_pixels(repo, tenant_id, raw: dict, master: ChannelConnectionModel) -> None:
    for px in raw.get("pixels", []):
        px_id = px["pixel_id"]
        config = {
            "asset_id": px_id,
            "pixel_name": px["pixel_name"],
            "linked_ad_account_id": px.get("linked_ad_account_id"),
            "parent_connection_id": str(master.id),
        }
        _upsert_asset(repo, tenant_id, ChannelType.META_PIXEL, px_id, config, {})


def _sync_whatsapp_accounts(
    repo,
    tenant_id,
    raw: dict,
    master: ChannelConnectionModel,
) -> None:
    for wa in raw.get("whatsapp_accounts", []):
        waba_id = wa["waba_id"]
        config = {
            "asset_id": waba_id,
            "waba_name": wa["waba_name"],
            "currency": wa.get("currency"),
            "timezone_id": wa.get("timezone_id"),
            "business_id": wa.get("business_id"),
            "business_name": wa.get("business_name"),
            "phone_numbers": wa.get("phone_numbers", []),
            "parent_connection_id": str(master.id),
        }
        _upsert_asset(
            repo,
            tenant_id,
            ChannelType.WHATSAPP_BUSINESS_ACCOUNT,
            waba_id,
            config,
            master.credentials,
        )


def _cleanup_stale_assets(
    repo: ChannelConnectionRepository,
    tenant_id,
    raw: dict,
) -> None:
    """Remove assets from DB that Meta no longer returns (e.g. permissions revoked)."""
    synced_ids = {
        ChannelType.FACEBOOK_PAGE: {p["page_id"] for p in raw.get("pages", [])},
        ChannelType.INSTAGRAM_ACCOUNT: {ig["ig_account_id"] for ig in raw.get("instagram_accounts", [])},
        ChannelType.META_ADS_ACCOUNT: {ad["ad_account_id"] for ad in raw.get("ads_accounts", [])},
        ChannelType.META_PIXEL: {px["pixel_id"] for px in raw.get("pixels", [])},
        ChannelType.WHATSAPP_BUSINESS_ACCOUNT: {wa["waba_id"] for wa in raw.get("whatsapp_accounts", [])},
    }

    existing = repo.get_all_by_tenant_and_types(tenant_id, list(synced_ids.keys()))
    for conn in existing:
        cfg = conn.config or {}
        asset_id = cfg.get("asset_id", "")
        ct = ChannelType(conn.channel_type)
        if asset_id and asset_id not in synced_ids.get(ct, set()):
            logger.info(
                "meta_sync_removing_stale_asset",
                channel_type=ct.value,
                asset_id=asset_id,
                tenant_id=str(tenant_id),
            )
            repo.delete(conn)


async def _sync_assets_for_tenant(
    adapter: MetaAdapter,
    repo: ChannelConnectionRepository,
    tenant_id,
    master: ChannelConnectionModel,
) -> tuple[dict, list[str]]:
    """Fetch business assets from Meta API and store them.

    Returns (raw_assets, warnings).
    Uses create_asset for NEW rows (not upsert) to correctly handle
    multiple assets of the same channel type per tenant.
    """
    warnings: list[str] = []

    # Check token permissions for diagnostics
    try:
        permissions = await adapter.get_token_permissions()
        logger.info(
            "meta_sync_token_permissions",
            tenant_id=str(tenant_id),
            permissions=permissions,
        )
        if "instagram_basic" not in permissions:
            warnings.append(
                "El token no tiene el permiso instagram_basic. "
                "Agréguelo en la configuración de Facebook Login for Business y reconecte.",
            )
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("meta_sync_permissions_check_failed", error=str(e))

    raw = await adapter.get_business_assets()

    _sync_pages(repo, tenant_id, raw, master)
    _sync_instagram_accounts(repo, tenant_id, raw, master)
    _sync_ad_accounts(repo, tenant_id, raw, master)
    _sync_pixels(repo, tenant_id, raw, master)
    _sync_whatsapp_accounts(repo, tenant_id, raw, master)
    _cleanup_stale_assets(repo, tenant_id, raw)

    # Warn if pages exist but none have IG linked
    if raw.get("pages") and not raw.get("instagram_accounts"):
        warnings.append(
            "Ninguna de tus Pages tiene una cuenta de Instagram Business/Creator vinculada. "
            "Verifica que tu cuenta de IG sea profesional y esté vinculada a una Page.",
        )

    return raw, warnings


def _resolve_primary_asset(
    assets: list[ChannelConnectionModel],
    preferred_id: str | None,
) -> ChannelConnectionModel | None:
    """Find the primary asset by preferred ID, falling back to first active."""
    if preferred_id:
        match = next(
            (a for a in assets if (a.config or {}).get("asset_id") == preferred_id),
            None,
        )
        if match:
            return match
    return assets[0] if assets else None


def _flatten_page(
    page: ChannelConnectionModel | None,
    master: ChannelConnectionModel,
) -> tuple[dict, dict]:
    """Extract credentials/config updates from the resolved primary page."""
    if not page:
        return {}, {}
    page_cfg = page.config or {}
    page_creds = page.credentials or {}
    creds = {
        "page_id": page_cfg.get("asset_id"),
        "page_access_token": page_creds.get(
            "access_token",
            master.credentials.get("access_token"),
        ),
    }
    config = {
        "tracked_page_name": page_cfg.get("page_name"),
        "tracked_page_id": page_cfg.get("asset_id"),
    }
    return creds, config


def _flatten_ig(ig: ChannelConnectionModel | None) -> tuple[dict, dict]:
    """Extract credentials/config updates from the resolved primary IG account."""
    if not ig:
        return {}, {}
    ig_cfg = ig.config or {}
    creds = {"instagram_account_id": ig_cfg.get("asset_id")}
    config = {
        "tracked_ig_username": ig_cfg.get("ig_username"),
        "tracked_ig_id": ig_cfg.get("asset_id"),
    }
    return creds, config


def _flatten_ad_account(ad: ChannelConnectionModel | None) -> tuple[dict, dict]:
    """Extract credentials/config updates from the resolved primary ad account."""
    if not ad:
        return {}, {}
    ad_cfg = ad.config or {}
    creds: dict = {"ad_account_id": ad_cfg.get("asset_id")}
    config: dict = {
        "tracked_ad_account_name": ad_cfg.get("ad_account_name"),
        "tracked_ad_account_id": ad_cfg.get("asset_id"),
    }
    if ad_cfg.get("currency"):
        creds["currency"] = ad_cfg["currency"]
    return creds, config


def _flatten_asset_ids_to_master(
    repo: ChannelConnectionRepository,
    tenant_id,
    master: ChannelConnectionModel,
) -> dict:
    """Resolve primary assets and flatten their IDs into the master META connection."""
    master_config = master.config or {}

    children = repo.get_all_by_tenant_and_types(
        tenant_id,
        [
            ChannelType.FACEBOOK_PAGE,
            ChannelType.INSTAGRAM_ACCOUNT,
            ChannelType.META_ADS_ACCOUNT,
        ],
    )

    # Group by type
    by_type: dict[str, list] = {}
    for c in children:
        if c.is_active:
            by_type.setdefault(c.channel_type, []).append(c)

    page = _resolve_primary_asset(
        by_type.get(ChannelType.FACEBOOK_PAGE.value, []),
        master_config.get("primary_page_id"),
    )
    ig = _resolve_primary_asset(
        by_type.get(ChannelType.INSTAGRAM_ACCOUNT.value, []),
        master_config.get("primary_ig_id"),
    )
    ad = _resolve_primary_asset(
        by_type.get(ChannelType.META_ADS_ACCOUNT.value, []),
        master_config.get("primary_ad_account_id"),
    )

    creds_update: dict = {}
    config_update: dict = {}

    page_c, page_cfg = _flatten_page(page, master)
    ig_c, ig_cfg = _flatten_ig(ig)
    ad_c, ad_cfg = _flatten_ad_account(ad)

    creds_update.update(page_c)
    creds_update.update(ig_c)
    creds_update.update(ad_c)
    config_update.update(page_cfg)
    config_update.update(ig_cfg)
    config_update.update(ad_cfg)

    if creds_update:
        existing_creds = dict(master.credentials) if master.credentials else {}
        existing_creds.update(creds_update)
        repo.update_credentials(master, existing_creds)

    if config_update:
        repo.update_config(master, config_update)

    logger.info(
        "meta_flatten_asset_ids",
        tenant_id=str(tenant_id),
        page_id=creds_update.get("page_id"),
        ig_id=creds_update.get("instagram_account_id"),
        ad_id=creds_update.get("ad_account_id"),
    )

    return config_update


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
    verify_token = settings.META_VERIFY_TOKEN
    if not verify_token:
        raise HTTPException(
            status_code=500,
            detail="META_VERIFY_TOKEN not configured on server",
        )
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
        ["facebook_page", "instagram_account", "meta", "instagram"],
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
        logger.exception("meta_webhook_process_error", error=str(e))

    return {"status": "processed"}


# ---------------------------------------------------------------------------
# Configuration (app_id / app_secret per-tenant)
# ---------------------------------------------------------------------------


@router.put("/configure", response_model=StatusSavedResponse)
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
    redirect_uri: str | None = None,
    user: User = Depends(get_current_user),
):
    if not redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI is required")

    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Meta no configurado en el servidor.",
        )

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
    logger.info(
        "meta_oauth_callback_start",
        tenant_id=str(user.tenant_id),
        redirect_uri=redirect_uri,
        code_length=len(code) if code else 0,
    )

    adapter = MetaAdapter()

    try:
        creds_data = await adapter.exchange_code(code, redirect_uri)
        logger.info(
            "meta_oauth_code_exchange_ok",
            tenant_id=str(user.tenant_id),
            has_access_token=bool(creds_data.get("access_token")),
        )
    except Exception as e:
        logger.exception(
            "meta_oauth_exchange_failed",
            error=str(e),
            tenant_id=str(user.tenant_id),
        )
        raise HTTPException(
            status_code=400,
            detail="Error de autenticacion con Meta",
        ) from e

    try:
        adapter_with_token = MetaAdapter(access_token=creds_data.get("access_token"))
        profile = await adapter_with_token.get_user_profile()
        user_id = profile.get("id")
        name = profile.get("name")
        if not user_id:
            msg = "User ID not found in profile"
            raise ValueError(msg)  # noqa: TRY301
        logger.info(
            "meta_oauth_profile_ok",
            tenant_id=str(user.tenant_id),
            meta_user_id=user_id,
            meta_name=name,
        )
    except Exception as e:
        logger.exception(
            "meta_oauth_profile_failed",
            error=str(e),
            tenant_id=str(user.tenant_id),
        )
        raise HTTPException(
            status_code=400,
            detail="No se pudo obtener el perfil de Meta.",
        ) from e

    # Log and store granted permissions for diagnostics
    granted_permissions: list[str] = []
    try:
        granted_permissions = await adapter_with_token.get_token_permissions()
        logger.info(
            "meta_oauth_granted_permissions",
            tenant_id=str(user.tenant_id),
            permissions=granted_permissions,
        )
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("meta_oauth_permissions_fetch_failed", error=str(e))

    config = {
        "user_id": user_id,
        "name": name,
        "granted_permissions": granted_permissions,
    }
    master = repo.upsert(
        tenant_id=user.tenant_id,
        channel_type=ChannelType.META,
        credentials=creds_data,
        config=config,
    )
    logger.info(
        "meta_oauth_upsert_complete",
        tenant_id=str(user.tenant_id),
        is_active=master.is_active,
        master_id=str(master.id),
        channel_type=master.channel_type,
    )

    # Verification read-back: confirm DB write succeeded
    verification = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
    if verification:
        logger.info(
            "meta_oauth_verify_readback",
            tenant_id=str(user.tenant_id),
            readback_is_active=verification.is_active,
            readback_has_token=bool(
                verification.credentials.get("access_token") if verification.credentials else False,
            ),
            readback_id=str(verification.id),
        )
    else:
        logger.error(
            "meta_oauth_verify_readback_failed",
            tenant_id=str(user.tenant_id),
            detail="Connection not found after upsert",
        )

    # Auto-sync business assets after successful OAuth
    assets_synced = False
    try:
        raw, _warnings = await _sync_assets_for_tenant(
            adapter_with_token,
            repo,
            user.tenant_id,
            master,
        )
        assets_synced = True
        logger.info(
            "meta_oauth_auto_sync_ok",
            tenant_id=str(user.tenant_id),
            pages=len(raw.get("pages", [])),
            instagram=len(raw.get("instagram_accounts", [])),
            ads=len(raw.get("ads_accounts", [])),
        )
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning(
            "meta_oauth_auto_sync_failed",
            error=str(e),
            tenant_id=str(user.tenant_id),
        )

    # Flatten primary asset IDs to master for ETL
    try:
        _flatten_asset_ids_to_master(repo, user.tenant_id, master)
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("meta_flatten_after_oauth_failed", error=str(e))

    return {
        "status": "connected",
        "is_connected": True,
        "profile": profile,
        "assets_synced": assets_synced,
    }


# ---------------------------------------------------------------------------
# Primary Asset Selection
# ---------------------------------------------------------------------------


class SetPrimaryAssetRequest(PydanticBaseModel):
    asset_type: str  # "facebook_page", "instagram_account", "meta_ads_account"
    asset_id: str


@router.put("/primary-asset", response_model=SetPrimaryAssetResponse)
async def set_primary_asset(
    body: SetPrimaryAssetRequest,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Set the primary asset for analytics tracking."""
    type_map = {
        "facebook_page": "primary_page_id",
        "instagram_account": "primary_ig_id",
        "meta_ads_account": "primary_ad_account_id",
    }
    config_key = type_map.get(body.asset_type)
    if not config_key:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de activo inválido: {body.asset_type}. Válidos: {list(type_map.keys())}",
        )

    master = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
    if not master:
        raise HTTPException(
            status_code=404,
            detail="Conecta tu cuenta de Meta primero.",
        )

    # Save primary selection to master config
    repo.update_config(master, {config_key: body.asset_id})

    # Re-flatten with new primary
    _flatten_asset_ids_to_master(repo, user.tenant_id, master)

    return {
        "status": "primary_set",
        "asset_type": body.asset_type,
        "asset_id": body.asset_id,
    }


# ---------------------------------------------------------------------------
# Status / Test / Disconnect
# ---------------------------------------------------------------------------


@router.get("/status", response_model=MetaStatusResponse)
async def get_status(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
    debug: bool = Query(
        default=False,
        description="Include diagnostic info in response",
    ),
):
    # Platform credentials from .env — the user never configures these
    is_configured = bool(settings.META_APP_ID and settings.META_APP_SECRET)

    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)

    if not connection or not connection.is_active or not connection.credentials:
        result: dict = MetaStatusResponse(
            is_connected=False,
            is_configured=is_configured,
        ).model_dump()
        if debug:
            result["debug"] = {
                "connection_exists": connection is not None,
                "is_active": connection.is_active if connection else None,
                "has_credentials": bool(connection.credentials) if connection else False,
                "updated_at": str(connection.updated_at) if connection and hasattr(connection, "updated_at") else None,
            }
        return result

    is_connected = bool(connection.credentials.get("access_token"))

    result = MetaStatusResponse(
        is_connected=is_connected,
        is_configured=is_configured,
        name=connection.config.get("name") if connection.config else None,
        account_id=connection.config.get("user_id") if connection.config else None,
        config=connection.config,
    ).model_dump()

    if debug:
        result["debug"] = {
            "connection_exists": True,
            "is_active": connection.is_active,
            "has_credentials": bool(connection.credentials),
            "has_access_token": bool(connection.credentials.get("access_token")),
            "updated_at": str(connection.updated_at) if hasattr(connection, "updated_at") else None,
            "connection_id": str(connection.id),
        }

    return result


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
    if connection:
        # Deactivate all child asset connections first
        child_assets = repo.get_all_by_tenant_and_types(
            user.tenant_id,
            _ASSET_CHANNEL_TYPES,
        )
        for asset in child_assets:
            repo.deactivate(asset)
        # Then deactivate master
        repo.deactivate(connection)
        logger.info(
            "meta_disconnect_complete",
            tenant_id=str(user.tenant_id),
            child_assets_deactivated=len(child_assets),
        )
    return {"status": "disconnected"}


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    connection = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)

    if not connection or not connection.credentials:
        raise HTTPException(status_code=400, detail="Meta no conectado")

    access_token = connection.credentials.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Token de acceso no encontrado. Conecta tu cuenta primero.",
        )

    try:
        adapter = MetaAdapter(access_token=access_token)
        profile = await adapter.get_user_profile()
    except Exception as e:
        logger.exception("meta_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}

    else:
        return {"status": "ok", "message": "Conexion exitosa", "data": profile}


# ---------------------------------------------------------------------------
# Business Assets
# ---------------------------------------------------------------------------


@router.get("/assets", response_model=MetaAssetsResponse)
async def get_assets(
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
):
    """Returns the list of Meta business assets stored in the DB for this tenant."""
    existing = repo.get_all_by_tenant_and_types(user.tenant_id, _ASSET_CHANNEL_TYPES)
    _by_id: dict[str, ChannelConnectionModel] = {
        conn.config.get("asset_id", ""): conn for conn in existing if conn.config
    }

    pages: list[FacebookPageAsset] = []
    instagram_accounts: list[InstagramAccountAsset] = []
    ads_accounts: list[MetaAdsAccountAsset] = []
    pixels: list[MetaPixelAsset] = []
    whatsapp_accounts: list[WhatsAppBusinessAsset] = []

    for conn in existing:
        cfg = conn.config or {}
        channel = conn.channel_type

        if channel == ChannelType.FACEBOOK_PAGE.value:
            pages.append(
                FacebookPageAsset(
                    page_id=cfg.get("asset_id", ""),
                    page_name=cfg.get("page_name", ""),
                    category=cfg.get("category"),
                    picture_url=cfg.get("picture_url"),
                    fan_count=cfg.get("fan_count"),
                    instagram_account_id=cfg.get("instagram_account_id"),
                    instagram_username=cfg.get("instagram_username"),
                    is_active=conn.is_active,
                    has_credentials=bool(conn.credentials),
                ),
            )
        elif channel == ChannelType.INSTAGRAM_ACCOUNT.value:
            instagram_accounts.append(
                InstagramAccountAsset(
                    ig_account_id=cfg.get("asset_id", ""),
                    ig_username=cfg.get("ig_username", ""),
                    profile_picture_url=cfg.get("profile_picture_url"),
                    follower_count=cfg.get("follower_count"),
                    linked_page_id=cfg.get("linked_page_id"),
                    linked_page_name=cfg.get("linked_page_name"),
                    is_active=conn.is_active,
                    has_credentials=bool(conn.credentials),
                ),
            )
        elif channel == ChannelType.META_ADS_ACCOUNT.value:
            ads_accounts.append(
                MetaAdsAccountAsset(
                    ad_account_id=cfg.get("asset_id", ""),
                    ad_account_name=cfg.get("ad_account_name", ""),
                    currency=cfg.get("currency"),
                    account_status=cfg.get("account_status"),
                    is_active=conn.is_active,
                    has_credentials=bool(conn.credentials),
                ),
            )
        elif channel == ChannelType.META_PIXEL.value:
            pixels.append(
                MetaPixelAsset(
                    pixel_id=cfg.get("asset_id", ""),
                    pixel_name=cfg.get("pixel_name", ""),
                    linked_ad_account_id=cfg.get("linked_ad_account_id"),
                    is_active=conn.is_active,
                    has_credentials=bool(conn.credentials),
                ),
            )
        elif channel == ChannelType.WHATSAPP_BUSINESS_ACCOUNT.value:
            whatsapp_accounts.append(
                WhatsAppBusinessAsset(
                    waba_id=cfg.get("asset_id", ""),
                    waba_name=cfg.get("waba_name", ""),
                    currency=cfg.get("currency"),
                    timezone_id=cfg.get("timezone_id"),
                    business_id=cfg.get("business_id"),
                    business_name=cfg.get("business_name"),
                    phone_numbers=[WhatsAppPhoneNumber(**ph) for ph in cfg.get("phone_numbers", [])],
                    is_active=conn.is_active,
                    has_credentials=bool(conn.credentials),
                ),
            )

    return MetaAssetsResponse(
        pages=pages,
        instagram_accounts=instagram_accounts,
        ads_accounts=ads_accounts,
        pixels=pixels,
        whatsapp_accounts=whatsapp_accounts,
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
        raise HTTPException(
            status_code=400,
            detail="Conecta tu cuenta de Meta primero.",
        )

    access_token = master.credentials.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token de acceso no encontrado.")

    adapter = MetaAdapter(access_token=access_token)
    try:
        _raw, warnings = await _sync_assets_for_tenant(
            adapter,
            repo,
            user.tenant_id,
            master,
        )
    except Exception as e:
        logger.exception("meta_sync_assets_failed", error=str(e))
        raise HTTPException(
            status_code=502,
            detail=f"Error consultando activos de Meta: {e}",
        ) from e

    # Flatten primary asset IDs to master for ETL
    try:
        _flatten_asset_ids_to_master(repo, user.tenant_id, master)
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("meta_flatten_after_sync_failed", error=str(e))

    # Return the refreshed asset list with warnings
    response = await get_assets(user=user, repo=repo)
    if warnings:
        response.warnings = warnings
    return response


@router.patch("/assets/{channel_type}/{asset_id}", response_model=ToggleAssetResponse)
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
        raise HTTPException(
            status_code=404,
            detail="Activo no encontrado. Sincroniza primero.",
        )

    if body.is_active:
        repo.activate(conn)
    else:
        repo.deactivate(conn)

    # Re-flatten if toggling might affect primary selection
    try:
        master = repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)
        if master:
            _flatten_asset_ids_to_master(repo, user.tenant_id, master)
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("meta_flatten_after_toggle_failed", error=str(e))

    return {
        "status": "updated",
        "channel_type": channel_type,
        "asset_id": asset_id,
        "is_active": body.is_active,
    }
