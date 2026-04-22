# Contract: Copilot Refactor

**Spec source:** `docs/domains/copilot/copilot-refactor-spec.md`
**Mockup:** `docs/mockups/copilot-sidebar-states.html`
**Date:** 2026-04-21
**Status:** approved for parallel implementation

This contract is the binding interface between sprints. Implementers do not redesign
what exists (tool registry, orchestrator skeleton, `CopilotConversationModel`, `InterviewSession`) —
they extend it per sections below.

Multitenancy: every row carries `tenant_id: UUID`. Every query filters by `tenant_id`.
No PII fields leave the backend in any response DTO defined here.

---

## 1. DB Schema

All migrations **idempotent raw SQL**, per `.claude/rules/backend-migrations.md`.
Single Alembic revision covers the three blocks below.

### 1.1 ALTER `copilot_conversations`

Existing table: `backend/src/modules/copilot/infrastructure/models/conversation_model.py`.
Columns to add (keep existing `title`, replace nothing):

```python
def upgrade() -> None:
    op.execute("""
        ALTER TABLE copilot_conversations
          ADD COLUMN IF NOT EXISTS summary              TEXT         NULL,
          ADD COLUMN IF NOT EXISTS summary_updated_at   TIMESTAMPTZ  NULL,
          ADD COLUMN IF NOT EXISTS summary_dirty_at     TIMESTAMPTZ  NULL,
          ADD COLUMN IF NOT EXISTS message_count        INTEGER      NOT NULL DEFAULT 0,
          ADD COLUMN IF NOT EXISTS total_tokens         INTEGER      NOT NULL DEFAULT 0,
          ADD COLUMN IF NOT EXISTS last_tier_used       TEXT         NULL,
          ADD COLUMN IF NOT EXISTS title_auto_generated BOOLEAN      NOT NULL DEFAULT FALSE,
          ADD COLUMN IF NOT EXISTS archived_at          TIMESTAMPTZ  NULL,
          ADD COLUMN IF NOT EXISTS procedure_id         UUID         NULL,
          ADD COLUMN IF NOT EXISTS procedure_state      JSONB        NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_tenant_user_active
          ON copilot_conversations (tenant_id, user_id, updated_at DESC)
          WHERE archived_at IS NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_summary_dirty
          ON copilot_conversations (summary_dirty_at)
          WHERE summary_dirty_at IS NOT NULL
    """)
```

Notes:
- `title` column already exists (String(255)) — do NOT redefine.
- `summary` column already exists (Text) — only the metadata columns are added.
- `deleted_at` still used for hard soft-delete (existing). `archived_at` is the
  user-visible "archive from history" flag; a row can be archived-but-not-deleted.

### 1.2 CREATE `copilot_routing_log`

```python
op.execute("""
    CREATE TABLE IF NOT EXISTS copilot_routing_log (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID         NOT NULL,
        conversation_id UUID         NOT NULL,
        message_id      UUID         NOT NULL,
        tier_selected   TEXT         NOT NULL,   -- nano|mini|reasoning|heavy
        classifier_used TEXT         NOT NULL,   -- rule|llm|default
        reason          TEXT         NOT NULL,
        confidence      NUMERIC(4,3) NULL,
        user_msg_length INTEGER      NOT NULL,
        tools_available INTEGER      NOT NULL,
        created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
    )
""")

op.execute("""
    CREATE INDEX IF NOT EXISTS ix_copilot_routing_log_tenant_time
      ON copilot_routing_log (tenant_id, created_at DESC)
""")

op.execute("""
    CREATE INDEX IF NOT EXISTS ix_copilot_routing_log_conv
      ON copilot_routing_log (conversation_id, created_at DESC)
""")
```

### 1.3 CREATE `copilot_mutation_journal`

```python
op.execute("""
    CREATE TABLE IF NOT EXISTS copilot_mutation_journal (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id       UUID        NOT NULL,
        conversation_id UUID        NOT NULL,
        message_id      UUID        NOT NULL,
        domain          TEXT        NOT NULL,    -- brand|offer|landing|buyer_persona|...
        entity_id       UUID        NULL,
        field_path      TEXT        NOT NULL,
        old_value       JSONB       NULL,
        new_value       JSONB       NULL,
        applied_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        reverted_at     TIMESTAMPTZ NULL
    )
""")

op.execute("""
    CREATE INDEX IF NOT EXISTS ix_copilot_mutation_journal_conv_time
      ON copilot_mutation_journal (conversation_id, applied_at DESC)
""")

op.execute("""
    CREATE INDEX IF NOT EXISTS ix_copilot_mutation_journal_tenant_active
      ON copilot_mutation_journal (tenant_id, applied_at DESC)
      WHERE reverted_at IS NULL
""")
```

### 1.4 Downgrade

Downgrade drops the two new tables and the added columns/indexes via
`DROP TABLE IF EXISTS ... CASCADE` and `ALTER TABLE ... DROP COLUMN IF EXISTS`.
Destructive — gated behind explicit manual run.

---

## 2. Domain Enums & Value Objects

All live in `backend/src/modules/copilot/domain/` — no SQLAlchemy imports.

### 2.1 `domain/model_tier.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum


class ModelTier(StrEnum):
    NANO = "nano"
    MINI = "mini"
    REASONING = "reasoning"
    HEAVY = "heavy"


@dataclass(frozen=True, slots=True)
class TierMetadata:
    tier: ModelTier
    model_name: str                      # e.g. "gpt-5.4-nano"
    price_input_per_1m: float            # USD per 1M input tokens
    price_output_per_1m: float
    price_cached_input_per_1m: float | None  # None = provider has no cache tier
    context_window_tokens: int
    supports_caching: bool
    is_reasoning: bool


TIER_METADATA: dict[ModelTier, TierMetadata] = {
    ModelTier.NANO: TierMetadata(
        tier=ModelTier.NANO, model_name="gpt-5.4-nano",
        price_input_per_1m=0.20, price_output_per_1m=1.25,
        price_cached_input_per_1m=0.02,
        context_window_tokens=1_000_000,
        supports_caching=True, is_reasoning=False,
    ),
    ModelTier.MINI: TierMetadata(
        tier=ModelTier.MINI, model_name="gpt-5.4-mini",
        price_input_per_1m=0.75, price_output_per_1m=4.50,
        price_cached_input_per_1m=0.075,
        context_window_tokens=1_000_000,
        supports_caching=True, is_reasoning=False,
    ),
    ModelTier.REASONING: TierMetadata(
        tier=ModelTier.REASONING, model_name="o4-mini",
        price_input_per_1m=1.10, price_output_per_1m=4.40,
        price_cached_input_per_1m=None,
        context_window_tokens=200_000,
        supports_caching=False, is_reasoning=True,
    ),
    ModelTier.HEAVY: TierMetadata(
        tier=ModelTier.HEAVY, model_name="o3",
        price_input_per_1m=2.00, price_output_per_1m=8.00,
        price_cached_input_per_1m=None,
        context_window_tokens=200_000,
        supports_caching=False, is_reasoning=True,
    ),
}
```

### 2.2 `domain/routing_policy.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from src.modules.copilot.domain.model_tier import ModelTier


class ClassifierType(StrEnum):
    RULE = "rule"
    LLM = "llm"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    tier: ModelTier
    reason: str                       # short human string, goes to DB + telemetry
    confidence: float                 # 0..1
    classifier_used: ClassifierType
    fallback_tier: ModelTier          # used if primary LLM call fails


@dataclass(frozen=True, slots=True)
class RoutingRule:
    """Data-only rule evaluated by RuleClassifier."""
    pattern: str                      # regex, case-insensitive; applied to user_message
    tier: ModelTier
    reason: str
    priority: int                     # lower wins; rules sorted asc
    min_msg_length: int | None = None # additional guard (for NANO short-msg rule)
    max_msg_length: int | None = None
    max_tools: int | None = None      # "sin tools" => max_tools=0
    required_keywords: tuple[str, ...] = ()  # all must appear (AND)


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    rules: tuple[RoutingRule, ...]
    default_tier: ModelTier = ModelTier.MINI
