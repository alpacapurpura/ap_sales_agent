"""Pre-call LLM cost estimator for BudgetGuard.check().

Pure function — same inputs → same output.  No side effects.

Algorithm (PR-6 CONTRACT §5.1):
1. estimated_input_tokens = ceil(len(prompt) * _TOKENS_PER_CHAR)
2. Resolve pricing snapshot via pricing_accessor (LRU+TTL cache).
   Falls back to module-level conservative rates on miss.
3. cost = (input_tokens * input_rate) + (max_output_tokens * output_rate)
4. Tier pricing (Kimi K2.6 / future): split at TIER_THRESHOLD=200k.
5. Apply 1.10x safety multiplier.
6. Return Decimal with 6dp precision.

Conservative fallback rates (when pricing snapshot missing):
- Input: $0.000005/token (~Claude Opus / GPT-4 Turbo)
- Output: $0.000015/token
Over-estimate forces budget gate slightly earlier on unknown models.
Better to fail-closed on budget than fail-open and runaway.

PR-6 / PI-1 S2.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import structlog
from luana_core_observability.cost.calculator import (
    _INPUT_TIER_KEY,
    _OUTPUT_TIER_KEY,
    _resolve_tier_rate,
    _split_at_tier,
)

if TYPE_CHECKING:
    from luana_core_observability.persistence.models.pricing_snapshot_model import (
        ModelPricingSnapshotModel,
    )

logger = structlog.get_logger(__name__)

# Conservative fallback rates (1000 clientes safety).
# Unknown model → assume worst-case tier (premium ~Claude Opus / GPT-4 Turbo).
# Over-estimate absorbs cost drift toward under-estimate.
_FALLBACK_INPUT_RATE = Decimal("0.000005")
_FALLBACK_OUTPUT_RATE = Decimal("0.000015")

# ~4 chars/token for Spanish LatAm text.
_TOKENS_PER_CHAR = Decimal("0.25")

# Safety multiplier: absorbs ±10% estimation drift (PR-2 Q9 acceptance).
_SAFETY_MULTIPLIER = Decimal("1.10")

# agent_kind → (provider, model) hint when caller doesn't provide model.
# These are the typical production models per module (PR-6 CONTRACT §5.3).
_AGENT_KIND_MODEL_HINTS: dict[str, tuple[str, str]] = {
    "sales_agent": ("deepseek", "deepseek-v4-flash"),
    "copilot": ("openai", "gpt-4o-mini"),
    "brand": ("openai", "gpt-4o-mini"),
}


def resolve_provider_model_hint(agent_kind: str) -> tuple[str, str]:
    """Return ``(provider, model)`` hint for the given agent_kind.

    Used when the caller does not pass an explicit ``model`` string.
    Returns fallback (openai, gpt-4o-mini) for unknown agent_kinds.
    """
    return _AGENT_KIND_MODEL_HINTS.get(agent_kind, ("openai", "gpt-4o-mini"))


def estimate_llm_cost(
    *,
    prompt: str,
    max_output_tokens: int,
    model: str | None,
    agent_kind: str,
    pricing_accessor: Any | None = None,
) -> Decimal:
    """Estimate USD cost BEFORE the LLM call for BudgetGuard.check.

    Parameters:
    -----------
    prompt :
        Full prompt string (system + user messages concatenated).
    max_output_tokens :
        Max completion tokens requested (worst-case estimate).
    model :
        Concrete model string (e.g. 'gpt-4o-mini'). If None, resolved
        from ``agent_kind`` hint.
    agent_kind :
        'sales_agent' | 'copilot' | 'brand' (used for hints and logging).
    pricing_accessor :
        Optional cached pricing snapshot (``ModelPricingSnapshotModel``).
        If None, falls back to conservative rates.

    Returns:
    --------
    Decimal
        Estimated cost in USD, quantized to 6 decimal places, with 1.10x
        safety multiplier applied.
    """
    estimated_input_tokens = max(
        math.ceil(len(prompt) * float(_TOKENS_PER_CHAR)),
        1,
    )

    pricing: ModelPricingSnapshotModel | None = pricing_accessor
    if pricing is None:
        input_rate = _FALLBACK_INPUT_RATE
        output_rate = _FALLBACK_OUTPUT_RATE
        logger.info(
            "cost_estimate_fallback_used",
            model=model,
            agent_kind=agent_kind,
        )
    else:
        input_rate = Decimal(str(pricing.input_cost_per_token))
        output_rate = Decimal(str(pricing.output_cost_per_token))

    # Tier pricing (Kimi K2.6 / future models with >200k threshold).
    input_tier = _resolve_tier_rate(pricing, _INPUT_TIER_KEY) if pricing else None
    output_tier = _resolve_tier_rate(pricing, _OUTPUT_TIER_KEY) if pricing else None

    input_cost = _split_at_tier(estimated_input_tokens, input_rate, input_tier)
    output_cost = _split_at_tier(max_output_tokens, output_rate, output_tier)

    raw = input_cost + output_cost
    # 6dp precision: preserves sub-cent costs for small calls.
    # BudgetGuard.check compares Decimal; 6dp is safe.
    safety = (raw * _SAFETY_MULTIPLIER).quantize(Decimal("0.000001"))
    return safety


def _messages_to_prompt(messages: Any) -> str:
    """Flatten LangChain message list / string to a single prompt string.

    Used by ``BudgetGuardingChatModel`` to estimate input tokens from the
    messages list passed to ``ainvoke`` / ``invoke``.
    """
    if isinstance(messages, str):
        return messages
    parts: list[str] = []
    if isinstance(messages, list):
        for msg in messages:
            # LangChain BaseMessage has .content; plain dicts have 'content'.
            content = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                # MultiModal: extract text blocks only.
                parts.extend(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
    return " ".join(parts)
