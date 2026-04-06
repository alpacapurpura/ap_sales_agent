# Meta Ads Dashboard — Rediseño Completo

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rediseñar las 5 pestañas del Meta Ads Dashboard (sidebar + fullpage) eliminando duplicación y llenando los 3 tabs placeholder con contenido operativo real.

**Architecture:** El backend ya tiene campaign metadata (`ad_campaigns`, `ad_sets`, `ads`) y métricas por `campaign_id` en `official_metrics`. Necesitamos un nuevo endpoint que cruce metadata + métricas agregadas. Frontend: renombrar tabs, redistribuir datos sin duplicación, implementar 3 tabs nuevos.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, React 18, Next.js, Tailwind CSS, Shadcn UI, Recharts, React Query, Vitest.

**Mockup de referencia:** `docs/mockups/meta-ads-dashboard-complete.html`

---

## Tab Mapping

| Antes | Ahora | Estado |
|---|---|---|
| Overview | **Resumen** | Refactor: quitar reach/freq, agregar alertas, 6 KPIs |
| Campañas (placeholder) | **Campañas** | NUEVO: tabla operativa per-campaign |
| Video (placeholder) | **Creativos** | NUEVO: top ads, format comparison, video retention |
| Audiencia (placeholder) | **Audiencia** | NUEVO: demographics + reach/freq (moved from Overview) |
| Costos | **Costos** | Expand: + cost evolution chart + CPA comparison |

---

## File Structure

```
backend/src/modules/analytics/
├── application/
│   ├── dto/
│   │   └── campaign_dto.py           # MODIFY — add CampaignPerformanceDTO, CampaignWithMetricsDTO
│   └── services/
│       └── campaign_service.py       # MODIFY — add get_performance() method
├── api/
│   └── campaigns.py                  # MODIFY — add /campaigns/performance endpoint

frontend/src/features/growth-studio/
├── types/
│   └── metrics.ts                    # MODIFY — update MetaAdsDashboardTab type
├── api/
│   └── campaigns-api.ts              # CREATE — React Query hooks for campaign performance
├── components/metrics-dashboard/sidebar/meta-ads/
│   ├── MetaAdsDashboard.tsx          # MODIFY — rename tabs, pass campaign data
│   ├── MetaAdsOverviewPanel.tsx      # MODIFY — add top campaigns preview to sidebar
│   └── tabs/
│       ├── ResumenTab.tsx            # CREATE (replaces OverviewTab import)
│       ├── CampaignsTab.tsx          # REWRITE — full operational table
│       ├── CreativosTab.tsx          # CREATE (replaces VideoTab import)
│       ├── AudienciaTab.tsx          # CREATE (replaces AudienceTab import)
│       └── CostosTab.tsx             # CREATE (replaces CostsTab import)

backend/tests/modules/analytics/
├── test_campaign_performance.py      # CREATE — test new endpoint/service

frontend/src/features/growth-studio/
├── api/__tests__/
│   └── campaigns-api.test.ts         # CREATE
├── components/metrics-dashboard/sidebar/meta-ads/__tests__/
│   └── CampaignsTab.test.tsx         # CREATE
```

---

## Task 1: Backend — New DTO `CampaignPerformanceDTO`

**Files:**
- Modify: `backend/src/modules/analytics/application/dto/campaign_dto.py`

- [ ] **Step 1: Add new DTOs at the end of campaign_dto.py**

```python
class CampaignMetricsDTO(BaseModel):
    """Aggregated metrics for a single campaign."""

    spend: float = 0.0
    conversions: float = 0.0
    cpa: float | None = None
    roas: float | None = None
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    frequency: float | None = None
    impressions: float = 0.0
    clicks: float = 0.0
    reach: float = 0.0


class CampaignWithMetricsDTO(BaseModel):
    """Campaign metadata + aggregated performance metrics."""

    external_id: str
    name: str
    objective: str | None = None
    status: str | None = None
    effective_status: str | None = None
    daily_budget: int | None = None
    lifetime_budget: int | None = None
    budget_remaining: int | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
    ad_sets_count: int = 0
    ads_count: int = 0
    metrics: CampaignMetricsDTO = CampaignMetricsDTO()
    health: str = "good"  # "good" | "warning" | "critical"


class CampaignPerformanceDTO(BaseModel):
    """Full campaign performance dashboard response."""

    campaigns: list[CampaignWithMetricsDTO]
    recommendations: list[RecommendationDTO]
    total_campaigns: int
    active_campaigns: int
    currency: str | None = None
    last_synced: datetime | None = None
```

- [ ] **Step 2: Verify lint**

```bash
cd backend && .venv/bin/ruff check src/modules/analytics/application/dto/campaign_dto.py --no-cache
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/analytics/application/dto/campaign_dto.py
git commit -m "feat(analytics): add CampaignPerformanceDTO for per-campaign metrics"
```

---

## Task 2: Backend — New service method `get_performance()`

**Files:**
- Modify: `backend/src/modules/analytics/application/services/campaign_service.py`

- [ ] **Step 1: Write failing test**

Create `backend/tests/modules/analytics/test_campaign_performance.py`:

