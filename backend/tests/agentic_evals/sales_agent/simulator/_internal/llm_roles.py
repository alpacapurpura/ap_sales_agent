"""Eval-only LLM role registry (T-6).

NOT part of production ``LLM_ROLE_BY_SITE`` SSoT — decision §2.1 in
``docs/product/stories/eval-foundation-simulator-homologation/03-arch-agentic.md``:

1. **SoC**: simulator is test-infra, NOT production code. Polluting
   ``LLM_ROLE_BY_SITE`` with eval-only roles violates §3 protected surfaces of
   ``sales-agent-expert`` skill.
2. **Cost-bucket separation reinforces**: customer LLM calls write to the
   ``eval_simulator_llm_call`` table (NOT ``sales_agent_llm_call``) — symmetric
   to a separate physical table → separate role registry.
3. **Builder ticket alignment (R23)**: changes to this file are test-infra
   (production_code: false). If the role lived in ``LLM_ROLE_BY_SITE``, every
   change would be production-code agentic, owner Opus mandatory.
4. **Future evolution**: stories E (judges) + I (adversarial classifiers) can
   append roles here (``EVAL_JUDGE_VOICE_FIDELITY``, ``EVAL_JAILBREAK_CLASSIFIER``)
   without bumping the production SSoT. Story B does NOT assume cardinality 1
   — the pattern scales N.
5. **Direct LiteLLM Proxy dispatch**: ``customer_node`` invokes
   ``LLMFactory.get_service().get_client(role=ModelRole.NANO)``; the proxy
   resolves the upstream model name via ``litellm_config.yaml``. Default model
   ``gpt-5-nano`` (env override possible at the proxy layer).

Format mirrored on ``LLM_ROLE_BY_SITE`` for ergonomic familiarity (string keys,
``ModelRole`` values).

Anchor for arch fitness gate (T-9 ``test_simulator_no_mirrors_shared.py``):
this file lives under ``simulator/_internal/`` and exposes only string keys
that DO NOT collide with ``LLM_ROLE_BY_SITE.keys()`` — invariant probed at
test time.
"""

from __future__ import annotations

from luana_core_platform.core.enums import ModelRole

# H1 forward-compat — append only. Role removal requires migration entry in
# ``simulator/_internal/schema_migrations.py`` because golden v1 fixtures may
# reference the role name string.
EVAL_LLM_ROLES: dict[str, ModelRole] = {
    "EVAL_USER_SIMULATOR": ModelRole.NANO,
}
"""Map of eval-only role name → ``ModelRole`` enum value.

Each role here corresponds to a customer / judge / classifier LLM call
made under ``backend/tests/agentic_evals/`` — NEVER from production
``backend/src/`` code.
"""


# Default upstream wire-name override per role. The LiteLLM Proxy resolves the
# actual provider chain via its config; this map gives ``customer_node`` a
# stable string handle for telemetry and metadata payloads.
EVAL_DEFAULT_MODELS: dict[str, str] = {
    "EVAL_USER_SIMULATOR": "gpt-5-nano",
}
"""Default model wire-name per eval role.

Story B ships ``gpt-5-nano`` for customer simulation (~$0.005/turn cost
target per D9). Future stories may rebind via this registry without
touching ``customer_node`` source.
"""


def get_eval_llm_model(role: str) -> str:
    """Resolve the default model wire-name for an eval role.

    Args:
        role: One of ``EVAL_LLM_ROLES`` keys (e.g. ``"EVAL_USER_SIMULATOR"``).

    Returns:
        The model wire-name string (e.g. ``"gpt-5-nano"``).

    Raises:
        KeyError: If the role is not registered. Defensive — surfaces
            misspellings during simulator wiring rather than silently
            falling through to a wrong model.
    """
    return EVAL_DEFAULT_MODELS[role]


__all__ = [
    "EVAL_DEFAULT_MODELS",
    "EVAL_LLM_ROLES",
    "get_eval_llm_model",
]