```

**Initial policy — exact rules from spec §1 matrix.** Ordered by priority; first
regex match that also passes length/tool guards wins.

```python
# domain/routing_policy.py  (continuation)
DEFAULT_ROUTING_POLICY: RoutingPolicy = RoutingPolicy(
    default_tier=ModelTier.MINI,
    rules=(
        # ── HEAVY (priority 10-19) ─────────────────────────────────────
        RoutingRule(
            priority=10,
            pattern=r"\b(audita|auditar|diagn[oó]stic[oa]|analiza a fondo)\b",
            tier=ModelTier.HEAVY,
            reason="keyword_audit_diagnostic",
        ),
        RoutingRule(
            priority=11,
            pattern=r"\bplan estrat[eé]gico\b|\bestrategia de\b",
            tier=ModelTier.HEAVY,
            reason="keyword_strategic_plan",
        ),
        RoutingRule(
            priority=12,
            pattern=r"\bad[oó]nde va mi\b|\bc[oó]mo mejorar (mi|la) (marca|oferta|funnel)\b",
            tier=ModelTier.HEAVY,
            reason="keyword_cross_module_improve",
        ),
        # ── REASONING (priority 20-29) ─────────────────────────────────
        RoutingRule(
            priority=20,
            pattern=r"\bpor qu[eé]\b|\bdame razones\b|\bexplica por qu[eé]\b",
            tier=ModelTier.REASONING,
            reason="keyword_causal_why",
        ),
        RoutingRule(
            priority=21,
            pattern=r"\bcomp[aá]rame\b|\boptimiza\b|\brazon[aá]\b|\bpiensa paso a paso\b",
            tier=ModelTier.REASONING,
            reason="keyword_compare_reason",
        ),
        RoutingRule(
            priority=22,
            pattern=r"\bc[oó]mo (puedo|podr[ií]a)\b",
            tier=ModelTier.REASONING,
            reason="keyword_how_can_i",
        ),
        # ── NANO (priority 30-39) short & toolless ─────────────────────
        RoutingRule(
            priority=30,
            pattern=r".*",
            tier=ModelTier.NANO,
            reason="short_msg_no_tools",
            max_msg_length=40,
            max_tools=0,
        ),
        # default falls through to policy.default_tier (MINI)
    ),
)
```

Internal (non-user) call tiers are chosen directly by callers, not by the
policy — see §7 "Internal tier usage".

### 2.3 `domain/context_window.py`

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextWindowConfig:
    RAW_WINDOW_TOKENS: int = 2000
    RAW_WINDOW_MAX_MESSAGES: int = 10
    RAW_WINDOW_MIN_MESSAGES: int = 4
    SUMMARY_MAX_CHARS: int = 400
    SUMMARY_TARGET_TOKENS: int = 150
    NUDGE_AFTER_TOTAL_TOKENS: int = 8000
    NUDGE_HARD_LIMIT_TOKENS: int = 16000
    NUDGE_AFTER_MESSAGE_COUNT: int = 12
    TOKEN_COUNTER: str = "tiktoken:cl100k_base"


DEFAULT_CONTEXT_WINDOW_CONFIG = ContextWindowConfig()
```

### 2.4 `domain/procedure_state.py`

Pydantic v2 model — lives in domain because it is serialized into the
`procedure_state JSONB` column. No ORM imports.

```python
from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ProcedureState(BaseModel):
    """Overlay stored on conversation.procedure_state (JSONB).

    Replaces the standalone InterviewSession table row-for-row for active
    procedures. See §6 migration.
    """
    model_config = ConfigDict(frozen=False, extra="forbid")

    procedure_id: str                       # e.g. "buyer_persona", "offer_first_edition"
    current_block: str
    completed_blocks: list[str] = Field(default_factory=list)
    answers: dict[str, object] = Field(default_factory=dict)   # mapa_global
    coverage: float = 0.0                   # 0..1 global
    entity_id: UUID | None = None           # optional target entity (offer id, etc.)
```

### 2.5 `domain/mutation_journal.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MutationJournalEntry:
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    message_id: UUID
    domain: str
    entity_id: UUID | None
    field_path: str
    old_value: Any | None           # JSON-serializable
    new_value: Any | None
    applied_at: datetime
    reverted_at: datetime | None
```

---

## 3. Port Interfaces

All live in `backend/src/modules/copilot/domain/ports.py`. Pure Protocols, no
concrete imports. Defaults ship in `infrastructure/` (see file layout §9).

```python
from __future__ import annotations
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.procedure_state import ProcedureState


# ── LLM provider ────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: str                # "system" | "user" | "assistant" | "tool"
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True, slots=True)
class LLMEvent:
    """One chunk of the streamed LLM response.

    `kind` is one of: "text" | "tool_start" | "tool_result" | "usage" | "done" | "error"
    `data` is kind-specific, JSON-serializable.
    """
    kind: str
    data: dict[str, Any]


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]: ...


# ── Conversation store ──────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ConversationPage:
    items: list["ConversationSummaryVO"]   # see below
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class ConversationSummaryVO:
    id: UUID
    title: str | None
    updated_at: Any                 # datetime; Any avoids naive import here
    message_count: int
    total_tokens: int
    last_tier_used: ModelTier | None
    has_procedure: bool
    procedure_progress: float | None       # coverage 0..1
    title_auto_generated: bool
    archived_at: Any | None


@runtime_checkable
class ConversationStore(Protocol):
    async def list(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 6,
        cursor: str | None = None,
        include_archived: bool = False,
    ) -> ConversationPage: ...

    async def get(
        self, *, tenant_id: UUID, user_id: UUID, conversation_id: UUID,
    ) -> ConversationSummaryVO | None: ...

    async def create(
        self, *, tenant_id: UUID, user_id: UUID, title: str | None = None,
    ) -> ConversationSummaryVO: ...

    async def append(
        self, *, tenant_id: UUID, conversation_id: UUID, message: LLMMessage,
        tier_used: ModelTier, tokens_added: int,
    ) -> None: ...

    async def update_summary(
        self, *, tenant_id: UUID, conversation_id: UUID, summary: str,
    ) -> None: ...

    async def update_title(
        self, *, tenant_id: UUID, conversation_id: UUID,
        title: str, auto_generated: bool,
    ) -> ConversationSummaryVO: ...

    async def archive(
        self, *, tenant_id: UUID, user_id: UUID, conversation_id: UUID,
    ) -> ConversationSummaryVO: ...

    async def update_procedure_state(
        self, *, tenant_id: UUID, conversation_id: UUID,
        procedure_state: ProcedureState | None,
    ) -> None: ...


# ── Tool registry ────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class CopilotContext:
    current_route: str | None
    selected_fields: list[dict[str, str]]
    form_data: dict[str, Any]
    locale: str
    procedure_state: ProcedureState | None = None


@runtime_checkable
class ToolRegistry(Protocol):
    def get_tools_for_context(self, ctx: CopilotContext) -> list[Any]: ...


# ── Identity provider ────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class UserPrincipal:
    user_id: UUID
    tenant_id: UUID


@runtime_checkable
class IdentityProvider(Protocol):
    async def current_user(self) -> UserPrincipal: ...
    async def tenant_id_for(self, user_id: UUID) -> UUID: ...
```

Default Nicolify implementations (see §9):
- `OpenAILLMProvider` → `infrastructure/llm/openai_provider.py`
- `PostgresConversationStore` → `infrastructure/repositories/conversation_store.py`
  (thin wrapper around existing `ConversationRepository`)
- `RouteBasedToolRegistry` → `infrastructure/tools/route_registry.py`
  (reuses existing `application/tools/registry.py::get_tools_for_context` after §6 refactor)
- `ClerkIdentityProvider` → `infrastructure/identity/clerk_provider.py`

---

## 4. API Contracts

Base path: `/api/v1/copilot`. All endpoints:
- Require Clerk Bearer + `X-Tenant-ID` (existing `get_current_user` + `get_tenant_context` deps).
- Have `response_model=` (arch test `test_all_endpoints_have_response_model` enforces).
- Filter by `tenant_id` AND `user_id` (conversations are per-user).
- **No PII fields** (no email/phone/name) in any response listed here.

Existing `POST /chat` is out of scope of this contract (unchanged signature —
only internals per §8).

### 4.1 Request / Response DTOs

Location: `backend/src/modules/copilot/api/conversation_dto.py`.
Pydantic v2, `model_config = ConfigDict(from_attributes=True)`.

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

ModelTierLiteral = Literal["nano", "mini", "reasoning", "heavy"]


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    title_auto_generated: bool
    updated_at: datetime
    message_count: int
    total_tokens: int
    last_tier_used: ModelTierLiteral | None
    has_procedure: bool
    procedure_progress: float | None = Field(default=None, ge=0.0, le=1.0)
    archived_at: datetime | None = None


class ConversationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[ConversationSummary]
    next_cursor: str | None = None


class PatchConversationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=120)
    archived: bool | None = None


class RevertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # When omitted -> revert ALL non-reverted mutations in the conversation.
    mutation_ids: list[UUID] | None = None


class RevertFailure(BaseModel):
    id: UUID
    error: str


class RevertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reverted_count: int
    failed: list[RevertFailure] = Field(default_factory=list)
```

### 4.2 Endpoints

File: `backend/src/modules/copilot/api/conversations.py` (new router).
Mounted at `/api/v1/copilot` by `main.py`.

| Method | Path                                               | Request         | Response (`response_model=`)   | Status |
|--------|----------------------------------------------------|-----------------|--------------------------------|--------|
| GET    | `/conversations`                                   | query params    | `ConversationListResponse`     | 200    |
| POST   | `/conversations`                                   | none            | `ConversationSummary`          | 201    |
| PATCH  | `/conversations/{conversation_id}`                 | `PatchConversationRequest` | `ConversationSummary` | 200    |
| DELETE | `/conversations/{conversation_id}`                 | none            | `None` (returns 204)           | 204    |
| POST   | `/conversations/{conversation_id}/revert`          | `RevertRequest` | `RevertResponse`               | 200    |

Query params for `GET /conversations`:
- `limit: int` — default 6, min 1, max 50.
- `cursor: str | None` — opaque base64 string produced by server.
- `include_archived: bool` — default `false`.

