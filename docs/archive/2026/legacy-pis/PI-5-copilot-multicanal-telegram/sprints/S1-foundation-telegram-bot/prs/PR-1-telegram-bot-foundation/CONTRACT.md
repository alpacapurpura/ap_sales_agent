# CONTRACT — PR-1-telegram-bot-foundation

> Architect run: 2026-04-30 (PM main thread direct, post architect agent timeout). SSoT pre-implementación. Builders agentic + frontend consumen este archivo en paralelo.

## §0 Context Summary

| Campo | Valor |
|---|---|
| PR | PR-1-telegram-bot-foundation (PI-5 S1) |
| Architect run | 2026-04-30 (PM main thread, Opus 4.7[1M]) |
| Surface scope | cross-stack: agentic (copilot module) + frontend |
| Surface ownership | `modules/copilot/**` → `nicolify-agentic` (Opus) + `nicolify-agentic-auditor`. `frontend/src/**` → `nicolify-frontend` (Sonnet) + `nicolify-frontend-auditor` |
| Modules touched | copilot (primary), shared (READ reuse), core (EXTEND Settings), frontend (NEW route group + features extension) |
| Modules NOT touched | sales_agent, connections, brand, offer, analytics, advertising, social_media, scheduling, iam, crm — D-PI5-005 separación física |
| CONTEXT-BRIEF source | § 7 + § 8 + § 12 ya verificados, faithfulness clean |
| Skills consulted | copilot-expert, tessl__langgraph (referencia), tessl__fastapi, tessl__graceful-degradation (rate limit + circuit breaker patterns), frontend-expert, tessl__zod, tessl__react-patterns, tessl__shadcn-ui |
| State-of-the-art validation | Telegram Bot API docs + Anthropic prompt caching docs validated 2026-04-30 (research file §5 §6). LangGraph N/A para PR-1 (HITL = S3) |

## §1 Existing Systems Audit (NO-NEW-LAYER rule applied)

Verbatim grep evidence en `CONTEXT-BRIEF.md` § 7 + § 13. Mechanical rule (≥80% overlap → EXTEND, <40% → NEW).

| Sistema | Path | Decisión | Razón |
|---|---|---|---|
| Sales_agent telegram adapter | `src/modules/connections/infrastructure/channels/telegram.py` | **NEW** copilot adapter | D-PI5-005 separación física inviolable. Adapter sales_agent usa `settings.TELEGRAM_BOT_TOKEN` + per-tenant via `connection_id`; copilot usa `COPILOT_TELEGRAM_BOT_TOKEN` global |
| Sales_agent telegram webhook | `src/modules/connections/api/telegram.py` | **NEW** copilot router | Mismo módulo distinto. Pattern reference (no imports). Sales_agent usa `BackgroundTasks` (sync inline); copilot usa ARQ enqueue (D-PI5-026 NON-BLOCKING) |
| Whatsapp webhook pattern | `src/modules/connections/api/whatsapp.py` | **REFERENCE only** | Pattern FastAPI router GET verify + POST handle |
| `escape_markdown_v2` | `src/shared/agent_observability/channels/format.py` | **REUSE** import | Utility puro |
| `sanitize_payload` | `src/shared/agent_observability/recording/sanitization.py` | **REUSE** import | Utility puro PII |
| ARQ stack | `src/core/arq_pool.py` + `src/workers/settings.py` | **EXTEND** | Registrar nueva async function `process_copilot_telegram_turn` en `WorkerSettings.functions` |
| `ConversationalChannelPort` | `src/shared/links/ports/conversational_channel.py` | **NEW pattern paralelo** | Port abstract para flow guided wizard "render question" — no aplicable webhook/orchestrator. Bot adapter clase concreta (KISS) |
| Tool registry | `src/modules/copilot/application/tools/registry.py` | **EXTEND** | Añadir `ToolGroupMeta` dataclass + filtro `channel` en `get_tools_for_context()` |
| Settings | `src/core/config.py` | **EXTEND** | Añadir 3 env vars |
| `CopilotConversationModel` | `src/modules/copilot/infrastructure/models/conversation_model.py` | **EXTEND** cols + index | Misma tabla, distinto `channel_type` |
| `check_rate_limit` (Redis sliding window) | `src/core/rate_limit.py` | **REFERENCE only** | Aplica a inbound API per-user; outbound bot send_message es Telegram API global limit (30/sec) — `asyncio.Semaphore` in-process es correcto |

