"""Email Intelligence Hub dashboard service.

Source-agnostic: reads from official_metrics table only.
Never imports provider-specific code.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import TYPE_CHECKING

import structlog
from pydantic import ValidationError
from sqlalchemy import String, cast, func, select

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    BenchmarkRangeDTO,
    FunnelStepDTO,
    MetricKpiDTO,
    MetricTimeSeriesDTO,
    TimeSeriesDataPointDTO,
)
from src.modules.analytics.application.dto.email_dashboard_dto import (
    ActivityHeatmapCellDTO,
    AutomationStepDTO,
    BounceBreakdownDTO,
    EmailAudienceResponseDTO,
    EmailAutomationDTO,
    EmailAutomationsResponseDTO,
    EmailCampaignDTO,
    EmailCampaignsResponseDTO,
    EmailCampaignSummaryDTO,
    EmailDashboardDTO,
    EmailEngagementSegmentDTO,
    EmailGrowthResponseDTO,
    EmailHealthResponseDTO,
    EmailHealthScoreDTO,
    EmailHealthSubScoreDTO,
    EmailTypePerformanceDTO,
    EngagementDecayDTO,
)
from src.modules.analytics.domain.industry_benchmarks import (
    IndustryCategory,
    get_benchmarks,
)
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

CHANNEL_SLUG = "email-nurture"
CAPTURE_SLUG = "email-capture"

# Period mapping
PERIOD_DAYS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90}


# -- Pure functions (testable without DB) --------------------------------------


def compute_health_score(
    open_rate: float,
    benchmark_open_rate: float,
    ctor: float,
    benchmark_ctor: float,
    deliverability_rate: float,
    list_growth_rate: float,
) -> EmailHealthScoreDTO:
    """Compute composite email health score 0-100."""

    def _score_ratio(value: float, benchmark: float) -> int:
        ratio = value / benchmark if benchmark > 0 else 0
        if ratio >= 1.1:
            return 100
        if ratio >= 0.9:
            return 80
        if ratio >= 0.7:
            return 60
        if ratio >= 0.5:
            return 40
        return 20

    def _score_color(score: int) -> str:
        if score >= 70:
            return "green"
        if score >= 50:
            return "yellow"
        return "red"

    engagement_score = _score_ratio(open_rate, benchmark_open_rate)
    contenido_score = _score_ratio(ctor, benchmark_ctor)

    if deliverability_rate >= 97:
        delivery_score = 100
    elif deliverability_rate >= 95:
        delivery_score = 80
    elif deliverability_rate >= 90:
        delivery_score = 60
    elif deliverability_rate >= 85:
        delivery_score = 40
    else:
        delivery_score = 20

    if list_growth_rate >= 5:
        growth_score = 100
    elif list_growth_rate >= 2:
        growth_score = 80
    elif list_growth_rate >= 0:
        growth_score = 60
    elif list_growth_rate >= -2:
        growth_score = 40
    else:
        growth_score = 20

    total = int(
        engagement_score * 0.30
        + delivery_score * 0.30
        + growth_score * 0.20
        + contenido_score * 0.20
    )

    sub_scores = [
        EmailHealthSubScoreDTO(
            area="engagement",
            label="Engagement",
            score=engagement_score,
            color=_score_color(engagement_score),
        ),
        EmailHealthSubScoreDTO(
            area="entregabilidad",
            label="Entregabilidad",
            score=delivery_score,
            color=_score_color(delivery_score),
        ),
        EmailHealthSubScoreDTO(
            area="crecimiento",
            label="Crecimiento",
            score=growth_score,
            color=_score_color(growth_score),
        ),
        EmailHealthSubScoreDTO(
            area="contenido",
            label="Contenido",
            score=contenido_score,
            color=_score_color(contenido_score),
        ),
    ]

    return EmailHealthScoreDTO(total=total, sub_scores=sub_scores)


def classify_engagement_segment(
    open_rate: float, click_rate: float, days_inactive: int
) -> str:
    """Classify a subscriber segment based on engagement metrics."""
    if days_inactive >= 60:
        return "dormidos"
    if days_inactive >= 30 or open_rate < 15:
        return "en_riesgo"
    if open_rate >= 50 and click_rate >= 5:
        return "champions"
    return "activos"


# -- Service class -------------------------------------------------------------


class EmailDashboardService:
    """Source-agnostic email dashboard service.

    Reads exclusively from official_metrics -- never imports provider code.
    """

    def __init__(self, db: Session) -> None:
        self._repo = OfficialMetricsRepository(db)
        self._db = db

    # -- Main dashboard (sidebar + panorama) -----------------------------------

    async def get_dashboard(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailDashboardDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        # Current and previous period metrics
        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, prev_start, prev_end
        )

        # Capture metrics for subscriber data
        capture = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end
        )

        # Daily data for time series
        ts_metrics = [
            "emails_sent",
            "open_rate",
            "click_rate",
            "click_to_open_rate",
            "unique_opens",
            "unique_clicks",
            "hard_bounces",
            "soft_bounces",
            "unsubscribes",
            "forwards",
            "active_subscribers",
            "new_subscribers",
        ]
        daily = self._repo.get_channel_daily_metrics(
            tenant_id, CHANNEL_SLUG, ts_metrics, start, end
        )

        # Also get capture daily for subscriber timeseries
        capture_daily = self._repo.get_channel_daily_metrics(
            tenant_id,
            CAPTURE_SLUG,
            ["active_subscribers", "new_subscribers"],
            start,
            end,
        )

        # Merge capture metrics into current
        for k, v in capture.items():
            if k not in current:
                current[k] = v

        # Build derived metrics
        sent = current.get("emails_sent", 0)
        hard = current.get("hard_bounces", 0)
        soft = current.get("soft_bounces", 0)
        deliverability = ((sent - hard - soft) / sent * 100) if sent > 0 else 100.0
        current["deliverability_rate"] = deliverability

        new_subs = current.get("new_subscribers", 0)
        unsubs = current.get("unsubscribes", 0)
        active = current.get("active_subscribers", 0) or 1
        current["list_growth_rate"] = (new_subs - unsubs) / active * 100

        fwd = current.get("forwards", 0)
        current["forward_rate"] = (fwd / sent * 100) if sent > 0 else 0.0

        current["churn_rate"] = (unsubs / active * 100) if active > 0 else 0.0

        # Health score
        b_open = get_benchmarks(IndustryCategory.GENERAL, "open_rate")
        b_ctor = get_benchmarks(IndustryCategory.GENERAL, "click_to_open_rate")
        health = compute_health_score(
            open_rate=current.get("open_rate", 0),
            benchmark_open_rate=b_open.median if b_open else 21.5,
            ctor=current.get("click_to_open_rate", 0),
            benchmark_ctor=b_ctor.median if b_ctor else 10.5,
            deliverability_rate=deliverability,
            list_growth_rate=current.get("list_growth_rate", 0),
        )

        # Build KPIs
        hero_metrics = [
            "emails_sent",
            "open_rate",
            "click_rate",
            "click_to_open_rate",
            "deliverability_rate",
            "active_subscribers",
        ]
        kpis = self._build_kpis(current, previous, hero_metrics)

        # Build time series
        time_series = self._build_time_series(daily + capture_daily)

        # Build funnel
        funnel = [
            FunnelStepDTO(
                label="Enviados",
                metric_name="emails_sent",
                value=current.get("emails_sent", 0),
                conversion_rate_from_previous=None,
            ),
            FunnelStepDTO(
                label="Entregados",
                metric_name="delivered",
                value=sent - hard - soft,
                conversion_rate_from_previous=deliverability,
            ),
            FunnelStepDTO(
                label="Abiertos",
                metric_name="unique_opens",
                value=current.get("unique_opens", 0),
                conversion_rate_from_previous=current.get("open_rate", 0),
            ),
            FunnelStepDTO(
                label="Clicks",
                metric_name="unique_clicks",
                value=current.get("unique_clicks", 0),
                conversion_rate_from_previous=current.get("click_rate", 0),
            ),
            FunnelStepDTO(
                label="Bajas",
                metric_name="unsubscribes",
                value=current.get("unsubscribes", 0),
                conversion_rate_from_previous=current.get("unsubscribe_rate", 0),
            ),
        ]

        # Best / worst campaign from extra data
        best, worst = await self._get_best_worst_campaigns(tenant_id, start, end)

        logger.info(
            "email_dashboard_served",
            tenant_id=str(tenant_id),
            period=period,
            kpi_count=len(kpis),
        )

        return EmailDashboardDTO(
            channel_slug=CHANNEL_SLUG,
            channel_name="Email Marketing",
            provider_name=None,
            period=period,
            health_score=health,
            kpis=kpis,
            time_series=time_series,
            funnel=funnel,
            best_campaign=best,
            worst_campaign=worst,
        )

    # -- Campaigns tab ---------------------------------------------------------

    async def get_campaigns(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailCampaignsResponseDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)

        campaigns = await self._get_campaign_list(tenant_id, start, end)

        # Group by type
        type_map: dict[str, list[EmailCampaignDTO]] = {}
        for c in campaigns:
            type_map.setdefault(c.campaign_type, []).append(c)

        type_performance = []
        for ctype, clist in type_map.items():
            avg_open = sum(c.open_rate for c in clist) / len(clist) if clist else 0
            avg_ctor = (
                sum(c.click_to_open_rate for c in clist) / len(clist) if clist else 0
            )
            type_performance.append(
                EmailTypePerformanceDTO(
                    campaign_type=ctype,
                    campaign_count=len(clist),
                    total_sent=sum(c.emails_sent for c in clist),
                    avg_open_rate=round(avg_open, 1),
                    avg_ctor=round(avg_ctor, 1),
                    total_unsubs=sum(c.unsubscribes for c in clist),
                )
            )

        # Rank types
        type_performance.sort(key=lambda t: t.avg_open_rate, reverse=True)
        for i, tp in enumerate(type_performance):
            if i == 0:
                tp.rank_label = "Mejor engagement"
            elif i == len(type_performance) - 1:
                tp.rank_label = "Menor engagement promedio"
            else:
                tp.rank_label = f"{i + 1}do mejor tipo"

        # Top subjects
        sorted_by_open = sorted(campaigns, key=lambda c: c.open_rate, reverse=True)
        top_subjects = [
            EmailCampaignSummaryDTO(
                campaign_name=c.campaign_name,
                campaign_subject=c.campaign_subject,
                campaign_type=c.campaign_type,
                sent_count=c.emails_sent,
                open_rate=c.open_rate,
                click_to_open_rate=c.click_to_open_rate,
                sent_date=c.sent_date,
            )
            for c in sorted_by_open[:5]
        ]

        return EmailCampaignsResponseDTO(
            period=period,
            type_performance=type_performance,
            campaigns=campaigns,
            top_subjects=top_subjects,
        )

    # -- Automations tab -------------------------------------------------------

    async def get_automations(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailAutomationsResponseDTO:
        """Return per-automation performance data from official_metrics.

        Reads rows where extra->>'source' = 'automation' and groups by
        campaign_id (= automation_id from Mailerlite).
        """
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)

        automations = await self._get_automation_list(tenant_id, start, end)

        # Build KPIs from automation data
        total_sent = sum(a.emails_sent for a in automations)
        total_completed = sum(a.completed for a in automations)
        auto_count = len(automations)

        avg_open = (
            sum(a.open_rate for a in automations) / auto_count if auto_count else 0
        )

        kpis = [
            MetricKpiDTO(
                metric_name="automation_emails_sent",
                display_name="Emails Automatizados",
                current_value=total_sent,
                previous_value=None,
                delta_pct=None,
                delta_absolute=None,
                unit="count",
                higher_is_better=True,
            ),
            MetricKpiDTO(
                metric_name="automation_avg_open_rate",
                display_name="Open Rate Promedio",
                current_value=round(avg_open, 1),
                previous_value=None,
                delta_pct=None,
                delta_absolute=None,
                unit="percentage",
                higher_is_better=True,
            ),
            MetricKpiDTO(
                metric_name="automation_completion_rate",
                display_name="Completación",
                current_value=total_completed,
                previous_value=None,
                delta_pct=None,
                delta_absolute=None,
                unit="count",
                higher_is_better=True,
            ),
        ]

        return EmailAutomationsResponseDTO(
            period=period,
            kpis=kpis,
            automations=automations,
        )

    async def _get_automation_list(
        self,
        tenant_id: UUID,
        start: date,
        end: date,
    ) -> list[EmailAutomationDTO]:
        """Build automation list from official_metrics with campaign_id grouping.

        Filters by extra->>'source' = 'automation' to distinguish from campaigns.
        Bug fixes applied:
        - active_subscribers = completed + in_queue (was just in_queue)
        - completion_rate = actual (was CTOR)
        - status reads from extra (was hardcoded 'active')
        Populates new fields: click_to_open_rate, unsubscribes, steps.
        """
        stmt = (
            select(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
                func.sum(OfficialMetricModel.value).label("total_value"),
                func.max(cast(OfficialMetricModel.extra, String)).label("extra"),
                func.max(OfficialMetricModel.metric_date).label("last_date"),
            )
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.channel_slug == CHANNEL_SLUG,
                OfficialMetricModel.metric_date >= start,
                OfficialMetricModel.metric_date <= end,
                OfficialMetricModel.campaign_id.isnot(None),
                OfficialMetricModel.campaign_id != "",
                OfficialMetricModel.extra.op("->>")("source") == "automation",
            )
            .group_by(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
            )
        )
        result = self._db.execute(stmt)
        rows = result.all()

        # Group by campaign_id (= automation_id)
        autos_map: dict[str, dict] = {}
        for row in rows:
            aid = row.campaign_id
            if aid not in autos_map:
                extra = json.loads(row.extra) if row.extra else {}
                completed = int(extra.get("completed_subscribers", 0))
                in_queue = int(extra.get("subscribers_in_queue", 0))
                autos_map[aid] = {
                    "automation_id": aid,
                    "name": extra.get("automation_name", aid),
                    "automation_type": extra.get("automation_type", "workflow"),
                    "status": extra.get("automation_status", "active"),
                    "completed": completed,
                    "ingresados": completed + in_queue,  # FIX: was just in_queue
                    "steps_raw": extra.get("steps", []),
                    "metrics": {},
                }
            metrics_dict = autos_map[aid]["metrics"]
            if isinstance(metrics_dict, dict):
                metrics_dict[row.metric_name] = row.total_value

        automations: list[EmailAutomationDTO] = []
        for adata in autos_map.values():
            m = adata.get("metrics", {})
            if not isinstance(m, dict):
                m = {}
            completed = int(adata.get("completed", 0))
            ingresados = int(adata.get("ingresados", 0))
            completion_rate = (
                round(completed / ingresados * 100, 1) if ingresados > 0 else 0.0
            )

            steps_raw = adata.get("steps_raw", [])
            steps: list[AutomationStepDTO] = []
            if isinstance(steps_raw, list):
                for s in steps_raw:
                    if not isinstance(s, dict):
                        continue
                    try:
                        steps.append(AutomationStepDTO(**s))
                    except ValidationError as exc:
                        logger.warning(
                            "automation.step.skipped_malformed",
                            automation_id=str(adata.get("automation_id", "")),
                            error=str(exc),
                        )

            automations.append(
                EmailAutomationDTO(
                    automation_id=str(adata["automation_id"]),
                    name=str(adata["name"]),
                    automation_type=str(adata["automation_type"]),
                    status=str(adata["status"]),
                    emails_sent=int(m.get("emails_sent", 0)),
                    open_rate=round(float(m.get("open_rate", 0)), 1),
                    click_rate=round(float(m.get("click_rate", 0)), 1),
                    click_to_open_rate=round(float(m.get("click_to_open_rate", 0)), 1),
                    completion_rate=completion_rate,
                    completed=completed,
                    active_subscribers=ingresados,
                    unsubscribes=int(m.get("unsubscribes", 0)),
                    steps=steps,
                )
            )
        return automations

    # -- Audience tab ----------------------------------------------------------

    async def get_audience(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailAudienceResponseDTO:
        """Return audience engagement segmentation data.

        Segments are estimated from aggregate campaign metrics.
        Per-subscriber segmentation requires future ETL enhancement.
        """
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end
        )
        capture = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end
        )

        active = capture.get("active_subscribers", 0) or current.get(
            "active_subscribers", 0
        )
        open_rate = current.get("open_rate", 0)

        # Estimate segments from aggregate data
        champions_pct = min(open_rate * 0.6, 25)
        activos_pct = min(open_rate * 1.2, 45)
        dormidos_pct = max(15, 100 - open_rate * 3)
        en_riesgo_pct = 100 - champions_pct - activos_pct - dormidos_pct

        total = max(active, 1)
        segments = [
            EmailEngagementSegmentDTO(
                segment_name="champions",
                label="Champions",
                count=int(total * champions_pct / 100),
                percentage=round(champions_pct, 1),
                open_rate=round(min(open_rate * 2.8, 95), 1),
                click_rate=round(min(current.get("click_rate", 0) * 4, 20), 1),
                ctor=round(min(current.get("click_to_open_rate", 0) * 1.5, 30), 1),
                avg_days_inactive=None,
                recommended_action="Enviales contenido premium y ofertas de acceso anticipado.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="activos",
                label="Activos",
                count=int(total * activos_pct / 100),
                percentage=round(activos_pct, 1),
                open_rate=round(min(open_rate * 1.7, 60), 1),
                click_rate=round(current.get("click_rate", 0) * 0.8, 1),
                ctor=round(current.get("click_to_open_rate", 0) * 0.5, 1),
                avg_days_inactive=None,
                recommended_action="Mejora los CTAs. Prueba contenido mas especifico y ofertas con urgencia.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="en_riesgo",
                label="En Riesgo",
                count=int(total * en_riesgo_pct / 100),
                percentage=round(en_riesgo_pct, 1),
                open_rate=round(max(open_rate * 0.35, 2), 1),
                click_rate=round(max(current.get("click_rate", 0) * 0.15, 0.1), 1),
                ctor=round(max(current.get("click_to_open_rate", 0) * 0.4, 2), 1),
                avg_days_inactive=42,
                recommended_action="Campana de re-engagement con incentivo. Si no responden en 30 dias, mover a Dormidos.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="dormidos",
                label="Dormidos",
                count=int(total * dormidos_pct / 100),
                percentage=round(dormidos_pct, 1),
                open_rate=round(max(open_rate * 0.04, 0.1), 1),
                click_rate=0.0,
                ctor=0.0,
                avg_days_inactive=95,
                recommended_action="Envia ultima oportunidad. Si no abren, eliminar para mejorar deliverability.",
            ),
        ]

        # Activity heatmap: estimated from industry patterns
        heatmap = self._build_estimated_heatmap()

        # Engagement decay: estimated from industry averages
        decay = [
            EngagementDecayDTO(
                period_label="0-30 dias", open_rate=round(open_rate * 1.9, 1)
            ),
            EngagementDecayDTO(
                period_label="31-90 dias", open_rate=round(open_rate * 1.3, 1)
            ),
            EngagementDecayDTO(
                period_label="91-180 dias", open_rate=round(open_rate * 0.75, 1)
            ),
            EngagementDecayDTO(
                period_label="180+ dias", open_rate=round(open_rate * 0.25, 1)
            ),
        ]

        return EmailAudienceResponseDTO(
            period=period,
            segments=segments,
            segment_type_matrix=[],  # Requires campaign x subscriber cross-reference
            sources=[],  # Requires subscriber source data from ETL
            engagement_decay=decay,
            activity_heatmap=heatmap,
        )

    # -- Health tab ------------------------------------------------------------

    async def get_health(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailHealthResponseDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, prev_start, prev_end
        )

        sent = current.get("emails_sent", 0)
        hard = current.get("hard_bounces", 0)
        soft = current.get("soft_bounces", 0)
        deliverability = ((sent - hard - soft) / sent * 100) if sent > 0 else 100.0
        current["deliverability_rate"] = deliverability

        b_open = get_benchmarks(IndustryCategory.GENERAL, "open_rate")
        b_ctor = get_benchmarks(IndustryCategory.GENERAL, "click_to_open_rate")
        health = compute_health_score(
            open_rate=current.get("open_rate", 0),
            benchmark_open_rate=b_open.median if b_open else 21.5,
            ctor=current.get("click_to_open_rate", 0),
            benchmark_ctor=b_ctor.median if b_ctor else 10.5,
            deliverability_rate=deliverability,
            list_growth_rate=0,  # Not relevant for health tab focus
        )

        kpis = self._build_kpis(
            current,
            previous,
            ["deliverability_rate", "bounce_rate", "unsubscribe_rate", "forward_rate"],
        )

        bounce_breakdown = BounceBreakdownDTO(
            hard_bounces=int(hard),
            soft_bounces=int(soft),
            hard_bounce_rate=round((hard / sent * 100) if sent > 0 else 0, 2),
            soft_bounce_rate=round((soft / sent * 100) if sent > 0 else 0, 2),
            total_delivered=int(sent - hard - soft),
        )

        ts_metrics = ["bounce_rate", "unsubscribe_rate", "deliverability_rate"]
        daily = self._repo.get_channel_daily_metrics(
            tenant_id, CHANNEL_SLUG, ts_metrics, start, end
        )
        time_series = self._build_time_series(daily)

        alerts = self._generate_health_alerts(current)

        campaigns_count = self._count_campaigns_from_extra(tenant_id, start, end)

        return EmailHealthResponseDTO(
            period=period,
            campaigns_count=campaigns_count,
            health_score=health,
            kpis=kpis,
            bounce_breakdown=bounce_breakdown,
            time_series=time_series,
            alerts=alerts,
        )

    # -- Growth tab ------------------------------------------------------------

    async def get_growth(
        self,
        tenant_id: UUID,
        period: str = "30d",
    ) -> EmailGrowthResponseDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end
        )
        nurture = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, prev_start, prev_end
        )

        # Merge nurture unsubs into capture metrics
        current["unsubscribes"] = nurture.get("unsubscribes", 0)

        active = current.get("active_subscribers", 0) or 1
        new_subs = current.get("new_subscribers", 0)
        unsubs = current.get("unsubscribes", 0)
        current["list_growth_rate"] = (new_subs - unsubs) / active * 100

        kpis = self._build_kpis(
            current,
            previous,
            [
                "active_subscribers",
                "new_subscribers",
                "unsubscribes",
                "list_growth_rate",
            ],
        )

        daily = self._repo.get_channel_daily_metrics(
            tenant_id,
            CAPTURE_SLUG,
            ["active_subscribers", "new_subscribers"],
            start,
            end,
        )
        nurture_daily = self._repo.get_channel_daily_metrics(
            tenant_id, CHANNEL_SLUG, ["unsubscribes"], start, end
        )
        time_series = self._build_time_series(daily + nurture_daily)

        return EmailGrowthResponseDTO(
            period=period,
            kpis=kpis,
            time_series=time_series,
            sources=[],  # Requires subscriber source from ETL
            retention_curve=[],  # Requires subscriber age from ETL
        )

    # -- Private helpers -------------------------------------------------------

    def _count_campaigns_from_extra(
        self,
        tenant_id: UUID,
        start: date,
        end: date,
    ) -> int:
        """Count campaigns stored in the extra JSON of emails_sent rows."""
        stmt = select(OfficialMetricModel.extra).where(
            OfficialMetricModel.tenant_id == tenant_id,
            OfficialMetricModel.channel_slug == CHANNEL_SLUG,
            OfficialMetricModel.metric_name == "emails_sent",
            OfficialMetricModel.metric_date >= start,
            OfficialMetricModel.metric_date <= end,
        )
        result = self._db.execute(stmt)
        total = 0
        for (extra,) in result.all():
            if extra and isinstance(extra, dict):
                campaigns = extra.get("campaigns", [])
                total += len(campaigns)
            elif extra and isinstance(extra, str):
                parsed = json.loads(extra)
                campaigns = parsed.get("campaigns", [])
                total += len(campaigns)
        return total

    def _build_kpis(
        self,
        current: dict[str, float],
        previous: dict[str, float],
        metric_names: list[str],
    ) -> list[MetricKpiDTO]:
        kpis: list[MetricKpiDTO] = []
        for name in metric_names:
            defn = get_metric_def(name)
            curr_val = current.get(name, 0)
            prev_val = previous.get(name)

            delta_pct: float | None = None
            delta_abs: float | None = None
            if prev_val is not None and prev_val != 0:
                delta_abs = round(curr_val - prev_val, 2)
                delta_pct = round((curr_val - prev_val) / prev_val * 100, 1)

            bench_dto: BenchmarkRangeDTO | None = None
            bench = get_benchmarks(IndustryCategory.GENERAL, name)
            if bench:
                if curr_val >= bench.high:
                    interp = "Excelente"
                elif curr_val >= bench.median:
                    interp = "Por encima del promedio"
                elif curr_val >= bench.low:
                    interp = "Por debajo del promedio"
                else:
                    interp = "Requiere atención"
                bench_dto = BenchmarkRangeDTO(
                    low=bench.low,
                    median=bench.median,
                    high=bench.high,
                    unit=bench.unit,
                    interpretation=interp,
                )

            kpis.append(
                MetricKpiDTO(
                    metric_name=name,
                    display_name=defn.display_name if defn else name,
                    current_value=round(curr_val, 2),
                    previous_value=round(prev_val, 2) if prev_val is not None else None,
                    delta_percent=delta_pct,
                    delta_absolute=delta_abs,
                    unit=defn.unit.value if defn else "count",
                    higher_is_better=defn.higher_is_better if defn else True,
                    benchmark=bench_dto,
                )
            )
        return kpis

    def _build_time_series(
        self,
        daily: list[tuple[date, str, float]],
    ) -> list[MetricTimeSeriesDTO]:
        by_metric: dict[str, list[TimeSeriesDataPointDTO]] = {}
        for metric_date, metric_name, value in daily:
            by_metric.setdefault(metric_name, []).append(
                TimeSeriesDataPointDTO(date=str(metric_date), value=round(value, 2))
            )
        result: list[MetricTimeSeriesDTO] = []
        for name, points in by_metric.items():
            defn = get_metric_def(name)
            points.sort(key=lambda p: p.date)
            result.append(
                MetricTimeSeriesDTO(
                    metric_name=name,
                    display_name=defn.display_name if defn else name,
                    unit=defn.unit.value if defn else "count",
                    data_points=points,
                )
            )
        return result

    async def _get_best_worst_campaigns(
        self,
        tenant_id: UUID,
        start: date,
        end: date,
    ) -> tuple[EmailCampaignSummaryDTO | None, EmailCampaignSummaryDTO | None]:
        """Get best and worst campaigns by open_rate from official_metrics extra data."""
        campaigns = await self._get_campaign_list(tenant_id, start, end)
        if not campaigns:
            return None, None

        sorted_camps = sorted(campaigns, key=lambda c: c.open_rate, reverse=True)
        best = sorted_camps[0] if sorted_camps else None
        worst = sorted_camps[-1] if len(sorted_camps) > 1 else None

        def _to_summary(c: EmailCampaignDTO) -> EmailCampaignSummaryDTO:
            return EmailCampaignSummaryDTO(
                campaign_name=c.campaign_name,
                campaign_subject=c.campaign_subject,
                campaign_type=c.campaign_type,
                sent_count=c.emails_sent,
                open_rate=c.open_rate,
                click_to_open_rate=c.click_to_open_rate,
                sent_date=c.sent_date,
            )

        return (
            _to_summary(best) if best else None,
            _to_summary(worst) if worst else None,
        )

    async def _get_campaign_list(
        self,
        tenant_id: UUID,
        start: date,
        end: date,
    ) -> list[EmailCampaignDTO]:
        """Build campaign list from official_metrics with campaign_id grouping."""
        stmt = (
            select(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
                func.sum(OfficialMetricModel.value).label("total_value"),
                func.max(cast(OfficialMetricModel.extra, String)).label("extra"),
                func.max(OfficialMetricModel.metric_date).label("last_date"),
            )
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.channel_slug == CHANNEL_SLUG,
                OfficialMetricModel.metric_date >= start,
                OfficialMetricModel.metric_date <= end,
                OfficialMetricModel.campaign_id.isnot(None),
                OfficialMetricModel.campaign_id != "",
            )
            .group_by(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
            )
        )
        result = self._db.execute(stmt)
        rows = result.all()

        # Group by campaign_id
        campaigns_map: dict[str, dict[str, str | dict[str, float] | None]] = {}
        for row in rows:
            cid = row.campaign_id
            if cid not in campaigns_map:
                extra = json.loads(row.extra) if row.extra else {}
                campaigns_map[cid] = {
                    "campaign_id": cid,
                    "campaign_name": extra.get("campaign_name", cid),
                    "campaign_subject": extra.get("campaign_subject"),
                    "campaign_type": extra.get("campaign_type", "contenido"),
                    "sent_date": str(row.last_date) if row.last_date else None,
                    "metrics": {},
                }
            metrics_dict = campaigns_map[cid]["metrics"]
            if isinstance(metrics_dict, dict):
                metrics_dict[row.metric_name] = row.total_value

        campaigns: list[EmailCampaignDTO] = []
        for cdata in campaigns_map.values():
            m = cdata.get("metrics", {})
            if not isinstance(m, dict):
                m = {}
            campaigns.append(
                EmailCampaignDTO(
                    campaign_id=str(cdata.get("campaign_id", "")),
                    campaign_name=str(cdata.get("campaign_name", "")),
                    campaign_subject=cdata.get("campaign_subject"),  # type: ignore[arg-type]
                    campaign_type=str(cdata.get("campaign_type", "contenido")),
                    sent_date=cdata.get("sent_date"),  # type: ignore[arg-type]
                    emails_sent=int(m.get("emails_sent", 0)),
                    open_rate=round(float(m.get("open_rate", 0)), 1),
                    click_rate=round(float(m.get("click_rate", 0)), 1),
                    click_to_open_rate=round(float(m.get("click_to_open_rate", 0)), 1),
                    bounce_rate=round(float(m.get("bounce_rate", 0)), 1),
                    unsubscribes=int(m.get("unsubscribes", 0)),
                    unique_opens=int(m.get("unique_opens", 0)),
                    unique_clicks=int(m.get("unique_clicks", 0)),
                )
            )
        return campaigns

    def _build_estimated_heatmap(self) -> list[ActivityHeatmapCellDTO]:
        """Build estimated activity heatmap based on industry patterns."""
        base_pattern: dict[tuple[int, str], float] = {
            (0, "9-12"): 0.12,
            (1, "9-12"): 0.14,
            (2, "9-12"): 0.12,
            (3, "9-12"): 0.11,
            (4, "9-12"): 0.09,
            (5, "9-12"): 0.03,
            (6, "9-12"): 0.03,
        }
        hours = ["6-9", "9-12", "12-15", "15-18", "18-21", "21-24"]
        cells: list[ActivityHeatmapCellDTO] = []
        for day in range(7):
            for hour in hours:
                rate = base_pattern.get((day, hour), 0.04)
                # Apply time-of-day modifiers
                if hour == "6-9":
                    rate *= 0.5
                elif hour in ("12-15", "15-18"):
                    rate *= 0.7
                elif hour == "18-21":
                    rate *= 0.8
                elif hour == "21-24":
                    rate *= 0.4
                cells.append(
                    ActivityHeatmapCellDTO(
                        day_of_week=day,
                        hour_block=hour,
                        open_rate=round(rate * 100, 1),
                    )
                )
        return cells

    def _generate_health_alerts(self, metrics: dict[str, float]) -> list[str]:
        alerts: list[str] = []
        bounce = metrics.get("bounce_rate", 0)
        spam = (
            metrics.get("spam_reports", 0) / max(metrics.get("emails_sent", 1), 1) * 100
        )
        unsub = metrics.get("unsubscribe_rate", 0)

        if bounce > 2:
            alerts.append(
                f"Bounce rate elevado ({bounce:.1f}%). Limpia la lista de emails invalidos."
            )
        if spam > 0.1:
            alerts.append(
                f"Tasa de spam ({spam:.2f}%) por encima del umbral. "
                "Revisa el contenido y la frecuencia de envio."
            )
        if unsub > 0.5:
            alerts.append(
                f"Tasa de bajas alta ({unsub:.1f}%). "
                "Verifica la relevancia del contenido para tu audiencia."
            )
        if not alerts:
            alerts.append("Tu reputacion de envio esta saludable. Sigue asi.")
        return alerts