Behaviour notes:
- `DELETE` sets `archived_at = now()` (soft). Hard delete = data retention job.
- `PATCH archived=true` is equivalent to `DELETE`. `archived=false` un-archives.
- `POST /revert` with no body = revert all active mutations newest-first.
- Cursor is a signed opaque string encoding `(updated_at, id)` — implementer
  chooses format; clients never parse it.

### 4.3 SSE additions to existing `POST /chat`

`POST /api/v1/copilot/chat` continues to return `text/event-stream` (unchanged
route). Two new event types added to `SSEEventType` in `api/dto.py`:

```python
SSEEventType = Literal[
    "text_chunk",
    "tool_start",
    "tool_result",
    "ui_action",
    "proposal",
    "confirmation_required",
    "status",
    "tier_decision",     # NEW — emitted exactly once, before first text_chunk
    "mutation_applied",  # NEW — emitted when a mutation is journaled
    "done",
    "error",
]
```

Payloads:

```jsonc
// tier_decision
{ "tier": "mini", "reason": "keyword_compare_reason",
  "classifier_used": "rule", "confidence": 0.92 }

// mutation_applied
{ "id": "<uuid>", "domain": "brand", "entity_id": "<uuid|null>",
  "field_path": "value_proposition", "can_revert": true }
```

`tier_decision` MUST be the first non-`status` event in the stream.

---

## 5. TypeScript Contracts

Location: `frontend/src/features/copilot/types/conversations.ts` (new file;
`types/index.ts` re-exports).

Camel-case mirror of section 4.1. Source of truth is backend; codegen optional.

```typescript
export type ModelTier = "nano" | "mini" | "reasoning" | "heavy";

export interface ConversationSummary {
  id: string;                      // UUID
  title: string | null;
  titleAutoGenerated: boolean;
  updatedAt: string;               // ISO 8601
  messageCount: number;
  totalTokens: number;
  lastTierUsed: ModelTier | null;
  hasProcedure: boolean;
  procedureProgress: number | null; // 0..1
  archivedAt: string | null;
}

export interface ConversationListResponse {
  items: ConversationSummary[];
  nextCursor: string | null;
}

export interface PatchConversationRequest {
  title?: string;
  archived?: boolean;
}

export interface RevertRequest {
  mutationIds?: string[];          // UUID[]; omit = revert all
}

export interface RevertFailure {
  id: string;
  error: string;
}

export interface RevertResponse {
  revertedCount: number;
  failed: RevertFailure[];
}

// SSE event additions
export interface TierDecisionEvent {
  tier: ModelTier;
  reason: string;
  classifierUsed: "rule" | "llm" | "default";
  confidence: number;
}

export interface MutationAppliedEvent {
  id: string;
  domain: string;
  entityId: string | null;
  fieldPath: string;
  canRevert: boolean;
}
```

Naming convention: request/response field names on the wire are **snake_case**
(Pydantic default). The FE API layer (`features/copilot/api/copilot-api.ts`)
is responsible for case-mapping. Do not introduce aliasing at the BE.

---

## 6. Tool Registry Changes

File: `backend/src/modules/copilot/application/tools/registry.py`.

### 6.1 Remove

- Delete import + group entry for `focus`.
- Delete helper `_get_tools_for_focus`.
- Delete the `if context.get("focus")` branch inside `get_tools_for_context`.
- Delete the `if context.get("interview_session_id")` branch.

### 6.2 Keep

- `ROUTE_TOOL_MAP`, `_match_route`, `get_tools_for_route`, `get_all_tools`,
  `TOOL_GROUPS` (with `focus` removed, `interview` removed — see §6.3).

### 6.3 Rename and restructure `PROCEDURE_TOOLS`

Current state:
- `application/tools/procedure_tools.py::PROCEDURE_TOOLS` is a **flat list**
  of 3 generic tools (`start_procedure`, `get_procedure_status`,
  `advance_procedure`).
- `application/tools/interview/__init__.py::INTERVIEW_TOOLS` is a list of
  interview-specific tools.

Target state:
- `application/tools/procedure_tools.py` exports:
  - `PROCEDURE_BASE_TOOLS: list` — the 3 generic tools (kept).
  - `PROCEDURE_TOOLS: dict[str, list]` — keyed by `procedure_id`. Each entry
    is `PROCEDURE_BASE_TOOLS + <specific tools for that procedure>`.
- `application/tools/interview/` → **deleted** (its tools move into
  `PROCEDURE_TOOLS["buyer_persona"]`, `PROCEDURE_TOOLS["offer_first_edition"]`,
  etc., as needed). Backfill mapping per sprint S5.

### 6.4 New `get_tools_for_context` signature

```python
def get_tools_for_context(context: CopilotContext | dict | None) -> list:
    """Route-based tools + procedure overlay (if procedure active).

    Deprecations:
      - context.focus: IGNORED (focus mode removed)
      - context.interview_session_id: IGNORED (migrated to procedure_state)
    """
    if not context:
        return get_tools_for_route(None)

    # Accept both dict (legacy callers) and CopilotContext
    route = context.current_route if hasattr(context, "current_route") else context.get("current_route")
    procedure_state = (
        context.procedure_state if hasattr(context, "procedure_state")
        else context.get("procedure_state")
    )

    tools = list(get_tools_for_route(route))
    seen = {t.name for t in tools}

    if procedure_state is not None:
        procedure_id = (
            procedure_state.procedure_id if hasattr(procedure_state, "procedure_id")
            else procedure_state.get("procedure_id")
        )
        for t in PROCEDURE_TOOLS.get(procedure_id, []):
            if t.name not in seen:
                tools.append(t)
                seen.add(t.name)

    return tools
```

### 6.5 Deprecation window

1 sprint (S5): `focus_*` and `interview_*` tools kept but decorated
`deprecated=True` (structured log line `copilot.tool_deprecated_called` per
invocation). After S5 landing: delete files + remove groups from
`TOOL_GROUPS`.

---

## 7. Routing Policy — Runtime

### 7.1 Data-only evaluation

`RoutingPolicy` (§2.2) is pure data. The evaluator lives in application:

```python
# application/router/rule_classifier.py
from src.modules.copilot.domain.routing_policy import (
    RoutingPolicy, RoutingDecision, DEFAULT_ROUTING_POLICY,
)
from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import ClassifierType


class RuleClassifier:
    def __init__(self, policy: RoutingPolicy = DEFAULT_ROUTING_POLICY) -> None:
        self._policy = policy
        # Rules pre-compiled on init; sorted by priority asc.

    def classify(
        self, *, user_message: str, tools_available: int,
    ) -> RoutingDecision | None:
        """Return decision or None if no rule matches confidently."""
```

Return `None` when no rule matches → `LLMClassifier` fallback, else
`RoutingDecision(tier=policy.default_tier, classifier_used=DEFAULT, confidence=0.5)`.

### 7.2 Internal (non-user) tier usage

These calls bypass the policy and pin `NANO`:

| Caller                                               | Tier | File                                               |
|------------------------------------------------------|------|----------------------------------------------------|
| Intent classification (LLMClassifier fallback)       | NANO | `application/router/classifiers/llm_classifier.py` |
| Title auto-generation (post msg 2)                   | NANO | `application/services/title_generator.py`          |
| Rolling summary update                               | NANO | `application/services/rolling_summarizer.py`       |
| Web scrape structure extraction                      | NANO | existing scrape service                            |

These all call `LLMProvider.complete(tier=ModelTier.NANO, ...)` directly. No
telemetry row is written for internal calls (routing_log is user-facing only).

### 7.3 Telemetry

One row in `copilot_routing_log` per user-initiated `POST /chat`, emitted
synchronously before the first LLM token is streamed:

```python
# application/router/routing_telemetry.py
async def log_decision(
    *, tenant_id: UUID, conversation_id: UUID, message_id: UUID,
    decision: RoutingDecision, user_msg_length: int, tools_available: int,
) -> None: ...
```

---

## 8. Orchestrator Signature Changes

File: `backend/src/modules/copilot/application/orchestrator/chat.py`.

### 8.1 New constructor dependencies

`CopilotOrchestrator.__init__` gains three deps (constructor-injected; no
service locator). Defaults construct the Nicolify impls so existing callers
(`api/chat.py`) can keep the `CopilotOrchestrator(db)` shape during migration.

```python
class CopilotOrchestrator:
    def __init__(
        self,
        db: Session,
        *,
        model_router: "ModelRouter | None" = None,
        context_builder: "ContextWindowBuilder | None" = None,
        rolling_summarizer: "RollingSummarizer | None" = None,
        mutation_journal: "MutationJournalRepository | None" = None,
    ) -> None: ...
```

Types (all in `application/`):
- `ModelRouter` — `application/router/model_router.py`
  `async def select(req: RoutingRequest) -> RoutingDecision`
- `ContextWindowBuilder` — `application/context/window_builder.py`
  `def build(conversation) -> list[LLMMessage]` (system + summary? + raw)
- `RollingSummarizer` — `application/services/rolling_summarizer.py`
  `async def maybe_update(conversation_id: UUID) -> None` (reads dirty flag,
  calls NANO, writes summary + clears `summary_dirty_at`)
