# Three Pending Items — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Clerk E2E resilience, Meta token health banner, and ad-level metrics (ETL + API + UI) matching the approved mockup.

**Architecture:** Three independent workstreams. Item 1 (E2E) is standalone. Item 2 (Meta health) has backend → frontend dependency. Item 3 (ad metrics) has ETL → API → UI dependency chain. Items 1, 2, and 3 can run in parallel.

**Tech Stack:** Python/FastAPI/SQLAlchemy (backend), Next.js/React/TypeScript/Tailwind (frontend), Playwright (E2E), pytest/vitest (tests)

**Spec:** `docs/superpowers/specs/2026-04-06-three-pending-items-design.md`
**Mockup reference:** `docs/mockups/meta-ads-dashboard-complete.html` (tab Creativos)

---

## Workstream A: Clerk E2E Auth Resilience

### Task 1: Add retry helper to Clerk E2E setup

**Files:**
- Modify: `frontend/e2e/setup/clerk.setup.ts`

- [ ] **Step 1: Add retry wrapper with exponential backoff**

Replace the full content of `frontend/e2e/setup/clerk.setup.ts`:

```typescript
import { clerk, clerkSetup, setupClerkTestingToken } from '@clerk/testing/playwright';
import { test as setup } from '@playwright/test';
import path from 'path';

setup.describe.configure({ mode: 'serial' });
const authFile = path.join(__dirname, '../../playwright/.clerk/user.json');

async function withRetry<T>(
  fn: () => Promise<T>,
  opts: { retries: number; label: string },
): Promise<T> {
  const delays = [2_000, 4_000, 8_000];
  for (let attempt = 1; attempt <= opts.retries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      const isLast = attempt === opts.retries;
      const msg = error instanceof Error ? error.message : String(error);
      console.warn(
        `[clerk-setup] ${opts.label} attempt ${attempt}/${opts.retries} failed: ${msg}`,
      );
      if (isLast) throw error;
      const delay = delays[attempt - 1] ?? 8_000;
      console.warn(`[clerk-setup] Retrying in ${delay}ms...`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}

setup('clerk setup', async ({}) => {
  await clerkSetup();
});

setup('authenticate', async ({ page }) => {
  setup.setTimeout(60_000);
  await setupClerkTestingToken({ page });
  await page.goto('/sign-in', { waitUntil: 'domcontentloaded', timeout: 45_000 });
  await withRetry(
    () =>
      clerk.signIn({
        page,
        signInParams: {
          strategy: 'password',
          identifier: process.env.E2E_CLERK_USER_EMAIL || process.env.E2E_CLERK_USER_USERNAME!,
          password: process.env.E2E_CLERK_USER_PASSWORD!,
        },
      }),
    { retries: 3, label: 'clerk.signIn' },
  );
  await page.context().storageState({ path: authFile });
});
```

- [ ] **Step 2: Verify E2E setup still works locally**

Run: `cd frontend && npx tsc --noEmit`
Expected: no type errors in `clerk.setup.ts`

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/setup/clerk.setup.ts
git commit -m "fix(e2e): add retry with exponential backoff to Clerk signIn setup"
```

### Task 2: Create .env.e2e.example

**Files:**
- Create: `frontend/.env.e2e.example`

- [ ] **Step 1: Create env example file**

```bash
# frontend/.env.e2e.example
# ─── Clerk Auth (required) ───
E2E_CLERK_USER_EMAIL=e2e-test@nicolify.com
E2E_CLERK_USER_USERNAME=e2e-test@nicolify.com
E2E_CLERK_USER_PASSWORD=your-test-password
CLERK_SECRET_KEY=sk_test_...
CLERK_TESTING_TOKEN=           # Auto-generated in CI via Clerk API
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...

# ─── Tenant Isolation (required) ───
E2E_TENANT_ID=your-test-tenant-uuid

# ─── Target URL (optional — defaults to http://localhost:3000) ───
E2E_BASE_URL=http://localhost:3000
```

- [ ] **Step 2: Commit**

```bash
git add frontend/.env.e2e.example
git commit -m "docs(e2e): add .env.e2e.example documenting all E2E variables"
```

---

## Workstream B: Meta Token Health + Proactive Banner

### Task 3: Backend — Connection health endpoint (test first)

**Files:**
- Create: `backend/tests/modules/connections/test_connection_health.py`
- Create: `backend/src/modules/connections/api/health.py`
- Modify: `backend/src/main.py` (import + mount router)

**Reference patterns:**
- Status endpoint: `backend/src/modules/connections/api/status.py`
- Main router mounting: `backend/src/main.py:639-644`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/modules/connections/test_connection_health.py`:

```python
"""Tests for connection health check endpoint logic."""

from datetime import UTC, datetime, timedelta

import pytest

from src.modules.connections.api.health import evaluate_connection_health


class TestEvaluateConnectionHealth:
    """Unit tests for health evaluation logic (no DB needed)."""

    def test_not_connected_when_none(self):
        result = evaluate_connection_health(None)
        assert result.status == "not_connected"
        assert result.expires_at is None

    def test_healthy_when_no_expires_at(self):
        credentials = {"access_token": "tok_123"}
        result = evaluate_connection_health(credentials)
        assert result.status == "healthy"

    def test_healthy_when_far_from_expiry(self):
        future = (datetime.now(UTC) + timedelta(days=30)).isoformat()
        credentials = {"access_token": "tok_123", "expires_at": future}
        result = evaluate_connection_health(credentials)
        assert result.status == "healthy"

    def test_expiring_soon_within_7_days(self):
        soon = (datetime.now(UTC) + timedelta(days=3)).isoformat()
        credentials = {"access_token": "tok_123", "expires_at": soon}
        result = evaluate_connection_health(credentials)
        assert result.status == "expiring_soon"

    def test_expired_when_past(self):
        past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        credentials = {"access_token": "tok_123", "expires_at": past}
        result = evaluate_connection_health(credentials)
        assert result.status == "expired"

    def test_expired_when_invalid_format(self):
        credentials = {"access_token": "tok_123", "expires_at": "not-a-date"}
        result = evaluate_connection_health(credentials)
        assert result.status == "healthy"  # Can't parse → assume healthy (safe default)

    def test_messages_in_spanish(self):
        result = evaluate_connection_health(None)
        assert "conectado" in result.message.lower() or "Meta" in result.message
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/modules/connections/test_connection_health.py -x -q --tb=short`
Expected: FAIL — `evaluate_connection_health` not defined

