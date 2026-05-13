"""ChatModelSpec — registry pattern for LangChain client classes.

Why this exists
---------------

Each LLM provider service (``OpenAIService``, ``DeepSeekService``,
``KimiService``, ``QwenService``, future Gemini, future Anthropic native…)
needs to instantiate a LangChain ``BaseChatModel`` subclass with the
right kwargs. Pre-pattern, the class name was hardcoded inside each
service's ``_get_chat_model``. Migrating from raw ``ChatOpenAI`` to a
native partner package (e.g. ``langchain_deepseek.ChatDeepSeek``) meant
editing the service body — risk of drift and regression.

The spec decouples three concerns:

1. **Which class to use** (`chat_class`).
2. **How to build it** (`builder` callable that takes a typed context).
3. **How to translate Nicolify-canonical kwargs** to the wire dialect
   (`kwargs_normalizer`).

Plus a telemetry tag (`library_name`) so admin dashboards surface which
LangChain package is live for each provider — the early-warning signal
for the silent ``max_tokens`` rewrite issue tracked in
``docs/mejoras-proceso/to-do.md`` #32.

Adding a new provider
---------------------

1. Pick or write a builder (most providers reuse ``build_chat_openai``
   for compat or ``build_with_chat_class`` for native partner packages).
2. Declare a ``ChatModelSpec`` instance.
3. Set it as ``CHAT_MODEL_SPEC`` on the service class.

That's it. The base flow (``_get_chat_model``) reads the spec via
``_build_chat_from_spec`` and never inspects which provider is live —
swapping libraries becomes a one-line change.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from luana_core_llm.providers._kwargs import (
    normalize_openai_protocol_kwargs,
)

__all__ = [
    "DEFAULT_OPENAI_SPEC",
    "ChatBuildContext",
    "ChatModelSpec",
    "_build_chat_from_spec",
    "build_chat_openai",
    "build_with_chat_class",
]


@dataclass(frozen=True, slots=True)
class ChatBuildContext:
    """Per-call context handed to a ``ChatModelSpec.builder``.

    Holds the run-time inputs (api_key, model, temperature) that the
    builder closes over the static configuration (chat_class, library
    extras) declared in the spec. Frozen so caching by-value is safe.
    """

    api_key: str
    base_url: str | None
    model: str
    temperature: float


@dataclass(frozen=True, slots=True)
class ChatModelSpec:
    """Declarative recipe for building a LangChain chat model client.

    Attributes:
        chat_class: The LangChain ``BaseChatModel`` subclass that will be
            instantiated. Used as a type hint and for telemetry.
        builder: Callable that turns a :class:`ChatBuildContext` into a
            configured chat client. Most providers reuse one of the
            two stock builders below; complex providers can pass their
            own closure.
        kwargs_normalizer: Translation function applied to ``**kwargs``
            before they reach the chat client at *call* time
            (``invoke``/``stream``). Receives the kwargs dict and the
            active spec so it can apply per-spec rules (e.g. reasoning
            budget reserve). Defaults to the OpenAI-protocol normaliser;
            non-OpenAI protocols (Gemini) override.
        library_name: Telemetry tag, e.g. ``"langchain_openai"`` /
            ``"langchain_deepseek"``. Surfaces in admin dashboards so
            operators see which LangChain package handled each call —
            critical for catching silent rewrites between major version
            bumps of LangChain or the partner packages.
        is_reasoning_model: True for models that consume the same
            ``max_tokens`` budget for *both* internal chain-of-thought
            tokens (``reasoning_content`` / ``reasoning`` / ``thinking``)
            and the visible answer (``content``). When True the
            normalizer adds :attr:`reasoning_token_reserve` to the
            caller's ``max_output_tokens`` before translating to the
            wire param so reasoning never starves the response.
            Documented trap reproduced across OpenAI o-series, DeepSeek
            R1/V4, Anthropic extended thinking, Gemini 2.5/3.
        reasoning_token_reserve: Tokens added on top of caller's visible
            budget when :attr:`is_reasoning_model` is True. 4000 is the
            industry-recommended floor (OpenAI Help Center, OpenRouter,
            tokenmix research). Operators escape-hatch via explicit
            ``max_tokens=`` which always wins.
        reasoning_effort_param: Native wire-param name for reasoning
            effort (``"reasoning_effort"`` for OpenAI o-series,
            ``"thinking.budget_tokens"`` for Anthropic adaptive
            thinking, ``"thinking_config.thinking_budget"`` for Gemini).
            When ``None`` the spec does not surface effort to the wire
            and the normalizer drops the canonical
            ``reasoning_effort`` kwarg silently — the wire would 400.
    """

    chat_class: type[BaseChatModel]
    builder: Callable[[ChatBuildContext], BaseChatModel]
    kwargs_normalizer: Callable[..., dict] = field(default=normalize_openai_protocol_kwargs)
    library_name: str = "langchain_openai"
    is_reasoning_model: bool = False
    reasoning_token_reserve: int = 0
    reasoning_effort_param: str | None = None


# ── Stock builders ───────────────────────────────────────────────────


def build_chat_openai(ctx: ChatBuildContext) -> ChatOpenAI:
    """Default builder for ``ChatOpenAI`` (real OpenAI + every compat clone).

    Skips ``base_url`` when ``ctx.base_url is None`` because passing a
    literal ``None`` to ``ChatOpenAI`` overrides the SDK's own
    ``OPENAI_BASE_URL`` resolution and breaks real-OpenAI flows.
    """
    init: dict[str, Any] = {
        "model": ctx.model,
        "api_key": ctx.api_key,
        "temperature": ctx.temperature,
    }
    if ctx.base_url:
        init["base_url"] = ctx.base_url
    return ChatOpenAI(**init)


def build_with_chat_class(
    chat_class: type[BaseChatModel],
    **extra_init_kwargs: object,
) -> Callable[[ChatBuildContext], BaseChatModel]:
    """Builder factory for native partner packages.

    Returns a builder closure pre-bound to ``chat_class`` and any
    static ``extra_init_kwargs`` (e.g. ``api_base`` for a private
    deployment). The returned builder accepts a :class:`ChatBuildContext`
    and produces a configured client.

    Native partner packages (``langchain_deepseek.ChatDeepSeek``,
    ``langchain_qwq.ChatQwen``, ...) embed their own endpoint, so
    ``ctx.base_url`` is intentionally dropped here. If a provider needs
    a custom ``api_base``/``endpoint`` kwarg, pass it via
    ``extra_init_kwargs``.
    """

    def _builder(ctx: ChatBuildContext) -> BaseChatModel:
        init: dict[str, Any] = {
            "model": ctx.model,
            "api_key": ctx.api_key,
            "temperature": ctx.temperature,
            **extra_init_kwargs,
        }
        return chat_class(**init)

    return _builder


# ── Stock specs ──────────────────────────────────────────────────────


DEFAULT_OPENAI_SPEC: ChatModelSpec = ChatModelSpec(
    chat_class=ChatOpenAI,
    builder=build_chat_openai,
    kwargs_normalizer=normalize_openai_protocol_kwargs,
    library_name="langchain_openai",
)
"""Default spec for ``OpenAIService`` and ``OpenAICompatibleService``
subclasses that have not migrated to a native partner package."""


# ── Shared dispatch ──────────────────────────────────────────────────


def _build_chat_from_spec(
    spec: ChatModelSpec,
    ctx: ChatBuildContext,
) -> BaseChatModel:
    """Dispatch to ``spec.builder``. Single seam for tests + telemetry hooks."""
    return spec.builder(ctx)