- `MutationJournalRepository` — `infrastructure/repositories/mutation_journal_repository.py`
  (see §9).

### 8.2 New stream contract

`stream_chat(...)` signature unchanged at the API surface but its yielded
event order becomes:

```
status           (existing "thinking…")
tier_decision    (NEW — exactly one, before any text_chunk)
text_chunk × N
tool_start / tool_result interleaved as today
mutation_applied (NEW — one per mutation journaled)
proposal / confirmation_required / ui_action (existing)
done
```

On error: emit `error` event + stop. `tier_decision` MUST still be emitted
before `error` unless the error is a routing failure itself (in which case
`error.data.stage = "routing"` and no tier_decision is sent).

### 8.3 Behaviours by phase

- **Phase 1 — route.** `ModelRouter.select(...)` → emit `tier_decision`
  → insert `copilot_routing_log` row.
- **Phase 2 — context.** `ContextWindowBuilder.build(conversation)` produces
  the prompt. If conversation has `displaced messages but summary is None`,
  builder runs a **synchronous** NANO summary to seed it.
- **Phase 3 — llm.** `LLMProvider.complete(tier=decision.tier, ...)`. Stream
  passthrough + token accounting.
- **Phase 4 — mutations.** Each mutation tool call that succeeds inserts a
  `copilot_mutation_journal` row **and** emits `mutation_applied`.
- **Phase 5 — post.** After `done`: `summary_dirty_at = now()` if new
  displacement; schedule `RollingSummarizer.maybe_update` (fire-and-forget
  asyncio.create_task). First post-msg-2 also schedules title generation.

### 8.4 Feature flag

`COPILOT_V2_ENABLED` (env, default `false` during S1–S4). When false, the
orchestrator skips router + context builder + journaling and runs the legacy
path. S5 flips to `true` per-tenant, then globally.

---

## 9. File Structure

```
backend/src/modules/copilot/
├── domain/
│   ├── model_tier.py              # NEW  §2.1
│   ├── routing_policy.py          # NEW  §2.2 + rules
│   ├── context_window.py          # NEW  §2.3
│   ├── procedure_state.py         # NEW  §2.4
│   ├── mutation_journal.py        # NEW  §2.5
│   ├── ports.py                   # NEW  §3
│   ├── interview_session.py       # KEEP (deprecated S5; read-only during backfill)
│   ├── interview_config.py        # KEEP
│   ├── interview_configs/         # KEEP (used to derive procedure_id tool bundles)
│   ├── navigation_map.py          # KEEP
│   ├── module_registry.py         # KEEP
│   └── schema_introspection.py    # KEEP
├── infrastructure/
│   ├── models/
│   │   ├── conversation_model.py  # EDIT  add new columns (SQLA 2.0 mapped_column preferred)
│   │   ├── routing_log_model.py   # NEW
│   │   └── mutation_journal_model.py # NEW
│   ├── repositories/
│   │   ├── conversation_repository.py # EDIT  add async list/get/archive/update_summary/update_procedure_state
│   │   ├── conversation_store.py      # NEW   adapts repo to ConversationStore port
│   │   ├── routing_log_repository.py  # NEW
│   │   └── mutation_journal_repository.py # NEW
│   ├── llm/
│   │   └── openai_provider.py     # NEW  OpenAILLMProvider (default LLMProvider)
│   ├── tools/
│   │   └── route_registry.py      # NEW  thin wrapper implementing ToolRegistry
│   └── identity/
│       └── clerk_provider.py      # NEW  ClerkIdentityProvider
├── application/
│   ├── orchestrator/
│   │   └── chat.py                # EDIT  §8
│   ├── router/
│   │   ├── model_router.py        # NEW
│   │   ├── routing_telemetry.py   # NEW
│   │   └── classifiers/
│   │       ├── rule_classifier.py # NEW
│   │       └── llm_classifier.py  # NEW
│   ├── context/
│   │   └── window_builder.py      # NEW
│   ├── services/
│   │   ├── title_generator.py     # NEW
│   │   └── rolling_summarizer.py  # NEW
│   ├── tools/
│   │   ├── registry.py            # EDIT  §6
│   │   ├── procedure_tools.py     # EDIT  PROCEDURE_TOOLS dict + PROCEDURE_BASE_TOOLS
│   │   ├── focus/                 # DELETE S5
│   │   └── interview/             # DELETE S5 (contents distributed into procedure_tools)
│   └── procedures/                # KEEP
└── api/
    ├── chat.py                    # EDIT  no signature change (internals via new orchestrator)
    ├── dto.py                     # EDIT  add tier_decision + mutation_applied SSEEventType
    ├── conversation_dto.py        # NEW  §4.1
    ├── conversations.py           # NEW  §4.2 router
    └── interview.py               # DELETE S5

frontend/src/features/copilot/
├── types/
│   ├── index.ts                   # EDIT re-export new types
│   └── conversations.ts           # NEW  §5
├── api/
│   ├── copilot-api.ts             # EDIT  tier_decision / mutation_applied handlers
│   └── conversations-api.ts       # NEW  list/create/patch/delete/revert
├── hooks/
│   ├── use-conversations.ts       # NEW  React Query: list + pagination cursor
│   ├── use-revert-conversation.ts # NEW
│   └── use-sidebar-state.ts       # NEW  localStorage: "copilot.sidebarState"
├── components/
│   ├── copilot-sidebar.tsx        # EDIT or NEW — 3 states per mockup
│   ├── copilot-rail.tsx           # NEW  60px always-visible column
│   ├── copilot-history-panel.tsx  # NEW  280px conversation list with sections
│   ├── copilot-chat-panel.tsx     # EDIT
│   ├── copilot-context-rot-banner.tsx # NEW
│   ├── copilot-tier-chip.tsx      # NEW  color-coded per tier
│   └── copilot-conversation-item.tsx  # NEW
└── store/
    └── copilot-store.ts           # EDIT  remove focus fields; add sidebarState, dismissedNudges
```

Migration file: `backend/alembic/versions/<new>_copilot_refactor_v2.py`.

---

## 10. Constraints Reminder

All items below are **invariants** enforced by arch tests or review.

1. Every new SQLAlchemy model uses `Column(UUID(as_uuid=True))` with
   `tenant_id` not-null + indexed, and (where applicable) `deleted_at`.
   New columns on existing `copilot_conversations` follow the same rules.
2. Every new endpoint declares `response_model=`. No raw dict returns.
   Enforced by `backend/tests/architecture/test_api_contracts.py`.
3. Every new repository method accepts `tenant_id` as a required kw-only
   argument and filters by it. Enforced by tenant-isolation review.
4. Domain layer (§2, §3, §9 `domain/`) imports **nothing** from
   `infrastructure/` or `api/`. No SQLA, no FastAPI, no httpx.
   Enforced by `test_domain_layer_has_no_framework_imports`.
5. No cross-module imports. `copilot` may import `shared/`, `core/`, and
   (per `copilot-resilience.md`) introspect other modules via
   `module_registry.py` — not via direct repo imports from other modules.
6. No PII fields (`email`, `phone`, `name`, `dob`, `address`, `ip`, etc.)
   appear in any DTO listed in §4.1 or §5. Conversation `title` is user-
   authored free text; implementer rejects any auto-generated title that
   looks like email/phone via regex.
7. All new datetime columns `TIMESTAMPTZ`; backend uses `utc_now()` from
   `shared/domain/datetime_utils`. No `datetime.utcnow()`.
8. Migration is idempotent (`IF NOT EXISTS` on every DDL). Tested against
   a clone of prod DB before prod push.
9. Pydantic v2 `ConfigDict` only — no inner `class Config`.
10. No `Any` in DTOs except where a JSONB passthrough is semantically
    required (`MutationJournalEntry.old_value/new_value`,
    `ProcedureState.answers`). Everything else is typed.

---

## 11. Parallel Implementation Map

Each sprint in spec §7 maps to a vertical slice of this contract:

| Sprint | Contract sections | Primary agents |
|--------|------------------|----------------|
| S1 | §1, §2.4, §2.5, §4, §5, §9 (conversations router + types) | backend + frontend |
| S2 | §2.1, §2.2, §3 (LLMProvider), §7, §8 (phase 1 only) | backend |
| S3 | §2.3, §8 (phase 2 + 5), rolling summarizer | backend |
| S4 | §5, §9 frontend components, mockup parity | frontend |
| S5 | §6 (focus delete + procedure dict), mutation journal revert UX, backfill | backend + frontend |

Every sprint closes with: native lint, native tests, arch tests, migration
test against prod clone, manual mockup QA (S4 onwards).

---

## 12. Skills Plugin System

Claude Code's `.claude/skills/` pattern ported into copilot runtime. Each
skill = one `.md` file with YAML frontmatter + expertise body. Discovered at
boot (prod) or hot-reloaded (dev).

### 12.1 File layout

- System skills: `backend/src/modules/copilot/skills/*.md` (shipped with code).
- Per-tenant overrides (future, schema accommodates now):
  `backend/src/modules/copilot/skills_tenant/{tenant_id}/*.md`.