**Por qué los existentes NO sirven (NEW justification):**
- Acoplar copilot bot adapter a `connections/.../telegram.py` rompe D-PI5-005 separación física → bot copilot ≠ bot sales_agent (distinto token, distinto webhook, distinta voz). Costo escala 1000+ tenants: confusión auth/persistence/billing.
- `BackgroundTasks` FastAPI no son durables (proceso muere → mensaje perdido). ARQ + Redis = durable + retry + observable.
- `ConversationalChannelPort.ask(contract)` recibe `FieldContract` para wizard guided — semántica wrong para un orchestrator que envía free-form text al usuario.

## §2 Domain entities

### `copilot/domain/telegram.py` (NEW)

```python
"""Telegram channel domain entities.

PI-5 PR-1: bot global Nicolify per D-PI5-001. Cero acoplamiento
sales_agent (D-PI5-005).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal


class ChannelType(str, Enum):
    """Canales soportados por copilot. MVP solo telegram."""

    TELEGRAM = "telegram"
    # WHATSAPP = "whatsapp"  # PI-6 futuro


class ChannelLinkRole(str, Enum):
    """Roles per (tenant, channel_user). MVP solo owner."""

    OWNER = "owner"
    # ASSISTANT = "assistant"           # PI futuro
    # FINANCE_ADMIN = "finance_admin"   # PI futuro
    # MARKETING_LEAD = "marketing_lead" # PI futuro


@dataclass(frozen=True, slots=True)
class TelegramChatId:
    """Numeric Telegram from_user.id (immutable identity).

    Stored as string in DB to avoid bigint overflow concerns in JSON
    serialization (Telegram chat_ids exceed JSON safe integer in some
    edge cases).
    """

    value: str  # numeric Telegram chat_id (private DM == from_user.id)


@dataclass(frozen=True, slots=True)
class ChannelLink:
    """Inmutable lookup row: chat_id ↔ tenant + user + role."""

    id: str  # UUID
    tenant_id: str
    user_id: str
    channel_type: ChannelType
    channel_user_id: str  # Telegram from_user.id (numeric as string)
    channel_username: str | None  # @handle (mutable, display only)
    role: ChannelLinkRole
    linked_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None  # soft delete
```

### `copilot/domain/telegram_link_token.py` (NEW)

```python
@dataclass(frozen=True, slots=True)
class LinkToken:
    """Single-use HMAC-SHA256 token for chat_id ↔ tenant linking.

    Ephemeral. Hash stored in DB (not plaintext). TTL = 15 min default
    (configurable via Settings.COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS).
    """

    id: str  # UUID
    token_hash: str  # SHA256 hex digest of token (NOT plaintext)
    tenant_id: str
    user_id: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime
```

## §3 API endpoints

### Pydantic v2 DTOs (`copilot/api/telegram_dto.py`)

