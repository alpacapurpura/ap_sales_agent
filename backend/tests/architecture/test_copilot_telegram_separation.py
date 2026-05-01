"""Architecture fitness tests for PI-5 PR-1 Copilot Telegram foundation.

Enforce D-PI5-005 separación física copilot↔sales_agent + D-PI5-001
bot global single token + D-PI5-029 private chat filter +
D-PI5-028 webhook secret validation.

These tests are RATCHET — failures block CI. NEW violations require
fix, not allowlist.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = BACKEND_ROOT / "src"
COPILOT_ROOT = SRC_ROOT / "modules" / "copilot"
ALEMBIC_ROOT = BACKEND_ROOT / "alembic" / "versions"


def test_copilot_telegram_bot_token_is_global() -> None:
    """COPILOT_TELEGRAM_BOT_TOKEN MUST be a distinct env var from
    TELEGRAM_BOT_TOKEN (sales_agent legacy global).

    D-PI5-001 + D-PI5-005: 1 global bot Nicolify, NOT per-tenant copilot.
    Sales_agent tokens are per-tenant via connections; copilot bot is
    process-wide singleton.
    """
    config_path = SRC_ROOT / "core" / "config.py"
    text = config_path.read_text()

    assert "COPILOT_TELEGRAM_BOT_TOKEN" in text, (
        "Settings must declare COPILOT_TELEGRAM_BOT_TOKEN (distinct from TELEGRAM_BOT_TOKEN)"
    )
    assert "TELEGRAM_BOT_TOKEN" in text, "Sales_agent legacy TELEGRAM_BOT_TOKEN must continue to exist"
    # Different declarations
    copilot_decl = re.search(r"COPILOT_TELEGRAM_BOT_TOKEN\s*:\s*str\s*=", text)
    sales_decl = re.search(r"^\s*TELEGRAM_BOT_TOKEN\s*:\s*str\s*=", text, re.MULTILINE)
    assert copilot_decl is not None, "COPILOT_TELEGRAM_BOT_TOKEN missing type annotation"
    assert sales_decl is not None, "TELEGRAM_BOT_TOKEN missing type annotation"


def test_copilot_telegram_no_per_tenant_token_lookup() -> None:
    """Copilot Telegram code MUST NOT look up tokens from DB or per-tenant
    config (D-PI5-001 — single global token).
    """
    bot_path = COPILOT_ROOT / "infrastructure" / "channels" / "telegram_bot.py"
    text = bot_path.read_text()
    forbidden = [
        "tenant_id",  # bot adapter must not be tenant-aware for token
        "connection_id",
        "TELEGRAM_BOT_TOKEN",  # must use COPILOT_TELEGRAM_BOT_TOKEN only
    ]
    for term in forbidden:
        # Allow comments mentioning the term but not actual code references
        # Crude check: term must NOT appear as code identifier
        # (acceptable in docstring/comment lines starting with '#' or '"""')
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith(("#", '"')):
                continue
            if term in line and term != "TELEGRAM_BOT_TOKEN":
                pytest.fail(
                    f"copilot/infrastructure/channels/telegram_bot.py:"
                    f"{line_no} contains forbidden term '{term}' — "
                    f"copilot bot is global, not per-tenant (D-PI5-001)"
                )
        # TELEGRAM_BOT_TOKEN forbidden as exact match (sales_agent var)
        if "TELEGRAM_BOT_TOKEN" in text and "COPILOT_TELEGRAM_BOT_TOKEN" not in text:
            pytest.fail(
                "telegram_bot.py uses TELEGRAM_BOT_TOKEN — must use "
                "COPILOT_TELEGRAM_BOT_TOKEN (D-PI5-005 separación física)"
            )


def test_copilot_channel_links_no_cross_module_fk() -> None:
    """copilot_channel_links migration MUST NOT have FK referencing
    sales_agent_* tables (D-PI5-005 separación física).

    Cero shared state between copilot and sales_agent — schemas are
    independent. Sales_agent has its own future telegram bot in a
    distinct PI.
    """
    migration = ALEMBIC_ROOT / "120_pi5_pr1_copilot_telegram_foundation.py"
    assert migration.exists(), f"Migration {migration} missing — PI-5 PR-1 not deployed"
    text = migration.read_text()

    # Forbidden: FOREIGN KEY / REFERENCES targeting sales_agent.* or connections.*
    forbidden_fk_patterns = [
        r"REFERENCES\s+sales_agent",
        r"REFERENCES\s+sa_\w+",
        r"FOREIGN\s+KEY.*sales_agent",
        r"FOREIGN\s+KEY.*connections",
    ]
    for pattern in forbidden_fk_patterns:
        assert not re.search(pattern, text, re.IGNORECASE), (
            f"Migration contains forbidden FK pattern '{pattern}' — D-PI5-005 separación física"
        )