```python
"""Tests for campaign performance aggregation."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.modules.analytics.application.services.campaign_service import CampaignService

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


class TestGetPerformance:
    """Tests for CampaignService.get_performance()."""

    def _make_campaign_row(self, **overrides):
        defaults = {
            "external_id": "camp_1",
            "name": "Test Campaign",
            "objective": "OUTCOME_SALES",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": 50000,
            "lifetime_budget": None,
            "budget_remaining": None,
            "buying_type": "AUCTION",
            "start_time": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "stop_time": None,
            "ad_sets_count": 2,
            "ads_count": 5,
        }
        defaults.update(overrides)
        mock_row = MagicMock()
        mock_row._mapping = defaults
        return mock_row

    def _make_metric_row(self, campaign_id, metric_name, total_value):
        mock_row = MagicMock()
        mock_row._mapping = {
            "campaign_id": campaign_id,
            "metric_name": metric_name,
            "total_value": total_value,
        }
        return mock_row

    def _make_rec_row(self, **overrides):
        defaults = {
            "recommendation_type": "CREATIVE_FATIGUE",
            "source": "account",
            "title": "Creative fatigue",
            "body": "Refresh your creatives",
            "importance": "HIGH",
            "lift_estimate": None,
            "opportunity_score": 0.8,
            "url": None,
            "object_ids": [],
        }
        defaults.update(overrides)
        mock_row = MagicMock()
        mock_row._mapping = defaults
        return mock_row

    def test_returns_campaigns_with_metrics(self):
        db = MagicMock()
        # 1st call: campaigns query
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[
                self._make_campaign_row(external_id="camp_1", name="Campaign A"),
            ])),
            # 2nd call: metrics aggregated by campaign
            MagicMock(fetchall=MagicMock(return_value=[
                self._make_metric_row("camp_1", "spend", 1000.0),
                self._make_metric_row("camp_1", "conversions", 50.0),
                self._make_metric_row("camp_1", "clicks", 2000.0),
                self._make_metric_row("camp_1", "impressions", 100000.0),
            ])),
            # 3rd call: recommendations
            MagicMock(fetchall=MagicMock(return_value=[])),
            # 4th call: currency
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"currency": "MXN"},
            ))),
            # 5th call: last_synced
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"last_synced": datetime(2026, 4, 6, tzinfo=timezone.utc)},
            ))),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        assert result.total_campaigns == 1
        assert result.active_campaigns == 1
        assert result.campaigns[0].name == "Campaign A"
        assert result.campaigns[0].metrics.spend == 1000.0
        assert result.campaigns[0].metrics.conversions == 50.0
        assert result.campaigns[0].metrics.cpa == 20.0  # 1000/50
        assert result.currency == "MXN"

    def test_health_critical_when_cpa_3x_average(self):
        db = MagicMock()
        db.execute.side_effect = [
            # campaigns
            MagicMock(fetchall=MagicMock(return_value=[
                self._make_campaign_row(external_id="camp_good", name="Good"),
                self._make_campaign_row(external_id="camp_bad", name="Bad"),
            ])),
            # metrics
            MagicMock(fetchall=MagicMock(return_value=[
                self._make_metric_row("camp_good", "spend", 100.0),
                self._make_metric_row("camp_good", "conversions", 10.0),
                self._make_metric_row("camp_bad", "spend", 300.0),
                self._make_metric_row("camp_bad", "conversions", 1.0),
            ])),
            # recommendations
            MagicMock(fetchall=MagicMock(return_value=[])),
            # currency
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"currency": "USD"},
            ))),
            # last_synced
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"last_synced": None},
            ))),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        good = next(c for c in result.campaigns if c.name == "Good")
        bad = next(c for c in result.campaigns if c.name == "Bad")
        assert good.health == "good"
        assert bad.health == "critical"  # CPA 300 vs avg 36.36 → >3x

    def test_empty_campaigns_returns_empty(self):
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"currency": None},
            ))),
            MagicMock(fetchone=MagicMock(return_value=MagicMock(
                _mapping={"last_synced": None},
            ))),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        assert result.total_campaigns == 0
        assert result.campaigns == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && .venv/bin/pytest tests/modules/analytics/test_campaign_performance.py -x -v
```

Expected: FAIL — `CampaignService.get_performance` does not exist.

- [ ] **Step 3: Implement `get_performance()` in campaign_service.py**

Add to `CampaignService` class after `get_overview()`:

```python
def get_performance(
    self, tenant_id: UUID, period: str = "30d"
) -> "CampaignPerformanceDTO":
    """Get campaigns with aggregated metrics for the given period."""
    from datetime import date, timedelta

    from src.modules.analytics.application.dto.campaign_dto import (
        CampaignMetricsDTO,
        CampaignPerformanceDTO,
        CampaignWithMetricsDTO,
        RecommendationDTO,
    )

    # Parse period
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # 1. Campaigns with counts
    camp_rows = self._db.execute(
        text("""
            SELECT c.*,
                (SELECT COUNT(*) FROM ad_sets s
                 WHERE s.tenant_id = c.tenant_id
                   AND s.campaign_external_id = c.external_id
                   AND s.deleted_at IS NULL) AS ad_sets_count,
                (SELECT COUNT(*) FROM ads a
                 WHERE a.tenant_id = c.tenant_id
                   AND a.campaign_external_id = c.external_id
                   AND a.deleted_at IS NULL) AS ads_count
            FROM ad_campaigns c
            WHERE c.tenant_id = :tenant_id
              AND c.deleted_at IS NULL
            ORDER BY
                CASE c.effective_status
                    WHEN 'ACTIVE' THEN 1
                    WHEN 'WITH_ISSUES' THEN 2
                    WHEN 'IN_PROCESS' THEN 3
                    WHEN 'PAUSED' THEN 4
                    ELSE 5
                END,
                c.name
        """),
        {"tenant_id": str(tenant_id)},
    ).fetchall()

    # 2. Metrics aggregated by campaign_id for the period
    metric_rows = self._db.execute(
        text("""
            SELECT campaign_id, metric_name,
                   SUM(value) AS total_value
            FROM official_metrics
            WHERE tenant_id = :tenant_id
              AND channel_slug = 'meta-ads'
              AND campaign_id IS NOT NULL
              AND metric_date BETWEEN :start_date AND :end_date
            GROUP BY campaign_id, metric_name
        """),
        {
            "tenant_id": str(tenant_id),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    ).fetchall()

    # Build metrics lookup: {campaign_id: {metric_name: value}}
    metrics_by_campaign: dict[str, dict[str, float]] = {}
    for row in metric_rows:
        r = row._mapping
        cid = r["campaign_id"]
        if cid not in metrics_by_campaign:
            metrics_by_campaign[cid] = {}
        metrics_by_campaign[cid][r["metric_name"]] = float(r["total_value"])

    # 3. Build campaign list with metrics
    campaigns: list[CampaignWithMetricsDTO] = []
    all_cpas: list[float] = []

    for row in camp_rows:
        r = row._mapping
        ext_id = r["external_id"]
        m = metrics_by_campaign.get(ext_id, {})

        spend = m.get("spend", 0.0)
        conversions = m.get("conversions", 0.0)
        clicks = m.get("clicks", 0.0)
        impressions = m.get("impressions", 0.0)

        cpa = spend / conversions if conversions > 0 else None
        roas_val = m.get("ROAS") or (
            (conversions * (spend / conversions if conversions > 0 else 0))
            if False
            else m.get("ROAS")
        )
        ctr = (clicks / impressions * 100) if impressions > 0 else None
        cpc = spend / clicks if clicks > 0 else None
        cpm = (spend / impressions * 1000) if impressions > 0 else None

        metrics_dto = CampaignMetricsDTO(
            spend=spend,
            conversions=conversions,
            cpa=round(cpa, 2) if cpa is not None else None,
            roas=round(float(roas_val), 2) if roas_val else None,
            ctr=round(ctr, 2) if ctr is not None else None,
            cpc=round(cpc, 2) if cpc is not None else None,
            cpm=round(cpm, 2) if cpm is not None else None,
            frequency=m.get("frequency"),
            impressions=impressions,
            clicks=clicks,
            reach=m.get("reach", 0.0),
        )

        if cpa is not None:
            all_cpas.append(cpa)

        campaigns.append(
            CampaignWithMetricsDTO(
                external_id=ext_id,
                name=r["name"],
                objective=r.get("objective"),
                status=r.get("status"),
                effective_status=r.get("effective_status"),
                daily_budget=r.get("daily_budget"),
                lifetime_budget=r.get("lifetime_budget"),
                budget_remaining=r.get("budget_remaining"),
                start_time=r.get("start_time"),
                stop_time=r.get("stop_time"),
                ad_sets_count=r.get("ad_sets_count", 0),
                ads_count=r.get("ads_count", 0),
                metrics=metrics_dto,
                health="good",  # placeholder, computed below
            )
        )

    # 4. Compute health based on CPA vs average
    avg_cpa = sum(all_cpas) / len(all_cpas) if all_cpas else None
    for camp in campaigns:
        if camp.metrics.cpa is not None and avg_cpa and avg_cpa > 0:
            ratio = camp.metrics.cpa / avg_cpa
            if ratio > 3:
                camp.health = "critical"
            elif ratio > 1.8:
                camp.health = "warning"
            else:
                camp.health = "good"
        elif camp.effective_status in ("WITH_ISSUES",):
            camp.health = "critical"

    # 5. Recommendations
    rec_rows = self._db.execute(
        text("""
            SELECT * FROM ad_recommendations
            WHERE tenant_id = :tenant_id
              AND deleted_at IS NULL
            ORDER BY opportunity_score DESC NULLS LAST, importance, created_at DESC
            LIMIT 20
        """),
        {"tenant_id": str(tenant_id)},
    ).fetchall()

    recommendations = [
        RecommendationDTO(
            recommendation_type=r._mapping["recommendation_type"],
            source=r._mapping["source"],
            title=r._mapping.get("title"),
            body=r._mapping.get("body"),
            importance=r._mapping.get("importance"),
            lift_estimate=r._mapping.get("lift_estimate"),
            opportunity_score=r._mapping.get("opportunity_score"),
            url=r._mapping.get("url"),
            object_ids=r._mapping.get("object_ids", []),
        )
        for r in rec_rows
    ]

    # 6. Currency from official_metrics
    currency_row = self._db.execute(
        text("""
            SELECT currency FROM official_metrics
            WHERE tenant_id = :tenant_id
              AND channel_slug = 'meta-ads'
              AND currency IS NOT NULL
            LIMIT 1
        """),
        {"tenant_id": str(tenant_id)},
    ).fetchone()
    currency = currency_row._mapping["currency"] if currency_row else None

    # 7. Last synced
    last_synced_row = self._db.execute(
        text("""
            SELECT MAX(updated_at) AS last_synced FROM ad_campaigns
            WHERE tenant_id = :tenant_id AND deleted_at IS NULL
        """),
        {"tenant_id": str(tenant_id)},
    ).fetchone()
    last_synced = last_synced_row._mapping["last_synced"] if last_synced_row else None

    active_count = sum(
        1 for c in campaigns if c.effective_status == "ACTIVE"
    )

    return CampaignPerformanceDTO(
        campaigns=campaigns,
        recommendations=recommendations,
        total_campaigns=len(campaigns),
        active_campaigns=active_count,
        currency=currency,
        last_synced=last_synced,
    )
```