```python
"""Pydantic v2 DTOs for /api/v1/copilot/telegram/*."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ── Inbound webhook (Telegram → us) ──────────────────────────────────────

class TelegramFrom(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    is_bot: bool
    username: str | None = None
    first_name: str | None = None  # NO persist (PII)
    last_name: str | None = None  # NO persist (PII)


class TelegramChat(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    type: Literal["private", "group", "supergroup", "channel"]


class TelegramMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    message_id: int
    from_: TelegramFrom = Field(alias="from")
    chat: TelegramChat
    text: str | None = None
    date: int  # Unix timestamp


class TelegramUpdate(BaseModel):
    """Telegram Bot API Update (subset we care about).

    Reference: https://core.telegram.org/bots/api#update
    Filter: only `message` field where `chat.type == "private"`. Others
    ignored at handler.
    """

    model_config = ConfigDict(extra="ignore")
    update_id: int
    message: TelegramMessage | None = None


class WebhookAck(BaseModel):
    """Always 200 OK to Telegram (D-PI5-026 NON-BLOCKING)."""

    model_config = ConfigDict(extra="forbid")
    ok: bool = True


# ── Magic link (web FE → us → bot) ────────────────────────────────────────

class LinkTokenRequest(BaseModel):
    """Empty body (auth via X-Tenant-ID + Clerk JWT)."""

    model_config = ConfigDict(extra="forbid")


class LinkTokenResponse(BaseModel):
    """Returned to FE. Plaintext token never persisted in DB."""

    model_config = ConfigDict(extra="forbid")
    token_id: UUID
    deep_link_url: HttpUrl  # t.me/<bot_username>?start=<token_plaintext>
    expires_at: datetime


class LinkStatusResponse(BaseModel):
    """Polled by FE every 3s × 60s."""

    model_config = ConfigDict(extra="forbid")
    linked: bool
    channel_user_id_masked: str | None = None  # "12345****" (NO full chat_id leak)
    linked_at: datetime | None = None


class UnlinkResponse(BaseModel):
    """Soft delete (revoked_at set)."""

    model_config = ConfigDict(extra="forbid")
    revoked: bool = True
```

### Endpoints

| Method | Path | Auth | Request | Response (response_model) | Status codes | Notes |
|---|---|---|---|---|---|---|
| POST | `/api/v1/copilot/telegram/webhook` | Header `X-Telegram-Bot-Api-Secret-Token` | `TelegramUpdate` | `WebhookAck` | 200 always (NON-BLOCKING), 401 si secret missing/invalid | D-PI5-026 NON-BLOCKING. Filter `chat.type=='private'`. Enqueue ARQ |
| POST | `/api/v1/copilot/telegram/link-tokens` | Clerk JWT + X-Tenant-ID | `LinkTokenRequest` (empty) | `LinkTokenResponse` | 201, 401, 403 | Genera HMAC token, hash en DB |
| GET | `/api/v1/copilot/telegram/link-status?token_id={uuid}` | Clerk JWT + X-Tenant-ID | query param | `LinkStatusResponse` | 200, 401, 404 token expired/unknown | FE polling 3s × 60s |
| DELETE | `/api/v1/copilot/telegram/link` | Clerk JWT + X-Tenant-ID | — | `UnlinkResponse` | 200, 401, 404 | Soft delete (set `revoked_at`) |

**Tenant isolation:** all endpoints (excepto webhook) extraen `tenant_id` from `X-Tenant-ID` header (existing middleware). Repos filter `WHERE tenant_id = :tenant_id` siempre.

**Webhook NO tiene tenant_id en URL** — el `chat_id` resuelve `(tenant_id, user_id)` via `copilot_channel_links` lookup. Sin link → response template "andá a tu cuenta" (anti-pattern A11 mitigation: bot sin link no expone tenant data).

## §4 DB schema

### Migration `alembic/versions/{timestamp}_pi5_pr1_copilot_telegram_foundation.py` (idempotente)

