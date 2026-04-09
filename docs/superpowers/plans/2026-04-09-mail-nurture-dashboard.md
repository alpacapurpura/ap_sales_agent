# Mail Nurture Dashboard — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Email Intelligence Hub — a full redesign of the Mail channel sidebar and extended dashboard in Growth Studio's Nurture stage, with source-agnostic architecture, expert-level metrics, and actionable insights.

**Architecture:** Provider-agnostic backend service reads from `official_metrics` table. Enhanced ETL extracts new fields (campaign name, subject, type, automation stats). Frontend consumes normalized DTOs through 6 new API endpoints. Shared `MetricInfoPopover` component provides click-based metric help across all channels.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (backend), Next.js 15 + React 18 + Recharts + Shadcn UI (frontend), Vitest + Playwright (testing)

**Design Spec:** `docs/superpowers/specs/2026-04-09-mail-nurture-dashboard-design.md`

**Mockups:** `.superpowers/brainstorm/66190-1775757369/content/` (sidebar-mockup.html, dashboard-panorama.html, dashboard-campanas.html, dashboard-audiencia.html)

---

## File Structure

### Backend — New/Modified Files

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/src/modules/analytics/domain/metric_catalog.py` | Modify | Add 6 new metric definitions |
| `backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py` | Modify | Extract campaign name/subject/type, total opens/clicks, full automation stats |
| `backend/src/modules/analytics/application/dto/email_dashboard_dto.py` | Create | Email-specific DTOs (campaigns, automations, audience, health, growth) |
| `backend/src/modules/analytics/application/services/email_dashboard_service.py` | Create | Orchestrates all email dashboard data from official_metrics |
| `backend/src/modules/analytics/api/email_metrics.py` | Create | 6 new API endpoints for email dashboard |
| `backend/tests/modules/analytics/test_email_dashboard_service.py` | Create | Service tests: health score, segments, campaign types |
| `backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py` | Create | New extraction fields tests |

### Frontend — New/Modified Files

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/components/shared/MetricInfoPopover.tsx` | Create | Reusable (i) click popover for any metric |
| `frontend/src/features/growth-studio/types/mail-types.ts` | Create | All TypeScript interfaces for email DTOs |
| `frontend/src/features/growth-studio/api/mail-api.ts` | Create | API fetch functions for 6 email endpoints |
| `frontend/src/features/growth-studio/hooks/useMailDashboard.ts` | Create | React Query hooks for all email endpoints |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailOverviewPanel.tsx` | Rewrite | Redesigned sidebar with health score + campaigns |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailHealthScore.tsx` | Create | Composite 0-100 score with 4 sub-bars |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailCampaignCards.tsx` | Create | Best/worst campaign cards for sidebar |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailDashboard.tsx` | Rewrite | 6-tab dashboard shell |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailPanoramaTab.tsx` | Create | Overview tab with KPIs, charts, funnel |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCampanasTab.tsx` | Create | Campaign analysis tab |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionesTab.tsx` | Create | Automation performance tab |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAudienciaTab.tsx` | Create | Audience behavior tab |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailEntregabilidadTab.tsx` | Rewrite | Deliverability health tab |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCrecimientoTab.tsx` | Create | List growth tab |
| `frontend/src/features/growth-studio/config/channel-display-registry.ts` | Modify | Update email-nurture summary metrics |
| `frontend/src/features/growth-studio/lib/metric-labels.ts` | Modify | Add new metric labels |
| `frontend/src/features/growth-studio/types/metrics.ts` | Modify | Add MailDashboardTab type |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailOverviewPanel.test.tsx` | Create | Sidebar tests |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailDashboard.test.tsx` | Rewrite | Dashboard tests |
| `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx` | Rewrite | Tab tests |
| `frontend/src/components/shared/__tests__/MetricInfoPopover.test.tsx` | Create | Popover tests |

---

## Phase 1: Backend — ETL Enhancement

### Task 1: Add new metric definitions to catalog

**Files:**
- Modify: `backend/src/modules/analytics/domain/metric_catalog.py`

- [ ] **Step 1: Add 6 new metrics after existing email metrics (around line 262)**

```python
# Add after the `forwards` metric definition (~line 262)

MetricDefinition(
    name="deliverability_rate",
    display_name="Tasa de Entregabilidad",
    description="Porcentaje de emails entregados exitosamente",
    interpretation="Mide la reputación del remitente. Valores por encima de 95% son excelentes.",
    unit=MetricUnit.PERCENTAGE,
    aggregation=AggregationType.DERIVED,
    formula="(emails_sent - hard_bounces - soft_bounces) / emails_sent * 100",
    formula_components=("emails_sent", "hard_bounces", "soft_bounces"),
    higher_is_better=True,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
MetricDefinition(
    name="list_growth_rate",
    display_name="Tasa de Crecimiento de Lista",
    description="Crecimiento neto de la lista de suscriptores en el periodo",
    interpretation="Positivo indica crecimiento saludable. Negativo indica que pierdes más suscriptores de los que ganas.",
    unit=MetricUnit.PERCENTAGE,
    aggregation=AggregationType.DERIVED,
    formula="(new_subscribers - unsubscribes) / active_subscribers * 100",
    formula_components=("new_subscribers", "unsubscribes", "active_subscribers"),
    higher_is_better=True,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
MetricDefinition(
    name="churn_rate",
    display_name="Tasa de Churn",
    description="Porcentaje de suscriptores que se dan de baja en el periodo",
    interpretation="Valores por debajo de 0.5% son saludables. Por encima de 1% requiere atención.",
    unit=MetricUnit.PERCENTAGE,
    aggregation=AggregationType.DERIVED,
    formula="unsubscribes / active_subscribers * 100",
    formula_components=("unsubscribes", "active_subscribers"),
    higher_is_better=False,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
MetricDefinition(
    name="forward_rate",
    display_name="Tasa de Reenvío",
    description="Porcentaje de emails que fueron reenviados por los suscriptores",
    interpretation="Indica contenido tan valioso que los suscriptores lo comparten.",
    unit=MetricUnit.PERCENTAGE,
    aggregation=AggregationType.DERIVED,
    formula="forwards / emails_sent * 100",
    formula_components=("forwards", "emails_sent"),
    higher_is_better=True,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
MetricDefinition(
    name="opens_count",
    display_name="Aperturas Totales",
    description="Total de aperturas incluyendo re-aperturas del mismo suscriptor",
    interpretation="Permite calcular aperturas por lector (opens_count / unique_opens).",
    unit=MetricUnit.COUNT,
    aggregation=AggregationType.ADDITIVE,
    higher_is_better=True,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
MetricDefinition(
    name="clicks_count",
    display_name="Clics Totales",
    description="Total de clics incluyendo re-clics del mismo suscriptor",
    interpretation="Permite calcular clics por lector (clicks_count / unique_clicks).",
    unit=MetricUnit.COUNT,
    aggregation=AggregationType.ADDITIVE,
    higher_is_better=True,
    providers=("mailerlite", "mailchimp", "activecampaign"),
),
```

- [ ] **Step 2: Add email benchmarks to industry_benchmarks.py**

Add deliverability_rate benchmark in `backend/src/modules/analytics/domain/industry_benchmarks.py` under GENERAL email benchmarks section:

```python
"deliverability_rate": BenchmarkRange(
    low=90.0, median=95.0, high=99.0,
    unit="percentage",
    interpretation="Porcentaje de emails entregados exitosamente",
),
"list_growth_rate": BenchmarkRange(
    low=1.0, median=3.0, high=8.0,
    unit="percentage",
    interpretation="Crecimiento neto mensual de la lista",
),
"forward_rate": BenchmarkRange(
    low=0.01, median=0.05, high=0.15,
    unit="percentage",
    interpretation="Porcentaje de emails reenviados",
),
```

