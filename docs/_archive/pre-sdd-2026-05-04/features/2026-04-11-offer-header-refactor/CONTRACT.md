# CONTRACT: Offer Studio Header + Lifecycle Refactor

**Date:** 2026-04-11
**Source of truth for:** backend implementers + frontend implementers
**Sibling docs:** `REQUIREMENTS.md` (what + why), `UI-SPEC.md` (visual spec)

This document is the single source of truth for types, DTOs, endpoints, and
cross-module boundaries. Nothing outside this file is authoritative.

---

## 0. Scope & ground rules

- **Module owner:** `offer` (new tables + endpoints live here).
- **Cross-module reads:** `advertising` (campaign aggregation) via a new
  `AdvertisingReadPort` in `shared/links/ports/advertising.py`.
- **Legacy table name:** the `Offer` aggregate persists into the `products`
  table (legacy). New child tables use the prefix **`offer_`** since they
  are new and the rename of `products → offers` is a separate concern.
- **Tenant isolation:** every column `tenant_id UUID NOT NULL` + every query
  filtered by `tenant_id`.
- **Soft delete:** every table carries `deleted_at TIMESTAMPTZ NULL`. Hard
  delete is forbidden.
- **Response model mandate:** every endpoint declares `response_model=` per
  `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md`.
- **Money:** any monetary field is paired with `currency: str | None` per
  `.claude/rules/currency-handling.md`.
- **Migrations:** idempotent raw SQL with `IF NOT EXISTS` per
  `.claude/rules/backend-migrations.md`.

---

## 1. Domain layer (pure Python — no framework imports)

### 1.1 Enums (new)

Location: `backend/src/modules/offer/domain/enums.py` (extend existing file).

```python
class OfferLifecycleStatus(str, Enum):
    """Writable lifecycle status as exposed by the header switcher.

    Subset of the existing OfferStatus enum that the UI can mutate.
    WAITLIST / SOLD_OUT remain in OfferStatus but are out of scope here.
    """
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"         # NEW — must be added to the DB enum too
    ARCHIVED = "archived"


class AssetType(str, Enum):
    FLYER = "flyer"
    VIDEO = "video"
    CAROUSEL = "carousel"
    DOCUMENT = "document"
    IMAGE = "image"


class AssetSource(str, Enum):
    AI = "ai"
    EXTERNAL = "external"     # uploaded by user


class AssetStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"  # async gen/upload in flight
    READY = "ready"
    ERROR = "error"


class KnowledgeSourceType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"
    VIDEO = "video"            # uploaded video file
    URL_YOUTUBE = "url_youtube"
    URL_ARTICLE = "url_article"
    URL_GOOGLE_DOC = "url_google_doc"


class KnowledgeSourceStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


class LandingJobStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
```

**DB enum note:** `PAUSED` must be added to the existing Postgres `offerstatus`
enum type if it exists as a native enum, or is already a free-text column (the
current `ProductModel.status` is `String`, so a check constraint is enough —
see migration §2).

### 1.2 Value objects

Location: `backend/src/modules/offer/domain/lifecycle.py` (NEW).

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.offer.domain.enums import OfferLifecycleStatus


@dataclass(frozen=True)
class OfferLifecycleTransition:
    offer_id: UUID
    tenant_id: UUID
    from_status: OfferLifecycleStatus
    to_status: OfferLifecycleStatus
    occurred_at: datetime
    actor_user_id: UUID | None
    reason: str | None = None

    def is_archival(self) -> bool:
        return self.to_status is OfferLifecycleStatus.ARCHIVED


