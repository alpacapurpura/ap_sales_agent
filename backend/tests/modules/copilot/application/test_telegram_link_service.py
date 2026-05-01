"""Unit tests for telegram_link_service (PI-5 PR-1).

Covers:
- HMAC-SHA256 hash determinism
- Token plaintext != hash (D-PI5-019)
- TTL configuration honored
- Deep link URL format (Telegram spec)
- chat_id masking helper
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from src.modules.copilot.application.services.telegram_link_service import (
    _mask_chat_id,
    build_deep_link_url,
    generate_link_token,
    hash_token_plaintext,
)


def test_generate_link_token_returns_three_values() -> None:
    """Token generator returns (plaintext, hash, expires_at)."""
    plaintext, token_hash, expires_at = generate_link_token(tenant_id=uuid4(), user_id=uuid4())
    assert isinstance(plaintext, str) and len(plaintext) > 20
    assert isinstance(token_hash, str) and len(token_hash) == 64  # SHA256 hex
    assert isinstance(expires_at, datetime)


def test_token_plaintext_not_equal_to_hash() -> None:
    """Plaintext and hash MUST differ (D-PI5-019: never store plaintext)."""
    plaintext, token_hash, _ = generate_link_token(tenant_id=uuid4(), user_id=uuid4())
    assert plaintext != token_hash


def test_hash_token_deterministic() -> None:
    """Hashing same plaintext yields same hash (validation reproducible)."""
    plaintext = "fixed_plaintext_for_test_xyz123"
    h1 = hash_token_plaintext(plaintext)
    h2 = hash_token_plaintext(plaintext)
    assert h1 == h2


def test_hash_different_plaintexts_different_hashes() -> None:
    """Different plaintexts MUST hash to different values."""
    h1 = hash_token_plaintext("plaintext_one")
    h2 = hash_token_plaintext("plaintext_two")
    assert h1 != h2


def test_token_expires_in_future() -> None:
    """Generated token expires_at > now (TTL configured)."""
    _, _, expires_at = generate_link_token(tenant_id=uuid4(), user_id=uuid4())
    now = datetime.now(timezone.utc)
    assert expires_at > now
    # Default TTL is 900s (15 min). Should be in [10min, 20min] window.
    assert expires_at < now + timedelta(minutes=20)
    assert expires_at > now + timedelta(minutes=10)


def test_build_deep_link_url_format() -> None:
    """Deep link URL must follow Telegram spec t.me/<bot>?start=<token>.

    Reference: https://core.telegram.org/bots/features#deep-linking
    """
    plaintext = "abc_test_token_xyz"
    url = build_deep_link_url(plaintext)
    assert url.startswith("https://t.me/")
    assert "?start=" in url
    assert plaintext in url


def test_mask_chat_id_short() -> None:
    """Short chat_ids fully masked (anti PII leak)."""
    assert _mask_chat_id("123") == "***"
    assert _mask_chat_id("12345") == "***"


def test_mask_chat_id_long() -> None:
    """Long chat_ids masked to first 5 chars + '***'."""
    assert _mask_chat_id("123456789") == "12345***"
    assert _mask_chat_id("9876543210") == "98765***"