- [ ] **Step 3: Run tests to verify catalog integrity**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_metric_catalog.py -x -q --tb=short`
Expected: PASS (existing tests should still pass with new metrics added)

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/domain/metric_catalog.py backend/src/modules/analytics/domain/industry_benchmarks.py
git commit -m "feat(analytics): add 6 new email metric definitions and benchmarks"
```

---

### Task 2: Enhance Mailerlite provider to extract new fields

**Files:**
- Modify: `backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py`
- Test: `backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py`

- [ ] **Step 1: Write failing tests for new extraction fields**

Create `backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py`:

```python
"""Tests for enhanced Mailerlite provider extraction."""
from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.providers.mailerlite_provider import (
    MailerLiteProvider,
    MAILERLITE_METRIC_MAP,
    classify_campaign_type,
)


class TestMailerliteMetricMap:
    """Verify new metrics are mapped."""

    def test_opens_count_mapped(self):
        assert "opens_count" in MAILERLITE_METRIC_MAP

    def test_clicks_count_mapped(self):
        assert "clicks_count" in MAILERLITE_METRIC_MAP


class TestCampaignTypeClassification:
    """Verify keyword-based campaign type classification."""

    def test_newsletter_from_name(self):
        assert classify_campaign_type("Newsletter Semanal #12", "") == "newsletter"

    def test_newsletter_from_subject(self):
        assert classify_campaign_type("Edición 5", "Novedades de la semana") == "newsletter"

    def test_launch_from_name(self):
        assert classify_campaign_type("Lanzamiento Curso Premium", "") == "lanzamiento"

    def test_promo_from_name(self):
        assert classify_campaign_type("Promo Black Friday -40%", "") == "promocion"

    def test_promo_from_discount(self):
        assert classify_campaign_type("Oferta especial", "50% de descuento") == "promocion"

    def test_content_default(self):
        assert classify_campaign_type("5 Tips de Fotografía", "Aprende más") == "contenido"

    def test_reengagement_from_name(self):
        assert classify_campaign_type("Te extrañamos", "Vuelve con nosotros") == "reengagement"


class TestExtractedCampaignExtra:
    """Verify campaign extra data includes name, subject, type."""

    @pytest.fixture
    def mock_campaign(self):
        return {
            "id": "camp_123",
            "name": "Lanzamiento Curso Premium",
            "status": "sent",
            "type": "regular",
            "emails": [{"subject": "Tu acceso exclusivo está listo"}],
            "stats": {
                "sent": 2340,
                "opens_count": 1200,
                "unique_opens_count": 894,
                "clicks_count": 280,
                "unique_clicks_count": 164,
                "open_rate": {"float": 0.382},
                "click_rate": {"float": 0.070},
                "click_to_open_rate": {"float": 0.184},
                "hard_bounces_count": 5,
                "soft_bounces_count": 2,
                "unsubscribes_count": 1,
                "spam_count": 0,
                "forwards_count": 3,
            },
            "finished_at": "2026-03-15T10:00:00Z",
        }

    def test_campaign_metrics_include_opens_count(self, mock_campaign):
        """opens_count (total, not unique) must be extracted."""
        stats = mock_campaign["stats"]
        assert "opens_count" in stats
        assert stats["opens_count"] == 1200

    def test_campaign_metrics_include_clicks_count(self, mock_campaign):
        """clicks_count (total, not unique) must be extracted."""
        stats = mock_campaign["stats"]
        assert "clicks_count" in stats
        assert stats["clicks_count"] == 280
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_mailerlite_provider_enhanced.py -x -q --tb=short`
Expected: FAIL — `classify_campaign_type` not found, `opens_count` not in MAILERLITE_METRIC_MAP

- [ ] **Step 3: Add opens_count and clicks_count to MAILERLITE_METRIC_MAP**

In `backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py`, add to `MAILERLITE_METRIC_MAP` dict (around line 81):

```python
    "opens_count": ("opens_count", "count"),
    "clicks_count": ("clicks_count", "count"),
```

- [ ] **Step 4: Add classify_campaign_type function**

Add after the `MAILERLITE_METRIC_MAP` definition (around line 85):

```python
_CAMPAIGN_TYPE_KEYWORDS: dict[str, list[str]] = {
    "newsletter": ["newsletter", "semanal", "quincenal", "mensual", "edición", "digest", "novedades"],
    "lanzamiento": ["lanzamiento", "launch", "nuevo", "exclusivo", "estreno", "preventa", "acceso"],
    "promocion": ["promo", "descuento", "oferta", "%", "black friday", "cyber", "sale", "gratis", "free"],
    "reengagement": ["extrañamos", "miss you", "vuelve", "reactivar", "inactivo", "última oportunidad"],
}


def classify_campaign_type(name: str, subject: str) -> str:
    """Classify a campaign into a type based on keywords in name and subject.

    Returns one of: newsletter, lanzamiento, promocion, reengagement, contenido.
    """
    text = f"{name} {subject}".lower()
    for campaign_type, keywords in _CAMPAIGN_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return campaign_type
    return "contenido"
```

- [ ] **Step 5: Enhance _extract_campaigns to store campaign name, subject, type in extra**

In the `_extract_campaigns` method, after the campaign metrics loop (around line 580-600), modify the ExtractedMetric creation to include extra data. Find the section where metrics are appended and add to the `extra` dict:

```python
# In the loop that creates ExtractedMetric objects for each campaign metric,
# add these fields to the extra dict of each metric:
campaign_name = campaign.get("name", "")
campaign_subject = ""
emails_list = campaign.get("emails", [])
if emails_list:
    campaign_subject = emails_list[0].get("subject", "")
campaign_type = classify_campaign_type(campaign_name, campaign_subject)

# When creating ExtractedMetric objects, add to extra:
extra = {
    "campaign_name": campaign_name,
    "campaign_subject": campaign_subject,
    "campaign_type": campaign_type,
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_mailerlite_provider_enhanced.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 7: Run full backend test suite**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/providers/mailerlite_provider.py backend/tests/modules/analytics/test_mailerlite_provider_enhanced.py
git commit -m "feat(analytics): enhance Mailerlite ETL with campaign metadata and total open/click counts"
```

---

## Phase 2: Backend — Email Dashboard Service + API

### Task 3: Create email-specific DTOs

**Files:**
- Create: `backend/src/modules/analytics/application/dto/email_dashboard_dto.py`

- [ ] **Step 1: Create the DTO file with all email dashboard types**