LIFECYCLE_TRANSITIONS: dict[OfferLifecycleStatus, set[OfferLifecycleStatus]] = {
    OfferLifecycleStatus.DRAFT: {
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.ACTIVE: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.PAUSED,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.PAUSED: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    # ARCHIVED is terminal from this endpoint — must use POST /restore
    OfferLifecycleStatus.ARCHIVED: set(),
}


class InvalidLifecycleTransitionError(ValueError):
    def __init__(
        self,
        from_status: OfferLifecycleStatus,
        to_status: OfferLifecycleStatus,
    ) -> None:
        super().__init__(
            f"Invalid transition {from_status.value} → {to_status.value}. "
            f"Allowed targets: "
            f"{sorted(s.value for s in LIFECYCLE_TRANSITIONS[from_status])}"
        )
        self.from_status = from_status
        self.to_status = to_status
```

### 1.3 Entities (domain — pure Pydantic `BaseEntity`)

Location: `backend/src/modules/offer/domain/assets.py` (NEW).

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType
from src.shared.domain.base_entity import BaseEntity


class OfferAsset(BaseEntity):
    id: UUID
    tenant_id: UUID
    offer_id: UUID
    name: str
    type: AssetType
    source: AssetSource
    status: AssetStatus = AssetStatus.DRAFT

    # File references (nullable until processing completes)
    file_url: str | None = None
    thumbnail_url: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None

    # Type-specific metadata (duration_seconds, slide_count, page_count, etc.)
    metadata: dict[str, Any] = {}

    # Source/provenance
    prompt_params: dict[str, Any] | None = None  # populated when source=ai
    editable_in_puck: bool = False                # true only when source=ai

    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

Location: `backend/src/modules/offer/domain/knowledge_source.py` (NEW).

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from src.shared.domain.base_entity import BaseEntity


class KnowledgeSource(BaseEntity):
    id: UUID
    tenant_id: UUID
    offer_id: UUID
    name: str
    type: KnowledgeSourceType
    status: KnowledgeSourceStatus = KnowledgeSourceStatus.QUEUED

    # Origin (one of url / file)
    source_url: str | None = None          # for URL-type sources
    file_url: str | None = None            # for uploaded files
    mime_type: str | None = None
    size_bytes: int | None = None

    # Indexing stats
    indexed_chunk_count: int = 0
    last_indexed_at: datetime | None = None
    qdrant_collection: str | None = None   # RAG collection handle
    qdrant_point_ids: list[str] = []

    # Content metadata (page_count, duration_seconds, transcript_lang, etc.)
    metadata: dict[str, Any] = {}

    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
```

### 1.4 Offer additions (extend existing `domain/offer.py`)

Existing `Offer` already has `status: OfferStatus`. Add these optional fields
to expose server-computed state:

```python
class Offer(BaseEntity):
    # ... existing fields ...

    # NEW — server-computed, read-only from outside the service layer.
    # Populated by OfferService.compute_completion(offer).
    completion_percentage: float | None = None   # 0.0 .. 100.0

    # NEW — mirrored from LandingPageModel for fast shell rendering.
    landing_generated_at: datetime | None = None
    landing_is_outdated: bool | None = None
```

### 1.5 Domain events

Location: `backend/src/modules/offer/domain/events.py` (NEW).

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from src.modules.offer.domain.enums import (
    AssetType,
    KnowledgeSourceStatus,
    OfferLifecycleStatus,
)
from src.shared.domain.base_entity import BaseEntity


class DomainEvent(BaseEntity):
    event_id: UUID
    tenant_id: UUID
    occurred_at: datetime


class OfferStatusChanged(DomainEvent):
    offer_id: UUID
    from_status: OfferLifecycleStatus
    to_status: OfferLifecycleStatus
    actor_user_id: UUID | None


class OfferAssetCreated(DomainEvent):
    offer_id: UUID
    asset_id: UUID
    type: AssetType
    source: str  # AssetSource.value


class OfferAssetDeleted(DomainEvent):
    offer_id: UUID
    asset_id: UUID


class KnowledgeSourceCreated(DomainEvent):
    offer_id: UUID
    source_id: UUID
    type: str


class KnowledgeSourceIndexed(DomainEvent):
    offer_id: UUID
    source_id: UUID
    chunk_count: int
    status: KnowledgeSourceStatus


class KnowledgeSourceDeleted(DomainEvent):
    offer_id: UUID
    source_id: UUID


class LandingGenerationRequested(DomainEvent):
    offer_id: UUID
    snapshot_version: str
    job_id: UUID


class LandingRegenerationRequested(DomainEvent):
    offer_id: UUID
    previous_snapshot_version: str | None
    snapshot_version: str
    job_id: UUID


class LandingPublished(DomainEvent):
    offer_id: UUID
    landing_page_id: UUID


class LandingUnpublished(DomainEvent):
    offer_id: UUID
    landing_page_id: UUID
    reason: str  # "manual" | "offer_archived"
```

### 1.6 Repository / service ports

Location: `backend/src/modules/offer/application/ports.py` (extend existing).

```python
from abc import ABC, abstractmethod
from typing import BinaryIO, Sequence
from uuid import UUID

from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import (
    AssetSource,
    AssetType,
    KnowledgeSourceType,
    OfferLifecycleStatus,
)
from src.modules.offer.domain.knowledge_source import KnowledgeSource


class IOfferAssetRepository(ABC):
    @abstractmethod
    async def create(self, asset: OfferAsset) -> OfferAsset: ...
    @abstractmethod
    async def get_by_id(
        self, tenant_id: UUID, offer_id: UUID, asset_id: UUID
    ) -> OfferAsset | None: ...
    @abstractmethod
    async def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type: AssetType | None = None,
        source: AssetSource | None = None,
        sort: str = "created_desc",
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[Sequence[OfferAsset], int]: ...  # (items, total_count)
    @abstractmethod
    async def update(self, asset: OfferAsset) -> OfferAsset: ...
    @abstractmethod
    async def soft_delete(
        self, tenant_id: UUID, offer_id: UUID, asset_id: UUID
    ) -> None: ...
    @abstractmethod
    async def count_by_offer(
        self, tenant_id: UUID, offer_id: UUID
    ) -> int: ...


class IKnowledgeSourceRepository(ABC):
    @abstractmethod
    async def create(self, source: KnowledgeSource) -> KnowledgeSource: ...
    @abstractmethod
    async def get_by_id(
        self, tenant_id: UUID, offer_id: UUID, source_id: UUID
    ) -> KnowledgeSource | None: ...
    @abstractmethod
    async def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type: KnowledgeSourceType | None = None,
    ) -> Sequence[KnowledgeSource]: ...
    @abstractmethod
    async def update(self, source: KnowledgeSource) -> KnowledgeSource: ...
    @abstractmethod
    async def soft_delete(
        self, tenant_id: UUID, offer_id: UUID, source_id: UUID
    ) -> None: ...
    @abstractmethod
    async def count_indexed_by_offer(
        self, tenant_id: UUID, offer_id: UUID
    ) -> int: ...


class IFileStoragePort(ABC):
    """Abstraction over R2/S3 uploads. Implementation lives in
    infrastructure/storage/."""
    @abstractmethod
    async def upload(
        self,
        tenant_id: UUID,
        folder: str,
        filename: str,
        content: BinaryIO,
        mime_type: str,
    ) -> tuple[str, int]: ...  # (public_url, size_bytes)

    @abstractmethod
    async def get_download_stream(self, file_url: str) -> BinaryIO: ...

    @abstractmethod
    async def delete(self, file_url: str) -> None: ...


class IRAGIndexerPort(ABC):
    """Abstraction over the Qdrant pipeline used to index knowledge sources."""
    @abstractmethod
    async def index_source(
        self, source: KnowledgeSource, raw_bytes: bytes | None = None
    ) -> tuple[list[str], int]: ...  # (qdrant_point_ids, chunk_count)

    @abstractmethod
    async def reindex_source(
        self, source: KnowledgeSource
    ) -> tuple[list[str], int]: ...

    @abstractmethod
    async def delete_source(self, source: KnowledgeSource) -> None: ...


class IOfferLifecycleService(ABC):
    @abstractmethod
    async def change_status(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        new_status: OfferLifecycleStatus,
        actor_user_id: UUID | None,
        reason: str | None = None,
    ) -> "Offer": ...  # noqa: F821 — forward ref


class IOfferCompletionService(ABC):
    @abstractmethod
    def compute(self, offer: "Offer") -> float: ...  # noqa: F821
