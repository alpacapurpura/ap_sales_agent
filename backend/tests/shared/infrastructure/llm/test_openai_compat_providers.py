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
    """Pull the base_url from a chat client across LangChain variants.

    ``ChatOpenAI`` stores it under ``openai_api_base`` / ``base_url``;
    partner packages (``ChatDeepSeek``) store it under ``api_base``.
    Survives package upgrades.
    """
    raw = (
        getattr(client, "openai_api_base", None)
        or getattr(client, "base_url", None)
        or getattr(client, "api_base", None)
    )
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


class TestDeepSeekNativePackage:
    """DeepSeek migrated to the native ``langchain_deepseek`` package
    (Fase 2, 2026-04-27). Validates the spec swap works end-to-end and
    that the cache + temperature semantics still hold.
    """

    def test_get_chat_model_returns_chat_deepseek(self) -> None:
        """The spec must dispatch to ChatDeepSeek, not raw ChatOpenAI.

        This is the regression net: if someone reverts the spec or the
        builder by accident, this test flips red immediately.
        """
        from langchain_deepseek import ChatDeepSeek

        from src.core.enums import ModelRole

        svc = DeepSeekService(api_key="sk-test-deepseek")
        client = svc.get_client(role=ModelRole.REASONING)
        assert isinstance(client, ChatDeepSeek)

    def test_spec_library_name_is_langchain_deepseek(self) -> None:
        """Telemetry tag exposed by the spec — admin dashboards consume it."""
        svc = DeepSeekService(api_key="sk-test-deepseek")
        assert svc.CHAT_MODEL_SPEC.library_name == "langchain_deepseek"

    def test_temperature_override_returns_distinct_instance(self) -> None:
        """Cache key (model_name, temperature) must keep working with the
        partner package — same invariant as raw ChatOpenAI."""
        from src.core.enums import ModelRole

        svc = DeepSeekService(api_key="sk-test-deepseek")
        a = svc.get_client(role=ModelRole.REASONING, temperature=0.0)
        b = svc.get_client(role=ModelRole.REASONING, temperature=0.7)
        assert a is not b

    def test_kwargs_normalizer_runs_for_native_path(self) -> None:
        """The spec normaliser must still strip ``max_output_tokens`` even
        though ChatDeepSeek inherits from ``BaseChatOpenAI`` and would
        accept it via the rewrite. Belt-and-suspenders: we own the
        translation regardless of partner-package internals."""
        kwargs = {"max_output_tokens": 256, "metadata": {"trace": "x"}}
        svc = DeepSeekService(api_key="sk-test-deepseek")
        svc.CHAT_MODEL_SPEC.kwargs_normalizer(kwargs)
        assert kwargs == {"max_tokens": 256}


class TestOpenAICompatKwargsTranslation:
    """``max_output_tokens`` is the Nicolify-internal canonical name for
    completion length (matches the ``ResolvedModelPolicy`` field). The
    legacy OpenAI SDK Chat Completions endpoint exposes the same knob as
    ``max_tokens``, and the OpenAI-compatible providers (DeepSeek, Kimi,
    Qwen) all wrap that endpoint.

    Pre-fix: only the OpenAI-specific provider translated the kwarg, so
    a call routed to DeepSeek/Kimi/Qwen leaked ``max_output_tokens`` into
    ``Completions.create()`` and crashed with::

        TypeError: Completions.create() got an unexpected keyword argument
        'max_output_tokens'

    This bug surfaced 2026-04-27 in the buyer-persona document extraction
    flow, where the orchestrator routed to DeepSeek for the structured
    extraction and the document was rejected at the LLM call.

    Fix: ``OpenAICompatibleService.generate_response`` strips the alias
    before invoking the LangChain client, so all subclasses behave
    consistently with the upstream OpenAI provider.
    """

    def _stub_chat_model(self, captured: dict[str, object]) -> object:
        from langchain_core.messages import AIMessage

        class _StubModel:
            def invoke(self, _messages, **kwargs):  # type: ignore[no-untyped-def]
                captured.update(kwargs)
                return AIMessage(content="ok")

        return _StubModel()

    @pytest.mark.parametrize(
        "service_factory",
        [
            lambda: DeepSeekService(api_key="sk-test-deepseek"),
            lambda: KimiService(api_key="sk-test-kimi"),
            lambda: QwenService(api_key="sk-test-qwen"),
        ],
        ids=["deepseek", "kimi", "qwen"],
    )
    def test_max_output_tokens_translated_to_max_tokens(
        self,
        service_factory,  # type: ignore[no-untyped-def]
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}
        svc = service_factory()
        monkeypatch.setattr(svc, "_get_chat_model", lambda role: self._stub_chat_model(captured))

        svc.generate_response(
            messages=[{"role": "user", "content": "hola"}],
            max_output_tokens=512,
        )

        # The kwarg must reach the underlying client renamed — never as
        # ``max_output_tokens`` (which the OpenAI SDK rejects).
        assert "max_output_tokens" not in captured
        assert captured.get("max_tokens") == 512

    def test_explicit_max_tokens_wins_when_both_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If a caller passes both keys, the explicit ``max_tokens`` is
        the authoritative one — translation must not silently overwrite
        it. Belt-and-suspenders against future double-passing bugs."""
        captured: dict[str, object] = {}
        svc = DeepSeekService(api_key="sk-test-deepseek")
        monkeypatch.setattr(svc, "_get_chat_model", lambda role: self._stub_chat_model(captured))

        svc.generate_response(
            messages=[{"role": "user", "content": "hola"}],
            max_tokens=2048,
            max_output_tokens=512,
        )

        assert "max_output_tokens" not in captured
        assert captured.get("max_tokens") == 2048


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