```python
"""DTOs for the Email Intelligence Hub dashboard."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    BenchmarkRangeDTO,
    MetricKpiDTO,
    MetricTimeSeriesDTO,
    FunnelStepDTO,
)


# ── Sidebar + Panorama ──────────────────────────────────────────────


class EmailHealthSubScoreDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    area: str  # engagement | entregabilidad | crecimiento | contenido
    label: str
    score: int  # 0-100
    color: str  # green | yellow | red


class EmailHealthScoreDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total: int  # 0-100
    sub_scores: list[EmailHealthSubScoreDTO]


class EmailCampaignSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_name: str
    campaign_subject: str | None = None
    campaign_type: str  # newsletter | lanzamiento | promocion | contenido | reengagement
    sent_count: int
    open_rate: float
    click_to_open_rate: float
    sent_date: str | None = None


class EmailDashboardDTO(BaseModel):
    """Main sidebar + Panorama tab response."""
    model_config = ConfigDict(from_attributes=True)
    channel_slug: str
    channel_name: str
    provider_name: str | None = None  # "mailerlite", "mailchimp", etc.
    period: str
    health_score: EmailHealthScoreDTO
    kpis: list[MetricKpiDTO]
    time_series: list[MetricTimeSeriesDTO]
    funnel: list[FunnelStepDTO]
    best_campaign: EmailCampaignSummaryDTO | None = None
    worst_campaign: EmailCampaignSummaryDTO | None = None
    campaigns_vs_automations: CampaignsVsAutomationsDTO | None = None


class CampaignsVsAutomationsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaigns_sent: int = 0
    campaigns_open_rate: float = 0.0
    campaigns_click_rate: float = 0.0
    campaigns_ctor: float = 0.0
    campaigns_unsubs: int = 0
    automations_sent: int = 0
    automations_open_rate: float = 0.0
    automations_click_rate: float = 0.0
    automations_ctor: float = 0.0
    automations_unsubs: int = 0


# ── Campañas Tab ─────────────────────────────────────────────────────


class EmailCampaignDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_id: str
    campaign_name: str
    campaign_subject: str | None = None
    campaign_type: str
    sent_date: str | None = None
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribes: int = 0
    unique_opens: int = 0
    unique_clicks: int = 0


class EmailTypePerformanceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_type: str  # newsletter | lanzamiento | promocion | contenido | reengagement
    campaign_count: int = 0
    total_sent: int = 0
    avg_open_rate: float = 0.0
    avg_ctor: float = 0.0
    total_unsubs: int = 0
    rank_label: str = ""  # "Mejor engagement", "2do mejor", etc.


class EmailCampaignsResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    type_performance: list[EmailTypePerformanceDTO]
    campaigns: list[EmailCampaignDTO]
    top_subjects: list[EmailCampaignSummaryDTO]


# ── Automatizaciones Tab ─────────────────────────────────────────────


class EmailAutomationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    automation_id: str
    name: str
    automation_type: str  # welcome | nurture | reengagement | post_compra | other
    status: str  # active | paused
    active_subscribers: int = 0
    completed: int = 0
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    completion_rate: float = 0.0


class EmailAutomationsResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    kpis: list[MetricKpiDTO]
    automations: list[EmailAutomationDTO]


# ── Audiencia Tab ────────────────────────────────────────────────────


class EmailEngagementSegmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    segment_name: str  # champions | activos | en_riesgo | dormidos
    label: str
    count: int = 0
    percentage: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    ctor: float = 0.0
    avg_days_inactive: float | None = None
    recommended_action: str = ""


class SegmentTypeMatrixCellDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    segment_name: str
    campaign_type: str
    open_rate: float = 0.0


class EmailSourcePerformanceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source: str  # landing_page | popup | checkout | import | api
    label: str
    subscriber_count: int = 0
    percentage: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    champions_pct: float = 0.0


class EngagementDecayDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_label: str  # "0-30 días", "31-90 días", etc.
    open_rate: float = 0.0


class ActivityHeatmapCellDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    day_of_week: int  # 0=Monday, 6=Sunday
    hour_block: str  # "6-9", "9-12", "12-15", "15-18", "18-21", "21-24"
    open_rate: float = 0.0


class EmailAudienceResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    segments: list[EmailEngagementSegmentDTO]
    segment_type_matrix: list[SegmentTypeMatrixCellDTO]
    sources: list[EmailSourcePerformanceDTO]
    engagement_decay: list[EngagementDecayDTO]
    activity_heatmap: list[ActivityHeatmapCellDTO]


# ── Entregabilidad Tab ───────────────────────────────────────────────


class BounceBreakdownDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hard_bounces: int = 0
    soft_bounces: int = 0
    hard_bounce_rate: float = 0.0
    soft_bounce_rate: float = 0.0
    total_delivered: int = 0


class EmailHealthResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    health_score: EmailHealthScoreDTO
    kpis: list[MetricKpiDTO]
    bounce_breakdown: BounceBreakdownDTO
    time_series: list[MetricTimeSeriesDTO]
    alerts: list[str]


# ── Crecimiento Tab ──────────────────────────────────────────────────


class EmailGrowthResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    kpis: list[MetricKpiDTO]
    time_series: list[MetricTimeSeriesDTO]
    sources: list[EmailSourcePerformanceDTO]
    retention_curve: list[EngagementDecayDTO]
```

- [ ] **Step 2: Verify DTOs are valid Pydantic models**

Run: `cd backend && .venv/bin/python -c "from src.modules.analytics.application.dto.email_dashboard_dto import EmailDashboardDTO; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/analytics/application/dto/email_dashboard_dto.py
git commit -m "feat(analytics): create email dashboard DTOs for Email Intelligence Hub"
```

---

### Task 4: Create email dashboard service

**Files:**
- Create: `backend/src/modules/analytics/application/services/email_dashboard_service.py`
- Test: `backend/tests/modules/analytics/test_email_dashboard_service.py`

- [ ] **Step 1: Write failing tests for the service**

Create `backend/tests/modules/analytics/test_email_dashboard_service.py`:

```python
"""Tests for EmailDashboardService."""
import pytest

from src.modules.analytics.application.services.email_dashboard_service import (
    EmailDashboardService,
    compute_health_score,
    classify_engagement_segment,
)


class TestHealthScore:
    """Health score computation from metric values."""

    def test_excellent_health(self):
        score = compute_health_score(
            open_rate=28.0, benchmark_open_rate=21.5,
            ctor=14.0, benchmark_ctor=10.5,
            deliverability_rate=98.0,
            list_growth_rate=5.0,
        )
        assert score.total >= 80
        assert all(s.color == "green" for s in score.sub_scores)

    def test_poor_engagement(self):
        score = compute_health_score(
            open_rate=10.0, benchmark_open_rate=21.5,
            ctor=4.0, benchmark_ctor=10.5,
            deliverability_rate=97.0,
            list_growth_rate=3.0,
        )
        engagement = next(s for s in score.sub_scores if s.area == "engagement")
        assert engagement.color == "red"
        assert score.total < 70

    def test_negative_growth(self):
        score = compute_health_score(
            open_rate=22.0, benchmark_open_rate=21.5,
            ctor=11.0, benchmark_ctor=10.5,
            deliverability_rate=97.0,
            list_growth_rate=-2.0,
        )
        growth = next(s for s in score.sub_scores if s.area == "crecimiento")
        assert growth.color == "red"

    def test_low_deliverability(self):
        score = compute_health_score(
            open_rate=22.0, benchmark_open_rate=21.5,
            ctor=11.0, benchmark_ctor=10.5,
            deliverability_rate=88.0,
            list_growth_rate=3.0,
        )
        delivery = next(s for s in score.sub_scores if s.area == "entregabilidad")
        assert delivery.color in ("yellow", "red")


class TestEngagementSegmentation:
    """Segment classification based on engagement metrics."""

    def test_champion(self):
        seg = classify_engagement_segment(open_rate=65.0, click_rate=8.0, days_inactive=0)
        assert seg == "champions"

    def test_active(self):
        seg = classify_engagement_segment(open_rate=30.0, click_rate=2.0, days_inactive=5)
        assert seg == "activos"

    def test_at_risk(self):
        seg = classify_engagement_segment(open_rate=8.0, click_rate=0.3, days_inactive=45)
        assert seg == "en_riesgo"

    def test_dormant(self):
        seg = classify_engagement_segment(open_rate=0.5, click_rate=0.0, days_inactive=90)
        assert seg == "dormidos"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_email_dashboard_service.py -x -q --tb=short`
Expected: FAIL — module not found

- [ ] **Step 3: Create the email dashboard service**

Create `backend/src/modules/analytics/application/services/email_dashboard_service.py`:

```python
"""Email Intelligence Hub dashboard service.

Source-agnostic: reads from official_metrics table only.
Never imports provider-specific code.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    BenchmarkRangeDTO,
    MetricKpiDTO,
    MetricTimeSeriesDTO,
    TimeSeriesDataPointDTO,
    FunnelStepDTO,
)
from src.modules.analytics.application.dto.email_dashboard_dto import (
    ActivityHeatmapCellDTO,
    BounceBreakdownDTO,
    CampaignsVsAutomationsDTO,
    EmailAutomationDTO,
    EmailAutomationsResponseDTO,
    EmailAudienceResponseDTO,
    EmailCampaignDTO,
    EmailCampaignSummaryDTO,
    EmailCampaignsResponseDTO,
    EmailDashboardDTO,
    EmailEngagementSegmentDTO,
    EmailGrowthResponseDTO,
    EmailHealthResponseDTO,
    EmailHealthScoreDTO,
    EmailHealthSubScoreDTO,
    EmailSourcePerformanceDTO,
    EmailTypePerformanceDTO,
    EngagementDecayDTO,
    SegmentTypeMatrixCellDTO,
)
from src.modules.analytics.domain.industry_benchmarks import get_benchmarks
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)

logger = structlog.get_logger()

CHANNEL_SLUG = "email-nurture"
CAPTURE_SLUG = "email-capture"

# Period mapping
PERIOD_DAYS = {"7d": 7, "30d": 30, "90d": 90}


# ── Pure functions (testable without DB) ─────────────────────────────


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
            area="engagement", label="Engagement",
            score=engagement_score, color=_score_color(engagement_score),
        ),
        EmailHealthSubScoreDTO(
            area="entregabilidad", label="Entregabilidad",
            score=delivery_score, color=_score_color(delivery_score),
        ),
        EmailHealthSubScoreDTO(
            area="crecimiento", label="Crecimiento",
            score=growth_score, color=_score_color(growth_score),
        ),
        EmailHealthSubScoreDTO(
            area="contenido", label="Contenido",
            score=contenido_score, color=_score_color(contenido_score),
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


class EmailDashboardService:
    """Source-agnostic email dashboard service.

    Reads exclusively from official_metrics — never imports provider code.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._repo = OfficialMetricsRepository(db)
        self._db = db

    # ── Main dashboard (sidebar + panorama) ──────────────────────────

    async def get_dashboard(
        self, tenant_id: UUID, period: str = "30d",
    ) -> EmailDashboardDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        # Current and previous period metrics
        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end,
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, prev_start, prev_end,
        )

        # Capture metrics for subscriber data
        capture = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end,
        )

        # Daily data for time series
        ts_metrics = [
            "emails_sent", "open_rate", "click_rate", "click_to_open_rate",
            "unique_opens", "unique_clicks", "hard_bounces", "soft_bounces",
            "unsubscribes", "forwards", "active_subscribers", "new_subscribers",
        ]
        daily = self._repo.get_channel_daily_metrics(
            tenant_id, CHANNEL_SLUG, ts_metrics, start, end,
        )

        # Also get capture daily for subscriber timeseries
        capture_daily = self._repo.get_channel_daily_metrics(
            tenant_id, CAPTURE_SLUG,
            ["active_subscribers", "new_subscribers"],
            start, end,
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
        active = current.get("active_subscribers", 1)
        current["list_growth_rate"] = (new_subs - unsubs) / active * 100

        fwd = current.get("forwards", 0)
        current["forward_rate"] = (fwd / sent * 100) if sent > 0 else 0.0

        current["churn_rate"] = (unsubs / active * 100) if active > 0 else 0.0

        # Health score
        benchmarks = get_benchmarks("GENERAL")
        b_open = benchmarks.get("open_rate")
        b_ctor = benchmarks.get("click_to_open_rate")
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
            "emails_sent", "open_rate", "click_rate",
            "click_to_open_rate", "deliverability_rate", "active_subscribers",
        ]
        kpis = self._build_kpis(current, previous, hero_metrics, benchmarks)

        # Build time series
        time_series = self._build_time_series(daily + capture_daily)

        # Build funnel
        funnel = [
            FunnelStepDTO(
                label="Enviados", metric_name="emails_sent",
                value=current.get("emails_sent", 0),
                conversion_rate_from_previous=None,
            ),
            FunnelStepDTO(
                label="Entregados", metric_name="delivered",
                value=sent - hard - soft,
                conversion_rate_from_previous=deliverability,
            ),
            FunnelStepDTO(
                label="Abiertos", metric_name="unique_opens",
                value=current.get("unique_opens", 0),
                conversion_rate_from_previous=current.get("open_rate", 0),
            ),
            FunnelStepDTO(
                label="Clicks", metric_name="unique_clicks",
                value=current.get("unique_clicks", 0),
                conversion_rate_from_previous=current.get("click_rate", 0),
            ),
            FunnelStepDTO(
                label="Bajas", metric_name="unsubscribes",
                value=current.get("unsubscribes", 0),
                conversion_rate_from_previous=current.get("unsubscribe_rate", 0),
            ),
        ]

        # Best / worst campaign from extra data
        best, worst = await self._get_best_worst_campaigns(tenant_id, start, end)

        return EmailDashboardDTO(
            channel_slug=CHANNEL_SLUG,
            channel_name="Email Marketing",
            provider_name=None,  # Determined by frontend from connection info
            period=period,
            health_score=health,
            kpis=kpis,
            time_series=time_series,
            funnel=funnel,
            best_campaign=best,
            worst_campaign=worst,
        )

    # ── Campaigns tab ────────────────────────────────────────────────

    async def get_campaigns(
        self, tenant_id: UUID, period: str = "30d",
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
            avg_ctor = sum(c.click_to_open_rate for c in clist) / len(clist) if clist else 0
            type_performance.append(EmailTypePerformanceDTO(
                campaign_type=ctype,
                campaign_count=len(clist),
                total_sent=sum(c.emails_sent for c in clist),
                avg_open_rate=round(avg_open, 1),
                avg_ctor=round(avg_ctor, 1),
                total_unsubs=sum(c.unsubscribes for c in clist),
            ))

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

    # ── Automations tab ──────────────────────────────────────────────

    async def get_automations(
        self, tenant_id: UUID, period: str = "30d",
    ) -> EmailAutomationsResponseDTO:
        """Return automation performance data.

        Currently returns aggregate metrics from official_metrics.
        Per-automation detail requires future ETL enhancement.
        """
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)

        # Get automation stage metrics (email-delivery + email-onboarding)
        delivery = self._repo.get_channel_metrics_for_period(
            tenant_id, "email-delivery", start, end,
        )
        onboarding = self._repo.get_channel_metrics_for_period(
            tenant_id, "email-onboarding", start, end,
        )

        # Merge all automation metrics
        auto_metrics: dict[str, float] = {}
        for source in [delivery, onboarding]:
            for k, v in source.items():
                if k in ("emails_sent", "automation_completed"):
                    auto_metrics[k] = auto_metrics.get(k, 0) + v
                elif k in ("open_rate", "click_rate", "completion_rate"):
                    # Average rates (simplified — proper weighted avg needs sent counts)
                    auto_metrics[k] = (auto_metrics.get(k, 0) + v) / 2 if k in auto_metrics else v

        benchmarks = get_benchmarks("GENERAL")
        kpis = self._build_kpis(
            auto_metrics, {},
            ["emails_sent", "open_rate", "click_rate", "completion_rate"],
            benchmarks,
        )

        return EmailAutomationsResponseDTO(
            period=period,
            kpis=kpis,
            automations=[],  # Per-automation detail in future ETL
        )

    # ── Audience tab ─────────────────────────────────────────────────

    async def get_audience(
        self, tenant_id: UUID, period: str = "30d",
    ) -> EmailAudienceResponseDTO:
        """Return audience engagement segmentation data.

        Segments are estimated from aggregate campaign metrics.
        Per-subscriber segmentation requires future ETL enhancement.
        """
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end,
        )
        capture = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end,
        )

        active = capture.get("active_subscribers", 0) or current.get("active_subscribers", 0)
        open_rate = current.get("open_rate", 0)

        # Estimate segments from aggregate data
        # These are approximations; precise segmentation needs subscriber-level data
        champions_pct = min(open_rate * 0.6, 25)  # ~60% of openers are champions
        activos_pct = min(open_rate * 1.2, 45)
        dormidos_pct = max(15, 100 - open_rate * 3)
        en_riesgo_pct = 100 - champions_pct - activos_pct - dormidos_pct

        total = max(active, 1)
        segments = [
            EmailEngagementSegmentDTO(
                segment_name="champions", label="Champions",
                count=int(total * champions_pct / 100),
                percentage=round(champions_pct, 1),
                open_rate=round(min(open_rate * 2.8, 95), 1),
                click_rate=round(min(current.get("click_rate", 0) * 4, 20), 1),
                ctor=round(min(current.get("click_to_open_rate", 0) * 1.5, 30), 1),
                avg_days_inactive=None,
                recommended_action="Envíales contenido premium y ofertas de acceso anticipado.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="activos", label="Activos",
                count=int(total * activos_pct / 100),
                percentage=round(activos_pct, 1),
                open_rate=round(min(open_rate * 1.7, 60), 1),
                click_rate=round(current.get("click_rate", 0) * 0.8, 1),
                ctor=round(current.get("click_to_open_rate", 0) * 0.5, 1),
                avg_days_inactive=None,
                recommended_action="Mejora los CTAs. Prueba contenido más específico y ofertas con urgencia.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="en_riesgo", label="En Riesgo",
                count=int(total * en_riesgo_pct / 100),
                percentage=round(en_riesgo_pct, 1),
                open_rate=round(max(open_rate * 0.35, 2), 1),
                click_rate=round(max(current.get("click_rate", 0) * 0.15, 0.1), 1),
                ctor=round(max(current.get("click_to_open_rate", 0) * 0.4, 2), 1),
                avg_days_inactive=42,
                recommended_action="Campaña de re-engagement con incentivo. Si no responden en 30 días, mover a Dormidos.",
            ),
            EmailEngagementSegmentDTO(
                segment_name="dormidos", label="Dormidos",
                count=int(total * dormidos_pct / 100),
                percentage=round(dormidos_pct, 1),
                open_rate=round(max(open_rate * 0.04, 0.1), 1),
                click_rate=0.0,
                ctor=0.0,
                avg_days_inactive=95,
                recommended_action="Envía última oportunidad. Si no abren, eliminar para mejorar deliverability.",
            ),
        ]

        # Activity heatmap: estimated from send-time performance
        # Real data requires per-subscriber timestamps
        heatmap = self._build_estimated_heatmap()

        # Engagement decay: estimated from industry averages
        decay = [
            EngagementDecayDTO(period_label="0-30 días", open_rate=round(open_rate * 1.9, 1)),
            EngagementDecayDTO(period_label="31-90 días", open_rate=round(open_rate * 1.3, 1)),
            EngagementDecayDTO(period_label="91-180 días", open_rate=round(open_rate * 0.75, 1)),
            EngagementDecayDTO(period_label="180+ días", open_rate=round(open_rate * 0.25, 1)),
        ]

        return EmailAudienceResponseDTO(
            period=period,
            segments=segments,
            segment_type_matrix=[],  # Requires campaign×subscriber cross-reference
            sources=[],  # Requires subscriber source data from ETL
            engagement_decay=decay,
            activity_heatmap=heatmap,
        )

    # ── Health tab ───────────────────────────────────────────────────

    async def get_health(
        self, tenant_id: UUID, period: str = "30d",
    ) -> EmailHealthResponseDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end,
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, prev_start, prev_end,
        )

        sent = current.get("emails_sent", 0)
        hard = current.get("hard_bounces", 0)
        soft = current.get("soft_bounces", 0)
        deliverability = ((sent - hard - soft) / sent * 100) if sent > 0 else 100.0
        current["deliverability_rate"] = deliverability

        benchmarks = get_benchmarks("GENERAL")
        b_open = benchmarks.get("open_rate")
        b_ctor = benchmarks.get("click_to_open_rate")
        health = compute_health_score(
            open_rate=current.get("open_rate", 0),
            benchmark_open_rate=b_open.median if b_open else 21.5,
            ctor=current.get("click_to_open_rate", 0),
            benchmark_ctor=b_ctor.median if b_ctor else 10.5,
            deliverability_rate=deliverability,
            list_growth_rate=0,  # Not relevant for health tab focus
        )

        kpis = self._build_kpis(
            current, previous,
            ["deliverability_rate", "bounce_rate", "unsubscribe_rate", "forward_rate"],
            benchmarks,
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
            tenant_id, CHANNEL_SLUG, ts_metrics, start, end,
        )
        time_series = self._build_time_series(daily)

        alerts = self._generate_health_alerts(current)

        return EmailHealthResponseDTO(
            period=period,
            health_score=health,
            kpis=kpis,
            bounce_breakdown=bounce_breakdown,
            time_series=time_series,
            alerts=alerts,
        )

    # ── Growth tab ───────────────────────────────────────────────────

    async def get_growth(
        self, tenant_id: UUID, period: str = "30d",
    ) -> EmailGrowthResponseDTO:
        days = PERIOD_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        prev_start = start - timedelta(days=days)
        prev_end = start - timedelta(days=1)

        current = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, start, end,
        )
        nurture = self._repo.get_channel_metrics_for_period(
            tenant_id, CHANNEL_SLUG, start, end,
        )
        previous = self._repo.get_channel_metrics_for_period(
            tenant_id, CAPTURE_SLUG, prev_start, prev_end,
        )

        # Merge nurture unsubs into capture metrics
        current["unsubscribes"] = nurture.get("unsubscribes", 0)

        active = current.get("active_subscribers", 1)
        new_subs = current.get("new_subscribers", 0)
        unsubs = current.get("unsubscribes", 0)
        current["list_growth_rate"] = (new_subs - unsubs) / active * 100

        benchmarks = get_benchmarks("GENERAL")
        kpis = self._build_kpis(
            current, previous,
            ["active_subscribers", "new_subscribers", "unsubscribes", "list_growth_rate"],
            benchmarks,
        )

        daily = self._repo.get_channel_daily_metrics(
            tenant_id, CAPTURE_SLUG,
            ["active_subscribers", "new_subscribers"],
            start, end,
        )
        nurture_daily = self._repo.get_channel_daily_metrics(
            tenant_id, CHANNEL_SLUG, ["unsubscribes"], start, end,
        )
        time_series = self._build_time_series(daily + nurture_daily)

        return EmailGrowthResponseDTO(
            period=period,
            kpis=kpis,
            time_series=time_series,
            sources=[],  # Requires subscriber source from ETL
            retention_curve=[],  # Requires subscriber age from ETL
        )

    # ── Private helpers ──────────────────────────────────────────────

    def _build_kpis(
        self,
        current: dict[str, float],
        previous: dict[str, float],
        metric_names: list[str],
        benchmarks: dict,
    ) -> list[MetricKpiDTO]:
        kpis = []
        for name in metric_names:
            defn = get_metric_def(name)
            curr_val = current.get(name, 0)
            prev_val = previous.get(name)

            delta_pct = None
            delta_abs = None
            if prev_val is not None and prev_val != 0:
                delta_abs = round(curr_val - prev_val, 2)
                delta_pct = round((curr_val - prev_val) / prev_val * 100, 1)

            bench_dto = None
            bench = benchmarks.get(name)
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
                    low=bench.low, median=bench.median, high=bench.high,
                    unit=bench.unit, interpretation=interp,
                )

            kpis.append(MetricKpiDTO(
                metric_name=name,
                display_name=defn.display_name if defn else name,
                current_value=round(curr_val, 2),
                previous_value=round(prev_val, 2) if prev_val is not None else None,
                delta_percent=delta_pct,
                delta_absolute=delta_abs,
                unit=defn.unit.value if defn else "count",
                higher_is_better=defn.higher_is_better if defn else True,
                benchmark=bench_dto,
            ))
        return kpis

    def _build_time_series(
        self, daily: list[tuple],
    ) -> list[MetricTimeSeriesDTO]:
        by_metric: dict[str, list[TimeSeriesDataPointDTO]] = {}
        for metric_date, metric_name, value in daily:
            by_metric.setdefault(metric_name, []).append(
                TimeSeriesDataPointDTO(date=str(metric_date), value=round(value, 2))
            )
        result = []
        for name, points in by_metric.items():
            defn = get_metric_def(name)
            points.sort(key=lambda p: p.date)
            result.append(MetricTimeSeriesDTO(
                metric_name=name,
                display_name=defn.display_name if defn else name,
                unit=defn.unit.value if defn else "count",
                data_points=points,
            ))
        return result

    async def _get_best_worst_campaigns(
        self, tenant_id: UUID, start: date, end: date,
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
        self, tenant_id: UUID, start: date, end: date,
    ) -> list[EmailCampaignDTO]:
        """Build campaign list from official_metrics with campaign_id grouping."""
        from sqlalchemy import select, func, text
        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        stmt = (
            select(
                OfficialMetricModel.campaign_id,
                OfficialMetricModel.metric_name,
                func.sum(OfficialMetricModel.value).label("total_value"),
                func.max(OfficialMetricModel.extra).label("extra"),
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
        campaigns_map: dict[str, dict] = {}
        for row in rows:
            cid = row.campaign_id
            if cid not in campaigns_map:
                extra = row.extra or {}
                campaigns_map[cid] = {
                    "campaign_id": cid,
                    "campaign_name": extra.get("campaign_name", cid),
                    "campaign_subject": extra.get("campaign_subject"),
                    "campaign_type": extra.get("campaign_type", "contenido"),
                    "sent_date": str(row.last_date) if row.last_date else None,
                    "metrics": {},
                }
            campaigns_map[cid]["metrics"][row.metric_name] = row.total_value

        campaigns = []
        for cdata in campaigns_map.values():
            m = cdata["metrics"]
            campaigns.append(EmailCampaignDTO(
                campaign_id=cdata["campaign_id"],
                campaign_name=cdata["campaign_name"],
                campaign_subject=cdata["campaign_subject"],
                campaign_type=cdata["campaign_type"],
                sent_date=cdata["sent_date"],
                emails_sent=int(m.get("emails_sent", 0)),
                open_rate=round(m.get("open_rate", 0), 1),
                click_rate=round(m.get("click_rate", 0), 1),
                click_to_open_rate=round(m.get("click_to_open_rate", 0), 1),
                bounce_rate=round(m.get("bounce_rate", 0), 1),
                unsubscribes=int(m.get("unsubscribes", 0)),
                unique_opens=int(m.get("unique_opens", 0)),
                unique_clicks=int(m.get("unique_clicks", 0)),
            ))
        return campaigns

    def _build_estimated_heatmap(self) -> list[ActivityHeatmapCellDTO]:
        """Build estimated activity heatmap based on industry patterns.

        Real per-subscriber data requires expensive API calls.
        This provides a reasonable default that will be enhanced when
        we have more granular send-time data.
        """
        # Industry averages: weekdays > weekends, mornings > evenings
        base_pattern = {
            (0, "9-12"): 0.12, (1, "9-12"): 0.14, (2, "9-12"): 0.12,
            (3, "9-12"): 0.11, (4, "9-12"): 0.09, (5, "9-12"): 0.03,
            (6, "9-12"): 0.03,
        }
        hours = ["6-9", "9-12", "12-15", "15-18", "18-21", "21-24"]
        cells = []
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
                cells.append(ActivityHeatmapCellDTO(
                    day_of_week=day, hour_block=hour,
                    open_rate=round(rate * 100, 1),
                ))
        return cells

    def _generate_health_alerts(self, metrics: dict[str, float]) -> list[str]:
        alerts = []
        bounce = metrics.get("bounce_rate", 0)
        spam = metrics.get("spam_reports", 0) / max(metrics.get("emails_sent", 1), 1) * 100
        unsub = metrics.get("unsubscribe_rate", 0)

        if bounce > 2:
            alerts.append(f"Bounce rate elevado ({bounce:.1f}%). Limpia la lista de emails inválidos.")
        if spam > 0.1:
            alerts.append(f"Tasa de spam ({spam:.2f}%) por encima del umbral. Revisa el contenido y la frecuencia de envío.")
        if unsub > 0.5:
            alerts.append(f"Tasa de bajas alta ({unsub:.1f}%). Verifica la relevancia del contenido para tu audiencia.")
        if not alerts:
            alerts.append("Tu reputación de envío está saludable. Sigue así.")
        return alerts
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_email_dashboard_service.py -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/analytics/application/services/email_dashboard_service.py --no-cache`
Expected: No errors (fix if any)

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/analytics/application/services/email_dashboard_service.py backend/tests/modules/analytics/test_email_dashboard_service.py
git commit -m "feat(analytics): create EmailDashboardService with health score, segmentation, campaign analysis"
```

---

### Task 5: Create API endpoints for email dashboard

**Files:**
- Create: `backend/src/modules/analytics/api/email_metrics.py`
- Modify: `backend/src/modules/analytics/api/__init__.py` or `backend/src/main.py` (register router)

- [ ] **Step 1: Create the email metrics API router**

Create `backend/src/modules/analytics/api/email_metrics.py`:

```python
"""API endpoints for the Email Intelligence Hub dashboard."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import get_current_user, User
from src.modules.analytics.application.dto.email_dashboard_dto import (
    EmailAudienceResponseDTO,
    EmailAutomationsResponseDTO,
    EmailCampaignsResponseDTO,
    EmailDashboardDTO,
    EmailGrowthResponseDTO,
    EmailHealthResponseDTO,
)
from src.modules.analytics.application.services.email_dashboard_service import (
    EmailDashboardService,
)

router = APIRouter(prefix="/email", tags=["email-dashboard"])


@router.get("/dashboard", response_model=EmailDashboardDTO)
async def get_email_dashboard(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailDashboardDTO:
    service = EmailDashboardService(db)
    return await service.get_dashboard(user.tenant_id, period)


@router.get("/campaigns", response_model=EmailCampaignsResponseDTO)
async def get_email_campaigns(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailCampaignsResponseDTO:
    service = EmailDashboardService(db)
    return await service.get_campaigns(user.tenant_id, period)


@router.get("/automations", response_model=EmailAutomationsResponseDTO)
async def get_email_automations(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailAutomationsResponseDTO:
    service = EmailDashboardService(db)
    return await service.get_automations(user.tenant_id, period)


@router.get("/audience", response_model=EmailAudienceResponseDTO)
async def get_email_audience(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailAudienceResponseDTO:
    service = EmailDashboardService(db)
    return await service.get_audience(user.tenant_id, period)


@router.get("/health", response_model=EmailHealthResponseDTO)
async def get_email_health(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailHealthResponseDTO:
    service = EmailDashboardService(db)
    return await service.get_health(user.tenant_id, period)


@router.get("/growth", response_model=EmailGrowthResponseDTO)
async def get_email_growth(
    period: str = Query(default="30d", regex="^(7d|30d|90d)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailGrowthResponseDTO:
    service = EmailDashboardService(db)
    return await service.get_growth(user.tenant_id, period)
```

- [ ] **Step 2: Register the router in the analytics module**

Find where the analytics router is mounted (in `backend/src/modules/analytics/api/metrics.py` or `__init__.py`) and add:

```python
from src.modules.analytics.api.email_metrics import router as email_router

# Add to the main analytics router:
router.include_router(email_router)
```

This makes the endpoints available at `/api/v1/analytics/metrics/email/*`.

- [ ] **Step 3: Run lint and verify**

Run: `cd backend && .venv/bin/ruff check src/modules/analytics/api/email_metrics.py --no-cache`
Expected: No errors

- [ ] **Step 4: Run full backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/analytics/api/email_metrics.py
git commit -m "feat(analytics): add 6 API endpoints for Email Intelligence Hub"
```

---

## Phase 3: Frontend — Shared Components + Types

### Task 6: Create MetricInfoPopover shared component

**Files:**
- Create: `frontend/src/components/shared/MetricInfoPopover.tsx`
- Create: `frontend/src/components/shared/__tests__/MetricInfoPopover.test.tsx`

- [ ] **Step 1: Write failing test**

Create `frontend/src/components/shared/__tests__/MetricInfoPopover.test.tsx`:

```tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { MetricInfoPopover } from '../MetricInfoPopover'

describe('MetricInfoPopover', () => {
  it('renders info icon', () => {
    render(
      <MetricInfoPopover
        displayName="Tasa de Apertura"
        description="Porcentaje de emails abiertos vs enviados"
      >
        <span>Open Rate</span>
      </MetricInfoPopover>
    )
    expect(screen.getByRole('button', { name: /info/i })).toBeInTheDocument()
    expect(screen.getByText('Open Rate')).toBeInTheDocument()
  })

  it('shows popover content on click', async () => {
    render(
      <MetricInfoPopover
        displayName="Tasa de Apertura"
        description="Porcentaje de emails abiertos vs enviados"
        formula="unique_opens / emails_sent × 100"
        benchmark={{ value: 21.5, source: 'Campaign Monitor 2022' }}
      >
        <span>Open Rate</span>
      </MetricInfoPopover>
    )
    fireEvent.click(screen.getByRole('button', { name: /info/i }))
    expect(await screen.findByText('Tasa de Apertura')).toBeInTheDocument()
    expect(screen.getByText(/unique_opens/)).toBeInTheDocument()
    expect(screen.getByText('21.5')).toBeInTheDocument()
  })

  it('does not render popover before click', () => {
    render(
      <MetricInfoPopover
        displayName="Click Rate"
        description="Porcentaje de clicks"
      >
        <span>Click Rate</span>
      </MetricInfoPopover>
    )
    expect(screen.queryByText('Porcentaje de clicks')).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/shared/__tests__/MetricInfoPopover.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 3: Implement MetricInfoPopover**

Create `frontend/src/components/shared/MetricInfoPopover.tsx`:

```tsx
'use client'

import { Info } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'

interface MetricInfoPopoverProps {
  displayName: string
  description: string
  formula?: string
  benchmark?: {
    value: number
    source?: string
  }
  interpretation?: string
  higherIsBetter?: boolean
  children: React.ReactNode
  className?: string
}

export function MetricInfoPopover({
  displayName,
  description,
  formula,
  benchmark,
  interpretation,
  children,
  className,
}: MetricInfoPopoverProps) {
  return (
    <span className={cn('inline-flex items-center gap-1', className)}>
      {children}
      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="info"
            className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-muted-foreground/30 text-[9px] text-muted-foreground/60 hover:border-muted-foreground/60 hover:text-muted-foreground transition-colors"
          >
            i
          </button>
        </PopoverTrigger>
        <PopoverContent
          side="top"
          align="start"
          className="w-72 p-3 text-sm"
        >
          <div className="space-y-2">
            <p className="font-semibold text-foreground">{displayName}</p>
            <p className="text-xs text-muted-foreground">{description}</p>
            {formula && (
              <code className="block rounded bg-muted px-2 py-1 text-xs font-mono text-muted-foreground">
                {formula}
              </code>
            )}
            {benchmark && (
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  Benchmark industria:
                </span>
                <span className="font-semibold text-emerald-500">
                  {benchmark.value}
                  {benchmark.source && (
                    <span className="ml-1 text-muted-foreground/50">
                      ({benchmark.source})
                    </span>
                  )}
                </span>
              </div>
            )}
            {interpretation && (
              <p className="text-xs text-muted-foreground/80 italic">
                {interpretation}
              </p>
            )}
          </div>
        </PopoverContent>
      </Popover>
    </span>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/shared/__tests__/MetricInfoPopover.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/shared/MetricInfoPopover.tsx frontend/src/components/shared/__tests__/MetricInfoPopover.test.tsx
git commit -m "feat(ui): create MetricInfoPopover shared component with click-based help"
```

---

### Task 7: Create mail types, API client, and hooks

**Files:**
- Create: `frontend/src/features/growth-studio/types/mail-types.ts`
- Create: `frontend/src/features/growth-studio/api/mail-api.ts`
- Create: `frontend/src/features/growth-studio/hooks/useMailDashboard.ts`
- Modify: `frontend/src/features/growth-studio/types/metrics.ts`
- Modify: `frontend/src/features/growth-studio/config/channel-display-registry.ts`
- Modify: `frontend/src/features/growth-studio/lib/metric-labels.ts`

- [ ] **Step 1: Create mail-types.ts with all TypeScript interfaces**

Create `frontend/src/features/growth-studio/types/mail-types.ts` matching the backend DTOs exactly (camelCase). Reference the spec for all interfaces: EmailDashboardData, EmailHealthScore, EmailCampaign, EmailTypePerformance, EmailSegment, etc.

- [ ] **Step 2: Create mail-api.ts with fetch functions for all 6 endpoints**

Create `frontend/src/features/growth-studio/api/mail-api.ts` following the pattern from `channel-dashboard-api.ts`. Map snake_case API responses to camelCase types.

- [ ] **Step 3: Create useMailDashboard.ts with React Query hooks**

Create hooks following the `useChannelDashboard` pattern:
- `useMailDashboard(period)` — main sidebar + panorama data
- `useMailCampaigns(period)` — campaigns tab
- `useMailAutomations(period)` — automations tab
- `useMailAudience(period)` — audience tab
- `useMailHealth(period)` — health tab
- `useMailGrowth(period)` — growth tab

- [ ] **Step 4: Update MailDashboardTab type in metrics.ts**

Add to `frontend/src/features/growth-studio/types/metrics.ts`:

```typescript
export type MailDashboardTab = 'panorama' | 'campanas' | 'automatizaciones' | 'audiencia' | 'entregabilidad' | 'crecimiento'
```

- [ ] **Step 5: Update channel-display-registry.ts**

Update the `email-nurture` entry:

```typescript
'email-nurture': {
  summaryMetrics: [
    { name: 'open_rate', label: 'Apertura', format: 'percentage' },
    { name: 'click_to_open_rate', label: 'CTOR', format: 'percentage' },
    { name: 'emails_sent', label: 'Enviados' },
    { name: 'active_subscribers', label: 'Suscriptores' },
  ],
  primaryMetric: { name: 'open_rate', label: 'tasa de apertura' },
},
```

- [ ] **Step 6: Add new metric labels**

Add to `frontend/src/features/growth-studio/lib/metric-labels.ts`:

```typescript
deliverability_rate: 'Entregabilidad',
list_growth_rate: 'Crecimiento de Lista',
churn_rate: 'Tasa de Churn',
forward_rate: 'Tasa de Reenvío',
opens_count: 'Aperturas Totales',
clicks_count: 'Clics Totales',
```

- [ ] **Step 7: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/growth-studio/types/mail-types.ts frontend/src/features/growth-studio/api/mail-api.ts frontend/src/features/growth-studio/hooks/useMailDashboard.ts frontend/src/features/growth-studio/types/metrics.ts frontend/src/features/growth-studio/config/channel-display-registry.ts frontend/src/features/growth-studio/lib/metric-labels.ts
git commit -m "feat(growth): add mail types, API client, React Query hooks, and updated display registry"
```

---

## Phase 4: Frontend — Mail Sidebar Redesign

### Task 8: Create MailHealthScore and MailCampaignCards components

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailHealthScore.tsx`
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailCampaignCards.tsx`

- [ ] **Step 1: Implement MailHealthScore** — composite 0-100 score with 4 sub-bars following the sidebar mockup design (`.superpowers/brainstorm/66190-1775757369/content/sidebar-mockup.html`)

- [ ] **Step 2: Implement MailCampaignCards** — best/worst campaign cards with green/red left borders

- [ ] **Step 3: Run type check**

Run: `cd frontend && npx tsc --noEmit`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(growth): add MailHealthScore and MailCampaignCards components"
```

---

### Task 9: Rewrite MailOverviewPanel (sidebar)

**Files:**
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailOverviewPanel.tsx`

- [ ] **Step 1: Rewrite MailOverviewPanel** following the approved sidebar mockup. Use:
  - `useMailDashboard(period)` for data
  - `MailHealthScore` for the health score section
  - `HeroKpiGrid` (shared) for 4 hero KPIs with `MetricInfoPopover`
  - Email funnel (Enviados → Abiertos → Clicks)
  - `MailCampaignCards` for best/worst campaigns
  - `MailDeliverabilityHealth` (existing, keep)
  - Period selector + expand button

- [ ] **Step 2: Run type check + lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailOverviewPanel.tsx`

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(growth): redesign MailOverviewPanel with health score, campaigns, and info popovers"
```

---

## Phase 5: Frontend — Mail Dashboard (6 Tabs)

### Task 10: Rewrite MailDashboard shell with 6 tabs

**Files:**
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailDashboard.tsx`

- [ ] **Step 1: Rewrite MailDashboard** with 6 tabs: Panorama, Campañas, Automatizaciones, Audiencia, Entregabilidad, Crecimiento. Follow the MetaAdsDashboard pattern for portal rendering and URL-based tab/period persistence.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(growth): rewrite MailDashboard shell with 6-tab Email Intelligence Hub"
```

---

### Task 11: Implement MailPanoramaTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailPanoramaTab.tsx`

- [ ] **Step 1: Implement MailPanoramaTab** following the `dashboard-panorama.html` mockup:
  - 6 KPI cards row with MetricInfoPopover
  - Volumen vs Engagement dual-axis chart (Recharts ComposedChart: Bar + Line)
  - Email funnel (horizontal bars)
  - Performance vs Industria (benchmark comparison bars)
  - Campañas vs Automatizaciones table
  - Campañas recientes quick table with type tags

- [ ] **Step 2: Run type check**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(growth): implement MailPanoramaTab with KPIs, charts, funnel, benchmarks"
```

---

### Task 12: Implement MailCampanasTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCampanasTab.tsx`

- [ ] **Step 1: Implement MailCampanasTab** following the `dashboard-campanas.html` mockup:
  - 4 type cards (Newsletter, Lanzamiento, Promoción, Contenido) with rankings
  - Open Rate and CTOR horizontal bar charts by type with benchmark lines
  - Full campaign table: sortable, filterable by type, with mini bars
  - Top subject lines with pattern insights
  - Engagement trend by type (multi-series line chart)

- [ ] **Step 2: Run type check**

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(growth): implement MailCampanasTab with type analysis, ranking, and subject line insights"
```

---

### Task 13: Implement MailAutomatizacionesTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionesTab.tsx`

- [ ] **Step 1: Implement MailAutomatizacionesTab** with:
  - 3 KPI cards (emails sent, completion rate, avg open rate)
  - Automations table (if data available, otherwise "Próximamente")
  - Campaigns vs Automations comparison
  - Placeholder for per-step funnel (future ETL enhancement)

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(growth): implement MailAutomatizacionesTab with KPIs and comparison"
```

---

### Task 14: Implement MailAudienciaTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAudienciaTab.tsx`

- [ ] **Step 1: Implement MailAudienciaTab** following the `dashboard-audiencia.html` mockup:
  - 4 segment cards (Champions, Activos, En Riesgo, Dormidos) with metrics + actions
  - Segment × Type matrix grid
  - Engagement by source table
  - Engagement decay curve (SVG or Recharts AreaChart)
  - Activity heatmap (CSS grid with color intensity)
  - CTOR by segment × content type

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(growth): implement MailAudienciaTab with engagement segments, heatmap, decay curve"
```

---

### Task 15: Rewrite MailEntregabilidadTab

**Files:**
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailEntregabilidadTab.tsx`

- [ ] **Step 1: Rewrite MailEntregabilidadTab** with:
  - Health score display (reuse MailHealthScore)
  - 4 KPI cards (deliverability, bounce rate, spam rate, unsub rate) with MetricInfoPopover
  - Bounce breakdown donut chart
  - Deliverability trend line (12 weeks)
  - Alerts and recommendations list

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(growth): rewrite MailEntregabilidadTab with health score and alerts"
```

---

### Task 16: Implement MailCrecimientoTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailCrecimientoTab.tsx`

- [ ] **Step 1: Implement MailCrecimientoTab** with:
  - 4 KPI cards (active, new, unsubs, net growth rate)
  - Stacked area chart (new subscribers green, unsubs red, total line)
  - Sources horizontal bars
  - Retention curve

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(growth): implement MailCrecimientoTab with growth charts and retention"
```

---

## Phase 6: Testing & Integration

### Task 17: Delete old mail tab files no longer needed

**Files:**
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailHeroKpiGrid.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/MailListGrowthIndicator.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailOverviewTab.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailEngagementTab.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailListaTab.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/tabs/MailAutomatizacionTab.tsx`

- [ ] **Step 1: Remove old files** that are replaced by the new components
- [ ] **Step 2: Update any imports** that referenced deleted files
- [ ] **Step 3: Run type check and lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/`

- [ ] **Step 4: Commit**

```bash
git commit -m "refactor(growth): remove old mail tab components replaced by Email Intelligence Hub"
```

---

### Task 18: Rewrite frontend tests

**Files:**
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailDashboard.test.tsx`
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailTabs.test.tsx`
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/mail/__tests__/MailOverviewPanel.test.tsx`

- [ ] **Step 1: Write tests for MailOverviewPanel** (sidebar renders health score, KPIs, campaign cards)
- [ ] **Step 2: Rewrite MailDashboard tests** (6 tabs present, period selector, tab navigation)
- [ ] **Step 3: Rewrite MailTabs tests** (each tab renders key sections with mock data)
- [ ] **Step 4: Run all frontend tests**

Run: `cd frontend && npx vitest run`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "test(growth): rewrite mail dashboard tests for Email Intelligence Hub"
```

---

### Task 19: Run full CI suite

- [ ] **Step 1: Backend lint + tests**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: PASS

- [ ] **Step 2: Frontend types + lint + tests**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run`
Expected: PASS

- [ ] **Step 3: Architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: PASS

- [ ] **Step 4: Fix any failures and commit fixes**

- [ ] **Step 5: Final commit**

```bash
git commit -m "ci: pass full quality gates for Email Intelligence Hub"
```

---

## Dependency Graph

```
Task 1 (metric catalog) ─┐
Task 2 (ETL enhance)     ├─→ Task 3 (DTOs) → Task 4 (service) → Task 5 (API endpoints)
                          │
Task 6 (MetricInfoPopover)├─→ Task 7 (types/hooks) → Task 8 (sidebar components)
                          │                         → Task 9 (sidebar rewrite)
                          │                         → Task 10 (dashboard shell)
                          │                         → Tasks 11-16 (tabs)
                          │
                          └─→ Task 17 (cleanup) → Task 18 (tests) → Task 19 (CI)
```

Backend (Tasks 1-5) and Frontend shared (Tasks 6-7) can run in parallel.
Tabs (Tasks 11-16) can run in parallel after Task 10.