```

### 1.7 Cross-module port (shared/links)

Location: `backend/src/shared/links/ports/advertising.py` (NEW directory if
absent).

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CampaignRowDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    channel: str            # "meta" | "google" | "tiktok" | ...
    status: str             # "active" | "paused" | "ended"
    spend: float
    leads: int
    cpl: float | None
    currency: str | None    # per-row currency (source of truth)


class CampaignAggregateKPIsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    active_count: int
    spend_7d: float
    leads_7d: int
    avg_cpl_7d: float | None
    currency: str | None    # tenant or source currency (resolution below)


class OfferCampaignsViewDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kpis: CampaignAggregateKPIsDTO
    campaigns: list[CampaignRowDTO]


class AdvertisingReadPort(ABC):
    """Read-only port so `offer` can aggregate campaigns without importing
    any advertising internals. Implementation lives in
    `advertising/application/services/offer_campaigns_read_adapter.py` and is
    wired via FastAPI dependency in `shared/links/ports/__init__.py`.
    """
    @abstractmethod
    async def get_campaigns_for_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        period_start: date,
        period_end: date,
        status: Literal["all", "active", "paused", "ended"] = "all",
        channel: str | None = None,
    ) -> OfferCampaignsViewDTO: ...
```

Rationale: `offer` MUST NOT import from `advertising`. The concrete adapter
is owned by `advertising` and registered as the `AdvertisingReadPort` binding
at startup. The `offer` router resolves the port via `Depends`.

---

## 2. SQLAlchemy 2.0 models (infrastructure)

All new models use the 2.0 `mapped_column()` syntax even though the existing
`ProductModel` still uses `Column()` (legacy — left untouched).

### 2.1 `offer_assets` table

Location: `backend/src/modules/offer/infrastructure/models/offer_asset_model.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime, Boolean

from src.shared.domain.base_entity import Base


class OfferAssetModel(Base):
    __tablename__ = "offer_assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)   # AssetType
    source: Mapped[str] = mapped_column(String, nullable=False) # AssetSource
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="draft", server_default="draft"
    )

    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
    prompt_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    editable_in_puck: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_offer_assets_tenant_offer", "tenant_id", "offer_id"),
        Index("ix_offer_assets_deleted_at", "deleted_at"),
    )
```

### 2.2 `offer_knowledge_sources` table

Location: `backend/src/modules/offer/infrastructure/models/knowledge_source_model.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from src.shared.domain.base_entity import Base


class KnowledgeSourceModel(Base):
    __tablename__ = "offer_knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="queued", server_default="queued"
    )

    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    indexed_chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    qdrant_collection: Mapped[str | None] = mapped_column(String, nullable=True)
    qdrant_point_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list, server_default="{}"
    )

    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "ix_offer_knowledge_sources_tenant_offer",
            "tenant_id",
            "offer_id",
        ),
        Index("ix_offer_knowledge_sources_deleted_at", "deleted_at"),
    )
```

### 2.3 `products` table — columns to ADD

(Existing table; these columns are additive.)

```sql
ALTER TABLE products ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
ALTER TABLE products ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMPTZ;
ALTER TABLE products ADD COLUMN IF NOT EXISTS completion_percentage FLOAT;
-- completion_percentage is recomputed on every write. Nullable because legacy
-- rows won't have it until first mutation.
```

A `CHECK` constraint on `status` enforces the writable subset:

```sql
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_status_check;
ALTER TABLE products ADD CONSTRAINT products_status_check
  CHECK (status IN (
    'draft','active','paused','archived','waitlist','sold_out'
  ));
```

### 2.4 `landing_pages` table — columns to ADD

Per REQUIREMENTS §Landing page rules. `is_outdated` is NOT stored — it's
computed at read time as `landing.generated_at < offer.updated_at`.

```sql
ALTER TABLE landing_pages
  ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ;
ALTER TABLE landing_pages
  ADD COLUMN IF NOT EXISTS offer_snapshot_version VARCHAR;
ALTER TABLE landing_pages
  ADD COLUMN IF NOT EXISTS generation_job_id UUID;
ALTER TABLE landing_pages
  ADD COLUMN IF NOT EXISTS generation_job_status VARCHAR;
ALTER TABLE landing_pages
  ADD COLUMN IF NOT EXISTS generation_error TEXT;
```

The `landing` module's SQLAlchemy model must be extended in a follow-up PR;
reads from `offer` use the DTOs in §4 below (not direct SA relationships) to
respect module boundaries.

---

## 3. Alembic migration (idempotent)

**File:** `backend/alembic/versions/2026_04_11_offer_header_refactor.py`

