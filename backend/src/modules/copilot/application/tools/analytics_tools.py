"""Analytics tools — copilot access to Growth Studio KPIs and ETL refresh.

Story 2B T-1 — growth-studio-actions-schemas-real.
Replaces legacy ``get_funnel_metrics`` (removed in this commit per 03-arch § 2.1).

3 new tools:
- ``get_stage_metrics``    — stage overview (Tier 1) with KPI serialization
- ``get_channel_overview`` — per-channel dashboard KPIs
- ``trigger_etl_refresh``  — ETL re-extraction with rate-limit + confirm guard

All tools:
- Source ``tenant_id`` from ``src.core.context.get_tenant_id()`` (never from payload)
- Return JSON strings (LangChain tool contract)
- Return structured errors on failure (no raw exception strings exposed)
- Are registered in ``ANALYTICS_TOOLS`` (consumed by ``registry.py``)
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
from typing import TYPE_CHECKING, Any, cast

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.modules.copilot.application.tools._analytics_inputs import (
    ChannelOverviewParams,
    StageFilterParams,
    TriggerEtlRefreshParams,
)

if TYPE_CHECKING:
    from src.modules.analytics.application.services.etl_refresh_guard import (
        EtlRefreshGuard,
        GuardDecision,
    )

logger = structlog.get_logger(__name__)

STAGE_SLUG_MAP: dict[str, str] = {
    "atraccion-captura": "attraction",
    "nutricion-oportunidad": "nurture",
    "ventas": "sales",
    "adopcion": "adoption",
    "expansion-evangelizacion": "evangelization",
}

PERIOD_MAP: dict[str, str] = {
    "7d": "last_7_days",
    "30d": "last_30_days",
    "90d": "last_90_days",
}

_CHANNEL_BREAKDOWN_LIMIT = 10

_SLUG_TO_PROVIDER: dict[str, str] = {
    "meta-ads": "meta",
    "yt-organic": "youtube",
    "email-nurture": "email",
    "ig-organic": "instagram",
    "website-total": "ga4",
}


async def _call_stage_overview(
    tenant_id: object,
    stage: str,
    period: str,
) -> object:
    """Call StageOverviewService and return a StageOverviewDTO.

    Isolated as a top-level async function so tests can patch it cleanly
    without instantiating real Redis / DB dependencies.
    """
    from src.core.database import SessionLocal
    from src.modules.analytics.application.services.stage_services.overview_stage import (
        StageOverviewService,
    )

    db = SessionLocal()
    try:
        service = StageOverviewService(db=db)
        return await service.get_stage_overview(str(tenant_id), stage, period)
    finally:
        db.close()


async def _call_channel_dashboard(
    tenant_id: object,
    channel_slug: str,
) -> object:
    """Call ChannelDashboardService and return a ChannelDashboardDTO.

    Isolated as a top-level async function so tests can patch it cleanly.
    """
    from src.core.database import SessionLocal
    from src.modules.analytics.application.services.channel_dashboard_service import (
        ChannelDashboardService,
    )

    db = SessionLocal()
    try:
        service = ChannelDashboardService(db=db)
        return await service.get_dashboard(tenant_id, channel_slug)  # type: ignore[arg-type]
    finally:
        db.close()


def _get_etl_refresh_guard() -> EtlRefreshGuard:
    """Factory: return an EtlRefreshGuard bound to the app Redis client.

    Isolated as a top-level sync function so tests can patch it cleanly.
    Returns a guard with a no-op config repo when Redis is unavailable
    (guard soft-fails open per tessl__graceful-degradation).
    """
    from src.modules.analytics.application.services.etl_refresh_guard import (
        EtlRefreshGuard,
    )

    class _NullConfigRepo:
        async def get_limit(self, tenant_id: object, channel_slug: str) -> int | None:
            return None

    try:
        from src.core.redis import get_redis_client

        redis_client = get_redis_client()
    except Exception:  # noqa: BLE001 — fail-open per graceful-degradation
        logger.warning("etl_refresh_guard_redis_unavailable_no_client")
        redis_client = None

    return EtlRefreshGuard(
        redis_client=redis_client,
        channel_config_repo=_NullConfigRepo(),
    )


async def _call_etl_refresh(
    tenant_id: object,
    channel_slug: str,
) -> dict[str, Any]:
    """Call the ETL service to trigger re-extraction for a channel.

    Isolated as a top-level async function so tests can patch it cleanly.
    Returns a dict with at minimum ``{"status": "...", "run_id": "..."}``.
    """
    from src.modules.analytics.infrastructure.providers.connection_port_impl import (
        ConnectionPortImpl,
    )

    from src.core.database import SessionLocal
    from src.modules.analytics.application.services.etl_service import ETLService
    from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache

    provider_name = _SLUG_TO_PROVIDER.get(channel_slug)
    if not provider_name:
        return {"status": "error", "error": f"Canal no reconocido: {channel_slug}"}

    db = SessionLocal()
    try:
        connection_port = ConnectionPortImpl(db)
        cache = MetricsCache(redis_client=None)  # best-effort; fail-open per graceful-degradation
        etl = ETLService(db, connection_port=connection_port, cache=cache)
        run = await etl.run_extraction(tenant_id, provider_name)  # type: ignore[arg-type]
        if run is None:
            return {"status": "queued", "run_id": None}
        return {"status": "ok", "run_id": str(run.id)}
    finally:
        db.close()


def _run_async(coro: object) -> object:
    """Run a coroutine from a sync context (tool body).

    Uses ``asyncio.run()`` when no event loop is running (tests, workers).
    Uses a thread executor when called from an existing async loop (FastAPI
    request context) to avoid ``RuntimeError: This event loop is already running``.
    """
    try:
        asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()  # type: ignore[arg-type]
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]


@tool(args_schema=StageFilterParams)
def get_stage_metrics(
    stage: str,
    channel: str | None = None,
    period: str = "30d",
) -> str:
    """Consulta métricas de un stage específico del funnel de Growth Studio.

    Usa este tool cuando el usuario pregunte por el rendimiento de una etapa
    del funnel (atracción, nutrición, ventas, adopción, expansión).

    Args:
        stage: Etapa del funnel. Valores válidos:
            atraccion-captura, nutricion-oportunidad, ventas, adopcion,
            expansion-evangelizacion.
        channel: (Opcional) Slug de canal para filtrar. Valores válidos:
            meta-ads, yt-organic, email-nurture, ig-organic, website-total.
        period: Período a consultar. Valores válidos: 7d, 30d, 90d.
            Por defecto: 30d.

    Returns:
        JSON con stage_name, period, kpis, channel_breakdown, tier_used,
        truncated y ui_action para renderizado en el copilot.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "no_tenant", "mensaje": "No se pudo determinar el tenant."})

    api_stage = STAGE_SLUG_MAP.get(stage, stage)
    api_period = PERIOD_MAP.get(period, "last_30_days")

    try:
        overview = _run_async(_call_stage_overview(tenant_id, api_stage, api_period))

        header_kpis = getattr(overview, "header_kpis", {}) or {}
        if isinstance(header_kpis, dict):
            kpis_list = [{"slug": name, "value": value} for name, value in header_kpis.items() if value is not None]
        else:
            kpis_list = [
                {
                    "slug": getattr(kpi, "name", str(kpi)),
                    "value": getattr(kpi, "value", 0),
                }
                for kpi in header_kpis
            ]

        _ch_real = getattr(overview, "channel_list", None)
        _ch_mock = getattr(overview, "channels", None)
        if isinstance(_ch_real, list):
            channel_list = _ch_real
        elif isinstance(_ch_mock, list):
            channel_list = _ch_mock
        else:
            channel_list = []

        channels_data = [
            {
                "channel": getattr(ch, "slug", str(ch)),
                "value": getattr(ch.headline_kpi, "value", None) if getattr(ch, "headline_kpi", None) else None,
            }
            for ch in channel_list
        ]

        truncated = len(channels_data) > _CHANNEL_BREAKDOWN_LIMIT
        channel_breakdown = channels_data[:_CHANNEL_BREAKDOWN_LIMIT]

        logger.info(
            "analytics_tool_stage_metrics",
            tenant_id=str(tenant_id),
            stage=stage,
            period=period,
            kpi_count=len(kpis_list),
            tier_used=1,
        )

        return json.dumps(
            {
                "stage_name": api_stage,
                "period": api_period,
                "kpis": kpis_list,
                "channel_breakdown": channel_breakdown,
                "tier_used": 1,
                "truncated": truncated,
                "ui_action": {
                    "type": "growth.stage-metrics",
                    "stage": api_stage,
                    "period": api_period,
                },
            }
        )

    except Exception as exc:  # noqa: BLE001 — tools must never leak raw exceptions to the LLM
        logger.warning(
            "analytics_tool_stage_metrics_error",
            tenant_id=str(tenant_id),
            stage=stage,
            error=str(exc),
        )
        return json.dumps({"error": "service_error", "mensaje": "No se pudieron obtener las métricas."})