- Optional Jinja2 output template companion: `{skill_name}.j2` next to the
  `.md` file. When present, `output_format` should be `"structured"` or
  `"procedure"` and the template id is implicit (`{skill_name}`).

Skill names kebab-case, globally unique (tenant override replaces system
skill of same `name`). Flat layout (no per-skill folder). Auxiliary files
use the Jinja2 companion convention only.

### 12.2 `SkillMetadata` (Pydantic v2, frontmatter schema)

Location: `backend/src/modules/copilot/domain/skills/skill_metadata.py`.

```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from src.modules.copilot.domain.model_tier import ModelTier

SkillOutputFormat = Literal["free", "structured", "procedure"]


class SkillMetadata(BaseModel):
    """Strict YAML frontmatter schema for a skill .md file."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9-]*$")
    description: str = Field(min_length=1, max_length=200)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    trigger_keywords: tuple[str, ...] = Field(default_factory=tuple)
    slash_command: str | None = Field(
        default=None,
        pattern=r"^/[a-z][a-z0-9-]*$",
        max_length=48,
    )
    allowed_tools: tuple[str, ...] = Field(default_factory=tuple)
    preferred_tier: ModelTier = ModelTier.MINI
    required_context: tuple[str, ...] = Field(default_factory=tuple)
    output_format: SkillOutputFormat = "free"
    procedure_id: str | None = None
    author: str = "nicolify"
    tenant_editable: bool = False
    requires_plan: bool = False           # triggers Plan Mode (§15)

    @field_validator("allowed_tools")
    @classmethod
    def _no_wildcards(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if any(t == "*" or "*" in t for t in v):
            raise ValueError("allowed_tools may not contain wildcards")
        return v
```

### 12.3 `SkillDefinition` (loaded artifact)

Location: `backend/src/modules/copilot/domain/skills/skill_definition.py`.

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from src.modules.copilot.domain.skills.skill_metadata import SkillMetadata


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    metadata: SkillMetadata
    body_markdown: str                  # raw body, pre-Jinja2
    source_path: Path                   # for debugging / hot reload
    tenant_id: str | None               # None = system skill
    jinja2_template_path: Path | None   # companion .j2 if present
```

### 12.4 `SkillRegistry` (in-memory index, boot-time populated)

Location: `backend/src/modules/copilot/domain/skills/skill_registry.py`.
Pure data structure; loader lives in `infrastructure/`.

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable
from src.modules.copilot.domain.skills.skill_definition import SkillDefinition


@runtime_checkable
class SkillRegistry(Protocol):
    def get(self, name: str, *, tenant_id: str | None = None) -> SkillDefinition | None: ...
    def by_slash_command(self, slug: str, *, tenant_id: str | None = None) -> SkillDefinition | None: ...
    def search_by_keyword(self, text: str, *, tenant_id: str | None = None) -> list[SkillDefinition]: ...
    def all(self, *, tenant_id: str | None = None) -> list[SkillDefinition]: ...
    def for_slash_autocomplete(self, *, tenant_id: str | None = None) -> list[SkillDefinition]: ...
```

Tenant resolution rule: `get("foo", tenant_id=T)` returns tenant override if
present, else system skill, else `None`.

### 12.5 `SkillsLoader` (file → registry)

Location: `backend/src/modules/copilot/infrastructure/skills_loader.py`.

```python
from __future__ import annotations
from pathlib import Path
from src.modules.copilot.domain.skills.skill_registry import SkillRegistry
from src.modules.copilot.domain.skills.skill_definition import SkillDefinition


class SkillsLoader:
    """Parses .md files + YAML frontmatter into SkillDefinition.

    Validation failures at load time raise SkillLoadError with file path.
    Prod: load once at module import; cached registry.
    Dev: watchdog observer re-invokes load() on file change.
    """

    def __init__(self, system_dir: Path, tenant_dir_root: Path | None = None) -> None: ...

    def load(self) -> SkillRegistry: ...

    def load_tenant_overrides(self, tenant_id: str) -> list[SkillDefinition]: ...
```

Parser: `frontmatter` lib or `pyyaml` + manual split. `SkillLoadError`
carries file path + parser error; arch test asserts zero.

### 12.6 `SkillResolver` (runtime — which skills to inject)

Location: `backend/src/modules/copilot/application/skills/skill_resolver.py`.

```python
from __future__ import annotations
from dataclasses import dataclass
from src.modules.copilot.domain.skills.skill_definition import SkillDefinition
from src.modules.copilot.domain.ports import CopilotContext


@dataclass(frozen=True, slots=True)
class SkillMatch:
    skill: SkillDefinition
    score: float                        # 0..1
    reason: str                         # "slash_command" | "keyword" | "procedure_active" | "semantic"


class SkillResolver:
    def resolve(
        self,
        *,
        user_message: str,
        context: CopilotContext,
        tenant_id: str,
        limit: int = 3,
    ) -> list[SkillMatch]: ...
```

Resolution precedence: (1) explicit `/slash-command` — score 1.0;
(2) `context.procedure_state.procedure_id` — score 1.0; (3) keyword regex
over `trigger_keywords` (case + accent insensitive) — 0.7–0.9; (4) optional
Qdrant semantic over `description+body` (phase 2) — ≤0.6. Returns top
`limit`, dedup by `name`. Composer (§20) decides inlining.

### 12.7 Initial skill stubs (deliverable files)

5 skill files with frontmatter filled + body stubs. S6 deliverables; must
pass §22 arch tests.

| File | `slash_command` | `procedure_id` | Tools subset |
|---|---|---|---|
| `skills/brand-audit.md` | `/audita-marca` | — | `navigate`, `read_entity`, `web_fetch`, `propose_field_updates` |
| `skills/offer-ladder-builder.md` | `/crea-oferta` | `offer_first_edition` | `read_entity`, `propose_field_updates`, `advance_procedure` |
| `skills/funnel-diagnosis.md` | `/diagnostica-funnel` | — | `read_entity`, `read_metrics`, `navigate` |
| `skills/content-ideas.md` | `/ideas-ig` | — | `read_entity`, `web_fetch` |
| `skills/web-research.md` | `/investiga` | — | `web_fetch`, `delegate` |

Each file must validate `SkillMetadata`, reference only tools that exist in
the `ToolRegistry` (§18), and use `ModelTier` from `domain/model_tier.py`.

### 12.8 Procedure ↔ Skill migration path

Legacy `InterviewConfig` entries in `domain/interview_configs/` become
**skills** with `output_format="procedure"` and a `procedure_id`. The body
of the skill is the interview instructions prompt; the `procedure_tools.py`
entry keyed by `procedure_id` (§6.3) stays the source of truth for bound
tools, so a skill's `allowed_tools` for procedure skills must be a subset of
`PROCEDURE_TOOLS[procedure_id]`.

Order per procedure: (1) write `{procedure_id}.md` mirroring the existing
config prompt; (2) arch test `test_all_procedures_have_skill` (§22) then
passes; (3) keep `InterviewConfig` until orchestrator resolves system prompt
from skill body (S7), then delete config + row.

### 12.9 Invariants

- Skill file = SoT for metadata + body. Never re-inline frontmatter in
  Python constants.
- Frontmatter strict (`extra="forbid"`); unknown keys fail load + arch test.
- `allowed_tools` may NEVER include `"*"` or glob (validator +
  `test_no_wildcard_allowed_tools`).
- Tenant overrides: `tenant_editable=true` only on themselves, `author` =
  tenant UUID.

---

## 13. Copilot Rules Plugin System

Parallel plugin surface for **behavioural rules** injected into system
prompts — global or scoped.

### 13.1 File layout

- Location: `backend/src/modules/copilot/rules/*.md`.
- No tenant override dir in phase 1 (platform guardrails only); future
  two-tier mirrors skills.

### 13.2 `RuleMetadata` (frontmatter)

```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

RuleScope = Literal["global"]  # extended below

class RuleMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9-]*$")
    description: str = Field(min_length=1, max_length=200)
    scope: str = Field(
        pattern=r"^(global|route:[a-z0-9/-]+|skill:[a-z0-9-]+)$",
    )
    priority: int = Field(ge=0, le=100)    # lower = earlier in system prompt
    enforceable: bool = False              # runtime guard emits warning when violated
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
```

Scope grammar:
- `global` — always loaded.
- `route:<prefix>` — loaded when `context.current_route` starts with prefix
  (same prefix matching as `_match_route`).
- `skill:<name>` — loaded only when a skill with that `name` is active for
  the current turn.

### 13.3 `RuleDefinition` + `RuleRegistry`

Location: `backend/src/modules/copilot/domain/rules/`.

```python
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class RuleDefinition:
    metadata: RuleMetadata
    body_markdown: str
    source_path: Path


@runtime_checkable
class RuleRegistry(Protocol):
    def global_rules(self) -> list[RuleDefinition]: ...
    def for_route(self, route: str | None) -> list[RuleDefinition]: ...
    def for_skill(self, skill_name: str) -> list[RuleDefinition]: ...
    def all(self) -> list[RuleDefinition]: ...
```

Loader mirrors §12.5, simpler (no tenant directory). Lives in
`infrastructure/rules_loader.py`.

### 13.4 Initial system rules (deliverable files)

