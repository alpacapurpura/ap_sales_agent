"""ModelRouter — chains IntentClassifiers to pick a tier per turn.

See CONTRACT §7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.modules.copilot.domain.model_tier import ModelTier
from src.modules.copilot.domain.routing_policy import (
    ClassifierType,
    RoutingDecision,
    RoutingPolicy,
)

if TYPE_CHECKING:
    from src.modules.copilot.application.router.classifiers.base import IntentClassifier

RoutingMode = Literal["chat", "procedure"]


class RoutingRequest(BaseModel):
    """Input payload for model-routing.

    ``user_msg`` is the raw user message. ``route`` is the current FE route
    (or ``None`` when no context). ``mode`` is ``"chat"`` or ``"procedure"``.
    ``available_tool_count`` is used by NANO short-msg-no-tools rule.
    ``procedure_active`` signals that a procedure overlay is driving tool
    selection.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_msg: str = Field(min_length=0, max_length=20_000)
    route: str | None = None
    mode: RoutingMode = "chat"
    available_tool_count: int = Field(ge=0, default=0)
    procedure_active: bool = False


class ModelRouter:
    """Chain-of-responsibility router over ordered IntentClassifiers.

    First classifier returning a non-None ``RoutingDecision`` wins. If none
    match, falls back to ``policy.default_tier`` with
    ``classifier_used=DEFAULT``.
    """

    def __init__(
        self,
        policy: RoutingPolicy,
        classifiers: list[IntentClassifier],
    ) -> None:
        """Store the policy + ordered classifiers."""
        self._policy = policy
        self._classifiers = tuple(classifiers)

    def select(self, request: RoutingRequest) -> RoutingDecision:
        """Select a tier by walking classifiers in order."""
        for classifier in self._classifiers:
            decision = classifier.classify(request)
            if decision is not None:
                return decision
        return RoutingDecision(
            tier=self._policy.default_tier,
            reason="no_rule_matched",
            confidence=0.5,
            classifier_used=ClassifierType.DEFAULT,
            fallback_tier=ModelTier.MINI,
        )