```python
"""PI-5 PR-1 — Copilot Telegram foundation: channel_links, link_tokens, conversation cols.

Revision ID: {generated}
Revises: {previous head}
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op


def upgrade() -> None:
    """All operations idempotent (rule backend-migrations.md)."""

    # 1. copilot_channel_links — chat_id ↔ tenant + user + role
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_channel_links (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            channel_user_id VARCHAR(64) NOT NULL,
            channel_username VARCHAR(64),
            role VARCHAR(32) NOT NULL DEFAULT 'owner',
            linked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen_at TIMESTAMPTZ,
            revoked_at TIMESTAMPTZ,
            CONSTRAINT uq_copilot_channel_link_chat
                UNIQUE (tenant_id, channel_type, channel_user_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_channel_links_lookup "
        "ON copilot_channel_links(channel_type, channel_user_id) "
        "WHERE revoked_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_channel_links_tenant "
        "ON copilot_channel_links(tenant_id) WHERE revoked_at IS NULL"
    )

    # 2. copilot_link_tokens — single-use HMAC magic link
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_link_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token_hash VARCHAR(128) NOT NULL,
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            used_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_copilot_link_token_hash UNIQUE (token_hash)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_link_tokens_lookup "
        "ON copilot_link_tokens(token_hash, expires_at) WHERE used_at IS NULL"
    )

    # 3. copilot_conversations — extend with channel_type + channel_chat_id
    op.execute(
        "ALTER TABLE copilot_conversations "
        "ADD COLUMN IF NOT EXISTS channel_type VARCHAR(32)"
    )
    op.execute(
        "ALTER TABLE copilot_conversations "
        "ADD COLUMN IF NOT EXISTS channel_chat_id VARCHAR(64)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_conversations_channel "
        "ON copilot_conversations(channel_type, channel_chat_id) "
        "WHERE channel_type IS NOT NULL"
    )


def downgrade() -> None:
    """Reverse upgrade — best effort. Cols remain (legacy data)."""
    op.execute("DROP TABLE IF EXISTS copilot_link_tokens")
    op.execute("DROP TABLE IF EXISTS copilot_channel_links")
    # NOTE: cols channel_type/channel_chat_id NOT dropped (avoid data loss)
```

**Cero FK cruzada con `sales_agent_*`** — arch fitness test enforce.

## §5 Settings (env vars EXTEND `core/config.py`)

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # ── Copilot Telegram bot (PI-5 PR-1) ────────────────────────────
    # Global Nicolify bot — DISTINTO de TELEGRAM_BOT_TOKEN (sales_agent).
    # D-PI5-001 + D-PI5-005 separación física.
    COPILOT_TELEGRAM_BOT_TOKEN: str = ""
    # Random secret validated en webhook header
    # X-Telegram-Bot-Api-Secret-Token. Generar con
    # `secrets.token_urlsafe(32)`. Setear via setWebhook con secret_token.
    COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN: str = ""
    # TTL magic link (default 15 min) — D-PI5-019
    COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS: int = 900
    # Bot username (display only — usado para construir deep link)
    COPILOT_TELEGRAM_BOT_USERNAME: str = "nicolify_copilot_bot"
    # API URL pública para construir webhook URL al registrar
    # (ya existe `API_URL` en Settings — reutilizar)
```

## §6 Bot adapter

### `copilot/infrastructure/channels/telegram_bot.py` (NEW)

```python
"""Copilot Telegram bot adapter — global Nicolify, NOT per-tenant.

D-PI5-001 + D-PI5-005 + D-PI5-027 (rate limiting). Reuses
`escape_markdown_v2` from shared (NO duplica).

NOTE: `connections/.../telegram.py` (sales_agent) NO se importa.
Cero shared state.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Final

import httpx
import structlog

from src.core.config import settings
from src.shared.agent_observability.channels.format import escape_markdown_v2

_LOGGER = structlog.get_logger(__name__)

# Telegram Bot API limits (D-PI5-027)
_GLOBAL_MAX_PER_SEC: Final[int] = 30
_TELEGRAM_API_BASE: Final[str] = "https://api.telegram.org/bot"
_HTTP_TIMEOUT_SECONDS: Final[float] = 10.0
_MAX_TEXT_CHARS: Final[int] = 4096


class CopilotTelegramBot:
    """Outbound bot client. Singleton per process."""

    _global_semaphore: asyncio.Semaphore = asyncio.Semaphore(_GLOBAL_MAX_PER_SEC)
    _chat_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __init__(self, token: str | None = None) -> None:
        self._token = token or settings.COPILOT_TELEGRAM_BOT_TOKEN
        if not self._token:
            raise RuntimeError(
                "COPILOT_TELEGRAM_BOT_TOKEN not set in Settings"
            )

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
        reply_markup: dict | None = None,
    ) -> None:
        """Send message with global + per-chat rate limiting + retry."""

        if parse_mode == "MarkdownV2":
            text = escape_markdown_v2(text)

        # Truncate if exceeds 4096 chars (Telegram limit)
        if len(text) > _MAX_TEXT_CHARS:
            text = text[: _MAX_TEXT_CHARS - 1] + "…"

        chat_lock = self._chat_locks[chat_id]
        async with self._global_semaphore:
            async with chat_lock:
                await self._send_with_retry(chat_id, text, parse_mode, reply_markup)
                # Sustain global rate (1/30 sec slot)
                await asyncio.sleep(1.0 / _GLOBAL_MAX_PER_SEC)

    async def _send_with_retry(
        self,
        chat_id: str,
        text: str,
        parse_mode: str,
        reply_markup: dict | None,
    ) -> None:
        """HTTP POST sendMessage with timeout + 1 retry on 429/5xx."""
        # ... implementation: httpx.AsyncClient with timeout=10s,
        # exponential backoff, structlog warning on failures (graceful
        # degradation per tessl__graceful-degradation rule).
        ...
```

### `copilot/infrastructure/channels/telegram_link_service.py` (NEW)

```python
"""HMAC-SHA256 magic link service — D-PI5-019..022."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.core.config import settings
# Repository → AsyncSession via DI


