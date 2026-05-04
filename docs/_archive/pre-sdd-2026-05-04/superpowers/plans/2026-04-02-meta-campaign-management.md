# Meta Campaign Management & Recommendations — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the full campaign hierarchy (campaigns, ad sets, ads, creatives) and optimization recommendations from Meta's Marketing API, store them as first-class entities, and display them in Growth Studio so users can monitor campaign structure, performance, and act on Meta's optimization suggestions.

**Architecture:** New `campaign_management` sub-module inside `analytics` (not a separate bounded context — campaigns are tightly coupled to metrics). Separate sync job from the metrics ETL to avoid bloating extraction runs. Reuses existing `ConnectionPort` for credentials and ARQ for scheduling. Frontend extends Growth Studio with a dedicated campaign panel.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Alembic (idempotent), Pydantic v2, httpx, ARQ (Redis), React/Next.js 15, Shadcn UI, React Query.

---

## Meta API Research Summary

The Meta Marketing API (v24.0) exposes a 4-level hierarchy with rich metadata:

| Level | Key Fields | API Endpoint |
|---|---|---|
| **Campaign** | name, objective (OUTCOME_*), status, effective_status, bid_strategy, daily_budget, lifetime_budget, budget_remaining, start/stop_time, special_ad_categories | `GET /act_{id}/campaigns` |
| **Ad Set** | name, targeting (JSONB: age, gender, geo, interests, custom_audiences, placements), optimization_goal, billing_event, daily_budget, learning_stage_info, recommendations | `GET /act_{id}/adsets` |
| **Ad** | name, status, effective_status, creative{id}, recommendations, preview_shareable_link | `GET /act_{id}/ads` |
| **Creative** | thumbnail_url, image_url, video_id, title, body, call_to_action_type, link_url, object_story_spec | `GET /{creative_id}` |
| **Recommendations** | type (40+ enum: CREATIVE_FATIGUE, SCALE_GOOD_CAMPAIGN, AUTOMATIC_PLACEMENTS...), object_ids, body, lift_estimate, opportunity_score, url | `GET /act_{id}/recommendations` |

**Rate limits:** 300 + 40×active_ads points/hour (dev), reads=1 point. Pagination cursor-based, limit ~500.

**Permissions needed:** `ads_read` (already granted via existing Meta connection).

---

## File Structure

```
backend/src/modules/analytics/
├── domain/
│   └── campaign_entities.py          # CREATE — CampaignStatus, AdSetLearningPhase enums + domain types
│
├── infrastructure/
│   ├── models/
│   │   ├── ad_campaign_model.py      # CREATE — AdCampaignModel
│   │   ├── ad_set_model.py           # CREATE — AdSetModel
│   │   ├── ad_model.py              # CREATE — AdModel
│   │   └── ad_recommendation_model.py # CREATE — AdRecommendationModel
│   │
│   ├── providers/
│   │   └── meta_campaign_provider.py  # CREATE — MetaCampaignProvider
│   │
│   ├── repositories/
│   │   └── campaign_repository.py     # CREATE — CampaignRepository
│   │
│   └── sync/
│       └── campaign_sync_pipeline.py  # CREATE — CampaignSyncPipeline
│
├── application/
│   ├── services/
│   │   └── campaign_service.py        # CREATE — CampaignService
│   └── dto/
│       └── campaign_dto.py            # CREATE — DTOs
│
├── api/
│   └── campaigns.py                   # CREATE — API routes
│
└── workers/
    └── tasks.py                       # MODIFY — add run_campaign_sync task

backend/alembic/versions/
└── 032_create_campaign_management_tables.py  # CREATE

backend/tests/modules/analytics/
├── test_meta_campaign_provider.py     # CREATE
├── test_campaign_repository.py        # CREATE
└── test_campaign_sync_pipeline.py     # CREATE

frontend/src/features/growth-studio/
├── api/
│   └── campaigns-api.ts               # CREATE — React Query hooks
├── types/
│   └── campaigns.ts                   # CREATE — TypeScript types
└── components/
    └── campaign-panel/
        ├── CampaignPanel.tsx           # CREATE — Main panel
        ├── CampaignCard.tsx            # CREATE — Single campaign card
        ├── AdSetDetail.tsx             # CREATE — Ad set targeting detail
        └── RecommendationsList.tsx     # CREATE — Recommendations feed
```

---

## Task 1: Alembic Migration — Campaign Management Tables

**Files:**
- Create: `backend/alembic/versions/032_create_campaign_management_tables.py`

- [ ] **Step 1: Get current alembic head**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic heads"
```

Expected: `031_expand_meta_ads_campaign_idx (head)`

- [ ] **Step 2: Write the migration**

```python
"""create_campaign_management_tables

Tables for storing Meta campaign hierarchy metadata and recommendations.

Revision ID: 032_campaign_management
Revises: 031_expand_meta_ads_campaign_idx
Create Date: 2026-04-02
"""
from alembic import op