Add required import at top of file:

```python
from datetime import date, timedelta
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd backend && .venv/bin/pytest tests/modules/analytics/test_campaign_performance.py -x -v
```

- [ ] **Step 5: Lint**

```bash
cd backend && .venv/bin/ruff check src/modules/analytics/application/services/campaign_service.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/analytics/application/services/campaign_service.py backend/tests/modules/analytics/test_campaign_performance.py
git commit -m "feat(analytics): add get_performance() for per-campaign metrics aggregation"
```

---

## Task 3: Backend — New API endpoint `/campaigns/performance`

**Files:**
- Modify: `backend/src/modules/analytics/api/campaigns.py`
- Modify: `backend/src/modules/analytics/application/dto/campaign_dto.py` (add to imports)

- [ ] **Step 1: Add endpoint to campaigns.py**

Add import at top:

```python
from fastapi import APIRouter, Depends, Query
```

Add to imports from dto:

```python
from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdSetDTO,
    CampaignOverviewDTO,
    CampaignPerformanceDTO,
)
```

Add new endpoint after `get_campaigns_overview`:

```python
@router.get("/performance", response_model=CampaignPerformanceDTO)
async def get_campaigns_performance(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all campaigns with aggregated performance metrics."""
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {valid_periods}",
        )
    service = CampaignService(db)
    return service.get_performance(user.tenant_id, period)
```

- [ ] **Step 2: Lint + test**

```bash
cd backend && .venv/bin/ruff check src/modules/analytics/api/campaigns.py --no-cache
cd backend && .venv/bin/pytest tests/modules/analytics/test_campaign_performance.py -x -v
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/analytics/api/campaigns.py
git commit -m "feat(analytics): add GET /campaigns/performance endpoint"
```

---

## Task 4: Frontend — Update types + create campaigns API

**Files:**
- Modify: `frontend/src/features/growth-studio/types/metrics.ts`
- Create: `frontend/src/features/growth-studio/api/campaigns-api.ts`

- [ ] **Step 1: Update `MetaAdsDashboardTab` type in metrics.ts**

Find and replace the type:

```typescript
// Before:
export type MetaAdsDashboardTab = 'overview' | 'campaigns' | 'audience' | 'video' | 'costs';

// After:
export type MetaAdsDashboardTab = 'resumen' | 'campanas' | 'creativos' | 'audiencia' | 'costos';
```

Add new types at end of file:

```typescript
// ── Campaign Performance Types ──

export interface CampaignMetrics {
  spend: number;
  conversions: number;
  cpa: number | null;
  roas: number | null;
  ctr: number | null;
  cpc: number | null;
  cpm: number | null;
  frequency: number | null;
  impressions: number;
  clicks: number;
  reach: number;
}

export interface CampaignWithMetrics {
  externalId: string;
  name: string;
  objective: string | null;
  status: string | null;
  effectiveStatus: string | null;
  dailyBudget: number | null;
  lifetimeBudget: number | null;
  budgetRemaining: number | null;
  startTime: string | null;
  stopTime: string | null;
  adSetsCount: number;
  adsCount: number;
  metrics: CampaignMetrics;
  health: 'good' | 'warning' | 'critical';
}

export interface CampaignRecommendation {
  recommendationType: string;
  source: string;
  title: string | null;
  body: string | null;
  importance: string | null;
  liftEstimate: string | null;
  opportunityScore: number | null;
  url: string | null;
  objectIds: string[];
}

export interface CampaignPerformanceData {
  campaigns: CampaignWithMetrics[];
  recommendations: CampaignRecommendation[];
  totalCampaigns: number;
  activeCampaigns: number;
  currency: string | null;
  lastSynced: string | null;
}
```

