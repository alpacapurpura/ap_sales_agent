"""Sprint 0 — DeepSeek / Kimi / Qwen provider adapters.

Verifies that each OpenAI-compatible provider:
- Builds its underlying ``ChatOpenAI`` with the correct base_url.
- Caches per-(role, temperature) like ``OpenAIService``.
- Refuses to construct without an API key.
- Honours the embedding contract (Qwen yes, DeepSeek/Kimi no).

These tests do not hit any network — they just inspect the configured
``ChatOpenAI`` instance.
"""

from __future__ import annotations

import pytest

from src.core.enums import ModelRole
from src.shared.infrastructure.llm.providers.deepseek import DeepSeekService
from src.shared.infrastructure.llm.providers.kimi import KimiService
from src.shared.infrastructure.llm.providers.qwen import QwenService


def _client_base_url(client: object) -> str:
    """Pull the base_url from a ChatOpenAI in a way that survives lib upgrades."""
    raw = getattr(client, "openai_api_base", None) or getattr(client, "base_url", None)
    return str(raw) if raw is not None else ""


class TestDeepSeekService:
    def test_uses_configured_base_url(self) -> None:
        svc = DeepSeekService(api_key="sk-test-deepseek")
        client = svc.get_client(role=ModelRole.REASONING)
        assert "api.deepseek.com" in _client_base_url(client)

    def test_temperature_override_returns_distinct_instance(self) -> None:
        svc = DeepSeekService(api_key="sk-test-deepseek")
        a = svc.get_client(role=ModelRole.REASONING, temperature=0.0)
        b = svc.get_client(role=ModelRole.REASONING, temperature=0.7)
        assert a is not b

    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.shared.infrastructure.llm.providers.deepseek.settings.DEEPSEEK_API_KEY",
            "",
        )
        with pytest.raises(ValueError, match="deepseek API key not configured"):
            DeepSeekService(api_key=None)

    def test_get_embedding_model_raises(self) -> None:
        svc = DeepSeekService(api_key="sk-test-deepseek")
        with pytest.raises(NotImplementedError):
            svc.get_embedding_model()


class TestKimiService:
    def test_uses_moonshot_base_url(self) -> None:
        svc = KimiService(api_key="sk-test-kimi")
        client = svc.get_client(role=ModelRole.AGENT)
        assert "moonshot.ai" in _client_base_url(client)

    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.shared.infrastructure.llm.providers.kimi.settings.KIMI_API_KEY",
            "",
        )
        with pytest.raises(ValueError, match="kimi API key not configured"):
            KimiService(api_key=None)

    def test_get_embedding_model_raises(self) -> None:
        svc = KimiService(api_key="sk-test-kimi")
        with pytest.raises(NotImplementedError):
            svc.get_embedding_model()

    def test_k2_6_temperature_clamped_to_required_value(self) -> None:
        """TP4-B4 + TP5-B8 regression — Kimi K2.6 has two server-enforced
        temperature regimes:

        - thinking enabled → only ``temperature=1.0`` works.
        - thinking disabled → only ``temperature=0.6`` works.

        We disable thinking globally (TP5-B8 — LangChain doesn't preserve
        ``reasoning_content`` across tool-call turns), so the live
        constraint is ``0.6``. Any explicit override gets clamped to keep
        callers (e.g. deep-agent harness) provider-agnostic.
        """
        svc = KimiService(api_key="sk-test-kimi")
        client = svc.get_client(role=ModelRole.AGENT, temperature=1.0)
        # langchain_openai stores temperature on the resolved client.
        assert client.temperature == 0.6

    def test_k2_6_disables_thinking_mode(self) -> None:
        """TP5-B8 regression — Kimi K2.6 thinking mode requires
        ``reasoning_content`` on every prior assistant message that issued a
        ``tool_call``. LangChain doesn't preserve that field across turns, so
        post-tool re-invocations explode with
        ``thinking is enabled but reasoning_content is missing in assistant
        tool call message at index N``.

        Until we rewire LangChain to round-trip ``reasoning_content``, the
        AGENT role must call K2.6 with thinking disabled
        (``extra_body={"thinking": {"type": "disabled"}}``). Tool calls + UX
        quality are unaffected — K2.6 without thinking still tops agentic
        benchmarks.
        """
        svc = KimiService(api_key="sk-test-kimi")
        client = svc.get_client(role=ModelRole.AGENT)
        # langchain_openai exposes the openai-SDK kwargs via ``model_kwargs``.
        extra_body = client.model_kwargs.get("extra_body", {})
        assert extra_body.get("thinking") == {"type": "disabled"}


class TestQwenService:
    def test_uses_dashscope_intl_base_url(self) -> None:
        svc = QwenService(api_key="sk-test-qwen")
        client = svc.get_client(role=ModelRole.VISION)
        assert "dashscope" in _client_base_url(client)

    def test_provides_embeddings(self) -> None:
        svc = QwenService(api_key="sk-test-qwen")
        emb = svc.get_embedding_model()
        # OpenAIEmbeddings exposes ``model`` + a base_url-like attr we can inspect.
        assert emb is not None
        assert "dashscope" in _client_base_url(emb)

    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.shared.infrastructure.llm.providers.qwen.settings.DASHSCOPE_API_KEY",
            "",
        )
        with pytest.raises(ValueError, match="qwen API key not configured"):
            QwenService(api_key=None)