5 rules shipped with the refactor, all `scope: global`, ordered by priority:

| File | priority | enforceable | Purpose |
|---|---|---|---|
| `rules/tenant-isolation.md` | 1 | true | never reference other tenants' data |
| `rules/pii-guardrails.md` | 5 | true | never emit email/phone/etc. in replies |
| `rules/honesty.md` | 10 | false | when data missing, say so — no fabrication |
| `rules/mutation-safety.md` | 15 | true | no mutation without `propose_field_updates` approval |
| `rules/tone-caveman-latam.md` | 20 | false | español neutro latam, caveman concision |

`enforceable=true` rules will in phase 2 be paired with runtime validators
(e.g. PII regex on outbound chunks). Phase 1 only injects text; validator
hook point is the `outbound_text_chunk` interceptor on the orchestrator
stream (stub now, implement S8+).

### 13.5 Invariants

- `scope: skill:<name>` where name missing in `SkillRegistry` → loader
  raises (arch test §22).
- `tone-caveman-latam.md` must cite `.claude/rules/spanish-text.md`.
- Priority ordering stable across boots (ties broken by filename).

---

## 14. Slash Commands

No dedicated surface — slash commands are a view over skills with
`slash_command` set. This keeps "1 file per feature" intact.

### 14.1 Endpoint

```
GET /api/v1/copilot/commands
    Response model: SlashCommandListResponse
```

DTO:

```python
# api/slash_commands_dto.py
from pydantic import BaseModel, ConfigDict

class SlashCommand(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    slug: str                       # e.g. "/audita-marca"
    name: str                       # skill.name (kebab)
    description: str                # skill.description
    icon: str | None = None         # optional lucide icon name

class SlashCommandListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: list[SlashCommand]
```

Backend collects from `SkillRegistry.for_slash_autocomplete(tenant_id=...)`.
Filtered to skills where `slash_command is not None` and, if the skill is
route-gated via metadata (future `allowed_routes`), matches `context.route`
query param when supplied.

### 14.2 Frontend binding

Input detects leading `/` → opens Combobox, fetches `/commands`, filters
client-side. On selection, prepends `slash_command` to the outbound message.
No execution endpoint — skill resolver (§12.6) handles via slash precedence.

### 14.3 Invariants

- `slash_command` uniqueness enforced per tenant by `SkillRegistry.load`
  (collision → load error).
- FE never hardcodes commands — always hydrated from endpoint.

---

## 15. Plan Mode (pre-execution approval)

