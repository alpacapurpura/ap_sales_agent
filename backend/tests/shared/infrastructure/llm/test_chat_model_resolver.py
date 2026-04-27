"""Unit tests for the ``ChatModelSpec`` registry pattern.

The spec is the seam that lets us swap LangChain client classes without
refactoring providers. Each provider declares its spec; the framework
calls ``spec.builder(ctx)`` to produce a configured client.

Goals proven here:

* Default builder (``build_chat_openai``) constructs a ``ChatOpenAI`` with
  the right kwargs, omitting ``base_url`` when None (real OpenAI flow).
* Native builder skeleton (``build_with_chat_class``) produces clients
  for partner packages like ``langchain-deepseek`` that embed their own
  endpoint and only need ``model`` + ``api_key`` + ``temperature``.
* ``_build_chat_from_spec`` shared helper threads the context through
  the spec — single source of truth for the build path so both
  ``OpenAIService`` and ``OpenAICompatibleService`` rely on the same
  code.
* Adding a new provider = declaring a new spec. No core flow changes.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from src.shared.infrastructure.llm.providers._chat_model_resolver import (
    ChatBuildContext,
    ChatModelSpec,
    _build_chat_from_spec,
    build_chat_openai,
    build_with_chat_class,
)
from src.shared.infrastructure.llm.providers._kwargs import (
    normalize_openai_protocol_kwargs,
)


class _StubChatModel(BaseChatModel):
    """Cheap stub to assert builder dispatch without hitting real LangChain init."""

    captured_kwargs: dict | None = None

    def __init__(self, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__()
        # Stash kwargs on the class for assertions; instance-level would
        # require Pydantic surgery and is not worth it for a smoke test.
        type(self).captured_kwargs = kwargs

    @property
    def _llm_type(self) -> str:
        return "stub"

    def _generate(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise NotImplementedError


# ── ChatBuildContext ─────────────────────────────────────────────────


class TestChatBuildContext:
    def test_minimum_payload(self) -> None:
        ctx = ChatBuildContext(
            api_key="sk-x",
            base_url=None,
            model="gpt-4o-mini",
            temperature=0.5,
        )
        assert ctx.api_key == "sk-x"
        assert ctx.base_url is None
        assert ctx.model == "gpt-4o-mini"
        assert ctx.temperature == 0.5


# ── build_chat_openai ────────────────────────────────────────────────


class TestBuildChatOpenAI:
    def test_omits_base_url_when_none(self) -> None:
        """Real OpenAI flow: do NOT pass ``base_url=None`` to ChatOpenAI —
        the SDK uses its own default. Passing None breaks resolution."""
        ctx = ChatBuildContext(api_key="sk-x", base_url=None, model="gpt-4o-mini", temperature=0.7)
        client = build_chat_openai(ctx)
        assert isinstance(client, ChatOpenAI)
        # base_url ends up at the default OpenAI endpoint (string),
        # never literal None.
        raw = getattr(client, "openai_api_base", None) or getattr(client, "base_url", None)
        assert raw is None or "openai.com" in str(raw)

    def test_passes_base_url_when_provided(self) -> None:
        """Compat-provider flow: base_url must reach ChatOpenAI."""
        ctx = ChatBuildContext(
            api_key="sk-x",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            temperature=0.3,
        )
        client = build_chat_openai(ctx)
        raw = getattr(client, "openai_api_base", None) or getattr(client, "base_url", None)
        assert "deepseek.com" in str(raw)


# ── build_with_chat_class (generic native partner builder) ───────────


class TestBuildWithChatClass:
    def test_uses_provided_class_and_drops_base_url(self) -> None:
        """Native partner packages (e.g. ChatDeepSeek) embed their own
        endpoint. Builder must NOT pass ``base_url`` because partner
        classes either reject it or use a different kwarg name."""
        builder = build_with_chat_class(_StubChatModel)
        ctx = ChatBuildContext(
            api_key="sk-x",
            base_url="https://ignored.example.com",
            model="deepseek-v4-pro",
            temperature=0.4,
        )
        builder(ctx)
        captured = _StubChatModel.captured_kwargs or {}
        assert "base_url" not in captured
        assert captured.get("model") == "deepseek-v4-pro"
        assert captured.get("api_key") == "sk-x"
        assert captured.get("temperature") == 0.4

    def test_extra_init_kwargs_are_forwarded(self) -> None:
        """Some partners want fixed extras (e.g. ``api_base`` for a private
        deployment). Builder accepts a closure of static kwargs."""
        builder = build_with_chat_class(_StubChatModel, api_base="https://private.deepseek.local/v1")
        ctx = ChatBuildContext(api_key="sk-x", base_url=None, model="x", temperature=0.0)
        builder(ctx)
        captured = _StubChatModel.captured_kwargs or {}
        assert captured.get("api_base") == "https://private.deepseek.local/v1"


# ── ChatModelSpec ────────────────────────────────────────────────────


class TestChatModelSpec:
    def test_default_normalizer_is_openai_protocol(self) -> None:
        """Specs default to the OpenAI-protocol normaliser. Subclasses for
        non-OpenAI protocols (Gemini, native Anthropic) override."""
        spec = ChatModelSpec(chat_class=ChatOpenAI, builder=build_chat_openai)
        assert spec.kwargs_normalizer is normalize_openai_protocol_kwargs

    def test_library_name_default(self) -> None:
        """``library_name`` is telemetry-only — surfaces in admin
        dashboards so operators see which LangChain package is live."""
        spec = ChatModelSpec(chat_class=ChatOpenAI, builder=build_chat_openai)
        assert spec.library_name == "langchain_openai"

    def test_library_name_override(self) -> None:
        spec = ChatModelSpec(
            chat_class=_StubChatModel,
            builder=build_with_chat_class(_StubChatModel),
            library_name="langchain_deepseek",
        )
        assert spec.library_name == "langchain_deepseek"


# ── _build_chat_from_spec ────────────────────────────────────────────


class TestBuildChatFromSpec:
    def test_dispatches_to_spec_builder(self) -> None:
        spec = ChatModelSpec(
            chat_class=_StubChatModel,
            builder=build_with_chat_class(_StubChatModel),
        )
        ctx = ChatBuildContext(api_key="sk-x", base_url=None, model="m", temperature=0.0)
        client = _build_chat_from_spec(spec, ctx)
        assert isinstance(client, _StubChatModel)
