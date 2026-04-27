"""Provider-agnostic response validation for LLM invocations.

Owns the detection contract for the *reasoning-budget exhaustion trap*:
reasoning-capable models (OpenAI o-series, DeepSeek R1/V4, Anthropic
extended thinking, Gemini 2.5/3) consume the same ``max_tokens`` budget
for both internal chain-of-thought and the visible answer. When the
budget is sized for the answer alone, reasoning eats it all and the
``content`` field comes back empty with ``finish_reason="length"`` —
the silent failure mode reported across every major provider in
2025-2026.

LangChain mirrors the underlying provider's ``reasoning_tokens`` /
``reasoning_content`` accounting onto two surfaces:

* ``response.usage_metadata["output_token_details"]["reasoning"]`` —
  provider-normalised by LangChain across DeepSeek / OpenAI / Anthropic
  adapters.
* ``response.response_metadata["token_usage"]["completion_tokens_details"]
  ["reasoning_tokens"]`` — raw passthrough from OpenAI-style providers.

The detector reads both, prefers the normalised path. Lives here (not
in ``ai_action_service``) because it is a *provider-protocol* concern —
any caller of a chat model client should be able to route through it,
not just the structured-action helper.

Sister contract: the ``kwargs_normalizer`` in :mod:`._kwargs` *prevents*
the trap by adding ``spec.reasoning_token_reserve`` to the wire budget.
The detector here *catches* the trap when prevention fails — e.g.
operator override, new reasoning model whose reserve has not been
calibrated, model emitting more reasoning than the configured reserve.
Failing loud is intentional: a silent retry with a bumped cap would
hide the policy bug. Operators see the typed error, pick the right
lever (raise reserve in the spec, or switch to a non-reasoning role for
the task).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.messages import AIMessage

__all__ = ["ReasoningBudgetExhaustedError", "detect_reasoning_budget_exhaustion"]


class ReasoningBudgetExhaustedError(RuntimeError):
    """Raised when reasoning consumed the budget, leaving empty content.

    Triggered when the model returns empty visible output with
    ``finish_reason="length"`` and a positive reasoning-token count.

    The exception name and message are stable — callers (notably
    :class:`AIActionService`) match on the type and surface the message
    to operators / dashboards. Carries enough diagnostics that an
    operator can pick the right policy lever without reproducing the
    failure.
    """


def detect_reasoning_budget_exhaustion(
    response: AIMessage,
    *,
    model_name: str,
) -> None:
    """Raise :class:`ReasoningBudgetExhaustedError` when the trap signature is met.

    Signature:

    1. ``response.content`` strips to empty (LangChain coerces the
       ``content`` field to ``str | list``; for chat completions it is
       the visible text).
    2. ``response.response_metadata["finish_reason"] == "length"`` —
       provider truncated the stream at the budget boundary.
    3. Reasoning token count > 0 — distinguishes the trap from
       unrelated truncations (e.g. a content filter or a 400 that
       still produced an ``AIMessage``).

    Returns silently for any other shape so the caller falls through to
    its normal parse / validate path.

    The function is intentionally provider-agnostic: same code catches
    the trap on OpenAI o-series, DeepSeek-V4 reasoning, Anthropic 4.6+
    adaptive thinking, and Gemini 2.5/3. Adding a new reasoning
    provider does not require touching this file as long as LangChain
    surfaces the standard ``finish_reason`` and ``usage_metadata``
    fields (the partner packages all do).
    """
    content = _extract_text_content(response)
    if content.strip():
        return

    finish_reason = response.response_metadata.get("finish_reason") if response.response_metadata else None
    if finish_reason != "length":
        return

    reasoning_tokens = _extract_reasoning_tokens(response)
    if reasoning_tokens <= 0:
        return

    msg = (
        f"Model '{model_name}' consumed {reasoning_tokens} reasoning tokens and emitted empty content "
        f"with finish_reason=length. The reasoning budget reserve was insufficient for the visible "
        f"answer. Lever: raise the spec's reasoning_token_reserve, bump max_output_tokens explicitly, "
        f"or switch to a non-reasoning role for this task."
    )
    raise ReasoningBudgetExhaustedError(msg)


def _extract_text_content(response: AIMessage) -> str:
    """Coerce ``AIMessage.content`` to a plain string for emptiness check."""
    raw: Any = response.content
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        # Chat-completion content blocks: collect text segments.
        parts: list[str] = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") in {"text", None}:
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return ""


def _extract_reasoning_tokens(response: AIMessage) -> int:
    """Read reasoning-token count from either LangChain surface.

    Preference order:

    1. ``usage_metadata.output_token_details.reasoning`` —
       provider-normalised by LangChain (DeepSeek / OpenAI / Anthropic
       partner packages all map onto this key).
    2. ``response_metadata.token_usage.completion_tokens_details.reasoning_tokens``
       — raw OpenAI-style passthrough used by the legacy ChatOpenAI
       adapter when LangChain has not yet normalised a new field.
    """
    usage_meta = getattr(response, "usage_metadata", None) or {}
    output_details = usage_meta.get("output_token_details") if isinstance(usage_meta, dict) else None
    if isinstance(output_details, dict):
        reasoning = output_details.get("reasoning")
        if isinstance(reasoning, int) and reasoning > 0:
            return reasoning

    response_meta = response.response_metadata or {}
    token_usage = response_meta.get("token_usage") or {}
    details = token_usage.get("completion_tokens_details") or {}
    if isinstance(details, dict):
        reasoning = details.get("reasoning_tokens")
        if isinstance(reasoning, int) and reasoning > 0:
            return reasoning

    return 0