When a turn is heavy, orchestrator produces a **plan** before executing
tools and pauses until user approves or rejects (Claude Code's Plan Mode) —
caps spend / mutation blast radius.

### 15.1 Triggers

Plan Mode activates when ANY of: `decision.tier == HEAVY`; active skill
has `requires_plan: true`; LLM-returned tool plan has ≥5 mutation field
paths across `propose_field_updates` calls; explicit `/plan` prefix
(reserved slash, not a skill).

### 15.2 New SSE event

Extend `SSEEventType` (already modified in §4.3):

```python
SSEEventType = Literal[
    ...existing...
    "plan_proposed",   # NEW
    "plan_resolved",   # NEW  (optional confirmation/cancellation summary)
]
```

Payloads:

```jsonc
// plan_proposed
{
  "plan_id": "<uuid>",
  "message_id": "<uuid>",
  "steps": [
    {
      "description": "Auditar identidad de marca",
      "tool": "read_entity",
      "args": { "entity": "brand.identity" },
      "estimated_cost_usd": 0.004
    }
  ],
  "total_cost_estimate": 0.027,
  "expires_at": "<iso8601>"
}

// plan_resolved
{ "plan_id": "<uuid>", "decision": "approved" | "rejected" | "expired" }
```

### 15.3 Approval endpoints

```
POST /api/v1/copilot/plan/{plan_id}/approve   -> 204
POST /api/v1/copilot/plan/{plan_id}/reject    -> 204
```

Both: Bearer + `X-Tenant-ID`; filter by `(tenant_id, conversation_id,
plan_id)`; 404 if cross-tenant.

### 15.4 Storage

Column already added to `copilot_conversations.procedure_state` is unrelated.
Add new JSONB column in the conversations alter block (amend §1.1 in a
follow-up migration, not a rewrite):

```python
op.execute("""
    ALTER TABLE copilot_conversations
      ADD COLUMN IF NOT EXISTS plan_state JSONB NULL
""")
```

Shape of `plan_state`:

```python
class PlanState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    plan_id: UUID
    message_id: UUID
    steps: list[PlanStep]
    total_cost_estimate: float
    proposed_at: datetime
    expires_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None

class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    description: str
    tool: str
    args: dict[str, object]
    estimated_cost_usd: float
```

### 15.5 Orchestrator handshake

1. After `tier_decision`, orchestrator asks the LLM for a plan (NANO
   planner call; execution tier unchanged).
2. Emit `plan_proposed`, persist `plan_state`, stream idles with 15s
   `status` heartbeat.
3. `approve` → resume with plan as tool queue. `reject` → `plan_resolved
   (rejected)` + `done`. Expiry 5min → `plan_resolved(expired)` + `done`.

### 15.6 Invariants

- Plan approved at most once (repeat → 409).
- Mutations under a plan journal `plan_id` in `copilot_mutation_journal.extra`
  (add `extra JSONB` column in follow-up migration if missing).
- Plan expiry idempotent — expired plans cannot be revived; user restarts.

---

## 16. Hook System (event bus subscriptions)

Leverages existing `shared/event_bus` — this section adds copilot-specific
events + subscribers.

### 16.1 Copilot events

Location: `backend/src/modules/copilot/domain/hooks/copilot_events.py`. All
events are frozen dataclasses with mandatory `tenant_id: UUID`, `occurred_at:
datetime`.

| Event | Emitted by | Payload highlights |
|---|---|---|
| `ConversationCreated` | `ConversationStore.create` | `conversation_id, user_id` |
| `MessageSent` | API on user POST /chat | `conversation_id, message_id, length` |
| `MessageReceived` | orchestrator on `done` | `conversation_id, message_id, tier, tokens_in/out` |
| `MutationApplied` | mutation journal write | `mutation_id, conversation_id, field_path` |
| `MutationReverted` | revert endpoint | `mutation_id, conversation_id` |
| `ProcedureAdvanced` | `advance_procedure` tool | `procedure_id, block_before, block_after, coverage` |
| `ProcedureCompleted` | orchestrator when coverage==1.0 | `procedure_id, conversation_id` |
| `TierDecided` | router emit | `tier, reason, classifier, confidence, message_id` |
| `PlanProposed` | §15 orchestrator | `plan_id, message_id, steps_count, total_cost` |
| `PlanResolved` | §15 approve/reject/expiry | `plan_id, decision` |

### 16.2 `HookRegistry`

```python
# domain/hooks/hook_registry.py
from __future__ import annotations
from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

HookHandler = Callable[[object], Awaitable[None]]

@runtime_checkable
class HookRegistry(Protocol):
    def subscribe(self, event_type: type, handler: HookHandler, *, name: str) -> None: ...
    def unsubscribe(self, name: str) -> None: ...
    def handlers_for(self, event_type: type) -> list[HookHandler]: ...
```

Concrete impl wraps `shared/event_bus` dispatch. Subscribers run via
`asyncio.create_task` — a slow or failing handler MUST never block the
request path (arch test `test_hooks_never_block` asserts the orchestrator's
emit site uses `create_task`, not `await`).

### 16.3 Initial subscribers (1 file each)

Location: `backend/src/modules/copilot/application/hooks/`.

| File | Event | Purpose |
|---|---|---|
| `rolling_summary_scheduler.py` | `MessageReceived` | set `summary_dirty_at`, spawn summarizer task |
| `title_generator.py` | `MessageSent` (msg #2) | NANO call to produce auto title |
| `routing_telemetry_logger.py` | `TierDecided` | insert `copilot_routing_log` row |
| `nudge_checker.py` | `MessageReceived` | check token thresholds, push SSE status to FE banner |
| `plan_auditor.py` | `PlanResolved` | structlog audit line w/ decision + delta cost |

Registered once at boot via
`infrastructure/hooks/bootstrap.py::register_copilot_hooks(registry)`.

### 16.4 Invariants

- Subscriber name unique; re-registration replaces.
- No subscriber writes to the SSE socket directly — emits domain events or
  enqueues jobs.
- Handler exceptions logged (`copilot.hook_failed`), swallowed, never
  propagate.

---

## 17. Sub-agent Delegation

Claude Code's Task tool, scoped to marketing. Top-level agent spawns
sub-agents via `delegate` builtin.

### 17.1 `SubAgentDefinition`

Location: `backend/src/modules/copilot/domain/sub_agents/sub_agent_definition.py`.

```python
from __future__ import annotations
from dataclasses import dataclass
from src.modules.copilot.domain.model_tier import ModelTier


@dataclass(frozen=True, slots=True)
class SubAgentDefinition:
    name: str                              # kebab, unique
    description: str                       # ≤200 chars, shown to parent LLM
    allowed_tools: tuple[str, ...]         # strict subset (no wildcards)
    default_tier: ModelTier
    system_prompt: str                     # rendered via Jinja2 at call time
    max_turns: int = 8                     # sub-agent loop cap
    timeout_seconds: int = 120
```

Registry: `domain/sub_agents/sub_agent_registry.py` with Protocol mirror of
skills (`get`, `all`). Implementation in
`infrastructure/sub_agents/registry.py` is populated by `@sub_agent`
decorator at import time.

### 17.2 `@sub_agent` decorator

```python
# application/sub_agents/decorator.py
def sub_agent(
    *,
    name: str,
    description: str,
    allowed_tools: tuple[str, ...],
    default_tier: ModelTier = ModelTier.MINI,
    max_turns: int = 8,
    timeout_seconds: int = 120,
) -> Callable[[Callable[..., str]], SubAgentDefinition]: ...
```

The decorated function returns the system prompt (plain str or Jinja2
template). Decoration registers the `SubAgentDefinition` in the module-level
registry.

### 17.3 The `delegate` builtin tool

Exposed to the parent agent:

```python
@copilot_tool(
    name="delegate",
    category="builtin",
    description="Delegate a scoped task to a specialist sub-agent. "
                "Returns the sub-agent's final message as a tool result.",
)
async def delegate(agent_name: str, task: str) -> str: ...
```

The tool (1) looks up `SubAgentDefinition`; (2) builds a LangGraph
sub-graph with tools `allowed_tools ∩ parent_available_tools`; (3) runs up
to `max_turns` / `timeout`; (4) returns final text as tool result; (5) emits
`tool_result` with `data.sub_agent = agent_name`. Child trace shares
`tenant_id` + `conversation_id`, own `message_id`.

### 17.4 Initial sub-agents

Files in `application/sub_agents/`:

| File | name | allowed_tools | Purpose |
|---|---|---|---|
| `web_extractor.py` | `web-extractor` | `web_fetch`, `read_entity` | Fetch + structured extract |
| `brand_auditor.py` | `brand-auditor` | `read_entity`, `web_fetch`, `navigate` | Multi-step brand audit |
| `content_hunter.py` | `content-hunter` | `read_entity`, `web_fetch` | Ideation pipeline |

Each is one file with a `@sub_agent(...)`-decorated function returning the
system prompt. No extra config needed.

### 17.5 Invariants

- `allowed_tools` is always a strict subset of the parent's available
  tools; runtime intersects. Empty ⇒ `delegate` returns
  `{ "error": "no_tools_available" }` (no LLM call).
- No nested delegation in phase 1 (`delegate` forbidden in any
  `SubAgentDefinition.allowed_tools` — arch test enforces).
- Sub-agent tier may differ from parent; `TierDecided` logged with
  `reason="sub_agent:<name>"`, `classifier_used="default"`.

---

## 18. Tool Plugin Architecture

Current `registry.py` hand-maintains groups + `ROUTE_TOOL_MAP`. Plugin
refactor flips this: tools self-register via decorator; registry = set of
all decorated callables at import time.

### 18.1 `ToolDescriptor`

Location: `backend/src/modules/copilot/domain/tools/tool_descriptor.py`.

```python
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

ToolCategory = Literal["builtin", "procedure", "provider", "skill"]


class ToolDescriptor(BaseModel):
    """Plugin-registered tool metadata.

    Thin superset of LangChain @tool. The actual callable lives in
    `handler`, but we never serialize it — only the descriptor is wire-
    visible (e.g. for /capabilities introspection).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    name: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1, max_length=400)
    category: ToolCategory
    routes: tuple[str, ...] = Field(default_factory=tuple)   # prefixes; empty = all
    required_scopes: tuple[str, ...] = Field(default_factory=tuple)
    procedure_ids: tuple[str, ...] = Field(default_factory=tuple)  # for category=procedure
    skill_names: tuple[str, ...] = Field(default_factory=tuple)    # for category=skill
    provider: str | None = None                              # for category=provider
    dangerous: bool = False                                  # triggers Plan Mode if ≥1 in plan
    ui_action_types: tuple[str, ...] = Field(default_factory=tuple)
    handler: object                                          # the @tool-decorated callable
```

### 18.2 `@copilot_tool` decorator

Location: `backend/src/modules/copilot/application/tools/decorator.py`.

```python
from __future__ import annotations
from typing import Callable

def copilot_tool(
    *,
    name: str,
    description: str,
    category: ToolCategory,
    routes: tuple[str, ...] = (),
    required_scopes: tuple[str, ...] = (),
    procedure_ids: tuple[str, ...] = (),
    skill_names: tuple[str, ...] = (),
    provider: str | None = None,
    dangerous: bool = False,
    ui_action_types: tuple[str, ...] = (),
) -> Callable: ...
```

Semantics:
- Wraps the target in LangChain `@tool` (keeps existing contract).
- Constructs a `ToolDescriptor` and appends it to the module-level
  `ToolRegistry` on import.
- Emits a structured log at registration in debug mode.

### 18.3 `ToolRegistry`

Location: `backend/src/modules/copilot/domain/tools/tool_registry.py` (Protocol)
+ `infrastructure/tools/registry_impl.py` (default, in-memory dict).

```python
@runtime_checkable
class ToolRegistry(Protocol):
    def register(self, descriptor: ToolDescriptor) -> None: ...
    def get(self, name: str) -> ToolDescriptor | None: ...
    def all(self) -> list[ToolDescriptor]: ...
    def by_category(self, category: ToolCategory) -> list[ToolDescriptor]: ...
    def for_route(self, route: str | None) -> list[ToolDescriptor]: ...
    def for_procedure(self, procedure_id: str) -> list[ToolDescriptor]: ...
    def for_skill(self, skill_name: str) -> list[ToolDescriptor]: ...
```

### 18.4 Migration of existing registry.py

The existing `ROUTE_TOOL_MAP` + `TOOL_GROUPS` table is replaced by:

1. Existing tool files add `@copilot_tool(..., routes=(...,))` per tool.
2. `TOOL_GROUPS` + `ROUTE_TOOL_MAP` deleted.
3. `get_tools_for_route(route)` → thin wrapper over `ToolRegistry.for_route`.
4. `get_tools_for_context(ctx)` composes `for_route + for_procedure +
   for_skill`, dedup by `name`.

Per-route bindings live on the tool. Adding tools never edits `registry.py`.

### 18.5 Auto-discovery at boot

`infrastructure/tools/bootstrap.py::load_all_tools()` force-imports every
tool module so decorators fire (explicit list or `pkgutil.walk_packages`).
Arch test asserts every `.py` under `application/tools/` (except
`__init__.py`, `registry.py`, `decorator.py`) is imported by bootstrap.

### 18.6 Invariants

- `ToolDescriptor.name` unique (collision at decoration → error).
- `category="provider"` ⇒ `provider` non-null; `"procedure"` ⇒
  `procedure_ids` non-empty; `"skill"` ⇒ `skill_names` non-empty.
- No wildcard in `routes`, `procedure_ids`, `skill_names`, `required_scopes`.

---

## 19. MCP-style External Provider Tools

Provider tools (ManyChat, Meta, Shopify, Gmail, Mailerlite, Telegram, …)
share an adapter base: credential/health preflight, structured error
envelope, one-line registration per method.

### 19.1 `ProviderToolAdapter` (base)

Location: `backend/src/modules/copilot/infrastructure/mcp/provider_tool_adapter.py`.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ProviderToolResult:
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None        # stable codes: "not_connected" | "auth_expired" | "rate_limited" | "unknown"
    error_detail: str | None = None


class ProviderToolAdapter(ABC):
    provider: str                    # "manychat" | "meta" | "shopify" | ...

    async def preflight(self, *, tenant_id: UUID) -> ProviderToolResult | None:
        """Check connection + token health. Returns error result or None."""

    @abstractmethod
    async def run(
        self,
        *,
        tenant_id: UUID,
        action: str,
        args: dict[str, Any],
    ) -> ProviderToolResult: ...
```

Concrete adapters: `infrastructure/mcp/manychat_adapter.py`, `meta_adapter.py`,
`shopify_adapter.py`, one file each. Reuse existing provider clients from
`modules/connections/` via the existing port in `shared/links/`.

### 19.2 Tool registration helper

```python
# application/tools/provider_tools.py
def register_provider_tool(
    *,
    adapter: ProviderToolAdapter,
    action: str,
    name: str,
    description: str,
    routes: tuple[str, ...] = (),
    dangerous: bool = False,
) -> None:
    @copilot_tool(
        name=name,
        description=description,
        category="provider",
        provider=adapter.provider,
        routes=routes,
        dangerous=dangerous,
    )
    async def _tool(args: dict) -> dict:
        tenant_id = current_tenant_id()
        pre = await adapter.preflight(tenant_id=tenant_id)
        if pre is not None:
            return pre.__dict__
        result = await adapter.run(tenant_id=tenant_id, action=action, args=args)
        return result.__dict__
```

One call per (adapter, action) pair registers a tool. Adding a new provider
method = one `register_provider_tool(...)` line.

### 19.3 Error envelope (runtime contract)

Returned under `tool_result.data` when `ok=false`:

```jsonc
{
  "ok": false,
  "error": "auth_expired",
  "error_detail": "manychat token refresh failed (401)"
}
```

The FE MUST render a dedicated "reconnect provider" card for
`error in { not_connected, auth_expired }`.

### 19.4 Invariants

- Adapters never raise from `run()` — always return `ProviderToolResult`.
- `preflight` runs before every invocation, cached per-request via FastAPI
  `Depends` for same tenant+provider within one turn.
- No provider-specific error codes leak — always map to the stable enum.

---

## 20. File Layout (augmented)

Extends §9. Only NEW or RENAMED paths shown.

```
backend/src/modules/copilot/
├── domain/
│   ├── skills/
│   │   ├── skill_metadata.py        # NEW §12.2
│   │   ├── skill_definition.py      # NEW §12.3
│   │   └── skill_registry.py        # NEW §12.4 (Protocol)
│   ├── rules/
│   │   ├── rule_metadata.py         # NEW §13.2
│   │   ├── rule_definition.py       # NEW §13.3
│   │   └── rule_registry.py         # NEW §13.3 (Protocol)
│   ├── tools/
│   │   ├── tool_descriptor.py       # NEW §18.1
│   │   └── tool_registry.py         # NEW §18.3 (Protocol)
│   ├── hooks/
│   │   ├── copilot_events.py        # NEW §16.1 (frozen dataclasses)
│   │   └── hook_registry.py         # NEW §16.2 (Protocol)
│   └── sub_agents/
│       ├── sub_agent_definition.py  # NEW §17.1
│       └── sub_agent_registry.py    # NEW §17 (Protocol)
├── infrastructure/
│   ├── skills_loader.py             # NEW §12.5
│   ├── rules_loader.py              # NEW §13.3
│   ├── tools/
│   │   ├── registry_impl.py         # NEW §18.3 in-memory impl
│   │   └── bootstrap.py             # NEW §18.5 auto-import
│   ├── hooks/
│   │   └── bootstrap.py             # NEW §16.3 register_copilot_hooks
│   ├── sub_agents/
│   │   └── registry.py              # NEW §17 in-memory impl
│   └── mcp/
│       ├── provider_tool_adapter.py # NEW §19.1 base
│       ├── manychat_adapter.py      # NEW (stubs OK for S-plugin)
│       ├── meta_adapter.py          # NEW
│       └── shopify_adapter.py       # NEW
├── application/
│   ├── skills/
│   │   └── skill_resolver.py        # NEW §12.6
│   ├── rules/                       # reserved for future (runtime enforcers)
│   ├── tools/
│   │   ├── decorator.py             # NEW §18.2 @copilot_tool
│   │   ├── provider_tools.py        # NEW §19.2 register_provider_tool
│   │   └── registry.py              # EDIT  thin wrapper over ToolRegistry
│   ├── hooks/
│   │   ├── rolling_summary_scheduler.py  # NEW §16.3
│   │   ├── title_generator.py            # MOVED from services/ §16.3
│   │   ├── routing_telemetry_logger.py   # NEW §16.3
│   │   ├── nudge_checker.py              # NEW §16.3
│   │   └── plan_auditor.py               # NEW §16.3
│   ├── sub_agents/
│   │   ├── decorator.py             # NEW §17.2 @sub_agent
│   │   ├── web_extractor.py         # NEW §17.4
│   │   ├── brand_auditor.py         # NEW §17.4
│   │   └── content_hunter.py        # NEW §17.4
│   └── orchestrator/
│       ├── chat.py                  # EDIT §8 + plan mode §15
│       └── system_prompt_composer.py # NEW §20.1
├── skills/                          # NEW §12.7 (5 .md files)
│   ├── brand-audit.md
│   ├── offer-ladder-builder.md
│   ├── funnel-diagnosis.md
│   ├── content-ideas.md
│   └── web-research.md
└── rules/                           # NEW §13.4 (5 .md files)
    ├── tone-caveman-latam.md
    ├── pii-guardrails.md
    ├── tenant-isolation.md
    ├── honesty.md
    └── mutation-safety.md
```

### 20.1 System Prompt Composer

Location: `backend/src/modules/copilot/application/orchestrator/system_prompt_composer.py`.

Composition order (top → bottom), produced as a single system message:

```
1. base_header                       # "You are Nicolify's copilot. Español LatAm."
2. global_rules                      # RuleRegistry.global_rules(), priority asc
3. route_rules                       # RuleRegistry.for_route(ctx.current_route)
4. active_skill_bodies               # top N from SkillResolver.resolve(...)
5. skill_rules                       # RuleRegistry.for_skill(s.name) for each s in (4)
6. tenant_context_block              # business_types, brand identity snippet, locale
7. conversation_summary              # conversation.summary if present
8. last_N_messages                   # raw window from §2.3
```

Signature:

```python
class SystemPromptComposer:
    async def compose(
        self,
        *,
        conversation: ConversationSummaryVO,
        context: CopilotContext,
        active_skills: list[SkillDefinition],
        tenant_id: UUID,
    ) -> list[LLMMessage]: ...
```

Stable-prefix cache key (sections 1–5): hash over rule + skill versions.
Section 6+ is per-conversation, not cacheable.

---

## 21. Scalability Checklist

Each of the following is a single-file change. Arch tests §22 assert that the
addition of a new X does not force edits to any other file beyond what the
checklist names.

- [ ] **Add a skill** — 1 file under `backend/src/modules/copilot/skills/*.md`.
      Dev: watcher reloads. Prod: next boot.
- [ ] **Add a tool** — 1 file under `application/tools/*.py` with a
      `@copilot_tool(...)` decorator. Bootstrap auto-imports.
- [ ] **Add a rule** — 1 file under `backend/src/modules/copilot/rules/*.md`.
- [ ] **Add a slash command** — add `slash_command:` key to an existing
      skill's frontmatter. Nothing else.
- [ ] **Add a provider tool** — 1 adapter class extending
      `ProviderToolAdapter` + one `register_provider_tool(...)` call per
      action.
- [ ] **Add a hook subscriber** — 1 file under `application/hooks/*.py`
      and one line in `infrastructure/hooks/bootstrap.py::register_copilot_hooks`.
- [ ] **Add a sub-agent** — 1 file under `application/sub_agents/*.py` with
      a `@sub_agent(...)` decorator.
- [ ] **Add a model tier** — 1 enum member in `ModelTier` + 1 row in
      `TIER_METADATA`.
- [ ] **Add a routing rule** — 1 `RoutingRule(...)` entry in the
      `DEFAULT_ROUTING_POLICY.rules` tuple.
- [ ] **Add a tenant skill override** — drop
      `skills_tenant/{tenant_id}/*.md`. No code.

---

## 22. Arch Tests for Plugin Integrity

Location: `backend/tests/architecture/test_copilot_plugins.py` (splittable
per concern as count grows).

| Test | Enforces |
|---|---|
| `test_all_skills_valid_frontmatter` | Every `.md` in `skills/` parses; `SkillMetadata` validates. Zero load errors. |
| `test_all_skill_allowed_tools_exist` | For each skill, every entry in `allowed_tools` matches a `ToolDescriptor.name` in the registry. |
| `test_procedure_skill_tools_subset_of_bundle` | For skills with `procedure_id`, `allowed_tools ⊆ PROCEDURE_TOOLS[procedure_id]` (names). |
| `test_all_rules_valid_frontmatter` | Every `.md` in `rules/` parses; `RuleMetadata` validates. |
| `test_rule_skill_scope_targets_exist` | Every rule with `scope=skill:<name>` references an existing skill. |
| `test_rule_route_scope_targets_exist` | Every rule with `scope=route:<prefix>` — prefix appears in `ROUTE_TOOL_MAP` or matches a known navigation prefix in `navigation_map.py`. |
| `test_all_tool_routes_match_navigation_map` | For every `ToolDescriptor.routes` entry, the prefix is a key in `ROUTE_TOOL_MAP` or its fallback (`"*"`). |
| `test_no_wildcard_allowed_tools` | No skill, rule, or sub-agent has `"*"` or glob in `allowed_tools`. |
| `test_all_procedures_have_skill` | Every `procedure_id` referenced by `ProcedureState` or `PROCEDURE_TOOLS.keys()` has a matching skill file. |
| `test_tool_names_unique` | Decorator registration never duplicates a name. |
| `test_tools_bootstrap_imports_all_files` | Every `.py` under `application/tools/` except excluded utility modules is imported by `bootstrap.load_all_tools`. |
| `test_provider_tools_have_adapter` | Every `ToolDescriptor(category="provider")` has `provider` matching a known `ProviderToolAdapter.provider`. |
| `test_sub_agents_allowed_tools_exist` | Every sub-agent's `allowed_tools` are registered names. |
| `test_no_nested_delegation` | No sub-agent's `allowed_tools` includes `"delegate"`. |
| `test_hooks_never_block` | AST check: orchestrator emit sites for copilot events use `asyncio.create_task` (no bare `await`). |
| `test_slash_command_uniqueness` | No two skills share a `slash_command` for the same tenant scope. |

Ratchet: allowlists only shrink (consistent with §10). New skill/tool/rule
that fails tests must be fixed, not allowlisted.

