"""Router package — model-tier routing for the Copilot orchestrator.

Public API:
    * ``ModelRouter`` — chain-of-responsibility evaluator.
    * ``RoutingRequest`` — input payload.
    * ``RuleClassifier`` — regex + length + tool-count first line.
    * ``LLMClassifier`` — NANO LLM fallback (F8).
    * ``build_default_router`` — canonical chain (rule → llm → default).

Consumers should call ``build_default_router()`` at boot and inject the
resulting ``ModelRouter`` instance. Bypassing the factory means re-deriving
ordering invariants by hand and skipping the F8 LLM fallback.
"""

from __future__ import annotations

from src.modules.copilot.application.router.classifiers.llm_classifier import (
    DEFAULT_THRESHOLD,
    LLMClassifier,
)
from src.modules.copilot.application.router.classifiers.rule_classifier import (
    RuleClassifier,
)
from src.modules.copilot.application.router.model_router import (
    ModelRouter,
    RoutingRequest,
)
from src.modules.copilot.domain.routing_policy import (
    DEFAULT_ROUTING_POLICY,
    RoutingPolicy,
)


def build_default_router(
    *,
    policy: RoutingPolicy | None = None,
    llm: object | None = None,
    llm_threshold: float = DEFAULT_THRESHOLD,
    enable_llm_fallback: bool = True,
) -> ModelRouter:
    """Build the canonical Copilot ``ModelRouter`` chain.

    Order:
        1. ``RuleClassifier(policy)`` — instant, regex + length guards.
        2. ``LLMClassifier(policy, threshold)`` — NANO LLM, only when (1)
           returned ``None``. Skipped when ``enable_llm_fallback=False``.
        3. ``ModelRouter`` default fallback to ``policy.default_tier``.

    ``llm`` overrides the LLMClassifier model (tests inject a stub). When
    ``None`` the LLMClassifier resolves ``ModelRole.NANO`` lazily via
    ``LLMFactory`` — keeps boot cheap and avoids module-import side-effects.
    """
    pol = policy if policy is not None else DEFAULT_ROUTING_POLICY
    chain = [RuleClassifier(pol)]
    if enable_llm_fallback:
        chain.append(LLMClassifier(pol, threshold=llm_threshold, llm=llm))
    return ModelRouter(pol, chain)


__all__ = (
    "DEFAULT_THRESHOLD",
    "LLMClassifier",
    "ModelRouter",
    "RoutingRequest",
    "RuleClassifier",
    "build_default_router",
)