def test_copilot_telegram_module_does_not_import_connections() -> None:
    """Copilot Telegram surface MUST NOT import from modules/connections/.

    D-PI5-005: distinct bot, distinct adapter, distinct webhook router.
    Reuse via shared/ ONLY (escape_markdown_v2, sanitize_payload).
    """
    surfaces = [
        COPILOT_ROOT / "infrastructure" / "channels" / "telegram_bot.py",
        COPILOT_ROOT / "infrastructure" / "workers" / "telegram_worker.py",
        COPILOT_ROOT / "api" / "telegram.py",
        COPILOT_ROOT / "api" / "telegram_dto.py",
        COPILOT_ROOT / "application" / "services" / "telegram_link_service.py",
    ]
    forbidden_imports = [
        "from src.modules.connections",
        "import src.modules.connections",
        "from src.modules.sales_agent",
        "import src.modules.sales_agent",
    ]
    for surface in surfaces:
        if not surface.exists():
            pytest.fail(f"PR-1 surface missing: {surface}")
        text = surface.read_text()
        for forbidden in forbidden_imports:
            assert forbidden not in text, (
                f"{surface.relative_to(BACKEND_ROOT)}: forbidden import "
                f"'{forbidden}' — D-PI5-005 separación física inviolable"
            )


def test_copilot_telegram_filters_private_chat_only() -> None:
    """Webhook handler MUST filter `chat.type == "private"`
    (D-PI5-029 anti-pattern A11)."""
    router_path = COPILOT_ROOT / "api" / "telegram.py"
    text = router_path.read_text()

    assert 'chat.type != "private"' in text or "msg.chat.type" in text, (
        "Webhook router must filter chat.type=='private' (D-PI5-029 anti-pattern A11)"
    )


def test_copilot_telegram_webhook_validates_secret_token() -> None:
    """Webhook handler MUST validate `X-Telegram-Bot-Api-Secret-Token`
    header before any processing (D-PI5-028 anti-pattern A10).
    """
    router_path = COPILOT_ROOT / "api" / "telegram.py"
    text = router_path.read_text()

    assert "X-Telegram-Bot-Api-Secret-Token" in text or ("x_telegram_bot_api_secret_token" in text), (
        "Webhook must validate X-Telegram-Bot-Api-Secret-Token header"
    )
    assert "401" in text, "Webhook must return 401 when secret_token missing/invalid"
    assert "COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN" in text, (
        "Webhook must compare against settings.COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN"
    )


def test_copilot_telegram_webhook_is_non_blocking() -> None:
    """Webhook handler MUST enqueue ARQ job (NOT process LLM inline).

    D-PI5-026 anti-pattern A8: Telegram retry timeout 5s — inline LLM
    causes duplicate messages. Handler must return 200 < 200ms.
    """
    router_path = COPILOT_ROOT / "api" / "telegram.py"
    text = router_path.read_text()

    assert "enqueue_job" in text, "Webhook handler must enqueue ARQ job (D-PI5-026 NON-BLOCKING)"
    assert "process_copilot_telegram_turn" in text, "Webhook must enqueue process_copilot_telegram_turn (worker name)"

    # No direct orchestrator/LLM invocation in webhook handler
    forbidden_inline = [
        "invoke_copilot_orchestrator(",
        "ChatOpenAI(",
        "ChatAnthropic(",
        "litellm.completion(",
    ]
    for term in forbidden_inline:
        assert term not in text, (
            f"Webhook handler contains inline LLM call '{term}' — D-PI5-026 violated (must be ARQ async)"
        )


def test_copilot_link_token_storage_is_hashed() -> None:
    """LinkToken DB row MUST store hash, NOT plaintext (D-PI5-019)."""
    service_path = COPILOT_ROOT / "application" / "services" / "telegram_link_service.py"
    text = service_path.read_text()

    assert "hmac" in text.lower(), "telegram_link_service must use HMAC-SHA256 (D-PI5-019)"
    assert "token_hash" in text, "Service must persist token_hash (NOT plaintext) — D-PI5-019"
    # Plaintext returned to caller but not stored
    assert "secrets.token_urlsafe" in text, "Token generation must use secrets.token_urlsafe(32) (256 bits entropy)"


def test_telegram_cache_prefix_meets_anthropic_threshold() -> None:
    """The Telegram cacheable fragment MUST be ≥2048 tokens (PR-2 Q3 PM-resolved).

    Anthropic prompt cache requires ≥1024 tokens of unchanged prefix to
    activate; ≥2048 is the safety floor PM Q3 mandates so Sonnet (Claude
    floor) and Kimi K2.6 (1024 default minimum) both reliably trigger
    cache reads on the second + subsequent turns.

    The fragment is byte-identical cross-tenant cross-turn — see
    ``tests/modules/copilot/application/orchestrator/test_telegram_channel_context_fragment.py``
    for the invariance contract. This test only enforces the size floor.
    """
    from src.modules.copilot.application.memory.token_counter import count_tokens
    from src.modules.copilot.application.orchestrator.graph import (
        _build_telegram_channel_context_fragment,
    )

    state = {"client_context": {"channel": "telegram"}}
    fragment = _build_telegram_channel_context_fragment(state)
    token_count = count_tokens(fragment)

    assert token_count >= 2048, (
        f"_TELEGRAM_CHANNEL_CONTEXT_ES yields {token_count} tokens (cl100k_base); "
        f"PR-2 Q3 PM-resolved floor is 2048 to ensure Sonnet + Kimi K2.6 cache hits. "
        f"Expand the constant in graph.py with ~stable Spanish prose (no interpolation, "
        f"no timestamps, no per-turn data)."
    )
