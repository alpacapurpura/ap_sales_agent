"""Provider/model aliasing for the pricing resolver.

Internal code records each LLM call under the **shortest stable identity**
the harness already uses (``provider="kimi"``, ``model="kimi-k2.6"``).
LiteLLM, the upstream pricing source, uses its own canonical naming
(``provider="moonshot"``, ``model="moonshot/kimi-k2-0905-preview"``).
Without a translation layer the resolver looks up ``(kimi, kimi-k2.6)``,
finds nothing, and falls back to the ``estimated`` zero-cost row — the
exact failure mode that turned ``/copilot-routing`` into a black hole on
2026-04-27.

This module owns that translation as a SSoT, keyed on the in-process
identity. Each entry maps ``(internal_provider, internal_model) →
(upstream_provider, upstream_model)``. The resolver consults the alias
on every miss before declaring the snapshot estimated; manual snapshots
written under the internal identity continue to win because they hit
the cache first.

When LangChain ships a native partner package for one of these
providers (langchain-moonshot, langchain-deepseek), the upstream model
id propagates straight from ``response_metadata.model_name`` and these
aliases collapse to identity — but until then the resolver needs the
hint.
"""

from __future__ import annotations

# (internal_provider, internal_model) → (upstream_provider, upstream_model)
#
# Internal naming follows ``OpenAICompatibleService.provider_name`` plus
# the model id selected by ``settings.AI_MODEL_AGENT`` / ``AI_MODEL_FAST``
# / ``AI_MODEL_REASONING``. Upstream naming follows the LiteLLM JSON
# (``raw.githubusercontent.com/BerriAI/litellm/main/...``).
PROVIDER_MODEL_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    # Kimi K2.6/K2.5 — Moonshot's intl endpoint reports the bare model id
    # (``kimi-k2.6``); LiteLLM stores the same id with its provider prefix
    # (``moonshot/kimi-k2.6``) and now ships rate cards for K2.6 and K2.5
    # at their real Moonshot pricing — distinct from the older
    # ``kimi-k2-0905-preview`` snapshot. Map each internal id to its
    # direct LiteLLM counterpart so the resolver picks up the correct
    # rate card without a manual DB override.
    ("kimi", "kimi-k2.6"): ("moonshot", "moonshot/kimi-k2.6"),
    ("kimi", "kimi-k2.5"): ("moonshot", "moonshot/kimi-k2.5"),
    ("kimi", "kimi-k2"): ("moonshot", "moonshot/kimi-k2-0711-preview"),
}


def resolve_alias(provider: str, model: str) -> tuple[str, str] | None:
    """Return the upstream ``(provider, model)`` for an internal identity.

    Returns ``None`` when the internal identity has no known alias —
    callers should then accept the original lookup as authoritative
    (manual snapshots, future native LangChain providers).
    """
    return PROVIDER_MODEL_ALIASES.get((provider, model))


__all__ = ["PROVIDER_MODEL_ALIASES", "resolve_alias"]