@tool(args_schema=ChannelOverviewParams)
def get_channel_overview(channel: str) -> str:
    """Consulta el dashboard de un canal específico de Growth Studio.

    Usa este tool cuando el usuario pregunte por el rendimiento de un canal
    específico (Meta Ads, YouTube, Email, Instagram, etc.).

    Args:
        channel: Slug del canal. Valores válidos:
            meta-ads, yt-organic, email-nurture, ig-organic, website-total.

    Returns:
        JSON con channel_name, dashboard_kpis, period y ui_action para
        renderizado en el copilot.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "no_tenant", "mensaje": "No se pudo determinar el tenant."})

    try:
        dashboard = _run_async(_call_channel_dashboard(tenant_id, channel))

        channel_name = getattr(dashboard, "channel_name", channel)
        period = getattr(dashboard, "period", "30d")
        raw_kpis = getattr(dashboard, "kpis", []) or []

        kpis_list = [
            {
                "slug": getattr(kpi, "name", str(kpi)),
                "value": getattr(kpi, "value", 0),
                "unit": getattr(kpi, "unit", None),
            }
            for kpi in raw_kpis
        ]

        logger.info(
            "analytics_tool_channel_overview",
            tenant_id=str(tenant_id),
            channel=channel,
            kpi_count=len(kpis_list),
        )

        return json.dumps(
            {
                "channel_name": channel_name,
                "dashboard_kpis": kpis_list,
                "period": period,
                "ui_action": {
                    "type": "growth.channel-overview",
                    "channel": channel,
                },
            }
        )

    except Exception as exc:  # noqa: BLE001 — tools must never leak raw exceptions to the LLM
        logger.warning(
            "analytics_tool_channel_overview_error",
            tenant_id=str(tenant_id),
            channel=channel,
            error=str(exc),
        )
        return json.dumps({"error": "service_error", "mensaje": "No se pudo obtener el dashboard del canal."})


@tool(args_schema=TriggerEtlRefreshParams)
def trigger_etl_refresh(channel: str, confirmed: bool = False) -> str:
    """Dispara una nueva extracción ETL para el canal indicado.

    Usa este tool cuando el usuario pida refrescar datos de un canal específico.
    Si el usuario ya refrescó una vez en la última hora, se requerirá confirmación
    explícita. El límite es 3 refrescos por hora por canal.

    Args:
        channel: Slug del canal a refrescar. Valores válidos:
            meta-ads, yt-organic, email-nurture, ig-organic, website-total.
        confirmed: Indica si el usuario confirmó explícitamente un refresh
            adicional. Por defecto: False.

    Returns:
        JSON con status (queued | requires_confirmation), current_count,
        limit, y retry_after_seconds si está bloqueado.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return json.dumps({"error": "no_tenant", "mensaje": "No se pudo determinar el tenant."})

    try:
        guard = _get_etl_refresh_guard()
        decision = cast("GuardDecision", _run_async(guard.check(tenant_id, channel, confirmed=confirmed)))

        if not decision.allowed:
            if decision.requires_confirmation:
                return json.dumps(
                    {
                        "status": "requires_confirmation",
                        "current_count": decision.current_count,
                        "limit": decision.limit,
                        "mensaje": (
                            "Ya iniciaste un refresh para este canal en la última hora. "
                            "Confirma si deseas ejecutar otro."
                        ),
                    }
                )
            return json.dumps(
                {
                    "error": "rate_limit_exceeded",
                    "current_count": decision.current_count,
                    "limit": decision.limit,
                    "retry_after_seconds": decision.retry_after_seconds,
                    "mensaje": (
                        f"Límite de refreshes alcanzado ({decision.current_count}/{decision.limit} "
                        f"por hora). Intenta de nuevo en {decision.retry_after_seconds or 0} segundos."
                    ),
                }
            )

        result = cast("dict[str, Any]", _run_async(_call_etl_refresh(tenant_id, channel)))

        logger.info(
            "analytics_tool_etl_refresh_queued",
            tenant_id=str(tenant_id),
            channel=channel,
            confirmed=confirmed,
            current_count=decision.current_count,
        )

        return json.dumps(
            {
                "status": result.get("status", "queued"),
                "run_id": result.get("run_id"),
                "current_count": decision.current_count,
                "limit": decision.limit,
                "channel": channel,
            }
        )

    except Exception as exc:  # noqa: BLE001 — tools must never leak raw exceptions to the LLM
        logger.warning(
            "analytics_tool_etl_refresh_error",
            tenant_id=str(tenant_id) if tenant_id else "unknown",
            channel=channel,
            error=str(exc),
        )
        return json.dumps({"error": "service_error", "mensaje": "No se pudo iniciar la extracción ETL."})


ANALYTICS_TOOLS = [get_stage_metrics, get_channel_overview, trigger_etl_refresh]