revision = "032_campaign_management"
down_revision = "031_expand_meta_ads_campaign_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ad_campaigns ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            objective VARCHAR(100),
            status VARCHAR(50),
            effective_status VARCHAR(50),
            bid_strategy VARCHAR(100),
            daily_budget BIGINT,
            lifetime_budget BIGINT,
            budget_remaining BIGINT,
            buying_type VARCHAR(50) DEFAULT 'AUCTION',
            special_ad_categories JSONB DEFAULT '[]'::jsonb,
            start_time TIMESTAMPTZ,
            stop_time TIMESTAMPTZ,
            external_created_time TIMESTAMPTZ,
            external_updated_time TIMESTAMPTZ,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ad_campaigns_tenant_provider_ext
        ON ad_campaigns (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_campaigns_tenant ON ad_campaigns (tenant_id)")

    # ── ad_sets ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_sets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            campaign_external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            status VARCHAR(50),
            effective_status VARCHAR(50),
            optimization_goal VARCHAR(100),
            billing_event VARCHAR(100),
            bid_strategy VARCHAR(100),
            daily_budget BIGINT,
            lifetime_budget BIGINT,
            budget_remaining BIGINT,
            targeting JSONB DEFAULT '{}'::jsonb,
            destination_type VARCHAR(100),
            learning_stage VARCHAR(50),
            start_time TIMESTAMPTZ,
            end_time TIMESTAMPTZ,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ad_sets_tenant_provider_ext
        ON ad_sets (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_sets_tenant ON ad_sets (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_sets_campaign ON ad_sets (tenant_id, campaign_external_id)")

    # ── ads ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            campaign_external_id VARCHAR(255) NOT NULL,
            ad_set_external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            status VARCHAR(50),
            effective_status VARCHAR(50),
            creative_id VARCHAR(255),
            creative_thumbnail_url TEXT,
            creative_image_url TEXT,
            creative_video_id VARCHAR(255),
            creative_title VARCHAR(500),
            creative_body TEXT,
            creative_cta VARCHAR(100),
            creative_link_url TEXT,
            preview_shareable_link TEXT,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ads_tenant_provider_ext
        ON ads (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ads_tenant ON ads (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ads_adset ON ads (tenant_id, ad_set_external_id)")

    # ── ad_recommendations ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_recommendations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            source VARCHAR(50) NOT NULL DEFAULT 'account',
            recommendation_type VARCHAR(100) NOT NULL,
            object_ids JSONB DEFAULT '[]'::jsonb,
            title VARCHAR(500),
            body TEXT,
            blame_field VARCHAR(100),
            importance VARCHAR(20),
            confidence VARCHAR(20),
            lift_estimate VARCHAR(100),
            opportunity_score FLOAT,
            url TEXT,
            recommendation_signature VARCHAR(500),
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_recs_tenant ON ad_recommendations (tenant_id)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_recs_tenant_type
        ON ad_recommendations (tenant_id, recommendation_type)
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ad_recommendations CASCADE")
    op.execute("DROP TABLE IF EXISTS ads CASCADE")
    op.execute("DROP TABLE IF EXISTS ad_sets CASCADE")
    op.execute("DROP TABLE IF EXISTS ad_campaigns CASCADE")
```

- [ ] **Step 3: Verify migration syntax**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && python -c \"import importlib; importlib.import_module('alembic.versions.032_create_campaign_management_tables')\" 2>&1 || echo 'Import check not needed for alembic — verify via alembic heads'"
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic heads"
```

Expected: Shows `032_campaign_management (head)`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/032_create_campaign_management_tables.py
git commit -m "feat(analytics): add migration for campaign management tables"
```

---

## Task 2: Domain Entities & Enums

**Files:**
- Create: `backend/src/modules/analytics/domain/campaign_entities.py`

- [ ] **Step 1: Write domain enums and types**

```python
"""Domain entities for campaign management.

Value objects and enums — no framework imports.
"""

from __future__ import annotations

from enum import Enum


class CampaignObjective(str, Enum):
    """Meta ODAX (Outcome-Driven Ad Experiences) objectives."""
    OUTCOME_AWARENESS = "OUTCOME_AWARENESS"
    OUTCOME_ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    OUTCOME_TRAFFIC = "OUTCOME_TRAFFIC"
    OUTCOME_LEADS = "OUTCOME_LEADS"
    OUTCOME_SALES = "OUTCOME_SALES"
    OUTCOME_APP_PROMOTION = "OUTCOME_APP_PROMOTION"
    # Legacy objectives (still returned by API for old campaigns)
    CONVERSIONS = "CONVERSIONS"
    LINK_CLICKS = "LINK_CLICKS"
    REACH = "REACH"
    BRAND_AWARENESS = "BRAND_AWARENESS"
    VIDEO_VIEWS = "VIDEO_VIEWS"
    POST_ENGAGEMENT = "POST_ENGAGEMENT"
    MESSAGES = "MESSAGES"
    LEAD_GENERATION = "LEAD_GENERATION"
    UNKNOWN = "UNKNOWN"


class CampaignStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    IN_PROCESS = "IN_PROCESS"
    WITH_ISSUES = "WITH_ISSUES"


class EffectiveStatus(str, Enum):
    """Effective status includes inherited states from parent objects."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    IN_PROCESS = "IN_PROCESS"
    WITH_ISSUES = "WITH_ISSUES"
    PENDING_REVIEW = "PENDING_REVIEW"
    DISAPPROVED = "DISAPPROVED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    ADSET_PAUSED = "ADSET_PAUSED"
    PREAPPROVED = "PREAPPROVED"


class BidStrategy(str, Enum):
    LOWEST_COST_WITHOUT_CAP = "LOWEST_COST_WITHOUT_CAP"
    LOWEST_COST_WITH_BID_CAP = "LOWEST_COST_WITH_BID_CAP"
    COST_CAP = "COST_CAP"
    LOWEST_COST_WITH_MIN_ROAS = "LOWEST_COST_WITH_MIN_ROAS"


class LearningStage(str, Enum):
    LEARNING = "LEARNING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class RecommendationSource(str, Enum):
    """Where the recommendation came from."""
    ACCOUNT = "account"      # GET /act_{id}/recommendations
    CAMPAIGN = "campaign"    # campaign.recommendations field
    AD_SET = "ad_set"        # adset.recommendations field
    AD = "ad"                # ad.recommendations field
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/modules/analytics/domain/campaign_entities.py
git commit -m "feat(analytics): add campaign management domain entities"
```

---

## Task 3: SQLAlchemy Models

**Files:**
- Create: `backend/src/modules/analytics/infrastructure/models/ad_campaign_model.py`
- Create: `backend/src/modules/analytics/infrastructure/models/ad_set_model.py`
- Create: `backend/src/modules/analytics/infrastructure/models/ad_model.py`
- Create: `backend/src/modules/analytics/infrastructure/models/ad_recommendation_model.py`

- [ ] **Step 1: Write AdCampaignModel**

```python
"""SQLAlchemy model for ad_campaigns table."""

import uuid

from sqlalchemy import Column, String, BigInteger, DateTime, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdCampaignModel(Base):
    __tablename__ = "ad_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    objective = Column(String(100))
    status = Column(String(50))
    effective_status = Column(String(50))
    bid_strategy = Column(String(100))
    daily_budget = Column(BigInteger)
    lifetime_budget = Column(BigInteger)
    budget_remaining = Column(BigInteger)
    buying_type = Column(String(50), default="AUCTION")
    special_ad_categories = Column(JSONB, server_default="[]")
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    external_created_time = Column(DateTime(timezone=True))
    external_updated_time = Column(DateTime(timezone=True))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
```

- [ ] **Step 2: Write AdSetModel**

```python
"""SQLAlchemy model for ad_sets table."""

import uuid

from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdSetModel(Base):
    __tablename__ = "ad_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    campaign_external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    status = Column(String(50))
    effective_status = Column(String(50))
    optimization_goal = Column(String(100))
    billing_event = Column(String(100))
    bid_strategy = Column(String(100))
    daily_budget = Column(BigInteger)
    lifetime_budget = Column(BigInteger)
    budget_remaining = Column(BigInteger)
    targeting = Column(JSONB, server_default="{}")
    destination_type = Column(String(100))
    learning_stage = Column(String(50))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
```

- [ ] **Step 3: Write AdModel**

```python
"""SQLAlchemy model for ads table."""

import uuid

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdModel(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    campaign_external_id = Column(String(255), nullable=False)
    ad_set_external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    status = Column(String(50))
    effective_status = Column(String(50))
    creative_id = Column(String(255))
    creative_thumbnail_url = Column(Text)
    creative_image_url = Column(Text)
    creative_video_id = Column(String(255))
    creative_title = Column(String(500))
    creative_body = Column(Text)
    creative_cta = Column(String(100))
    creative_link_url = Column(Text)
    preview_shareable_link = Column(Text)
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
```

- [ ] **Step 4: Write AdRecommendationModel**

```python
"""SQLAlchemy model for ad_recommendations table."""

import uuid

from sqlalchemy import Column, String, Text, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdRecommendationModel(Base):
    __tablename__ = "ad_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    source = Column(String(50), nullable=False, default="account")
    recommendation_type = Column(String(100), nullable=False)
    object_ids = Column(JSONB, server_default="[]")
    title = Column(String(500))
    body = Column(Text)
    blame_field = Column(String(100))
    importance = Column(String(20))
    confidence = Column(String(20))
    lift_estimate = Column(String(100))
    opportunity_score = Column(Float)
    url = Column(Text)
    recommendation_signature = Column(String(500))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/models/ad_campaign_model.py \
        backend/src/modules/analytics/infrastructure/models/ad_set_model.py \
        backend/src/modules/analytics/infrastructure/models/ad_model.py \
        backend/src/modules/analytics/infrastructure/models/ad_recommendation_model.py
git commit -m "feat(analytics): add SQLAlchemy models for campaign management"
```

---

## Task 4: Campaign Repository

**Files:**
- Create: `backend/src/modules/analytics/infrastructure/repositories/campaign_repository.py`
- Create: `backend/tests/modules/analytics/test_campaign_repository.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for CampaignRepository — upsert and query operations."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.modules.analytics.infrastructure.repositories.campaign_repository import (
    CampaignRepository,
)


class TestCampaignRepositoryUpsert:
    """Test upsert_campaigns correctly inserts and updates."""

    @pytest.mark.asyncio
    async def test_upsert_campaigns_insert(self, db_session):
        repo = CampaignRepository(db_session)
        tenant_id = uuid4()
        campaigns = [
            {
                "tenant_id": str(tenant_id),
                "provider": "meta",
                "external_id": "camp_001",
                "name": "Spring Sale",
                "objective": "OUTCOME_SALES",
                "status": "ACTIVE",
                "effective_status": "ACTIVE",
                "daily_budget": 5000,
            }
        ]
        count = await repo.upsert_campaigns(tenant_id, campaigns)
        assert count == 1

    @pytest.mark.asyncio
    async def test_upsert_campaigns_update_on_conflict(self, db_session):
        repo = CampaignRepository(db_session)
        tenant_id = uuid4()
        campaign = {
            "tenant_id": str(tenant_id),
            "provider": "meta",
            "external_id": "camp_001",
            "name": "Spring Sale",
            "status": "ACTIVE",
        }
        await repo.upsert_campaigns(tenant_id, [campaign])

        campaign["name"] = "Spring Sale V2"
        campaign["status"] = "PAUSED"
        count = await repo.upsert_campaigns(tenant_id, [campaign])
        assert count == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_campaign_repository.py -x -q --tb=short"
```

Expected: FAIL — module not found

- [ ] **Step 3: Write CampaignRepository**

```python
"""Repository for campaign management entities.

Handles upsert operations for campaigns, ad sets, ads, and recommendations.
Uses raw SQL for COALESCE-based ON CONFLICT (matching existing metric pattern).
"""

import json
import logging
from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CampaignRepository:
    """CRUD operations for campaign hierarchy + recommendations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # ── Campaigns ──

    _UPSERT_CAMPAIGN_SQL = text("""
        INSERT INTO ad_campaigns (
            tenant_id, provider, external_id, name, objective,
            status, effective_status, bid_strategy,
            daily_budget, lifetime_budget, budget_remaining,
            buying_type, special_ad_categories,
            start_time, stop_time,
            external_created_time, external_updated_time,
            extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id, :name, :objective,
            :status, :effective_status, :bid_strategy,
            :daily_budget, :lifetime_budget, :budget_remaining,
            :buying_type, :special_ad_categories::jsonb,
            :start_time, :stop_time,
            :external_created_time, :external_updated_time,
            :extra::jsonb, NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            name = EXCLUDED.name,
            objective = EXCLUDED.objective,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            bid_strategy = EXCLUDED.bid_strategy,
            daily_budget = EXCLUDED.daily_budget,
            lifetime_budget = EXCLUDED.lifetime_budget,
            budget_remaining = EXCLUDED.budget_remaining,
            buying_type = EXCLUDED.buying_type,
            special_ad_categories = EXCLUDED.special_ad_categories,
            start_time = EXCLUDED.start_time,
            stop_time = EXCLUDED.stop_time,
            external_created_time = EXCLUDED.external_created_time,
            external_updated_time = EXCLUDED.external_updated_time,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    async def upsert_campaigns(
        self, tenant_id: UUID, campaigns: List[dict],
    ) -> int:
        count = 0
        for c in campaigns:
            await self._session.execute(self._UPSERT_CAMPAIGN_SQL, {
                "tenant_id": str(tenant_id),
                "provider": c.get("provider", "meta"),
                "external_id": c["external_id"],
                "name": c.get("name", ""),
                "objective": c.get("objective"),
                "status": c.get("status"),
                "effective_status": c.get("effective_status"),
                "bid_strategy": c.get("bid_strategy"),
                "daily_budget": c.get("daily_budget"),
                "lifetime_budget": c.get("lifetime_budget"),
                "budget_remaining": c.get("budget_remaining"),
                "buying_type": c.get("buying_type", "AUCTION"),
                "special_ad_categories": json.dumps(c.get("special_ad_categories", [])),
                "start_time": c.get("start_time"),
                "stop_time": c.get("stop_time"),
                "external_created_time": c.get("external_created_time"),
                "external_updated_time": c.get("external_updated_time"),
                "extra": json.dumps(c.get("extra", {})),
            })
            count += 1
        return count

    # ── Ad Sets ──

    _UPSERT_ADSET_SQL = text("""
        INSERT INTO ad_sets (
            tenant_id, provider, external_id, campaign_external_id,
            name, status, effective_status,
            optimization_goal, billing_event, bid_strategy,
            daily_budget, lifetime_budget, budget_remaining,
            targeting, destination_type, learning_stage,
            start_time, end_time, extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id, :campaign_external_id,
            :name, :status, :effective_status,
            :optimization_goal, :billing_event, :bid_strategy,
            :daily_budget, :lifetime_budget, :budget_remaining,
            :targeting::jsonb, :destination_type, :learning_stage,
            :start_time, :end_time, :extra::jsonb, NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            campaign_external_id = EXCLUDED.campaign_external_id,
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            optimization_goal = EXCLUDED.optimization_goal,
            billing_event = EXCLUDED.billing_event,
            bid_strategy = EXCLUDED.bid_strategy,
            daily_budget = EXCLUDED.daily_budget,
            lifetime_budget = EXCLUDED.lifetime_budget,
            budget_remaining = EXCLUDED.budget_remaining,
            targeting = EXCLUDED.targeting,
            destination_type = EXCLUDED.destination_type,
            learning_stage = EXCLUDED.learning_stage,
            start_time = EXCLUDED.start_time,
            end_time = EXCLUDED.end_time,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    async def upsert_ad_sets(
        self, tenant_id: UUID, ad_sets: List[dict],
    ) -> int:
        count = 0
        for a in ad_sets:
            await self._session.execute(self._UPSERT_ADSET_SQL, {
                "tenant_id": str(tenant_id),
                "provider": a.get("provider", "meta"),
                "external_id": a["external_id"],
                "campaign_external_id": a["campaign_external_id"],
                "name": a.get("name", ""),
                "status": a.get("status"),
                "effective_status": a.get("effective_status"),
                "optimization_goal": a.get("optimization_goal"),
                "billing_event": a.get("billing_event"),
                "bid_strategy": a.get("bid_strategy"),
                "daily_budget": a.get("daily_budget"),
                "lifetime_budget": a.get("lifetime_budget"),
                "budget_remaining": a.get("budget_remaining"),
                "targeting": json.dumps(a.get("targeting", {})),
                "destination_type": a.get("destination_type"),
                "learning_stage": a.get("learning_stage"),
                "start_time": a.get("start_time"),
                "end_time": a.get("end_time"),
                "extra": json.dumps(a.get("extra", {})),
            })
            count += 1
        return count

    # ── Ads ──

    _UPSERT_AD_SQL = text("""
        INSERT INTO ads (
            tenant_id, provider, external_id,
            campaign_external_id, ad_set_external_id,
            name, status, effective_status,
            creative_id, creative_thumbnail_url, creative_image_url,
            creative_video_id, creative_title, creative_body,
            creative_cta, creative_link_url,
            preview_shareable_link, extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :external_id,
            :campaign_external_id, :ad_set_external_id,
            :name, :status, :effective_status,
            :creative_id, :creative_thumbnail_url, :creative_image_url,
            :creative_video_id, :creative_title, :creative_body,
            :creative_cta, :creative_link_url,
            :preview_shareable_link, :extra::jsonb, NOW(), NOW()
        )
        ON CONFLICT (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
        DO UPDATE SET
            campaign_external_id = EXCLUDED.campaign_external_id,
            ad_set_external_id = EXCLUDED.ad_set_external_id,
            name = EXCLUDED.name,
            status = EXCLUDED.status,
            effective_status = EXCLUDED.effective_status,
            creative_id = EXCLUDED.creative_id,
            creative_thumbnail_url = EXCLUDED.creative_thumbnail_url,
            creative_image_url = EXCLUDED.creative_image_url,
            creative_video_id = EXCLUDED.creative_video_id,
            creative_title = EXCLUDED.creative_title,
            creative_body = EXCLUDED.creative_body,
            creative_cta = EXCLUDED.creative_cta,
            creative_link_url = EXCLUDED.creative_link_url,
            preview_shareable_link = EXCLUDED.preview_shareable_link,
            extra = EXCLUDED.extra,
            updated_at = NOW()
    """)

    async def upsert_ads(
        self, tenant_id: UUID, ads: List[dict],
    ) -> int:
        count = 0
        for ad in ads:
            await self._session.execute(self._UPSERT_AD_SQL, {
                "tenant_id": str(tenant_id),
                "provider": ad.get("provider", "meta"),
                "external_id": ad["external_id"],
                "campaign_external_id": ad["campaign_external_id"],
                "ad_set_external_id": ad["ad_set_external_id"],
                "name": ad.get("name", ""),
                "status": ad.get("status"),
                "effective_status": ad.get("effective_status"),
                "creative_id": ad.get("creative_id"),
                "creative_thumbnail_url": ad.get("creative_thumbnail_url"),
                "creative_image_url": ad.get("creative_image_url"),
                "creative_video_id": ad.get("creative_video_id"),
                "creative_title": ad.get("creative_title"),
                "creative_body": ad.get("creative_body"),
                "creative_cta": ad.get("creative_cta"),
                "creative_link_url": ad.get("creative_link_url"),
                "preview_shareable_link": ad.get("preview_shareable_link"),
                "extra": json.dumps(ad.get("extra", {})),
            })
            count += 1
        return count

    # ── Recommendations ──

    _UPSERT_RECOMMENDATION_SQL = text("""
        INSERT INTO ad_recommendations (
            tenant_id, provider, source, recommendation_type,
            object_ids, title, body, blame_field,
            importance, confidence, lift_estimate,
            opportunity_score, url, recommendation_signature,
            extra, created_at, updated_at
        ) VALUES (
            :tenant_id, :provider, :source, :recommendation_type,
            :object_ids::jsonb, :title, :body, :blame_field,
            :importance, :confidence, :lift_estimate,
            :opportunity_score, :url, :recommendation_signature,
            :extra::jsonb, NOW(), NOW()
        )
        ON CONFLICT DO NOTHING
    """)

    async def upsert_recommendations(
        self, tenant_id: UUID, recommendations: List[dict],
    ) -> int:
        count = 0
        for r in recommendations:
            await self._session.execute(self._UPSERT_RECOMMENDATION_SQL, {
                "tenant_id": str(tenant_id),
                "provider": r.get("provider", "meta"),
                "source": r.get("source", "account"),
                "recommendation_type": r["recommendation_type"],
                "object_ids": json.dumps(r.get("object_ids", [])),
                "title": r.get("title"),
                "body": r.get("body"),
                "blame_field": r.get("blame_field"),
                "importance": r.get("importance"),
                "confidence": r.get("confidence"),
                "lift_estimate": r.get("lift_estimate"),
                "opportunity_score": r.get("opportunity_score"),
                "url": r.get("url"),
                "recommendation_signature": r.get("recommendation_signature"),
                "extra": json.dumps(r.get("extra", {})),
            })
            count += 1
        return count

    # ── Queries ──

    async def get_campaigns(
        self, tenant_id: UUID, provider: str = "meta",
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT * FROM ad_campaigns
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "provider": provider},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_ad_sets(
        self, tenant_id: UUID, campaign_external_id: str,
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT * FROM ad_sets
                WHERE tenant_id = :tenant_id
                  AND campaign_external_id = :campaign_external_id
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "campaign_external_id": campaign_external_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_ads(
        self, tenant_id: UUID, ad_set_external_id: str,
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT * FROM ads
                WHERE tenant_id = :tenant_id
                  AND ad_set_external_id = :ad_set_external_id
                  AND deleted_at IS NULL
                ORDER BY effective_status = 'ACTIVE' DESC, name
            """),
            {"tenant_id": str(tenant_id), "ad_set_external_id": ad_set_external_id},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def get_recommendations(
        self, tenant_id: UUID, provider: str = "meta",
    ) -> list:
        result = await self._session.execute(
            text("""
                SELECT * FROM ad_recommendations
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                ORDER BY opportunity_score DESC NULLS LAST, importance, created_at DESC
                LIMIT 50
            """),
            {"tenant_id": str(tenant_id), "provider": provider},
        )
        return [dict(row._mapping) for row in result.fetchall()]

    async def soft_delete_stale(
        self, tenant_id: UUID, provider: str, table: str, active_external_ids: list,
    ) -> int:
        """Soft-delete entities no longer returned by the API."""
        if not active_external_ids:
            return 0
        placeholders = ", ".join(f":id_{i}" for i in range(len(active_external_ids)))
        params = {"tenant_id": str(tenant_id), "provider": provider}
        params.update({f"id_{i}": eid for i, eid in enumerate(active_external_ids)})
        result = await self._session.execute(
            text(f"""
                UPDATE {table}
                SET deleted_at = NOW(), updated_at = NOW()
                WHERE tenant_id = :tenant_id
                  AND provider = :provider
                  AND deleted_at IS NULL
                  AND external_id NOT IN ({placeholders})
            """),
            params,
        )
        return result.rowcount
```

- [ ] **Step 4: Run tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_campaign_repository.py -x -q --tb=short"
```

Note: These tests require DB fixtures. If the test infra doesn't have a `db_session` fixture, use a simpler unit test approach or skip integration tests for now.

- [ ] **Step 5: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/repositories/campaign_repository.py \
        backend/tests/modules/analytics/test_campaign_repository.py
git commit -m "feat(analytics): add CampaignRepository with upsert operations"
```

---

## Task 5: Meta Campaign Provider (API Extraction)

**Files:**
- Create: `backend/src/modules/analytics/infrastructure/providers/meta_campaign_provider.py`
- Create: `backend/tests/modules/analytics/test_meta_campaign_provider.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for MetaCampaignProvider — campaign hierarchy extraction from Meta API."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
    MetaCampaignProvider,
)

TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_token",
    "ad_account_id": "111222",
    "currency": "MXN",
}


def _ok_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestExtractCampaigns:
    @pytest.mark.asyncio
    async def test_extracts_campaigns_with_all_fields(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "id": "camp_001",
                    "name": "Spring Sale",
                    "objective": "OUTCOME_SALES",
                    "status": "ACTIVE",
                    "effective_status": "ACTIVE",
                    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                    "daily_budget": "5000",
                    "budget_remaining": "3200",
                    "buying_type": "AUCTION",
                    "special_ad_categories": [],
                    "start_time": "2026-03-01T00:00:00-0500",
                    "created_time": "2026-02-28T10:00:00-0500",
                    "updated_time": "2026-03-15T14:00:00-0500",
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        result = await provider.extract_campaigns(client, CREDS)

        assert len(result) == 1
        camp = result[0]
        assert camp["external_id"] == "camp_001"
        assert camp["name"] == "Spring Sale"
        assert camp["objective"] == "OUTCOME_SALES"
        assert camp["daily_budget"] == 5000

    @pytest.mark.asyncio
    async def test_no_ad_account_returns_empty(self):
        provider = MetaCampaignProvider()
        client = AsyncMock()
        result = await provider.extract_campaigns(client, {"access_token": "tok"})
        assert result == []


class TestExtractAdSets:
    @pytest.mark.asyncio
    async def test_extracts_ad_sets_with_targeting(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "id": "adset_001",
                    "campaign_id": "camp_001",
                    "name": "Mujeres 25-34 CDMX",
                    "status": "ACTIVE",
                    "effective_status": "ACTIVE",
                    "optimization_goal": "CONVERSIONS",
                    "billing_event": "IMPRESSIONS",
                    "daily_budget": "2000",
                    "targeting": {
                        "age_min": 25,
                        "age_max": 34,
                        "genders": [2],
                        "geo_locations": {"cities": [{"key": "2673660"}]},
                        "interests": [{"id": "123", "name": "Yoga"}],
                    },
                    "destination_type": "WEBSITE",
                    "learning_stage_info": {"status": "SUCCESS"},
                    "recommendations": [
                        {
                            "title": "Expand Audience",
                            "message": "Your audience is too narrow",
                            "code": 1942008,
                            "importance": "HIGH",
                            "confidence": "HIGH",
                            "blame_field": "targeting",
                        }
                    ],
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        ad_sets, inline_recs = await provider.extract_ad_sets(client, CREDS)

        assert len(ad_sets) == 1
        adset = ad_sets[0]
        assert adset["external_id"] == "adset_001"
        assert adset["targeting"]["age_min"] == 25
        assert adset["learning_stage"] == "SUCCESS"

        # Inline recommendation extracted
        assert len(inline_recs) == 1
        assert inline_recs[0]["recommendation_type"] == "1942008"
        assert inline_recs[0]["source"] == "ad_set"


class TestExtractRecommendations:
    @pytest.mark.asyncio
    async def test_extracts_account_recommendations(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "recommendation_data": {
                        "recommendation_signature": "sig_abc123",
                        "type": "CREATIVE_FATIGUE",
                        "object_ids": ["camp_001"],
                        "recommendation_content": {
                            "body": "Your creative has been shown too many times",
                            "lift_estimate": "+15% CTR",
                            "opportunity_score_lift": 8.5,
                        },
                        "url": "https://business.facebook.com/adsmanager/...",
                    },
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        recs = await provider.extract_account_recommendations(client, CREDS)

        assert len(recs) == 1
        rec = recs[0]
        assert rec["recommendation_type"] == "CREATIVE_FATIGUE"
        assert rec["source"] == "account"
        assert rec["opportunity_score"] == 8.5
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_meta_campaign_provider.py -x -q --tb=short"
```

Expected: FAIL — module not found

- [ ] **Step 3: Write MetaCampaignProvider**

```python
"""MetaCampaignProvider — extracts campaign hierarchy + recommendations from Meta API.

Separate from MetaProvider (metrics) to keep sync jobs independent.
Uses the same credential pattern (access_token, ad_account_id from ConnectionPort).
"""

import json
import logging
from typing import List, Tuple

import httpx

GRAPH_API_BASE = "https://graph.facebook.com/v24.0"

logger = logging.getLogger(__name__)

_CAMPAIGN_FIELDS = (
    "id,name,objective,status,effective_status,bid_strategy,"
    "daily_budget,lifetime_budget,budget_remaining,buying_type,"
    "special_ad_categories,start_time,stop_time,"
    "created_time,updated_time"
)

_ADSET_FIELDS = (
    "id,campaign_id,name,status,effective_status,"
    "optimization_goal,billing_event,bid_strategy,"
    "daily_budget,lifetime_budget,budget_remaining,"
    "targeting,destination_type,learning_stage_info,"
    "start_time,end_time,recommendations"
)

_AD_FIELDS = (
    "id,campaign_id,adset_id,name,status,effective_status,"
    "creative{id,thumbnail_url,image_url,video_id,title,body,"
    "call_to_action_type,effective_object_story_id,url_tags},"
    "preview_shareable_link,recommendations"
)

_RECOMMENDATION_FIELDS = (
    "recommendation_data{recommendation_signature,type,object_ids,"
    "recommendation_content,url}"
)


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def _raise_for_meta_error(response: httpx.Response, context: str) -> None:
    if response.status_code >= 400:
        body = response.text[:500]
        logger.error("meta_campaign_api_error context=%s status=%s body=%s",
                      context, response.status_code, body)
        response.raise_for_status()


async def _paginate(
    client: httpx.AsyncClient, url: str, headers: dict,
    params: dict, context: str, max_pages: int = 20,
) -> List[dict]:
    """Fetch all pages of a Meta API response."""
    all_data = []
    for _ in range(max_pages):
        resp = await client.get(url, headers=headers, params=params)
        _raise_for_meta_error(resp, context)
        body = resp.json()
        all_data.extend(body.get("data", []))

        paging = body.get("paging", {})
        next_url = paging.get("next")
        if not next_url:
            break
        # Next URL is absolute — use it directly
        url = next_url
        params = {}  # params are embedded in the next URL
    return all_data


class MetaCampaignProvider:
    """Extracts campaign hierarchy and recommendations from Meta Marketing API."""

    async def extract_campaigns(
        self, client: httpx.AsyncClient, credentials: dict,
    ) -> List[dict]:
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/campaigns",
            _auth_headers(access_token),
            {"fields": _CAMPAIGN_FIELDS, "limit": "500"},
            "campaigns",
        )

        campaigns = []
        for row in rows:
            campaigns.append({
                "external_id": row["id"],
                "name": row.get("name", ""),
                "objective": row.get("objective"),
                "status": row.get("status"),
                "effective_status": row.get("effective_status"),
                "bid_strategy": row.get("bid_strategy"),
                "daily_budget": int(row["daily_budget"]) if row.get("daily_budget") else None,
                "lifetime_budget": int(row["lifetime_budget"]) if row.get("lifetime_budget") else None,
                "budget_remaining": int(row["budget_remaining"]) if row.get("budget_remaining") else None,
                "buying_type": row.get("buying_type", "AUCTION"),
                "special_ad_categories": row.get("special_ad_categories", []),
                "start_time": row.get("start_time"),
                "stop_time": row.get("stop_time"),
                "external_created_time": row.get("created_time"),
                "external_updated_time": row.get("updated_time"),
            })
        return campaigns

    async def extract_ad_sets(
        self, client: httpx.AsyncClient, credentials: dict,
    ) -> Tuple[List[dict], List[dict]]:
        """Returns (ad_sets, inline_recommendations)."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return [], []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/adsets",
            _auth_headers(access_token),
            {"fields": _ADSET_FIELDS, "limit": "500"},
            "adsets",
        )

        ad_sets = []
        inline_recs = []
        for row in rows:
            learning_info = row.get("learning_stage_info", {})
            ad_sets.append({
                "external_id": row["id"],
                "campaign_external_id": row.get("campaign_id", ""),
                "name": row.get("name", ""),
                "status": row.get("status"),
                "effective_status": row.get("effective_status"),
                "optimization_goal": row.get("optimization_goal"),
                "billing_event": row.get("billing_event"),
                "bid_strategy": row.get("bid_strategy"),
                "daily_budget": int(row["daily_budget"]) if row.get("daily_budget") else None,
                "lifetime_budget": int(row["lifetime_budget"]) if row.get("lifetime_budget") else None,
                "budget_remaining": int(row["budget_remaining"]) if row.get("budget_remaining") else None,
                "targeting": row.get("targeting", {}),
                "destination_type": row.get("destination_type"),
                "learning_stage": learning_info.get("status") if learning_info else None,
                "start_time": row.get("start_time"),
                "end_time": row.get("end_time"),
            })

            for rec in row.get("recommendations", []):
                inline_recs.append({
                    "source": "ad_set",
                    "recommendation_type": str(rec.get("code", "")),
                    "object_ids": [row["id"]],
                    "title": rec.get("title"),
                    "body": rec.get("message"),
                    "blame_field": rec.get("blame_field"),
                    "importance": rec.get("importance"),
                    "confidence": rec.get("confidence"),
                })
        return ad_sets, inline_recs

    async def extract_ads(
        self, client: httpx.AsyncClient, credentials: dict,
    ) -> Tuple[List[dict], List[dict]]:
        """Returns (ads, inline_recommendations)."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return [], []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/ads",
            _auth_headers(access_token),
            {"fields": _AD_FIELDS, "limit": "500"},
            "ads",
        )

        ads = []
        inline_recs = []
        for row in rows:
            creative = row.get("creative", {})
            ads.append({
                "external_id": row["id"],
                "campaign_external_id": row.get("campaign_id", ""),
                "ad_set_external_id": row.get("adset_id", ""),
                "name": row.get("name", ""),
                "status": row.get("status"),
                "effective_status": row.get("effective_status"),
                "creative_id": creative.get("id"),
                "creative_thumbnail_url": creative.get("thumbnail_url"),
                "creative_image_url": creative.get("image_url"),
                "creative_video_id": creative.get("video_id"),
                "creative_title": creative.get("title"),
                "creative_body": creative.get("body"),
                "creative_cta": creative.get("call_to_action_type"),
                "creative_link_url": None,  # Extracted from object_story_spec if needed
                "preview_shareable_link": row.get("preview_shareable_link"),
            })

            for rec in row.get("recommendations", []):
                inline_recs.append({
                    "source": "ad",
                    "recommendation_type": str(rec.get("code", "")),
                    "object_ids": [row["id"]],
                    "title": rec.get("title"),
                    "body": rec.get("message"),
                    "blame_field": rec.get("blame_field"),
                    "importance": rec.get("importance"),
                    "confidence": rec.get("confidence"),
                })
        return ads, inline_recs

    async def extract_account_recommendations(
        self, client: httpx.AsyncClient, credentials: dict,
    ) -> List[dict]:
        """Extract account-level performance recommendations."""
        ad_account_id = credentials.get("ad_account_id")
        access_token = credentials.get("access_token", "")
        if not ad_account_id:
            return []

        rows = await _paginate(
            client,
            f"{GRAPH_API_BASE}/act_{ad_account_id}/recommendations",
            _auth_headers(access_token),
            {"fields": _RECOMMENDATION_FIELDS, "limit": "100"},
            "account_recommendations",
        )

        recs = []
        for row in rows:
            rec_data = row.get("recommendation_data", row)
            content = rec_data.get("recommendation_content", {})
            recs.append({
                "source": "account",
                "recommendation_type": rec_data.get("type", "UNKNOWN"),
                "object_ids": rec_data.get("object_ids", []),
                "body": content.get("body"),
                "lift_estimate": content.get("lift_estimate"),
                "opportunity_score": content.get("opportunity_score_lift"),
                "url": rec_data.get("url"),
                "recommendation_signature": rec_data.get("recommendation_signature"),
            })
        return recs
```

- [ ] **Step 4: Run tests**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_meta_campaign_provider.py -x -q --tb=short"
```

Expected: All PASS

- [ ] **Step 5: Lint**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src/modules/analytics/infrastructure/providers/meta_campaign_provider.py --no-cache"
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/providers/meta_campaign_provider.py \
        backend/tests/modules/analytics/test_meta_campaign_provider.py
git commit -m "feat(analytics): add MetaCampaignProvider for campaign hierarchy extraction"
```

---

## Task 6: Campaign Sync Pipeline

**Files:**
- Create: `backend/src/modules/analytics/infrastructure/sync/campaign_sync_pipeline.py`
- Create: `backend/tests/modules/analytics/test_campaign_sync_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for CampaignSyncPipeline — orchestrates full campaign sync."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.modules.analytics.infrastructure.sync.campaign_sync_pipeline import (
    CampaignSyncPipeline,
)


class TestCampaignSyncPipeline:
    @pytest.mark.asyncio
    async def test_run_sync_calls_all_extractors_and_upserts(self):
        mock_provider = MagicMock()
        mock_provider.extract_campaigns = AsyncMock(return_value=[
            {"external_id": "c1", "name": "Camp 1"},
        ])
        mock_provider.extract_ad_sets = AsyncMock(return_value=(
            [{"external_id": "as1", "campaign_external_id": "c1", "name": "AdSet 1"}],
            [{"source": "ad_set", "recommendation_type": "1942008", "body": "tip"}],
        ))
        mock_provider.extract_ads = AsyncMock(return_value=(
            [{"external_id": "ad1", "campaign_external_id": "c1", "ad_set_external_id": "as1", "name": "Ad 1"}],
            [],
        ))
        mock_provider.extract_account_recommendations = AsyncMock(return_value=[
            {"source": "account", "recommendation_type": "CREATIVE_FATIGUE", "body": "Refresh creative"},
        ])

        mock_repo = MagicMock()
        mock_repo.upsert_campaigns = AsyncMock(return_value=1)
        mock_repo.upsert_ad_sets = AsyncMock(return_value=1)
        mock_repo.upsert_ads = AsyncMock(return_value=1)
        mock_repo.upsert_recommendations = AsyncMock(return_value=2)
        mock_repo.soft_delete_stale = AsyncMock(return_value=0)

        tenant_id = uuid4()
        creds = {"access_token": "tok", "ad_account_id": "123"}

        pipeline = CampaignSyncPipeline(
            provider=mock_provider,
            repository=mock_repo,
        )
        result = await pipeline.run_sync(tenant_id, creds)

        assert result["campaigns_synced"] == 1
        assert result["ad_sets_synced"] == 1
        assert result["ads_synced"] == 1
        assert result["recommendations_synced"] == 2
        mock_repo.upsert_campaigns.assert_called_once()
        mock_repo.upsert_ad_sets.assert_called_once()
        mock_repo.upsert_ads.assert_called_once()
```

- [ ] **Step 2: Write CampaignSyncPipeline**

```python
"""Campaign Sync Pipeline — orchestrates extraction and storage of campaign hierarchy.

Separate from ETLPipeline (metrics) to keep concerns isolated.
Runs as an independent job via ARQ.
"""

import logging
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
    MetaCampaignProvider,
)
from src.modules.analytics.infrastructure.repositories.campaign_repository import (
    CampaignRepository,
)

logger = logging.getLogger(__name__)


class CampaignSyncPipeline:
    """Orchestrates full campaign hierarchy sync."""

    def __init__(
        self,
        provider: MetaCampaignProvider,
        repository: CampaignRepository,
    ):
        self._provider = provider
        self._repo = repository

    async def run_sync(
        self, tenant_id: UUID, credentials: dict,
    ) -> dict:
        """Extract and upsert full campaign hierarchy + recommendations.

        Returns summary dict with counts.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Campaigns
            campaigns = await self._provider.extract_campaigns(client, credentials)
            campaigns_count = await self._repo.upsert_campaigns(tenant_id, campaigns)

            # 2. Ad Sets + inline recommendations
            ad_sets, adset_recs = await self._provider.extract_ad_sets(client, credentials)
            adsets_count = await self._repo.upsert_ad_sets(tenant_id, ad_sets)

            # 3. Ads + inline recommendations
            ads, ad_recs = await self._provider.extract_ads(client, credentials)
            ads_count = await self._repo.upsert_ads(tenant_id, ads)

            # 4. Account-level recommendations
            account_recs = await self._provider.extract_account_recommendations(
                client, credentials,
            )

            # 5. Merge all recommendations and upsert
            all_recs = adset_recs + ad_recs + account_recs
            recs_count = await self._repo.upsert_recommendations(tenant_id, all_recs)

            # 6. Soft-delete entities that disappeared from the API
            campaign_ids = [c["external_id"] for c in campaigns]
            adset_ids = [a["external_id"] for a in ad_sets]
            ad_ids = [a["external_id"] for a in ads]

            stale_camps = await self._repo.soft_delete_stale(
                tenant_id, "meta", "ad_campaigns", campaign_ids,
            )
            stale_adsets = await self._repo.soft_delete_stale(
                tenant_id, "meta", "ad_sets", adset_ids,
            )
            stale_ads = await self._repo.soft_delete_stale(
                tenant_id, "meta", "ads", ad_ids,
            )

        summary = {
            "campaigns_synced": campaigns_count,
            "ad_sets_synced": adsets_count,
            "ads_synced": ads_count,
            "recommendations_synced": recs_count,
            "stale_deleted": stale_camps + stale_adsets + stale_ads,
        }
        logger.info("campaign_sync_complete tenant=%s summary=%s", tenant_id, summary)
        return summary
```

- [ ] **Step 3: Run tests + lint**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/analytics/test_campaign_sync_pipeline.py -x -q --tb=short"
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src/modules/analytics/infrastructure/sync/ --no-cache"
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/infrastructure/sync/campaign_sync_pipeline.py \
        backend/tests/modules/analytics/test_campaign_sync_pipeline.py
git commit -m "feat(analytics): add CampaignSyncPipeline orchestration"
```

---

## Task 7: ARQ Worker Task + Scheduler Integration

**Files:**
- Modify: `backend/src/modules/analytics/workers/tasks.py`

- [ ] **Step 1: Read the existing tasks.py to understand the pattern**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && head -80 src/modules/analytics/workers/tasks.py"
```

- [ ] **Step 2: Add `run_campaign_sync` task**

Add a new async function `run_campaign_sync(ctx, tenant_id_str, provider)` following the same pattern as `run_tenant_extraction`. It should:
1. Get credentials via ConnectionPort
2. Create CampaignSyncPipeline
3. Call `pipeline.run_sync(tenant_id, credentials)`
4. Handle `ConnectionRevokedException` as permanent failure
5. Use Fibonacci backoff on transient errors

- [ ] **Step 3: Register the task in the ARQ worker class**

Add `run_campaign_sync` to the `functions` list of the ARQ worker settings.

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/analytics/workers/tasks.py
git commit -m "feat(analytics): add ARQ task for campaign sync"
```

---

## Task 8: API Endpoints + DTOs

**Files:**
- Create: `backend/src/modules/analytics/application/dto/campaign_dto.py`
- Create: `backend/src/modules/analytics/application/services/campaign_service.py`
- Create: `backend/src/modules/analytics/api/campaigns.py`
- Modify: `backend/src/main.py` (register router)

- [ ] **Step 1: Write Pydantic DTOs**

```python
"""DTOs for campaign management API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CampaignDTO(BaseModel):
    external_id: str
    name: str
    objective: Optional[str] = None
    status: Optional[str] = None
    effective_status: Optional[str] = None
    bid_strategy: Optional[str] = None
    daily_budget: Optional[int] = None
    lifetime_budget: Optional[int] = None
    budget_remaining: Optional[int] = None
    buying_type: Optional[str] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    ad_sets_count: int = 0
    ads_count: int = 0


class AdSetDTO(BaseModel):
    external_id: str
    campaign_external_id: str
    name: str
    status: Optional[str] = None
    effective_status: Optional[str] = None
    optimization_goal: Optional[str] = None
    targeting_summary: Optional[dict] = None
    learning_stage: Optional[str] = None
    daily_budget: Optional[int] = None
    ads_count: int = 0


class AdDTO(BaseModel):
    external_id: str
    name: str
    status: Optional[str] = None
    effective_status: Optional[str] = None
    creative_thumbnail_url: Optional[str] = None
    creative_title: Optional[str] = None
    creative_cta: Optional[str] = None
    preview_shareable_link: Optional[str] = None


class RecommendationDTO(BaseModel):
    recommendation_type: str
    source: str
    title: Optional[str] = None
    body: Optional[str] = None
    importance: Optional[str] = None
    lift_estimate: Optional[str] = None
    opportunity_score: Optional[float] = None
    url: Optional[str] = None
    object_ids: list = []


class CampaignOverviewDTO(BaseModel):
    campaigns: list[CampaignDTO]
    recommendations: list[RecommendationDTO]
    total_campaigns: int
    active_campaigns: int
    last_synced: Optional[datetime] = None
```

- [ ] **Step 2: Write CampaignService**

The service queries the repository and maps to DTOs. Add `get_overview()`, `get_campaign_detail()`, `trigger_sync()` methods.

- [ ] **Step 3: Write FastAPI routes**

```python
"""Campaign management API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Header

from src.modules.analytics.application.dto.campaign_dto import (
    CampaignOverviewDTO,
)
from src.modules.analytics.application.services.campaign_service import (
    CampaignService,
)

router = APIRouter(prefix="/api/v1/analytics/campaigns", tags=["campaigns"])


@router.get("", response_model=CampaignOverviewDTO)
async def get_campaigns_overview(
    x_tenant_id: UUID = Header(...),
    service: CampaignService = Depends(),
) -> CampaignOverviewDTO:
    return await service.get_overview(x_tenant_id)


@router.get("/{campaign_external_id}/adsets")
async def get_campaign_ad_sets(
    campaign_external_id: str,
    x_tenant_id: UUID = Header(...),
    service: CampaignService = Depends(),
):
    return await service.get_ad_sets(x_tenant_id, campaign_external_id)


@router.get("/adsets/{ad_set_external_id}/ads")
async def get_ad_set_ads(
    ad_set_external_id: str,
    x_tenant_id: UUID = Header(...),
    service: CampaignService = Depends(),
):
    return await service.get_ads(x_tenant_id, ad_set_external_id)


@router.post("/sync")
async def trigger_campaign_sync(
    x_tenant_id: UUID = Header(...),
    service: CampaignService = Depends(),
):
    return await service.trigger_sync(x_tenant_id)
```

- [ ] **Step 4: Register router in main.py**

- [ ] **Step 5: Lint + commit**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src/modules/analytics/api/campaigns.py src/modules/analytics/application/ --no-cache"
git add backend/src/modules/analytics/application/dto/campaign_dto.py \
        backend/src/modules/analytics/application/services/campaign_service.py \
        backend/src/modules/analytics/api/campaigns.py \
        backend/src/main.py
git commit -m "feat(analytics): add campaign management API endpoints"
```

---

## Task 9: Frontend Types + API Hooks

**Files:**
- Create: `frontend/src/features/growth-studio/types/campaigns.ts`
- Create: `frontend/src/features/growth-studio/api/campaigns-api.ts`

- [ ] **Step 1: Write TypeScript types**

Mirror the backend DTOs: `Campaign`, `AdSet`, `Ad`, `Recommendation`, `CampaignOverview`.

- [ ] **Step 2: Write React Query hooks**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchClient } from '@/lib/fetchClient';
import type { CampaignOverview } from '../types/campaigns';

export function useCampaignOverview() {
  return useQuery<CampaignOverview>({
    queryKey: ['campaigns', 'overview'],
    queryFn: () => fetchClient('/api/v1/analytics/campaigns'),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCampaignAdSets(campaignExternalId: string) {
  return useQuery({
    queryKey: ['campaigns', campaignExternalId, 'adsets'],
    queryFn: () => fetchClient(`/api/v1/analytics/campaigns/${campaignExternalId}/adsets`),
    enabled: !!campaignExternalId,
  });
}

export function useTriggerCampaignSync() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => fetchClient('/api/v1/analytics/campaigns/sync', { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaigns'] }),
  });
}
```

- [ ] **Step 3: tsc check + commit**

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
git add frontend/src/features/growth-studio/types/campaigns.ts \
        frontend/src/features/growth-studio/api/campaigns-api.ts
git commit -m "feat(growth-studio): add campaign management types and API hooks"
```

---

## Task 10: Frontend Campaign Panel

**Files:**
- Create: `frontend/src/features/growth-studio/components/campaign-panel/CampaignPanel.tsx`
- Create: `frontend/src/features/growth-studio/components/campaign-panel/CampaignCard.tsx`
- Create: `frontend/src/features/growth-studio/components/campaign-panel/AdSetDetail.tsx`
- Create: `frontend/src/features/growth-studio/components/campaign-panel/RecommendationsList.tsx`

This task requires a **UI design phase** (invoke `ux-disruptivo` skill). The components should:

- **CampaignPanel**: Tabbed view integrated into Growth Studio. Tab "Campañas" alongside "Atracción", etc.
- **CampaignCard**: Card per campaign showing name, objective badge, status dot, budget bar (remaining/total), and expandable ad sets.
- **AdSetDetail**: Shows targeting summary (age range, gender, location, interests), learning phase badge, optimization goal.
- **RecommendationsList**: Feed of Meta recommendations sorted by opportunity_score. Each card shows type icon, body, lift estimate, and "Ver en Ads Manager" link.

- [ ] **Step 1: Design the UI with ux-disruptivo**

Invoke `/ux-disruptivo` with the campaign panel spec to get a UI-SPEC.md before coding.

- [ ] **Step 2: Implement CampaignPanel.tsx**

Server Component shell that renders the tab and delegates to client components.

- [ ] **Step 3: Implement CampaignCard.tsx**

Client component with collapsible ad sets. Uses `useCampaignAdSets()` on expand.

- [ ] **Step 4: Implement RecommendationsList.tsx**

Client component rendering the recommendation feed with importance badges.

- [ ] **Step 5: tsc check + lint + commit**

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
docker exec -t visionarias_client_dev npx next lint
git add frontend/src/features/growth-studio/components/campaign-panel/
git commit -m "feat(growth-studio): add campaign management panel UI"
```

---

## Task 11: Integration Testing & Full CI

- [ ] **Step 1: Run full backend CI**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache"
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```

- [ ] **Step 2: Run full frontend CI**

```bash
docker exec -t visionarias_client_dev npx tsc --noEmit
docker exec -t visionarias_client_dev npx next lint
```

- [ ] **Step 3: Test migration on cloned DB**

```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp head'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

- [ ] **Step 4: Final commit if any fixes needed**

---

## Rate Limiting Budget

| Extractor | API Calls | Points | Notes |
|---|---|---|---|
| Campaigns | 1-2 (paginated) | 1-2 | ~500 campaigns/page |
| Ad Sets | 1-5 (paginated) | 1-5 | ~500 ad sets/page |
| Ads | 2-10 (paginated) | 2-10 | ~500 ads/page, includes creative expand |
| Recommendations | 1-2 | 1-2 | ~100/page |
| **Total per sync** | **~5-19** | **~5-19** | vs limit of 300+40×ads/hr |

Safe to run hourly or on-demand without throttling concerns.