- [ ] **Step 2: Create campaigns-api.ts**

```typescript
import { useQuery } from '@tanstack/react-query';

import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { useAuth } from '@clerk/nextjs';

import type { CampaignPerformanceData, MetaAdsPeriod } from '../types/metrics';

const API_BASE = config.api.baseUrl;

export async function fetchCampaignPerformance(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<CampaignPerformanceData> {
  const url = `${API_BASE}/api/v1/analytics/campaigns/performance?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch campaign performance: ${res.status}`);
  }
  return res.json();
}

export function useCampaignPerformance(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['campaign-performance', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchCampaignPerformance(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 min
  });
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/growth-studio/types/metrics.ts frontend/src/features/growth-studio/api/campaigns-api.ts
git commit -m "feat(frontend): add campaign performance types and API hook"
```

---

## Task 5: Frontend — Rewrite MetaAdsDashboard.tsx (tab container)

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`

- [ ] **Step 1: Update imports and tabs**

Replace the entire file content:

```typescript
'use client';

import { useState } from 'react';
import { createPortal } from 'react-dom';
import { ArrowLeft, BarChart3, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import { useCampaignPerformance } from '../../../../api/campaigns-api';
import type { MetaAdsPeriod, MetaAdsDashboardTab } from '../../../../types/metrics';
import { MetaAdsPeriodSelector } from './MetaAdsPeriodSelector';
import { ResumenTab } from './tabs/ResumenTab';
import { CampaignsTab } from './tabs/CampaignsTab';
import { CreativosTab } from './tabs/CreativosTab';
import { AudienciaTab } from './tabs/AudienciaTab';
import { CostosTab } from './tabs/CostosTab';

interface MetaAdsDashboardProps {
  onClose: () => void;
}

export function MetaAdsDashboard({ onClose }: MetaAdsDashboardProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const [activeTab, setActiveTab] = useState<MetaAdsDashboardTab>('resumen');
  const { data: dashboardData, isLoading: isDashboardLoading } = useChannelDashboard('meta-ads', period);
  const { data: campaignData, isLoading: isCampaignLoading } = useCampaignPerformance(period);

  const content = (
    <div className="fixed inset-0 z-50 flex flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onClose} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <h1 className="text-lg font-semibold">Meta Ads &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <MetaAdsPeriodSelector value={period} onChange={setPeriod} />
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={v => setActiveTab(v as MetaAdsDashboardTab)}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="resumen">Resumen</TabsTrigger>
            <TabsTrigger value="campanas">Campañas</TabsTrigger>
            <TabsTrigger value="creativos">Creativos</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="costos">Costos</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="resumen" className="m-0 p-6">
            <ResumenTab data={dashboardData} isLoading={isDashboardLoading} />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <CampaignsTab
              data={campaignData}
              isLoading={isCampaignLoading}
              currency={campaignData?.currency ?? dashboardData?.kpis.find(k => k.currency)?.currency}
            />
          </TabsContent>
          <TabsContent value="creativos" className="m-0 p-6">
            <CreativosTab data={dashboardData} isLoading={isDashboardLoading} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <AudienciaTab data={dashboardData} isLoading={isDashboardLoading} />
          </TabsContent>
          <TabsContent value="costos" className="m-0 p-6">
            <CostosTab
              data={dashboardData}
              campaignData={campaignData}
              isLoading={isDashboardLoading}
            />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (typeof document === 'undefined') return null;
  return createPortal(content, document.body);
}
```

- [ ] **Step 2: Verify no TypeScript errors (will have missing tab imports — that's expected, they're created in next tasks)**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx
git commit -m "refactor(meta-ads): restructure dashboard tabs — resumen, campañas, creativos, audiencia, costos"
```

---

## Task 6: Frontend — Create ResumenTab (replaces OverviewTab)

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/ResumenTab.tsx`

- [ ] **Step 1: Create ResumenTab.tsx**

This tab shows: 6 KPIs + alerts banner + spend vs conversions chart + full funnel.
NO reach/frequency (moved to Audiencia), NO per-campaign data, NO cost details.

```typescript
'use client';

import { Loader2, TrendingDown, TrendingUp, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { Bar, ComposedChart, CartesianGrid, Line, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { formatMoney } from '@/lib/format-money';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import { cn } from '@/lib/utils';
import type { ChannelDashboardData, MetricKpiData } from '../../../../../types/metrics';

interface ResumenTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const RESUMEN_KPIS = ['spend', 'ROAS', 'conversions', 'CPA', 'CTR', 'reach'];

function formatKpiValue(value: number, unit: string, currency?: string): string {
  if (unit === 'currency') return formatMoney(value, currency || 'USD');
  if (unit === 'percentage') return `${value.toFixed(2)}%`;
  if (unit === 'ratio') return `${value.toFixed(2)}x`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString('en-US');
}

const KPI_TOOLTIPS: Record<string, string> = {
  spend: 'Total invertido en Meta Ads durante el periodo seleccionado.',
  ROAS: 'ROAS = Por cada $1 invertido, cuánto recuperas. Ej: 3.2x = ganas $3.20 por cada $1.',
  conversions: 'Total de resultados (ventas, leads, etc.) generados por todas tus campañas.',
  CPA: 'CPA = Costo por cada resultado obtenido. Menor es mejor.',
  CTR: 'CTR = % de personas que ven tu anuncio y hacen clic. Más alto es mejor.',
  reach: 'Personas únicas que vieron tus anuncios. No es una suma diaria.',
};

export function ResumenTab({ data, isLoading }: ResumenTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const kpis = RESUMEN_KPIS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  const spendSeries = data.timeSeries.find(ts => ts.metricName === 'spend');
  const convSeries = data.timeSeries.find(ts => ts.metricName === 'conversions');

  const compositeData = spendSeries?.dataPoints.map(sp => {
    const conv = convSeries?.dataPoints.find(c => c.date === sp.date);
    return {
      date: sp.date.slice(5),
      spend: sp.value,
      conversions: conv?.value ?? 0,
    };
  }) ?? [];

  return (
    <div className="space-y-6">
      {/* 6 KPI cards */}
      <div className="grid grid-cols-6 gap-2.5">
        {kpis.map(kpi => {
          const isPositive =
            kpi.deltaPct != null &&
            (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);
          return (
            <div
              key={kpi.metricName}
              className="rounded-lg border bg-card p-3 space-y-1"
              title={KPI_TOOLTIPS[kpi.metricName] ?? ''}
            >
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                {kpi.displayName}
              </p>
              <p className="text-xl font-bold tabular-nums">
                {formatKpiValue(kpi.currentValue, kpi.unit, kpi.currency)}
              </p>
              {kpi.deltaPct != null && (
                <span
                  className={cn(
                    'inline-flex items-center gap-0.5 text-[10px] font-medium',
                    isPositive ? 'text-emerald-600' : 'text-red-600',
                  )}
                >
                  {isPositive ? (
                    <TrendingUp className="h-3 w-3" />
                  ) : (
                    <TrendingDown className="h-3 w-3" />
                  )}
                  {Math.abs(kpi.deltaPct).toFixed(1)}% vs ant.
                </span>
              )}
              {kpi.benchmark && (
                <BenchmarkBadge
                  value={kpi.currentValue}
                  benchmark={kpi.benchmark}
                  higherIsBetter={kpi.higherIsBetter}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* 2-column: Chart + Funnel */}
      <div className="grid grid-cols-2 gap-4">
        {/* Spend vs Conversions chart */}
        {compositeData.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
              Inversión vs Resultados
            </h3>
            <ChartContainer
              config={{
                spend: { label: 'Inversión', color: 'hsl(var(--chart-1))' },
                conversions: { label: 'Resultados', color: 'hsl(var(--chart-2))' },
              }}
              className="h-[250px] w-full"
            >
              <ComposedChart data={compositeData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis yAxisId="left" className="text-xs" />
                <YAxis yAxisId="right" orientation="right" className="text-xs" />
                <RechartsTooltip />
                <Bar yAxisId="left" dataKey="spend" fill="var(--color-spend)" radius={[2, 2, 0, 0]} />
                <Line yAxisId="right" type="monotone" dataKey="conversions" stroke="var(--color-conversions)" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ChartContainer>
          </div>
        )}

        {/* Full Funnel */}
        <div className="space-y-2">
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Embudo de conversión
          </h3>
          <MetaAdsMiniFunnel steps={data.funnel.steps} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/ResumenTab.tsx
git commit -m "feat(meta-ads): create ResumenTab — 6 KPIs + trend chart + funnel"
```

---

## Task 7: Frontend — Rewrite CampaignsTab (operational table)

**Files:**
- Rewrite: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx`

- [ ] **Step 1: Rewrite CampaignsTab.tsx with full operational table**

This is the largest component. Includes: summary KPIs, alerts, campaign table with 8 metrics columns, action buttons, budget pacing, health indicators, and expandable ad set detail.

Due to size, this will be implemented as a single file matching the mockup exactly. The file should be created using the `Write` tool with the complete component code following the patterns from OverviewTab/CostsTab (loading state, no-data state, data rendering).

Key sections:
- Campaign summary (4 KPIs: active/total, spend, results, ROAS)
- Alert cards from recommendations
- Table with columns: Campaign | Inversión | Resultados | CPA | ROAS | CTR | CPC | Freq | Acciones
- Status dots (active=green, learning=yellow, error=red, paused=gray)
- Budget pacing bars
- Tooltip on every metric header

The component accepts:
```typescript
interface CampaignsTabProps {
  data: CampaignPerformanceData | undefined;
  isLoading: boolean;
  currency?: string;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CampaignsTab.tsx
git commit -m "feat(meta-ads): implement CampaignsTab — operational table with actions"
```

---

## Task 8: Frontend — Create CreativosTab (was VideoTab)

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/VideoTab.tsx`

- [ ] **Step 1: Create CreativosTab.tsx**

Shows: placeholder for creative performance (top ads, format comparison, video retention).
Uses `ChannelDashboardData` for video metrics from timeSeries.

Since the backend doesn't yet have per-ad performance data or video retention metrics available via the channel dashboard endpoint, this tab will show:
1. A "Próximamente" section for top ads grid (needs future ad-level metrics endpoint)
2. Video KPI cards (if video metrics exist in kpis)
3. Format comparison placeholder

```typescript
'use client';

import { Loader2, Film, Image, LayoutGrid } from 'lucide-react';

import type { ChannelDashboardData } from '../../../../../types/metrics';

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function CreativosTab({ data, isLoading }: CreativosTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Performing Ads — placeholder until ad-level metrics endpoint exists */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Top anuncios por rendimiento
        </h3>
        <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
          <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="font-medium">Próximamente</p>
          <p className="mt-1 text-xs">
            Ranking de tus mejores y peores anuncios con thumbnails, ROAS y CPA por creativo.
          </p>
        </div>
      </div>

      {/* Format Comparison — placeholder */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Rendimiento por formato
          </h3>
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Film className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Video</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos próximamente</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <LayoutGrid className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Carrusel</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos próximamente</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Image className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Imagen estática</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos próximamente</span>
            </div>
          </div>
        </div>

        {/* Video Retention — placeholder */}
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
              title="Cuántas personas ven tu video hasta cada punto. Ideal: >30% completa el video.">
            Retención de video
          </h3>
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            <p className="font-medium">Próximamente</p>
            <p className="mt-1 text-xs">
              Gráfico de retención: Play → 25% → 50% → 75% → 100% completado.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Delete old VideoTab.tsx and AudienceTab.tsx**

These will be replaced by the new files.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx
git rm frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/VideoTab.tsx
git rm frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/AudienceTab.tsx
git commit -m "feat(meta-ads): create CreativosTab, remove old VideoTab/AudienceTab"
```

---

## Task 9: Frontend — Create AudienciaTab

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/AudienciaTab.tsx`

- [ ] **Step 1: Create AudienciaTab.tsx**

Shows: Reach + Frequency (moved from Overview/Costs) + demographic placeholders.
Reach/Frequency data comes from `ChannelDashboardData.kpis` (metricName: 'reach', 'frequency') and `frequencyAlert`.

```typescript
'use client';

import { Loader2, Users } from 'lucide-react';

import { ReachFrequencySection } from '../ReachFrequencySection';
import type { ChannelDashboardData } from '../../../../../types/metrics';

interface AudienciaTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function AudienciaTab({ data, isLoading }: AudienciaTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Reach + Frequency — moved here from Overview/Costs */}
      <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />

      {/* Demographic Breakdown — placeholder until audience data endpoint exists */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Demografía de tu audiencia
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">Distribución por edad</p>
            <p className="mt-1 text-[10px]">Próximamente — desglose 18-24, 25-34, 35-44, 45-54, 55+</p>
          </div>
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">Distribución por género</p>
            <p className="mt-1 text-[10px]">Próximamente — femenino vs masculino</p>
          </div>
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">Dónde aparecen tus ads</p>
            <p className="mt-1 text-[10px]">Próximamente — Feed, Stories, Reels, Otros</p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/AudienciaTab.tsx
git commit -m "feat(meta-ads): create AudienciaTab — reach/frequency + demographic placeholders"
```

---

## Task 10: Frontend — Rewrite CostosTab (expanded)

**Files:**
- Create: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CostosTab.tsx`
- Delete: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CostsTab.tsx`

- [ ] **Step 1: Create CostosTab.tsx**

Shows: 4 cost KPIs with benchmarks + cost evolution chart + CPA by campaign comparison.
NO reach/frequency (moved to Audiencia).

```typescript
'use client';

import { Loader2 } from 'lucide-react';
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import type { ChannelDashboardData, MetricKpiData, CampaignPerformanceData } from '../../../../../types/metrics';

interface CostosTabProps {
  data: ChannelDashboardData | undefined;
  campaignData: CampaignPerformanceData | undefined;
  isLoading: boolean;
}

const COST_METRICS = ['CPC', 'CPM', 'CPL', 'CPA'];

const COST_TOOLTIPS: Record<string, string> = {
  CPC: 'CPC = Cuánto pagas cada vez que alguien hace clic en tu anuncio. Menor es mejor.',
  CPM: 'CPM = Cuánto pagas por cada 1,000 veces que se muestra tu anuncio.',
  CPL: 'CPL = Cuánto cuesta cada contacto interesado que generas. Menor es mejor.',
  CPA: 'CPA = Cuánto pagas por cada resultado (venta o acción). Menor es mejor.',
};

export function CostosTab({ data, campaignData, isLoading }: CostosTabProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const costKpis = COST_METRICS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  // Build cost evolution data from timeSeries
  const costSeries = COST_METRICS.map(name =>
    data.timeSeries.find(ts => ts.metricName === name),
  ).filter(Boolean);

  const costChartData: Record<string, number | string>[] = [];
  const firstSeries = costSeries[0];
  if (firstSeries) {
    for (const point of firstSeries.dataPoints) {
      const entry: Record<string, number | string> = { date: point.date.slice(5) };
      for (const s of costSeries) {
        if (!s) continue;
        const p = s.dataPoints.find(dp => dp.date === point.date);
        entry[s.metricName] = p?.value ?? 0;
      }
      costChartData.push(entry);
    }
  }

  // CPA by campaign from campaignData
  const campaignsWithCpa = campaignData?.campaigns
    .filter(c => c.metrics.cpa != null && c.metrics.cpa > 0)
    .sort((a, b) => (a.metrics.cpa ?? 0) - (b.metrics.cpa ?? 0)) ?? [];
  const maxCpa = campaignsWithCpa.length > 0
    ? Math.max(...campaignsWithCpa.map(c => c.metrics.cpa ?? 0))
    : 1;

  return (
    <div className="space-y-6">
      {/* 4 Cost KPIs with benchmarks */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {costKpis.map(kpi => (
          <div
            key={kpi.metricName}
            className="space-y-1.5 rounded-lg border bg-card p-4"
            title={COST_TOOLTIPS[kpi.metricName] ?? ''}
          >
            <p className="text-xs text-muted-foreground">{kpi.displayName}</p>
            <p className="text-2xl font-semibold tabular-nums">
              {formatMoney(kpi.currentValue, kpi.currency || 'USD')}
            </p>
            {kpi.benchmark && (
              <BenchmarkBadge
                value={kpi.currentValue}
                benchmark={kpi.benchmark}
                higherIsBetter={kpi.higherIsBetter}
              />
            )}
          </div>
        ))}
      </div>

      {/* Cost Evolution Chart */}
      {costChartData.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
            Evolución de costos
          </h3>
          <ChartContainer
            config={{
              CPC: { label: 'CPC', color: 'hsl(var(--chart-1))' },
              CPM: { label: 'CPM', color: 'hsl(var(--chart-3))' },
              CPL: { label: 'CPL', color: 'hsl(var(--chart-4))' },
            }}
            className="h-[250px] w-full"
          >
            <LineChart data={costChartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip />
              <Line type="monotone" dataKey="CPC" stroke="var(--color-CPC)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="CPM" stroke="var(--color-CPM)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="CPL" stroke="var(--color-CPL)" strokeWidth={2} dot={false} />
            </LineChart>
          </ChartContainer>
        </div>
      )}

      {/* CPA by Campaign comparison */}
      {campaignsWithCpa.length > 0 && (
        <div className="space-y-2">
          <h3
            className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider"
            title="Compara el costo por resultado de cada campaña."
          >
            CPA por campaña
          </h3>
          <div className="rounded-lg border bg-card p-4 space-y-2.5">
            {campaignsWithCpa.map(camp => {
              const pct = ((camp.metrics.cpa ?? 0) / maxCpa) * 100;
              const isHigh = camp.health === 'critical';
              return (
                <div key={camp.externalId} className="flex items-center gap-3">
                  <span
                    className={cn(
                      'text-xs w-36 truncate',
                      isHigh ? 'text-destructive' : 'text-muted-foreground',
                    )}
                  >
                    {camp.name}
                  </span>
                  <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full flex items-center justify-end pr-2 text-[10px] font-semibold',
                        isHigh ? 'bg-destructive/50 text-destructive' : 'bg-emerald-500/40',
                      )}
                      style={{ width: `${Math.max(pct, 8)}%` }}
                    >
                      {formatMoney(camp.metrics.cpa ?? 0, campaignData?.currency || 'USD')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Delete old CostsTab.tsx and OverviewTab.tsx**

```bash
git rm frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CostsTab.tsx
git rm frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/OverviewTab.tsx
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CostosTab.tsx
git commit -m "feat(meta-ads): create CostosTab — cost KPIs + evolution chart + CPA comparison"
```

---

## Task 11: Frontend — Update sidebar (MetaAdsOverviewPanel) with top campaigns

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsOverviewPanel.tsx`

- [ ] **Step 1: Add top campaigns preview to sidebar**

Add `useCampaignPerformance` import and show a compact campaign list between the funnel and reach/frequency sections. Follow the mockup: show top 3 campaigns by spend, with name, spend value, and ROAS with color coding.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsOverviewPanel.tsx
git commit -m "feat(meta-ads): add top campaigns preview to sidebar panel"
```

---

## Task 12: Full integration verification

- [ ] **Step 1: Backend lint + tests**

```bash
cd backend && .venv/bin/ruff check src/ --no-cache
cd backend && .venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 2: Frontend lint + types + tests**

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
```

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(meta-ads): integration fixes for dashboard redesign"
```

---

## Verification

1. **Backend:** `cd backend && .venv/bin/pytest tests/modules/analytics/test_campaign_performance.py -v`
2. **Backend lint:** `cd backend && .venv/bin/ruff check src/ --no-cache`
3. **Frontend types:** `cd frontend && npx tsc --noEmit`
4. **Frontend tests:** `cd frontend && npx vitest run`
5. **Visual:** Open `https://dev-app.nicolify.com/[tenantId]/growth-studio/atraccion-captura` → Meta Ads → Dashboard completo → verify all 5 tabs render correctly