def generate_link_token(tenant_id: str, user_id: str) -> tuple[str, str, datetime]:
    """Generate plaintext token + hash + expires_at.

    Returns:
        (plaintext_token, token_hash, expires_at)

    Plaintext returned ONCE to caller — caller embeds in deep_link_url.
    Hash stored in DB. Plaintext discarded after.
    """
    plaintext = secrets.token_urlsafe(32)
    # HMAC-SHA256 with app secret = anti-forge guard
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        plaintext.encode(),
        hashlib.sha256,
    ).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS,
    )
    return plaintext, digest, expires_at


def hash_token_plaintext(plaintext: str) -> str:
    """Validate inbound /start TOKEN by hashing it back."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        plaintext.encode(),
        hashlib.sha256,
    ).hexdigest()


def build_deep_link_url(plaintext_token: str) -> str:
    """t.me/<bot_username>?start=<plaintext>."""
    return f"https://t.me/{settings.COPILOT_TELEGRAM_BOT_USERNAME}?start={plaintext_token}"
```

## §7 ARQ worker

### `copilot/infrastructure/workers/telegram_worker.py` (NEW)

```python
"""ARQ worker job: process_copilot_telegram_turn.

D-PI5-026 NON-BLOCKING contract. Webhook handler enqueues a payload
< 200ms; this worker processes LLM async + sends response via bot.
"""

from typing import Any

import structlog

from src.core.database import session_factory
from src.modules.copilot.application.orchestrator import (
    invoke_copilot_orchestrator,  # existing function — añadir param channel
)
from src.modules.copilot.application.services.telegram_link_service import (
    resolve_chat_id_to_tenant_user,
    send_unlinked_cta_response,
)
from src.modules.copilot.infrastructure.channels.telegram_bot import (
    CopilotTelegramBot,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload

_LOGGER = structlog.get_logger(__name__)


async def process_copilot_telegram_turn(
    ctx: dict,
    payload: dict[str, Any],
) -> None:
    """Process inbound Telegram message.

    payload schema (sanitized): {
        "update_id": int,
        "chat_id": str (numeric as str),
        "message_id": int,
        "text": str,
        "received_at": ISO datetime str,
    }

    Steps:
    1. sanitize_payload(payload)  # ya hecho en handler, defense in depth
    2. Resolve chat_id → channel_link → (tenant_id, user_id, role) | None
    3. If unlinked AND text starts with "/start TOKEN":
        - Validate token (hash + TTL + unused) → bind chat_id → reply success
       Else if unlinked:
        - send_unlinked_cta_response(chat_id) with onboarding URL
       Else (linked):
        - Update last_seen_at
        - Invoke orchestrator with channel='telegram', tenant_id, user_id
        - Send response via bot (escape_markdown_v2 inside bot.send_message)
    4. structlog with try/except — never raise to ARQ (graceful degrade)
    """
    ...
```

### Worker registration (`workers/settings.py` EXTEND)

```python
class WorkerSettings:
    functions = [
        # ... existing
        process_copilot_telegram_turn,  # NEW
    ]
```

## §8 Webhook router

### `copilot/api/telegram.py` (NEW)

```python
"""Copilot Telegram webhook + magic link endpoints.