```python
"""offer header refactor — assets, knowledge sources, lifecycle, landing snapshots

Revision ID: 2026_04_11_offer_header_refactor
Revises: <last_head>
Create Date: 2026-04-11
"""
from typing import Sequence, Union
from alembic import op

revision: str = "2026_04_11_offer_header_refactor"
down_revision: Union[str, None] = None  # FILL IN from `alembic heads`
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- offer_assets -------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS offer_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'draft',
            file_url VARCHAR,
            thumbnail_url VARCHAR,
            mime_type VARCHAR,
            size_bytes INTEGER,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            prompt_params JSONB,
            editable_in_puck BOOLEAN NOT NULL DEFAULT false,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_offer_assets_tenant_id
            ON offer_assets (tenant_id);
        CREATE INDEX IF NOT EXISTS ix_offer_assets_offer_id
            ON offer_assets (offer_id);
        CREATE INDEX IF NOT EXISTS ix_offer_assets_tenant_offer
            ON offer_assets (tenant_id, offer_id);
        CREATE INDEX IF NOT EXISTS ix_offer_assets_deleted_at
            ON offer_assets (deleted_at);
    """)

    # --- offer_knowledge_sources --------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS offer_knowledge_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'queued',
            source_url VARCHAR,
            file_url VARCHAR,
            mime_type VARCHAR,
            size_bytes INTEGER,
            indexed_chunk_count INTEGER NOT NULL DEFAULT 0,
            last_indexed_at TIMESTAMPTZ,
            qdrant_collection VARCHAR,
            qdrant_point_ids VARCHAR[] NOT NULL DEFAULT '{}',
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_tenant_id
            ON offer_knowledge_sources (tenant_id);
        CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_offer_id
            ON offer_knowledge_sources (offer_id);
        CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_tenant_offer
            ON offer_knowledge_sources (tenant_id, offer_id);
        CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_deleted_at
            ON offer_knowledge_sources (deleted_at);
    """)

    # --- products: lifecycle + completion -----------------------------------
    op.execute("""
        ALTER TABLE products ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;
        ALTER TABLE products ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMPTZ;
        ALTER TABLE products ADD COLUMN IF NOT EXISTS completion_percentage FLOAT;
    """)
    op.execute("""
        ALTER TABLE products DROP CONSTRAINT IF EXISTS products_status_check;
        ALTER TABLE products ADD CONSTRAINT products_status_check
            CHECK (status IN (
                'draft','active','paused','archived','waitlist','sold_out'
            ));
    """)

    # --- landing_pages: generation snapshot ---------------------------------
    op.execute("""
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ;
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS offer_snapshot_version VARCHAR;
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_job_id UUID;
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_job_status VARCHAR;
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_error TEXT;
    """)


def downgrade() -> None:
    # Reference-only downgrade (not required to work per project rules).
    # --
    # DROP TABLE IF EXISTS offer_knowledge_sources;
    # DROP TABLE IF EXISTS offer_assets;
    # ALTER TABLE products DROP CONSTRAINT IF EXISTS products_status_check;
    # ALTER TABLE products DROP COLUMN IF EXISTS paused_at;
    # ALTER TABLE products DROP COLUMN IF EXISTS status_changed_at;
    # ALTER TABLE products DROP COLUMN IF EXISTS completion_percentage;
    # ALTER TABLE landing_pages DROP COLUMN IF EXISTS generated_at;
    # ALTER TABLE landing_pages DROP COLUMN IF EXISTS offer_snapshot_version;
    # ALTER TABLE landing_pages DROP COLUMN IF EXISTS generation_job_id;
    # ALTER TABLE landing_pages DROP COLUMN IF EXISTS generation_job_status;
    # ALTER TABLE landing_pages DROP COLUMN IF EXISTS generation_error;
    pass
```

---

## 4. Pydantic v2 DTOs

All DTOs live under `backend/src/modules/offer/api/dto/`. New files:

- `lifecycle_dtos.py`
- `counts_dtos.py`
- `landing_dtos.py`
- `asset_dtos.py`
- `knowledge_dtos.py`
- `campaigns_dtos.py`

Every DTO uses `model_config = ConfigDict(from_attributes=True)`.

### 4.1 Lifecycle DTOs — `lifecycle_dtos.py`

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.enums import OfferLifecycleStatus


class ChangeOfferStatusRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: OfferLifecycleStatus
    reason: str | None = None


class OfferStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    offer_id: UUID
    status: OfferLifecycleStatus
    previous_status: OfferLifecycleStatus
    status_changed_at: datetime
    completion_percentage: float
    landing_auto_unpublished: bool   # true only on → ARCHIVED
```

### 4.2 Offer counts DTO — `counts_dtos.py`

```python
from pydantic import BaseModel, ConfigDict


class OfferCountsResponse(BaseModel):
    """Used by the persistent shell to render tab badges."""
    model_config = ConfigDict(from_attributes=True)
    assets: int
    campaigns: int
    knowledge: int
    active_campaigns: int         # subset used in header "Activas" pill
```

### 4.3 Landing DTOs — `landing_dtos.py`

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.enums import LandingJobStatus


class LandingStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    offer_id: UUID
    landing_page_id: UUID | None
    is_generated: bool
    is_published: bool
    is_outdated: bool
    generated_at: datetime | None
    offer_snapshot_version: str | None
    offer_updated_at: datetime
    job_id: UUID | None
    job_status: LandingJobStatus
    landing_url: str | None         # public URL when is_published
    editor_url: str | None          # /{tenantId}/editor/{offerId}
    completion_percentage: float    # server-computed, used by gate


class LandingGenerateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    job_id: UUID
    job_status: LandingJobStatus
    offer_snapshot_version: str
    queued_at: datetime


class LandingPublishResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    landing_page_id: UUID
    is_published: bool
    landing_url: str
    published_at: datetime


class LandingUnpublishResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    landing_page_id: UUID
    is_published: bool
    unpublished_at: datetime
```

### 4.4 Asset DTOs — `asset_dtos.py`

```python
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType


AssetSortKey = Literal["created_desc", "created_asc", "name_asc", "name_desc"]


class AssetListQuery(BaseModel):
    """Parsed from query params via FastAPI `Depends()`."""
    model_config = ConfigDict(from_attributes=True)
    search: str | None = None
    type: AssetType | None = None
    source: AssetSource | None = None
    sort: AssetSortKey = "created_desc"
    limit: int = Field(default=24, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    offer_id: UUID
    name: str
    type: AssetType
    source: AssetSource
    status: AssetStatus
    file_url: str | None
    thumbnail_url: str | None
    mime_type: str | None
    size_bytes: int | None
    metadata: dict[str, Any]
    editable_in_puck: bool
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None


class AssetListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[AssetResponse]
    total: int
    limit: int
    offset: int


class AssetGenerateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: AssetType
    name: str | None = None
    prompt_params: dict[str, Any] = Field(default_factory=dict)


class AssetUpdateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = None
    metadata: dict[str, Any] | None = None


# Upload is multipart — no request body DTO. Validation happens in the
# route via `UploadFile` + size/mime checks in the service.
```

### 4.5 Knowledge DTOs — `knowledge_dtos.py`

