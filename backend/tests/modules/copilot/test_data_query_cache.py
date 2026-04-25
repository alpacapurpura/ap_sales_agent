"""F5 — DataQueryCache tests (Redis wrapper, gracefully degrades)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from src.modules.copilot.infrastructure.cache.data_query_cache import (
    DataQueryCache,
    make_cache_key,
)

TENANT = uuid.UUID("ca5cab1e-0000-4000-8000-000000000001")


class _FakeRedis:
    """Minimal in-memory stub matching the redis-py call surface used here."""

    def __init__(self) -> None:
        self.store: dict[str, tuple[str, int]] = {}
        self.calls: list[tuple[str, ...]] = []

    def get(self, key: str) -> bytes | None:
        self.calls.append(("get", key))
        entry = self.store.get(key)
        if entry is None:
            return None
        return entry[0].encode("utf-8")

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.calls.append(("setex", key, str(ttl), value))
        self.store[key] = (value, ttl)


def test_make_cache_key_stable_per_inputs() -> None:
    a = make_cache_key(TENANT, "cuántas personas escribieron", "chat")
    b = make_cache_key(TENANT, "cuántas personas escribieron", "chat")
    assert a == b
    assert TENANT.hex in a or str(TENANT) in a


def test_make_cache_key_differs_per_question() -> None:
    a = make_cache_key(TENANT, "cuántas personas escribieron", "chat")
    b = make_cache_key(TENANT, "dame resumen del programa propósito", "chat")
    assert a != b


def test_make_cache_key_differs_per_channel() -> None:
    a = make_cache_key(TENANT, "x", "chat")
    b = make_cache_key(TENANT, "x", "whatsapp")
    assert a != b


def test_get_returns_none_when_redis_is_none() -> None:
    cache = DataQueryCache(redis=None)
    assert cache.get("any-key") is None


def test_set_is_noop_when_redis_is_none() -> None:
    cache = DataQueryCache(redis=None)
    cache.set("any-key", "value")  # must not raise


def test_get_returns_decoded_value_on_hit() -> None:
    fake = _FakeRedis()
    fake.store["k"] = ("hello", 60)
    cache = DataQueryCache(redis=fake)
    assert cache.get("k") == "hello"


def test_set_calls_setex_with_ttl() -> None:
    fake = _FakeRedis()
    cache = DataQueryCache(redis=fake)
    cache.set("k", "v", ttl=42)
    assert ("setex", "k", "42", "v") in fake.calls
    assert fake.store["k"] == ("v", 42)


def test_default_ttl_is_60s() -> None:
    fake = _FakeRedis()
    cache = DataQueryCache(redis=fake)
    cache.set("k", "v")
    assert fake.store["k"][1] == 60


def test_get_swallows_redis_exception_and_returns_none() -> None:
    class _BoomRedis:
        def get(self, key: str) -> Any:
            msg = "redis down"
            raise RuntimeError(msg)

        def setex(self, *a: Any, **k: Any) -> None:
            pass

    cache = DataQueryCache(redis=_BoomRedis())
    assert cache.get("k") is None


def test_set_swallows_redis_exception() -> None:
    class _BoomRedis:
        def get(self, key: str) -> Any:
            return None

        def setex(self, *a: Any, **k: Any) -> None:
            msg = "redis down"
            raise RuntimeError(msg)

    cache = DataQueryCache(redis=_BoomRedis())
    cache.set("k", "v")  # must not raise


@pytest.mark.parametrize("text", ["áéíóú", "ñ ç", "emoji 🎉", "tab\tand\nnewline"])
def test_make_cache_key_handles_unicode_inputs(text: str) -> None:
    key = make_cache_key(TENANT, text, "chat")
    # Key must be ASCII-safe for Redis storage.
    key.encode("ascii")