D-PI5-026 NON-BLOCKING + D-PI5-028 secret_token + D-PI5-029 private only.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_async_db
from src.core.arq_pool import get_arq_pool
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.copilot.api.telegram_dto import (
    LinkStatusResponse,
    LinkTokenRequest,
    LinkTokenResponse,
    TelegramUpdate,
    UnlinkResponse,
    WebhookAck,
)
from src.modules.copilot.application.services.telegram_link_service import (
    generate_link_token,
    build_deep_link_url,
    create_link_token,
    fetch_link_status,
    revoke_chat_link,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload

router = APIRouter(prefix="/api/v1/copilot/telegram", tags=["copilot-telegram"])
_LOGGER = structlog.get_logger(__name__)


@router.post("/webhook", response_model=WebhookAck, status_code=status.HTTP_200_OK)
async def copilot_telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> WebhookAck:
    """Telegram → Nicolify webhook. NON-BLOCKING enqueue ARQ."""

    # D-PI5-028 secret validation (anti-pattern A10)
    if x_telegram_bot_api_secret_token != settings.COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN:
        _LOGGER.warning("copilot_telegram_webhook_unauthorized")
        raise HTTPException(status_code=401, detail="Invalid secret token")

    # D-PI5-029 filter private chats only (anti-pattern A11)
    msg = update.message
    if msg is None or msg.chat.type != "private":
        return WebhookAck()  # silent ignore (still 200 to Telegram)

    # D-PI5-030 sanitize before persist/log (anti-pattern A3)
    payload = sanitize_payload({
        "update_id": update.update_id,
        "chat_id": str(msg.chat.id),
        "message_id": msg.message_id,
        "text": msg.text or "",
        "received_at": datetime.now(timezone.utc).isoformat(),
    })

    # D-PI5-026 NON-BLOCKING — enqueue + return 200 < 200ms
    pool = await get_arq_pool()
    try:
        await pool.enqueue_job("process_copilot_telegram_turn", payload)
    except Exception as exc:
        # Graceful degradation — log + still ack
        _LOGGER.warning("copilot_telegram_enqueue_failed", error=str(exc))

    return WebhookAck()


@router.post(
    "/link-tokens",
    response_model=LinkTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_telegram_link_token(
    body: LinkTokenRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> LinkTokenResponse:
    """Generate magic link for user to bind their Telegram chat."""

    plaintext, token_hash, expires_at = generate_link_token(
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
    )
    token_id = await create_link_token(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    deep_link = build_deep_link_url(plaintext)
    return LinkTokenResponse(
        token_id=token_id,
        deep_link_url=deep_link,
        expires_at=expires_at,
    )


@router.get(
    "/link-status",
    response_model=LinkStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_link_status(
    token_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> LinkStatusResponse:
    """FE polls every 3s × 60s to confirm chat_id binding."""

    status_data = await fetch_link_status(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_id=token_id,
    )
    return LinkStatusResponse(**status_data)


@router.delete("/link", response_model=UnlinkResponse)
async def unlink_telegram(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> UnlinkResponse:
    """Soft delete current link (set revoked_at)."""

    await revoke_chat_link(db, tenant_id=user.tenant_id, user_id=user.id)
    return UnlinkResponse()
```

### Router registration (`copilot/api/__init__.py` EXTEND)

```python
"""Copilot API package."""

from src.modules.copilot.api.telegram import router as telegram_router  # NEW
# ... existing routers ...
```

Then `main.py` mounts `app.include_router(telegram_router)` (matches existing pattern).

## §9 Tool registry extension

### `copilot/application/tools/registry.py` (EXTEND)

```python
# NEW dataclass at top of file (after imports, before _build_tool_groups)
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ToolGroupMeta:
    """Metadata per tool group. PI-5 D-PI5-023..025."""

    name: str
    available_channels: frozenset[str] = frozenset({"web", "telegram", "whatsapp"})


# NEW SSoT mapping group_name → meta
TOOL_GROUP_META: Final[dict[str, ToolGroupMeta]] = {
    "navigation": ToolGroupMeta("navigation", available_channels=frozenset({"web"})),
    "guided": ToolGroupMeta("guided", available_channels=frozenset({"web"})),
    "landing_mutation": ToolGroupMeta(
        "landing_mutation", available_channels=frozenset({"web"})
    ),
    "offer_section_mutation": ToolGroupMeta(
        "offer_section_mutation", available_channels=frozenset({"web"})
    ),
    # All other groups default = {"web", "telegram", "whatsapp"} via factory
}


def _meta_for_group(name: str) -> ToolGroupMeta:
    """Default meta if not explicitly configured."""
    return TOOL_GROUP_META.get(name, ToolGroupMeta(name))


# EXTEND existing `get_tools_for_context()` signature:
def get_tools_for_context(
    context: dict | None,
    channel: str = "web",  # NEW param — default web (backward compat)
) -> list:
    """Filter tools by route + channel availability."""
    # ... existing logic, plus filter:
    # for each group included → if channel not in _meta_for_group(group).available_channels → skip
    ...
```

### Redirect template (`copilot/application/tools/telegram_redirect.py` NEW)

```python
"""Friendly redirect template when user requests web-only tool from Telegram.

D-PI5-025 — UX template, NO error técnico.
"""

from typing import Final

from src.core.config import settings


# Spanish neutro tuteo (rule spanish-text.md)
TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE: Final[str] = (
    "Ese ajuste requiere el editor web. "
    "Aquí tienes el link directo: {url}\n\n"
    "¿Quieres que te lo recuerde más tarde o prefieres abrirlo ahora?"
)


def build_redirect_url(tenant_id: str, target_path: str) -> str:
    """Construye URL absoluta hacia FE app."""
    base = settings.FRONTEND_URL or "https://app.nicolify.com"
    return f"{base}/{tenant_id}{target_path}"
```

LLM system prompt extension (cuando `channel=='telegram'`): añadir instrucción "Si el usuario pide algo que requiere la web, usa el template `TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE` y ofrece el link directo construido con `build_redirect_url`."

## §10 Conversation model extension

### `copilot/infrastructure/models/conversation_model.py` (EXTEND)

```python
class CopilotConversationModel(Base):
    # ... existing columns ...

    # PI-5 PR-1: Telegram channel support (D-PI5-007)
    channel_type = Column(String(32), nullable=True)  # 'telegram' | NULL = web
    channel_chat_id = Column(String(64), nullable=True)
```

Lookup conversation por `(tenant_id, user_id, channel_type, channel_chat_id)`. NULL == default web (backward compat).

## §11 Eventos / outbox

PR-1 NO emite ni consume domain events. HITL escalation = S3.

## §12 Retry / idempotency policy

| Operación | Idempotency key | Retry | Circuit breaker |
|---|---|---|---|
| Webhook handler | `update_id` (Telegram) | NO retry inbound (return 200 always) | N/A |
| ARQ job `process_copilot_telegram_turn` | `update_id` (in payload) — worker checks DB before processing duplicate | 1 retry on transient (httpx timeout, Redis transient) | Graceful degrade: log + drop after retry |
| Bot `send_message` | N/A (Telegram dedupes per `chat_id` `message_id`) | 1 retry on 429 (Telegram rate limit) + 1 retry on 5xx, exp backoff | After 2 fails → log + skip (no infinite loop) |
| Magic link `/start TOKEN` | `token_hash` UNIQUE constraint + `used_at` set atomic | NO retry | Sin link valid → reject + CTA |

## §13 Tenant isolation

| Endpoint / Op | Tenant resolution | Enforce |
|---|---|---|
| `/webhook` | Resolve via `copilot_channel_links.channel_user_id` lookup → `tenant_id` | NO X-Tenant-ID (Telegram doesn't send). Sin link match → no tenant access |
| `/link-tokens` | `X-Tenant-ID` header (existing middleware) | Repo filters tenant_id |
| `/link-status` | `X-Tenant-ID` | Repo filters tenant_id (token_id MUST match user's tenant) |
| `/link` DELETE | `X-Tenant-ID` | Repo filters tenant_id |
| ARQ worker | tenant_id resolved from `copilot_channel_links` lookup | Orchestrator invocation passes `tenant_id` strict |
| `copilot_channel_links` repo | All queries `WHERE tenant_id = :tenant_id` | Includes lookup-by-chat_id (composite index) |

## §14 Observability

structlog campos clave (rule `copilot-observability.md`):

| Event | Fields |
|---|---|
| `copilot_telegram_webhook_received` | `update_id`, `chat_type`, `text_len_chars` (NO text content) |
| `copilot_telegram_webhook_unauthorized` | `client_ip` (sanitized) |
| `copilot_telegram_enqueue_failed` | `update_id`, `error` |
| `copilot_telegram_link_created` | `tenant_id`, `user_id`, `token_id`, `expires_at` |
| `copilot_telegram_link_bound` | `tenant_id`, `user_id`, `chat_id_prefix` (5 digits + `***`) |
| `copilot_telegram_link_unbound` | `tenant_id`, `user_id` |
| `copilot_telegram_unlinked_message_received` | `chat_id_prefix` (CTA enviada) |
| `copilot_telegram_send_message_failed` | `chat_id_prefix`, `attempt`, `error` |

PII redaction: NUNCA loggear `text` content del mensaje, `username` Telegram, `first_name`, `last_name`, `phone`. Solo `chat_id` masked + length-only metadata.

`copilot_trace_event` con try/except + structlog warning (rule `copilot-observability.md`).

## §15 Research Notes

- Telegram Bot API setWebhook + secret_token: https://core.telegram.org/bots/api#setwebhook (accessed 2026-04-30)
- Telegram deep linking: https://core.telegram.org/bots/features#deep-linking (accessed 2026-04-30)
- Telegram Bot rate limits: https://core.telegram.org/bots/faq#broadcasting-to-users (30 msg/sec global, 1/sec per chat — accessed 2026-04-30)
- Anthropic prompt caching boundary: https://platform.claude.com/docs/en/build-with-claude/prompt-caching (1024 tokens umbral — research §1)
- FastAPI dependency injection + non-blocking handler patterns: https://fastapi.tiangolo.com/ (accessed 2026-04-30)

## §16 Open questions for PM

1. **`SECRET_KEY` for HMAC** — does `core/config.py::Settings` ya tiene `SECRET_KEY` env var, o necesitamos añadir `COPILOT_TELEGRAM_HMAC_SECRET` separado? Ver `grep "SECRET_KEY" backend/src/core/config.py` durante builder. Default: reusar app `SECRET_KEY` si existe; si no, builder añade nuevo env var dedicado.
2. **`FRONTEND_URL` env var** — existe en Settings? Si no, builder añade. Default fallback: `https://app.nicolify.com` (prod) / `https://dev-app.nicolify.com` (dev).
3. **Bot username — production vs dev** — research file asume `@nicolify_copilot_bot` global. Chris ya provee 2 tokens distintos (dev + prod) → necesitamos 2 bots distintos, 2 usernames distintos. PM define naming: dev = `@nicolify_copilot_dev_bot`, prod = `@nicolify_copilot_bot`?
4. **Webhook URL registration** — quién llama setWebhook con secret_token al deployment? Sugerencia: comando admin Streamlit one-time + script en `scripts/setup_copilot_telegram_webhook.py` ejecutable. Builder produce el script.
5. **Link cleanup worker** — `copilot_link_tokens` con `used_at IS NOT NULL` o `expires_at < now()` se acumulan. ¿Añadir ARQ scheduled job cleanup en este PR o S5? Sugerencia: cleanup = S5 PR-5 (arch fitness + observabilidad sprint).
6. **Frontend bot username display** — FE necesita el bot username para construir el deep link en el modal "Conectar Telegram"? O backend devuelve `deep_link_url` ya construido (ELEGIDO en endpoint design — backend construye URL completa, FE solo abre).

PM resolverá estas durante builder phase si emergen como blocker.

---

<!-- @pm: CONTRACT.md ready. Surface mapping declared in § 0. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-1 architect done" para review. -->