```python
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)


class KnowledgeListQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    search: str | None = None
    type: KnowledgeSourceType | None = None


class KnowledgeSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    offer_id: UUID
    name: str
    type: KnowledgeSourceType
    status: KnowledgeSourceStatus
    source_url: str | None
    file_url: str | None
    mime_type: str | None
    size_bytes: int | None
    indexed_chunk_count: int
    last_indexed_at: datetime | None
    metadata: dict[str, Any]
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None


class KnowledgeListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[KnowledgeSourceResponse]
    total: int


class KnowledgeUrlIngestRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    url: HttpUrl
    name: str | None = None  # defaults to page title after fetch
```

### 4.6 Campaigns DTOs — `campaigns_dtos.py`

These are thin aggregates. They mirror the shared port DTOs (§1.7) so the
`offer` router can forward them with no re-mapping beyond filtering.

```python
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


CampaignStatusFilter = Literal["all", "active", "paused", "ended"]


class OfferCampaignsQuery(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: CampaignStatusFilter = "all"
    channel: str | None = None  # "meta" | "google" | "tiktok"
    period_start: date | None = None
    period_end: date | None = None


class OfferCampaignRowDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    channel: str
    status: str
    spend: float
    leads: int
    cpl: float | None
    currency: str | None


class OfferCampaignsKPIsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    active_count: int
    spend_7d: float
    leads_7d: int
    avg_cpl_7d: float | None
    currency: str | None


class OfferCampaignsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    offer_id: UUID
    kpis: OfferCampaignsKPIsDTO
    campaigns: list[OfferCampaignRowDTO]
```

**PII audit:** none of the fields above trigger the PII patterns (email,
phone, address, ssn, dob, ip, financial account). Safe to expose.

---

## 5. API endpoints

All endpoints are mounted under `/api/v1/offer/offers/{offer_id}/…`. Every
handler resolves `tenant_id = user.tenant_id` and filters every query by it.

Auth dependency (universal):

```python
user: User = Depends(get_current_user)
```

Status codes: `200 OK` on successful GET/POST/PATCH, `204 No Content` on
DELETE and `POST /.../unpublish` when there's no body, `404` when the entity
is not found under the user's tenant, `409` for invalid lifecycle transition
or publish-without-generation, `422` for Pydantic validation errors, `400`
for business-rule violations (e.g. generate with completion < 90).

### 5.1 Lifecycle + shell

| # | Method | Path | Req DTO | Resp DTO | Codes |
|---|---|---|---|---|---|
| 1 | POST | `/offers/{id}/status` | `ChangeOfferStatusRequest` | `OfferStatusResponse` | 200, 404, 409 |
| 2 | GET | `/offers/{id}/counts` | — | `OfferCountsResponse` | 200, 404 |

**Endpoint 1 — POST `/offers/{id}/status`**

- Resolves current `status`, validates against `LIFECYCLE_TRANSITIONS`.
- Invalid → `409 Conflict` with body `{detail: "invalid_transition", from, to}`.
- On `→ ARCHIVED`: also calls landing service to unpublish (if published),
  sets `landing_auto_unpublished=true` in response.
- Emits `OfferStatusChanged`.

**Endpoint 2 — GET `/offers/{id}/counts`**

- Returns counts for the shell's tab badges. MUST be cheap (three `COUNT(*)`
  queries + one filtered). No N+1.

### 5.2 Landing

| # | Method | Path | Req DTO | Resp DTO | Codes |
|---|---|---|---|---|---|
| 3 | GET | `/offers/{id}/landing/status` | — | `LandingStatusResponse` | 200, 404 |
| 4 | POST | `/offers/{id}/landing/generate` | — | `LandingGenerateResponse` | 202, 400, 404 |
| 5 | POST | `/offers/{id}/landing/regenerate` | — | `LandingGenerateResponse` | 202, 400, 404 |
| 6 | POST | `/offers/{id}/landing/publish` | — | `LandingPublishResponse` | 200, 404, 409 |
| 7 | POST | `/offers/{id}/landing/unpublish` | — | `LandingUnpublishResponse` | 200, 404 |

- `generate`/`regenerate` return `202 Accepted`. `job_status` begins
  `QUEUED`. Pipeline is stubbed for now (per REQUIREMENTS §Out of scope).
- `generate` requires `completion_percentage ≥ 90` → otherwise `400 Bad
  Request` with `{detail: "offer_incomplete", completion_percentage: <n>}`.
- `publish` requires `is_generated=true` → otherwise `409 Conflict`.
- All handlers compute `is_outdated = landing.generated_at < offer.updated_at`.

### 5.3 Assets

| # | Method | Path | Req | Resp | Codes |
|---|---|---|---|---|---|
| 8 | GET | `/offers/{id}/assets` | query → `AssetListQuery` | `AssetListResponse` | 200, 404 |
| 9 | POST | `/offers/{id}/assets/upload` | multipart file | `AssetResponse` | 201, 400, 404, 413, 415 |
| 10 | POST | `/offers/{id}/assets/generate` | `AssetGenerateRequest` | `AssetResponse` | 202, 400, 404 |
| 11 | GET | `/offers/{id}/assets/{asset_id}` | — | `AssetResponse` | 200, 404 |
| 12 | PATCH | `/offers/{id}/assets/{asset_id}` | `AssetUpdateRequest` | `AssetResponse` | 200, 404, 422 |
| 13 | DELETE | `/offers/{id}/assets/{asset_id}` | — | — (204) | 204, 404 |
| 14 | GET | `/offers/{id}/assets/{asset_id}/download` | — | `StreamingResponse` (`application/octet-stream`) | 200, 404 |

- **Upload constraints:** `max_size=25 MB`, allowed MIME = `image/png`,
  `image/jpeg`, `image/webp`, `video/mp4`, `video/quicktime`,
  `application/pdf`, `application/zip`. Others → `415`. Over size → `413`.
- **Generate:** stub implementation returns an `AssetResponse` with
  `status=PROCESSING` and queues a placeholder job (implementation deferred).
- **Download:** route returns `StreamingResponse` so there's no Pydantic
  model to declare; use FastAPI's `response_class=StreamingResponse` (exempt
  from the `response_model=` rule — allowlist the route in the fitness test
  if needed).