- [ ] **Step 3: Implement health evaluation + endpoint**

Create `backend/src/modules/connections/api/health.py`:

```python
"""Connection health check endpoint.

Returns token health status so the frontend can show proactive banners
when a connection is expiring or expired.
"""

from datetime import UTC, datetime, timedelta
from typing import Literal

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["connections-health"])
logger = structlog.get_logger()

EXPIRING_THRESHOLD_DAYS = 7

_MESSAGES = {
    "healthy": "Conexión activa",
    "expiring_soon": (
        "Tu conexión con {channel} expira pronto. "
        "Reconecta para evitar interrupciones."
    ),
    "expired": (
        "Tu conexión con {channel} expiró. "
        "Reconecta para reactivar la sincronización de datos."
    ),
    "not_connected": (
        "{channel} no está conectado. "
        "Conecta tu cuenta para ver métricas."
    ),
}


class ConnectionHealthResponse(BaseModel):
    """Health status of a channel connection."""

    status: Literal["healthy", "expiring_soon", "expired", "not_connected"]
    channel_slug: str
    expires_at: datetime | None = None
    message: str


def evaluate_connection_health(
    credentials: dict | None,
    channel_slug: str = "meta",
) -> ConnectionHealthResponse:
    """Pure function — evaluate health from credentials dict."""
    channel_display = channel_slug.replace("-", " ").title()

    if credentials is None:
        return ConnectionHealthResponse(
            status="not_connected",
            channel_slug=channel_slug,
            expires_at=None,
            message=_MESSAGES["not_connected"].format(channel=channel_display),
        )

    expires_at_str = credentials.get("expires_at")
    if not expires_at_str:
        return ConnectionHealthResponse(
            status="healthy",
            channel_slug=channel_slug,
            expires_at=None,
            message=_MESSAGES["healthy"],
        )

    try:
        expires_at = datetime.fromisoformat(expires_at_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        logger.warning("connection_health_invalid_expires_at", value=expires_at_str)
        return ConnectionHealthResponse(
            status="healthy",
            channel_slug=channel_slug,
            expires_at=None,
            message=_MESSAGES["healthy"],
        )

    now = datetime.now(UTC)
    threshold = now + timedelta(days=EXPIRING_THRESHOLD_DAYS)

    if expires_at <= now:
        status = "expired"
    elif expires_at <= threshold:
        status = "expiring_soon"
    else:
        status = "healthy"

    return ConnectionHealthResponse(
        status=status,
        channel_slug=channel_slug,
        expires_at=expires_at,
        message=_MESSAGES[status].format(channel=channel_display),
    )


@router.get("/{channel_slug}/health", response_model=ConnectionHealthResponse)
async def get_connection_health(
    channel_slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionHealthResponse:
    """Check health/expiry status of a channel connection."""
    repo = ChannelConnectionRepository(db)

    # Map channel_slug to channel_type
    slug_to_type = {
        "meta": "meta",
        "meta-ads": "meta",
        "google-analytics": "google_analytics",
        "youtube": "youtube",
        "shopify": "shopify",
    }
    channel_type = slug_to_type.get(channel_slug, channel_slug)

    connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)
    if not connection or not connection.is_active:
        return evaluate_connection_health(None, channel_slug=channel_slug)

    return evaluate_connection_health(
        connection.credentials, channel_slug=channel_slug
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/connections/test_connection_health.py -x -q --tb=short`
Expected: 7 passed

- [ ] **Step 5: Mount router in main.py**

Add import at line ~52 (after `conn_status` import):
```python
from src.modules.connections.api import health as conn_health
```

Add router mount after line ~644 (after `conn_status` block):
```python
app.include_router(
    conn_health.router,
    prefix="/api/v1/connections",
    tags=["Connections - Health"],
    dependencies=[Depends(get_tenant_context)],
)
```

- [ ] **Step 6: Run backend lint + arch tests**

Run: `cd backend && .venv/bin/ruff check src/ --no-cache && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: all pass (new endpoint has `response_model=`)

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/connections/api/health.py backend/tests/modules/connections/test_connection_health.py backend/src/main.py
git commit -m "feat(connections): add connection health endpoint with token expiry detection"
```

### Task 4: Frontend — Connection health banner

**Files:**
- Create: `frontend/src/features/growth-studio/hooks/use-connection-health.ts`
- Create: `frontend/src/features/growth-studio/components/connection-health-banner.tsx`
- Create: `frontend/src/features/growth-studio/components/__tests__/connection-health-banner.test.tsx`
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`

**Reference patterns:**
- Hook pattern: `frontend/src/features/growth-studio/api/campaigns-api.ts:171-187` (useCreativesOverview)
- Component pattern: existing Alert from Shadcn UI

- [ ] **Step 1: Write the hook**

Create `frontend/src/features/growth-studio/hooks/use-connection-health.ts`:

```typescript
import { useAuth } from '@clerk/nextjs';
import { useQuery } from '@tanstack/react-query';

import { fetchClient } from '@/lib/fetch-client';

export interface ConnectionHealth {
  status: 'healthy' | 'expiring_soon' | 'expired' | 'not_connected';
  channelSlug: string;
  expiresAt: string | null;
  message: string;
}

async function fetchConnectionHealth(
  token: string,
  channelSlug: string,
): Promise<ConnectionHealth> {
  const res = await fetchClient(`/api/v1/connections/${channelSlug}/health`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  const data = await res.json();
  return {
    status: data.status,
    channelSlug: data.channel_slug,
    expiresAt: data.expires_at,
    message: data.message,
  };
}

export function useConnectionHealth(channelSlug: string, enabled = true) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['connection-health', channelSlug],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchConnectionHealth(token, channelSlug);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
```

- [ ] **Step 2: Write the banner component test**

Create `frontend/src/features/growth-studio/components/__tests__/connection-health-banner.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  ConnectionHealthBanner,
} from '../connection-health-banner';