- **Delete:** soft delete only (`deleted_at=now()`). File stays in R2 until
  a janitor sweeps it (out of scope).

### 5.4 Knowledge sources

| # | Method | Path | Req | Resp | Codes |
|---|---|---|---|---|---|
| 15 | GET | `/offers/{id}/knowledge` | query → `KnowledgeListQuery` | `KnowledgeListResponse` | 200, 404 |
| 16 | POST | `/offers/{id}/knowledge/upload` | multipart file | `KnowledgeSourceResponse` | 202, 400, 404, 413, 415 |
| 17 | POST | `/offers/{id}/knowledge/url` | `KnowledgeUrlIngestRequest` | `KnowledgeSourceResponse` | 202, 400, 404 |
| 18 | DELETE | `/offers/{id}/knowledge/{source_id}` | — | — (204) | 204, 404 |
| 19 | POST | `/offers/{id}/knowledge/{source_id}/reindex` | — | `KnowledgeSourceResponse` | 202, 404, 409 |

- Upload MIME allowlist: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`, `text/markdown`, `video/mp4`. Max 50 MB.
- Delete removes points from Qdrant (via `IRAGIndexerPort.delete_source`)
  before marking `deleted_at`. On Qdrant failure → log + continue soft-delete.
- Reindex sets status back to `PROCESSING`, queues job. `409` if already
  in-flight.

### 5.5 Campaigns (cross-module read)

| # | Method | Path | Req | Resp | Codes |
|---|---|---|---|---|---|
| 20 | GET | `/offers/{id}/campaigns` | query → `OfferCampaignsQuery` | `OfferCampaignsResponse` | 200, 404 |

- Handler injects `AdvertisingReadPort` via `Depends`, calls
  `get_campaigns_for_offer()`, reshapes into `OfferCampaignsResponse`.
- If the offer has no associated campaigns → return empty lists + zeroed
  KPIs (not 404).

### 5.6 Reused existing endpoints (no change)

- `PATCH /offers/{id}/psychology` — extended to persist `objections` list
  (already covered by `OfferPsychologyUpdate.objections`).
- `PATCH /offers/{id}/{section}` — all partial-update endpoints remain and
  power the auto-save flow.
- `POST /offers/{id}/archive`, `POST /offers/{id}/restore` — existing
  archive flow is kept. The new `POST /offers/{id}/status` delegates to
  `archive_offer()` when the target is `ARCHIVED`, so there's a single write
  path.

---

## 6. TypeScript types

To be copied to `frontend/src/features/offer-studio/types/`. `camelCase`
keys are used; the backend uses `snake_case` → the frontend hooks either
alias via `fetchClient`'s normaliser or consume `snake_case` directly (the
repo currently uses `snake_case` in most DTOs, so **default to `snake_case`**
and only camelCase if a file already does so).

> **Convention for this feature:** `snake_case` to match existing offer
> feature types. Only the campaigns view uses camelCase because its backing
> advertising DTOs are camelCase already (`_CamelModel`). If the frontend
> prefers camelCase everywhere, a normaliser should be added in
> `features/offer-studio/api/` — not inside these types.

### 6.1 Enums

```ts
// features/offer-studio/types/enums.ts

export const OFFER_LIFECYCLE_STATUS = [
  "draft",
  "active",
  "paused",
  "archived",
] as const;
export type OfferLifecycleStatus = (typeof OFFER_LIFECYCLE_STATUS)[number];

export const ASSET_TYPE = [
  "flyer",
  "video",
  "carousel",
  "document",
  "image",
] as const;
export type AssetType = (typeof ASSET_TYPE)[number];

export const ASSET_SOURCE = ["ai", "external"] as const;
export type AssetSource = (typeof ASSET_SOURCE)[number];

export const ASSET_STATUS = [
  "draft",
  "processing",
  "ready",
  "error",
] as const;
export type AssetStatus = (typeof ASSET_STATUS)[number];

export const KNOWLEDGE_SOURCE_TYPE = [
  "pdf",
  "docx",
  "txt",
  "markdown",
  "video",
  "url_youtube",
  "url_article",
  "url_google_doc",
] as const;
export type KnowledgeSourceType = (typeof KNOWLEDGE_SOURCE_TYPE)[number];

export const KNOWLEDGE_SOURCE_STATUS = [
  "queued",
  "processing",
  "indexed",
  "error",
] as const;
export type KnowledgeSourceStatus = (typeof KNOWLEDGE_SOURCE_STATUS)[number];

export const LANDING_JOB_STATUS = [
  "idle",
  "queued",
  "running",
  "success",
  "error",
] as const;
export type LandingJobStatus = (typeof LANDING_JOB_STATUS)[number];
```

### 6.2 Lifecycle

```ts
// features/offer-studio/types/lifecycle.ts
import type { OfferLifecycleStatus } from "./enums";

export interface ChangeOfferStatusPayload {
  status: OfferLifecycleStatus;
  reason?: string;
}

export interface OfferStatusResponse {
  offer_id: string;
  status: OfferLifecycleStatus;
  previous_status: OfferLifecycleStatus;
  status_changed_at: string; // ISO 8601 UTC
  completion_percentage: number;
  landing_auto_unpublished: boolean;
}
```

### 6.3 Counts

```ts
// features/offer-studio/types/counts.ts
export interface OfferCountsResponse {
  assets: number;
  campaigns: number;
  knowledge: number;
  active_campaigns: number;
}
```

### 6.4 Landing

```ts
// features/offer-studio/types/landing-status.ts
import type { LandingJobStatus } from "./enums";

export interface LandingStatusResponse {
  offer_id: string;
  landing_page_id: string | null;
  is_generated: boolean;
  is_published: boolean;
  is_outdated: boolean;
  generated_at: string | null;
  offer_snapshot_version: string | null;
  offer_updated_at: string;
  job_id: string | null;
  job_status: LandingJobStatus;
  landing_url: string | null;
  editor_url: string | null;
  completion_percentage: number;
}

export interface LandingGenerateResponse {
  job_id: string;
  job_status: LandingJobStatus;
  offer_snapshot_version: string;
  queued_at: string;
}

export interface LandingPublishResponse {
  landing_page_id: string;
  is_published: boolean;
  landing_url: string;
  published_at: string;
}

export interface LandingUnpublishResponse {
  landing_page_id: string;
  is_published: boolean;
  unpublished_at: string;
}
```

### 6.5 Assets

```ts
// features/offer-studio/types/assets.ts
import type {
  AssetSource,
  AssetStatus,
  AssetType,
} from "./enums";

export type AssetSortKey =
  | "created_desc"
  | "created_asc"
  | "name_asc"
  | "name_desc";

export interface AssetListQuery {
  search?: string;
  type?: AssetType;
  source?: AssetSource;
  sort?: AssetSortKey;
  limit?: number;
  offset?: number;
}

export interface AssetResponse {
  id: string;
  offer_id: string;
  name: string;
  type: AssetType;
  source: AssetSource;
  status: AssetStatus;
  file_url: string | null;
  thumbnail_url: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  metadata: Record<string, unknown>;
  editable_in_puck: boolean;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AssetListResponse {
  items: AssetResponse[];
  total: number;
  limit: number;
  offset: number;
}

export interface AssetGeneratePayload {
  type: AssetType;
  name?: string;
  prompt_params?: Record<string, unknown>;
}

export interface AssetUpdatePayload {
  name?: string;
  metadata?: Record<string, unknown>;
}
```

### 6.6 Knowledge

```ts
// features/offer-studio/types/knowledge.ts
import type {
  KnowledgeSourceStatus,
  KnowledgeSourceType,
} from "./enums";

export interface KnowledgeListQuery {
  search?: string;
  type?: KnowledgeSourceType;
}

export interface KnowledgeSourceResponse {
  id: string;
  offer_id: string;
  name: string;
  type: KnowledgeSourceType;
  status: KnowledgeSourceStatus;
  source_url: string | null;
  file_url: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  indexed_chunk_count: number;
  last_indexed_at: string | null;
  metadata: Record<string, unknown>;
  error_message: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface KnowledgeListResponse {
  items: KnowledgeSourceResponse[];
  total: number;
}

export interface KnowledgeUrlIngestPayload {
  url: string;
  name?: string;
}
```

### 6.7 Campaigns

```ts
// features/offer-studio/types/campaigns.ts
export type CampaignStatusFilter = "all" | "active" | "paused" | "ended";

export interface OfferCampaignsQuery {
  status?: CampaignStatusFilter;
  channel?: "meta" | "google" | "tiktok" | string;
  period_start?: string; // YYYY-MM-DD
  period_end?: string;
}

export interface OfferCampaignRow {
  id: string;
  name: string;
  channel: string;
  status: string;
  spend: number;
  leads: number;
  cpl: number | null;
  currency: string | null;
}

export interface OfferCampaignsKPIs {
  active_count: number;
  spend_7d: number;
  leads_7d: number;
  avg_cpl_7d: number | null;
  currency: string | null;
}

export interface OfferCampaignsResponse {
  offer_id: string;
  kpis: OfferCampaignsKPIs;
  campaigns: OfferCampaignRow[];
}
```

---

## 7. Cross-module integration detail

### 7.1 Why a port?

`offer` cannot import from `advertising` (DDD boundary). `advertising` owns
the campaign metrics. The contract is:

1. `shared/links/ports/advertising.py` — abstract port + DTOs (§1.7).
2. `advertising/application/services/offer_campaigns_read_adapter.py` — concrete
   implementation. Reads from `metrics_repository` (already exists) and
   `ad_offer_association` (already exists).
3. `shared/links/ports/__init__.py` — binds the port in a DI container
   (`AdvertisingReadPort = OfferCampaignsReadAdapter`) at startup.
4. `offer/api/routers/campaigns_router.py` — `Depends(get_advertising_read_port)`
   resolves the port. Handler never mentions the concrete class.

### 7.2 Field mapping (advertising → offer DTO)

| Source (`advertising`) | Target (`OfferCampaignRowDTO`) |
|---|---|
| `CampaignModel.id` | `id` |
| `CampaignModel.name` | `name` |
| `CampaignModel.channel_slug` | `channel` |
| `CampaignModel.status` | `status` (one of `active|paused|ended`) |
| `period_metrics.total_spend` | `spend` |
| `period_metrics.leads` | `leads` |
| `period_metrics.cpl` | `cpl` |
| `official_metrics.currency` (1 row per channel) | `currency` |

KPIs (`spend_7d`, `leads_7d`, `avg_cpl_7d`) come from the last 7d slice of
`period_metrics`. `active_count` counts rows where `status='active'`.

### 7.3 Scope of the adapter

Read-only. No writes. No cascading deletes. The `offer` module never mutates
anything in `advertising`.

---

## 8. File structure (create/modify/delete)

```
backend/src/modules/offer/
├── domain/
│   ├── enums.py                               # EXTEND (new enums)
│   ├── lifecycle.py                           # NEW
│   ├── assets.py                              # NEW
│   ├── knowledge_source.py                    # NEW
│   ├── events.py                              # NEW
│   └── offer.py                               # EXTEND (3 new fields)
├── infrastructure/
│   ├── models/
│   │   ├── offer_asset_model.py               # NEW
│   │   └── knowledge_source_model.py          # NEW
│   ├── repositories/
│   │   ├── offer_asset_repository.py          # NEW
│   │   └── knowledge_source_repository.py     # NEW
│   ├── storage/
│   │   └── r2_file_storage_adapter.py         # NEW (IFileStoragePort impl)
│   └── rag/
│       └── qdrant_rag_indexer.py              # NEW (IRAGIndexerPort impl)
├── application/
│   ├── ports.py                               # EXTEND (new ports §1.6)
│   └── services/
│       ├── offer_lifecycle_service.py         # NEW
│       ├── offer_completion_service.py        # NEW
│       ├── offer_counts_service.py            # NEW
│       ├── landing_status_service.py          # NEW
│       ├── offer_asset_service.py             # NEW
│       ├── knowledge_source_service.py        # NEW
│       └── offer_campaigns_view_service.py    # NEW (orchestrator over port)
└── api/
    ├── dto/
    │   ├── lifecycle_dtos.py                  # NEW
    │   ├── counts_dtos.py                     # NEW
    │   ├── landing_dtos.py                    # NEW
    │   ├── asset_dtos.py                      # NEW
    │   ├── knowledge_dtos.py                  # NEW
    │   └── campaigns_dtos.py                  # NEW
    └── routers/
        ├── lifecycle_router.py                # NEW
        ├── counts_router.py                   # NEW
        ├── landing_router.py                  # NEW
        ├── assets_router.py                   # NEW
        ├── knowledge_router.py                # NEW
        └── campaigns_router.py                # NEW

backend/src/shared/links/
└── ports/
    ├── __init__.py                            # NEW (port registry)
    └── advertising.py                         # NEW (AdvertisingReadPort)

backend/src/modules/advertising/
└── application/services/
    └── offer_campaigns_read_adapter.py        # NEW (concrete port impl)

backend/alembic/versions/
└── 2026_04_11_offer_header_refactor.py        # NEW

backend/tests/modules/offer/
├── domain/
│   ├── test_lifecycle_transitions.py          # NEW
│   └── test_offer_completion.py               # NEW
├── infrastructure/
│   ├── test_offer_asset_repository.py         # NEW
│   └── test_knowledge_source_repository.py    # NEW
├── application/
│   ├── test_offer_lifecycle_service.py        # NEW
│   ├── test_landing_status_service.py         # NEW
│   ├── test_offer_asset_service.py            # NEW
│   ├── test_knowledge_source_service.py       # NEW
│   └── test_offer_campaigns_view_service.py   # NEW
└── api/
    ├── test_lifecycle_router.py               # NEW
    ├── test_counts_router.py                  # NEW
    ├── test_landing_router.py                 # NEW
    ├── test_assets_router.py                  # NEW
    ├── test_knowledge_router.py               # NEW
    └── test_campaigns_router.py               # NEW
```

---

## 9. Lifecycle state machine (canonical table)

This is the machine the service MUST enforce. UI mirror in
`REQUIREMENTS.md` §Lifecycle rules.

```python
# src/modules/offer/domain/lifecycle.py
LIFECYCLE_TRANSITIONS: dict[OfferLifecycleStatus, set[OfferLifecycleStatus]] = {
    OfferLifecycleStatus.DRAFT: {
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.ACTIVE: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.PAUSED,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.PAUSED: {
        OfferLifecycleStatus.DRAFT,
        OfferLifecycleStatus.ACTIVE,
        OfferLifecycleStatus.ARCHIVED,
    },
    OfferLifecycleStatus.ARCHIVED: set(),  # terminal — use /restore
}
```

Side effects per transition (enforced in `OfferLifecycleService.change_status`):

| Transition | Side effects |
|---|---|
| `draft → active` | `status_changed_at = now()`. No landing side effect. Event `OfferStatusChanged`. |
| `active → paused` | `paused_at = now()`, `status_changed_at = now()`. Landing stays live. |
| `paused → active` | `paused_at = NULL`. |
| `active/paused → draft` | `status_changed_at = now()`. Landing stays live. |
| `draft → archived` | delegate to `archive_offer()` (soft archive). Landing auto-unpublish. |
| `active/paused → archived` | delegate to `archive_offer()`. Landing auto-unpublish. `landing_auto_unpublished=True` in response. |
| `archived → *` | **rejected** → `409`. Use `POST /offers/{id}/restore`. |

---

## 10. Acceptance contract mapping

| REQUIREMENTS acceptance criterion | Satisfied by |
|---|---|
| `POST /offers/{id}/status` validates transitions | §5.1, §9 |
| Modal consequences match lifecycle table | FE reads from §9 |
| `offer.completion_percentage` computed server-side | §1.4 + `IOfferCompletionService` + §2.3 column |
| Landing endpoints (generate/publish/unpublish/regenerate/status) | §5.2 |
| Assets CRUD with file upload/download, soft delete, tenant iso | §5.3 + §2.1 + §8 |
| Knowledge CRUD with Qdrant indexing | §5.4 + §1.6 (`IRAGIndexerPort`) |
| `GET /offers/{id}/campaigns` aggregates advertising | §5.5 + §7 |
| All endpoints declare `response_model=` | §5 (every row lists Resp DTO) |
| Every query filters `tenant_id` | §2.1–§2.2 tenant_id columns + repo interfaces |
| Migrations idempotent | §3 |
| No new DDD violations | §7 port pattern + §8 file layout |

---

## 11. Open questions (flag for implementers)

1. **Landing DB table:** `landing_pages` is owned by `landing`. The new
   columns (`generated_at`, `offer_snapshot_version`, etc.) live there, but
   the `offer` service needs to read/write them. Agreed approach: extend
   `landing/application/services` with a `LandingGenerationService` exposed
   via a port in `shared/links/ports/landing.py` (TBD — out of scope for
   this contract; for now the `offer` module may read `landing_pages` rows
   directly through a thin read-only repository inside its own
   infrastructure, as the column additions are part of this migration).
   **Decision to revisit in REVIEW.md** — do not block implementation.
2. **Snapshot version algorithm:** proposed
   `hashlib.sha256(json.dumps(subset_sorted).encode()).hexdigest()[:16]` with
   `subset` = `{headline_promise, primary_outcome, time_to_value,
   deliverables, pricing_options, marketing_pain_points, marketing_desires,
   objections, specific_details}`. Confirm during implementation.
3. **R2 path layout:** proposed
   `tenants/{tenant_id}/offers/{offer_id}/assets/{asset_id}/{filename}` for
   assets, `tenants/{tenant_id}/offers/{offer_id}/knowledge/{source_id}/...`
   for knowledge sources. Not a hard contract — implementer may adjust.