describe('ConnectionHealthBanner', () => {
  it('renders nothing when healthy', () => {
    const { container } = render(
      <ConnectionHealthBanner
        status="healthy"
        message="Conexión activa"
        channelSlug="meta"
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders warning banner when expiring_soon', () => {
    render(
      <ConnectionHealthBanner
        status="expiring_soon"
        message="Tu conexión con Meta expira pronto."
        channelSlug="meta"
      />,
    );
    expect(screen.getByText(/expira pronto/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /reconectar/i })).toBeInTheDocument();
  });

  it('renders error banner when expired', () => {
    render(
      <ConnectionHealthBanner
        status="expired"
        message="Tu conexión con Meta expiró."
        channelSlug="meta"
      />,
    );
    expect(screen.getByText(/expiró/i)).toBeInTheDocument();
  });

  it('renders info banner when not_connected', () => {
    render(
      <ConnectionHealthBanner
        status="not_connected"
        message="Meta no está conectado."
        channelSlug="meta"
      />,
    );
    expect(screen.getByText(/no está conectado/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/__tests__/connection-health-banner.test.tsx`
Expected: FAIL — module not found

- [ ] **Step 4: Implement the banner component**

Create `frontend/src/features/growth-studio/components/connection-health-banner.tsx`:

```typescript
'use client';

import { AlertCircle, AlertTriangle, Info } from 'lucide-react';
import Link from 'next/link';

interface ConnectionHealthBannerProps {
  status: 'healthy' | 'expiring_soon' | 'expired' | 'not_connected';
  message: string;
  channelSlug: string;
}

const config = {
  expiring_soon: {
    icon: AlertTriangle,
    bg: 'bg-amber-500/10 border-amber-500/30',
    text: 'text-amber-400',
    label: 'Reconectar',
  },
  expired: {
    icon: AlertCircle,
    bg: 'bg-red-500/10 border-red-500/30',
    text: 'text-red-400',
    label: 'Reconectar',
  },
  not_connected: {
    icon: Info,
    bg: 'bg-blue-500/10 border-blue-500/30',
    text: 'text-blue-400',
    label: 'Conectar',
  },
} as const;

export function ConnectionHealthBanner({
  status,
  message,
  channelSlug,
}: ConnectionHealthBannerProps) {
  if (status === 'healthy') return null;

  const c = config[status];
  const Icon = c.icon;

  return (
    <div className={`flex items-center justify-between gap-3 rounded-lg border p-3 ${c.bg}`}>
      <div className="flex items-center gap-2">
        <Icon className={`h-4 w-4 shrink-0 ${c.text}`} />
        <p className={`text-sm ${c.text}`}>{message}</p>
      </div>
      <Link
        href="/connections"
        role="link"
        className={`shrink-0 rounded-md border px-3 py-1.5 text-xs font-medium ${c.bg} ${c.text} hover:opacity-80`}
      >
        {c.label}
      </Link>
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/growth-studio/components/__tests__/connection-health-banner.test.tsx`
Expected: 4 passed

- [ ] **Step 6: Wire banner into MetaAdsDashboard**

Modify `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx`.

Add imports at the top:
```typescript
import { ConnectionHealthBanner } from '../../../connection-health-banner';
import { useConnectionHealth } from '../../../../hooks/use-connection-health';
```

Inside the component, after the existing hooks, add:
```typescript
const { data: health } = useConnectionHealth('meta-ads');
```

Inside the JSX, right before the `<Tabs>` component (after the header), add:
```typescript
{health && health.status !== 'healthy' && (
  <div className="px-6 pt-4">
    <ConnectionHealthBanner
      status={health.status}
      message={health.message}
      channelSlug={health.channelSlug}
    />
  </div>
)}
```

- [ ] **Step 7: Run frontend type check + lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/growth-studio/`
Expected: no errors

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/growth-studio/hooks/use-connection-health.ts frontend/src/features/growth-studio/components/connection-health-banner.tsx frontend/src/features/growth-studio/components/__tests__/connection-health-banner.test.tsx frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/MetaAdsDashboard.tsx
git commit -m "feat(growth-studio): add connection health banner with token expiry detection"
```

---

## Workstream C: Ad-Level Metrics Full Stack

### Task 5: Backend ETL — Ad-level extraction in Meta provider

**Files:**
- Modify: `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`
- Create: `backend/tests/modules/analytics/test_meta_provider_ad_level.py`

**Reference patterns:**
- `_extract_meta_ads_campaigns` at line 1353 (exact pattern to follow)
- `extract_metrics` at line 309 (where to wire into pipeline)
- `_ADS_EXPANDED_FIELDS` at line 49

- [ ] **Step 1: Write failing test for ad-level extraction**

Create `backend/tests/modules/analytics/test_meta_provider_ad_level.py`:

```python
"""Tests for ad-level metric extraction in MetaProvider."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider


def _ok_response(data: list) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": data}
    return resp


def _ad_insight_row(ad_id: str, ad_name: str, spend: str = "50.00") -> dict:
    return {
        "ad_id": ad_id,
        "ad_name": ad_name,
        "impressions": "1000",
        "clicks": "50",
        "spend": spend,
        "ctr": "5.0",
        "cpc": "1.00",
        "reach": "800",
        "frequency": "1.25",
        "actions": [
            {"action_type": "purchase", "value": "5"},
            {"action_type": "link_click", "value": "45"},
        ],
        "cost_per_action_type": [
            {"action_type": "purchase", "value": "10.00"},
        ],
        "purchase_roas": [{"action_type": "omni_purchase", "value": "3.5"}],
    }


class TestExtractMetaAdsByAd:
    """Test _extract_meta_ads_by_ad method."""

    @pytest.mark.asyncio
    async def test_extracts_metrics_with_ad_id(self):
        provider = MetaProvider()
        credentials = {
            "access_token": "tok_test",
            "ad_account_id": "123456",
            "currency": "USD",
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            return_value=_ok_response([
                _ad_insight_row("ad_001", "Video Testimonio"),
                _ad_insight_row("ad_002", "Carrusel Beneficios"),
            ])
        )

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
        )

        # Should have metrics for both ads
        ad_ids = {m.ad_id for m in metrics if m.ad_id}
        assert "ad_001" in ad_ids
        assert "ad_002" in ad_ids

        # Each ad should have spend metric
        spend_metrics = [m for m in metrics if m.metric_name == "spend"]
        assert len(spend_metrics) >= 2

        # All metrics should have ad_id set
        for m in metrics:
            assert m.ad_id is not None

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_ad_account(self):
        provider = MetaProvider()
        credentials = {"access_token": "tok_test", "currency": "USD"}
        mock_client = AsyncMock()

        metrics = await provider._extract_meta_ads_by_ad(
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_api_called_with_level_ad(self):
        provider = MetaProvider()
        credentials = {
            "access_token": "tok_test",
            "ad_account_id": "123456",
            "currency": "USD",
        }
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=_ok_response([]))

        await provider._extract_meta_ads_by_ad(
            mock_client, credentials, date(2026, 3, 1), date(2026, 3, 31)
        )

        call_args = mock_client.get.call_args
        params = call_args.kwargs.get("params") or call_args[1].get("params")
        assert params["level"] == "ad"
        assert "ad_id" in params["fields"]
        assert "ad_name" in params["fields"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_meta_provider_ad_level.py -x -q --tb=short`
Expected: FAIL — `_extract_meta_ads_by_ad` not found

- [ ] **Step 3: Implement _extract_meta_ads_by_ad**

Add this method to `MetaProvider` class in `backend/src/modules/analytics/infrastructure/providers/meta_provider.py`, after the `_extract_meta_ads_campaigns_daily` method (around line 1443):

```python
    async def _extract_meta_ads_by_ad(
        self,
        client: httpx.AsyncClient,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract Meta Ads metrics at individual ad level."""
        ad_account_id = credentials.get("ad_account_id")
        if not ad_account_id:
            return []
        access_token = credentials.get("access_token", "")
        currency = credentials.get("currency", "USD")

        response = await client.get(
            f"{GRAPH_API_BASE}/act_{ad_account_id}/insights",
            headers=_auth_headers(access_token),
            params={
                "fields": f"ad_id,ad_name,{_ADS_EXPANDED_FIELDS}",
                "time_range": json.dumps({
                    "since": start_date.isoformat(),
                    "until": end_date.isoformat(),
                }),
                "level": "ad",
                "limit": "500",
            },
        )
        _raise_for_meta_error(response, "meta_ads_by_ad")
        rows = response.json().get("data", [])

        metrics: list[ExtractedMetric] = []
        for row in rows:
            ad_id = row.get("ad_id")
            ad_name = row.get("ad_name", "")
            parsed = self._parse_ads_row(row, currency, end_date)
            for m in parsed:
                m.ad_id = ad_id
                m.extra = {**m.extra, "ad_name": ad_name}
            metrics.extend(parsed)
        return metrics
```

- [ ] **Step 4: Wire into extract_metrics pipeline**

In the same file, inside `extract_metrics()` method, after the `meta_ads_campaigns` block (after line 384), add:

```python
                ad_level_metrics, fail = await self._safe_extract(
                    self._extract_meta_ads_by_ad,
                    client,
                    credentials,
                    start_date,
                    end_date,
                    extractor_name="meta_ads_by_ad",
                )
                metrics.extend(ad_level_metrics)
                if fail:
                    failures.append(fail)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_meta_provider_ad_level.py -x -q --tb=short`
Expected: 3 passed

- [ ] **Step 6: Run full backend tests**

Run: `cd backend && .venv/bin/ruff check src/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/providers/meta_provider.py backend/tests/modules/analytics/test_meta_provider_ad_level.py
git commit -m "feat(analytics): add ad-level metric extraction to Meta provider"
```

### Task 6: Backend API — Ad performance DTOs

**Files:**
- Modify: `backend/src/modules/analytics/application/dto/campaign_dto.py`

- [ ] **Step 1: Add ad performance and format comparison DTOs**

Add at the end of `backend/src/modules/analytics/application/dto/campaign_dto.py`, before the `_rebuild_models()` function:

```python
# ---------------------------------------------------------------------------
# Ad-Level Performance DTOs
# ---------------------------------------------------------------------------


class AdMetricsDTO(BaseModel):
    """Single ad with performance metrics for the Creativos tab."""

    ad_id: str
    ad_name: str
    campaign_name: str | None = None
    campaign_external_id: str | None = None
    format_type: str = "unknown"  # "video" | "carousel" | "image" | "unknown"
    thumbnail_url: str | None = None
    spend: float = 0.0
    impressions: float = 0.0
    clicks: float = 0.0
    conversions: float = 0.0
    roas: float | None = None
    cpa: float | None = None
    ctr: float | None = None
    cpc: float | None = None
    performance_tag: str = "average"  # "top_performer" | "average" | "underperformer"


class AdPerformanceListDTO(BaseModel):
    """Response for ad-level performance endpoint."""

    ads: list[AdMetricsDTO] = []
    period: str
    total_ads: int = 0


class FormatComparisonItemDTO(BaseModel):
    """Aggregated metrics for a single ad format type."""

    format_type: str
    emoji: str  # "🎬" | "🖼" | "📷"
    ad_count: int = 0
    avg_ctr: float = 0.0
    avg_cpa: float | None = None
    avg_roas: float | None = None
    total_spend: float = 0.0
    performance_score: float = 0.0  # 0-100 normalized


class FormatComparisonDTO(BaseModel):
    """Response for format comparison endpoint."""

    formats: list[FormatComparisonItemDTO] = []
    period: str
```

- [ ] **Step 2: Run lint**

Run: `cd backend && .venv/bin/ruff check src/modules/analytics/application/dto/ --no-cache`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/analytics/application/dto/campaign_dto.py
git commit -m "feat(analytics): add ad-level performance and format comparison DTOs"
```

### Task 7: Backend API — Ad performance service + endpoint (test first)

**Files:**
- Create: `backend/tests/modules/analytics/test_ad_performance.py`
- Create: `backend/src/modules/analytics/application/services/ad_performance_service.py`
- Modify: `backend/src/modules/analytics/api/campaigns.py` (add endpoints)
- Modify: `backend/src/main.py` (no change needed — campaigns router already mounted)

**Reference patterns:**
- CampaignService query pattern: `backend/src/modules/analytics/application/services/campaign_service.py:173-189`
- Campaigns API: `backend/src/modules/analytics/api/campaigns.py`

- [ ] **Step 1: Write failing test for ad performance service**

Create `backend/tests/modules/analytics/test_ad_performance.py`:

```python
"""Tests for ad performance service — aggregation logic."""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.analytics.application.services.ad_performance_service import (
    AdPerformanceService,
)


def _make_metric_row(ad_id: str, metric_name: str, value: float, ad_name: str = "Test Ad"):
    """Create a mock DB row for official_metrics."""
    row = MagicMock()
    row._mapping = {
        "ad_id": ad_id,
        "metric_name": metric_name,
        "total_value": value,
        "ad_name": ad_name,
    }
    return row


class TestAdPerformanceService:
    def test_get_top_ads_aggregates_by_ad_id(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            _make_metric_row("ad_001", "spend", 100.0, "Video Testimonio"),
            _make_metric_row("ad_001", "conversions", 10.0, "Video Testimonio"),
            _make_metric_row("ad_001", "roas", 3.5, "Video Testimonio"),
            _make_metric_row("ad_001", "ctr", 2.4, "Video Testimonio"),
            _make_metric_row("ad_001", "cpc", 0.42, "Video Testimonio"),
            _make_metric_row("ad_002", "spend", 200.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "conversions", 5.0, "Carrusel Beneficios"),
            _make_metric_row("ad_002", "roas", 1.2, "Carrusel Beneficios"),
        ]

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d", limit=10)

        assert result.total_ads == 2
        assert result.period == "30d"
        assert len(result.ads) == 2

        # Should be sorted by spend descending
        assert result.ads[0].ad_id == "ad_002"
        assert result.ads[0].spend == 200.0
        assert result.ads[1].ad_id == "ad_001"
        assert result.ads[1].spend == 100.0
        assert result.ads[1].conversions == 10.0
        assert result.ads[1].roas == 3.5

    def test_get_top_ads_assigns_performance_tags(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            _make_metric_row("ad_top", "spend", 100.0),
            _make_metric_row("ad_top", "roas", 5.0),
            _make_metric_row("ad_mid", "spend", 100.0),
            _make_metric_row("ad_mid", "roas", 2.0),
            _make_metric_row("ad_bad", "spend", 100.0),
            _make_metric_row("ad_bad", "roas", 0.5),
        ]

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        tags = {ad.ad_id: ad.performance_tag for ad in result.ads}
        assert tags["ad_top"] == "top_performer"
        assert tags["ad_bad"] == "underperformer"

    def test_get_top_ads_empty_when_no_data(self):
        tenant_id = uuid4()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []

        service = AdPerformanceService(mock_db)
        result = service.get_top_ads(tenant_id, "meta-ads", "30d")

        assert result.total_ads == 0
        assert result.ads == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_ad_performance.py -x -q --tb=short`
Expected: FAIL — module not found

- [ ] **Step 3: Implement AdPerformanceService**

Create `backend/src/modules/analytics/application/services/ad_performance_service.py`:

```python
"""Service for ad-level performance aggregation.

Queries official_metrics WHERE ad_id IS NOT NULL to build per-ad KPIs
for the Creativos tab dashboard.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlalchemy import text

from src.modules.analytics.application.dto.campaign_dto import (
    AdMetricsDTO,
    AdPerformanceListDTO,
    FormatComparisonDTO,
    FormatComparisonItemDTO,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

_PERIOD_TO_DAYS = {"7d": 7, "30d": 30, "90d": 90}

_FORMAT_EMOJIS = {
    "video": "\U0001f3ac",
    "carousel": "\U0001f5bc",
    "image": "\U0001f4f7",
    "unknown": "\u2753",
}


class AdPerformanceService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _date_range(self, period: str) -> tuple[date, date]:
        days = _PERIOD_TO_DAYS.get(period, 30)
        end = date.today()
        start = end - timedelta(days=days)
        return start, end

    def get_top_ads(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str,
        limit: int = 10,
    ) -> AdPerformanceListDTO:
        start_date, end_date = self._date_range(period)

        rows = self._db.execute(
            text("""
                SELECT ad_id, metric_name,
                       SUM(value) AS total_value,
                       MAX(extra->>'ad_name') AS ad_name
                FROM official_metrics
                WHERE tenant_id = :tenant_id
                  AND channel_slug = :channel_slug
                  AND ad_id IS NOT NULL
                  AND metric_date BETWEEN :start_date AND :end_date
                GROUP BY ad_id, metric_name
            """),
            {
                "tenant_id": str(tenant_id),
                "channel_slug": channel_slug,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        ).fetchall()

        # Build lookup: {ad_id: {metric_name: value, "_ad_name": name}}
        metrics_by_ad: dict[str, dict[str, float | str]] = {}
        for row in rows:
            r = row._mapping
            aid = r["ad_id"]
            if aid not in metrics_by_ad:
                metrics_by_ad[aid] = {"_ad_name": r.get("ad_name") or aid}
            metrics_by_ad[aid][r["metric_name"]] = float(r["total_value"])

        # Build ad DTOs
        ads: list[AdMetricsDTO] = []
        for aid, m in metrics_by_ad.items():
            spend = m.get("spend", 0.0)
            conversions = m.get("conversions", 0.0)
            ads.append(
                AdMetricsDTO(
                    ad_id=aid,
                    ad_name=str(m.get("_ad_name", aid)),
                    spend=float(spend),
                    impressions=float(m.get("impressions", 0)),
                    clicks=float(m.get("clicks", 0)),
                    conversions=float(conversions),
                    roas=float(m["roas"]) if "roas" in m else None,
                    cpa=float(spend) / float(conversions) if conversions else None,
                    ctr=float(m["ctr"]) if "ctr" in m else None,
                    cpc=float(m["cpc"]) if "cpc" in m else None,
                )
            )

        # Sort by spend descending
        ads.sort(key=lambda a: a.spend, reverse=True)

        # Assign performance tags based on ROAS
        if ads:
            roas_values = [a.roas for a in ads if a.roas is not None]
            if roas_values:
                avg_roas = sum(roas_values) / len(roas_values)
                for ad in ads:
                    if ad.roas is not None:
                        if ad.roas >= avg_roas * 1.3:
                            ad.performance_tag = "top_performer"
                        elif ad.roas < avg_roas * 0.7:
                            ad.performance_tag = "underperformer"

        return AdPerformanceListDTO(
            ads=ads[:limit],
            period=period,
            total_ads=len(ads),
        )

    def get_format_comparison(
        self,
        tenant_id: UUID,
        channel_slug: str,
        period: str,
    ) -> FormatComparisonDTO:
        """Aggregate metrics by ad format type.

        Format type is derived from ad metadata stored in the campaigns table.
        Falls back to 'unknown' if not available.
        """
        start_date, end_date = self._date_range(period)

        # Get ad-level metrics
        result = self.get_top_ads(tenant_id, channel_slug, period, limit=500)

        # Group by format_type
        by_format: dict[str, list[AdMetricsDTO]] = {}
        for ad in result.ads:
            fmt = ad.format_type or "unknown"
            by_format.setdefault(fmt, []).append(ad)

        formats: list[FormatComparisonItemDTO] = []
        max_roas = 0.0
        for fmt, ads in by_format.items():
            avg_ctr = sum(a.ctr or 0 for a in ads) / len(ads) if ads else 0
            roas_vals = [a.roas for a in ads if a.roas is not None]
            avg_roas = sum(roas_vals) / len(roas_vals) if roas_vals else None
            cpa_vals = [a.cpa for a in ads if a.cpa is not None]
            avg_cpa = sum(cpa_vals) / len(cpa_vals) if cpa_vals else None
            total_spend = sum(a.spend for a in ads)

            if avg_roas and avg_roas > max_roas:
                max_roas = avg_roas

            formats.append(
                FormatComparisonItemDTO(
                    format_type=fmt,
                    emoji=_FORMAT_EMOJIS.get(fmt, "\u2753"),
                    ad_count=len(ads),
                    avg_ctr=round(avg_ctr, 2),
                    avg_cpa=round(avg_cpa, 2) if avg_cpa else None,
                    avg_roas=round(avg_roas, 1) if avg_roas else None,
                    total_spend=round(total_spend, 2),
                )
            )

        # Normalize performance_score (0-100)
        if max_roas > 0:
            for f in formats:
                f.performance_score = round(
                    ((f.avg_roas or 0) / max_roas) * 100, 1
                )

        formats.sort(key=lambda f: f.performance_score, reverse=True)

        return FormatComparisonDTO(formats=formats, period=period)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/modules/analytics/test_ad_performance.py -x -q --tb=short`
Expected: 3 passed

- [ ] **Step 5: Add API endpoints to campaigns router**

Modify `backend/src/modules/analytics/api/campaigns.py`.

Add imports at top:
```python
from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdPerformanceListDTO,
    AdSetDTO,
    CampaignOverviewDTO,
    CampaignPerformanceDTO,
    CreativesOverviewDTO,
    FormatComparisonDTO,
)
from src.modules.analytics.application.services.ad_performance_service import (
    AdPerformanceService,
)
```

Add endpoints before the `/{campaign_external_id}/adsets` route (before line 79):

```python
@router.get("/ads/performance", response_model=AdPerformanceListDTO)
async def get_ads_performance(
    period: str = Query(default="30d"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get top ads with per-ad performance metrics (ROAS, CPA, CTR, CPC)."""
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {valid_periods}",
        )
    service = AdPerformanceService(db)
    return service.get_top_ads(user.tenant_id, "meta-ads", period, limit)


@router.get("/ads/format-comparison", response_model=FormatComparisonDTO)
async def get_ads_format_comparison(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get aggregated metrics by ad format (video, carousel, image)."""
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {valid_periods}",
        )
    service = AdPerformanceService(db)
    return service.get_format_comparison(user.tenant_id, "meta-ads", period)
```

- [ ] **Step 6: Run backend lint + arch tests**

Run: `cd backend && .venv/bin/ruff check src/ --no-cache && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: all pass

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/analytics/application/services/ad_performance_service.py backend/tests/modules/analytics/test_ad_performance.py backend/src/modules/analytics/api/campaigns.py
git commit -m "feat(analytics): add ad performance service and API endpoints for per-ad metrics"
```

### Task 8: Frontend — Ad performance hooks and types

**Files:**
- Modify: `frontend/src/features/growth-studio/api/campaigns-api.ts`
- Modify: `frontend/src/features/growth-studio/types/metrics.ts` (if needed)

- [ ] **Step 1: Add types and hooks for ad performance**

Add to `frontend/src/features/growth-studio/api/campaigns-api.ts` at the end of the file:

```typescript
// ─── Ad-Level Performance ─────────────────────────────────────────────

export interface AdMetrics {
  adId: string;
  adName: string;
  campaignName: string | null;
  campaignExternalId: string | null;
  formatType: string;
  thumbnailUrl: string | null;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  roas: number | null;
  cpa: number | null;
  ctr: number | null;
  cpc: number | null;
  performanceTag: string; // "top_performer" | "average" | "underperformer"
}

export interface AdPerformanceData {
  ads: AdMetrics[];
  period: string;
  totalAds: number;
}

export interface FormatComparisonItem {
  formatType: string;
  emoji: string;
  adCount: number;
  avgCtr: number;
  avgCpa: number | null;
  avgRoas: number | null;
  totalSpend: number;
  performanceScore: number;
}

export interface FormatComparisonData {
  formats: FormatComparisonItem[];
  period: string;
}

async function fetchAdPerformance(
  token: string,
  period: MetaAdsPeriod = '30d',
  limit = 10,
): Promise<AdPerformanceData> {
  const res = await fetchClient(
    `/api/v1/analytics/campaigns/ads/performance?period=${period}&limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok) throw new Error(`Ad performance fetch failed: ${res.status}`);
  return camelizeKeys(await res.json()) as AdPerformanceData;
}

async function fetchFormatComparison(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<FormatComparisonData> {
  const res = await fetchClient(
    `/api/v1/analytics/campaigns/ads/format-comparison?period=${period}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok) throw new Error(`Format comparison fetch failed: ${res.status}`);
  return camelizeKeys(await res.json()) as FormatComparisonData;
}

export function useAdPerformance(
  period: MetaAdsPeriod = '30d',
  limit = 10,
  enabled = true,
) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['ad-performance', period, limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchAdPerformance(token, period, limit);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

export function useFormatComparison(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: ['format-comparison', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchFormatComparison(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
```

Note: Check if `camelizeKeys` already exists in the file. If not, add this utility at the top of the file:

```typescript
function camelizeKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(camelizeKeys);
  if (obj !== null && typeof obj === 'object') {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [
        k.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase()),
        camelizeKeys(v),
      ]),
    );
  }
  return obj;
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/api/campaigns-api.ts
git commit -m "feat(growth-studio): add hooks for ad performance and format comparison APIs"
```

### Task 9: Frontend — Rewrite CreativosTab matching mockup

**Files:**
- Modify: `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx`

**Reference:** `docs/mockups/meta-ads-dashboard-complete.html` tab Creativos (lines 591-748)

- [ ] **Step 1: Rewrite CreativosTab with real ad metrics**

Replace the full content of `frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx`:

```typescript
'use client';

import { Film, ImageIcon, LayoutGrid, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import {
  useAdPerformance,
  useCreativesOverview,
  useFormatComparison,
} from '../../../../../api/campaigns-api';
import type { ChannelDashboardData, MetaAdsPeriod } from '../../../../../types/metrics';

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

const formatIcons: Record<string, typeof Film> = {
  video: Film,
  carousel: LayoutGrid,
  image: ImageIcon,
};

function formatNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toFixed(0);
}

export function CreativosTab({ data, isLoading, period }: CreativosTabProps) {
  const activePeriod = period ?? '30d';
  const { data: creatives } = useCreativesOverview(activePeriod);
  const { data: adPerf, isLoading: adPerfLoading } = useAdPerformance(activePeriod, 6);
  const { data: formatComp } = useFormatComparison(activePeriod);

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
      {/* Top Performing Ads */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Top anuncios por rendimiento
        </h3>
        {adPerf?.ads && adPerf.ads.length > 0 ? (
          <div className="grid grid-cols-3 gap-3">
            {adPerf.ads.slice(0, 3).map(ad => (
              <div
                key={ad.adId}
                className={cn(
                  'rounded-xl border bg-card p-3 space-y-3',
                  ad.performanceTag === 'underperformer' && 'border-red-500/20',
                )}
              >
                {ad.thumbnailUrl ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={ad.thumbnailUrl}
                    alt={ad.adName}
                    className="h-32 w-full rounded-lg object-cover"
                  />
                ) : (
                  <div className="h-32 rounded-lg bg-muted flex items-center justify-center text-sm text-muted-foreground">
                    {ad.formatType === 'video' ? '\uD83C\uDFAC' : '\uD83D\uDDBC'} {ad.adName}
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium truncate">{ad.adName}</p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {ad.campaignName ?? 'Sin campa\u00f1a'}
                  </p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-[9px] text-muted-foreground">ROAS</p>
                    <p
                      className={cn(
                        'text-sm font-bold',
                        ad.roas != null && ad.roas >= 3
                          ? 'text-emerald-400'
                          : ad.roas != null && ad.roas < 1
                            ? 'text-red-400'
                            : 'text-amber-400',
                      )}
                    >
                      {ad.roas != null ? `${ad.roas.toFixed(1)}x` : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] text-muted-foreground">Ventas</p>
                    <p className="text-sm font-bold">{ad.conversions.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-[9px] text-muted-foreground">CPA</p>
                    <p
                      className={cn(
                        'text-sm font-bold',
                        ad.performanceTag === 'top_performer'
                          ? 'text-emerald-400'
                          : ad.performanceTag === 'underperformer'
                            ? 'text-red-400'
                            : 'text-amber-400',
                      )}
                    >
                      {ad.cpa != null ? `$${ad.cpa.toFixed(2)}` : '—'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {ad.performanceTag === 'top_performer' && (
                    <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[9px] text-emerald-400">
                      Top performer
                    </span>
                  )}
                  {ad.performanceTag === 'underperformer' && (
                    <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-[9px] text-red-400">
                      Peor rendimiento
                    </span>
                  )}
                  <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[9px] text-blue-400">
                    {ad.formatType === 'video'
                      ? 'Video'
                      : ad.formatType === 'carousel'
                        ? 'Carrusel'
                        : ad.formatType === 'image'
                          ? 'Imagen'
                          : ad.formatType}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : adPerfLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p className="font-medium">Sin datos de rendimiento por anuncio</p>
            <p className="mt-1 text-xs">
              Los datos aparecerán después de la próxima sincronización.
            </p>
          </div>
        )}
      </div>

      {/* Format Comparison + Video Retention */}
      <div className="grid grid-cols-2 gap-4">
        {/* Format Comparison */}
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Rendimiento por formato
          </h3>
          <div className="rounded-lg border bg-card p-4 space-y-3">
            {formatComp?.formats && formatComp.formats.length > 0 ? (
              formatComp.formats.map(fmt => {
                const Icon = formatIcons[fmt.formatType] ?? Film;
                return (
                  <div key={fmt.formatType} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-xs">
                          {fmt.formatType === 'video'
                            ? 'Video'
                            : fmt.formatType === 'carousel'
                              ? 'Carrusel'
                              : fmt.formatType === 'image'
                                ? 'Imagen estática'
                                : fmt.formatType}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs tabular-nums">
                        <span>
                          CTR{' '}
                          <strong
                            className={
                              fmt.avgCtr >= 2
                                ? 'text-emerald-400'
                                : fmt.avgCtr >= 1
                                  ? 'text-amber-400'
                                  : 'text-red-400'
                            }
                          >
                            {fmt.avgCtr.toFixed(1)}%
                          </strong>
                        </span>
                        <span>
                          CPA{' '}
                          <strong
                            className={
                              fmt.avgCpa != null && fmt.avgCpa <= 20
                                ? 'text-emerald-400'
                                : fmt.avgCpa != null && fmt.avgCpa <= 40
                                  ? 'text-amber-400'
                                  : 'text-red-400'
                            }
                          >
                            {fmt.avgCpa != null ? `$${fmt.avgCpa.toFixed(2)}` : '—'}
                          </strong>
                        </span>
                        <span>
                          ROAS{' '}
                          <strong
                            className={
                              fmt.avgRoas != null && fmt.avgRoas >= 3
                                ? 'text-emerald-400'
                                : fmt.avgRoas != null && fmt.avgRoas >= 1.5
                                  ? 'text-amber-400'
                                  : 'text-red-400'
                            }
                          >
                            {fmt.avgRoas != null ? `${fmt.avgRoas.toFixed(1)}x` : '—'}
                          </strong>
                        </span>
                      </div>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className={cn(
                          'h-2 rounded-full',
                          fmt.performanceScore >= 70
                            ? 'bg-emerald-500/60'
                            : fmt.performanceScore >= 40
                              ? 'bg-amber-500/60'
                              : 'bg-red-500/60',
                        )}
                        style={{ width: `${Math.max(fmt.performanceScore, 5)}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <>
                {[
                  { icon: Film, label: 'Video' },
                  { icon: LayoutGrid, label: 'Carrusel' },
                  { icon: ImageIcon, label: 'Imagen estática' },
                ].map(({ icon: Icon, label }) => (
                  <div key={label} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{label}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">Datos próximamente</span>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

        {/* Video Retention */}
        <div>
          <h3
            className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
            title="Cuántas personas ven tu video hasta cada punto. Ideal: >30% completa el video."
          >
            Retención de video
          </h3>
          {creatives?.videoRetention && creatives.videoRetention.plays > 0 ? (
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-end gap-2 h-[180px] px-2">
                {[
                  { label: 'Play', value: creatives.videoRetention.plays, pct: 100 },
                  {
                    label: '25%',
                    value: creatives.videoRetention.p25,
                    pct: (creatives.videoRetention.p25 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '50%',
                    value: creatives.videoRetention.p50,
                    pct: (creatives.videoRetention.p50 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '75%',
                    value: creatives.videoRetention.p75,
                    pct: (creatives.videoRetention.p75 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '100%',
                    value: creatives.videoRetention.p100,
                    pct: (creatives.videoRetention.p100 / creatives.videoRetention.plays) * 100,
                  },
                ].map((step, i) => (
                  <div key={step.label} className="flex-1 flex flex-col items-center gap-1">
                    <p className="text-[10px] font-semibold tabular-nums">
                      {formatNumber(step.value)}
                    </p>
                    <div
                      className={cn(
                        'w-full rounded-t',
                        i === 4
                          ? 'bg-emerald-500/50'
                          : i >= 3
                            ? 'bg-amber-500/40'
                            : 'bg-blue-500/50',
                      )}
                      style={{ height: `${Math.max(step.pct * 1.6, 4)}px` }}
                    />
                    <p className="text-[9px] text-muted-foreground">{step.label}</p>
                    {i > 0 && <p className="text-[8px] text-blue-400">{step.pct.toFixed(0)}%</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
              <p className="font-medium">Próximamente</p>
              <p className="mt-1 text-xs">
                Gráfico de retención: Play → 25% → 50% → 75% → 100% completado.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Video KPIs */}
      {creatives?.videoRetention && creatives.videoRetention.plays > 0 && (
        <div className="grid grid-cols-4 gap-2.5">
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Video Views</p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {formatNumber(creatives.videoRetention.plays)}
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Vistas 50%+</p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {formatNumber(creatives.videoRetention.p50)}
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Completados</p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {formatNumber(creatives.videoRetention.p100)}
            </p>
            <p className="text-[9px] text-emerald-500">
              {((creatives.videoRetention.p100 / creatives.videoRetention.plays) * 100).toFixed(0)}% completion
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Retención 75%</p>
            <p className="text-xl font-bold tabular-nums mt-1">
              {formatNumber(creatives.videoRetention.p75)}
            </p>
            <p className="text-[9px] text-amber-400">
              {((creatives.videoRetention.p75 / creatives.videoRetention.plays) * 100).toFixed(0)}% del total
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Run type check + lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx`
Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/growth-studio/components/metrics-dashboard/sidebar/meta-ads/tabs/CreativosTab.tsx
git commit -m "feat(growth-studio): rewrite CreativosTab with per-ad metrics matching mockup"
```

### Task 10: Final verification

- [ ] **Step 1: Run full backend suite**

Run: `cd backend && .venv/bin/ruff check src/ --no-cache && .venv/bin/pytest -x -q --tb=short`
Expected: all pass

- [ ] **Step 2: Run full frontend suite**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run`
Expected: all pass

- [ ] **Step 3: Verify git log**

Run: `git log --oneline -10`
Expected: ~7-8 new commits, all with conventional format

---

## Parallelization Guide

These workstreams can run in parallel with `isolation: "worktree"`:

| Agent | Workstream | Tasks | Dependencies |
|-------|-----------|-------|-------------|
| Agent 1 | E2E Resilience | Tasks 1-2 | None |
| Agent 2 | Meta Health Backend | Task 3 | None |
| Agent 3 | Meta Health Frontend | Task 4 | Needs Task 3 committed |
| Agent 4 | Ad Metrics Backend | Tasks 5-7 | None |
| Agent 5 | Ad Metrics Frontend | Tasks 8-9 | Needs Tasks 6-7 committed |

Conservative: 3 agents (Agent 1: Tasks 1-2, Agent 2: Tasks 3-4, Agent 3: Tasks 5-9).
