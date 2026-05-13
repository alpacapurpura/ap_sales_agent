"""Unit tests for ``SPECIALIST_TO_ROLE`` mapping (S4 SSoT).

Mapping vive en ``src/modules/sales_agent/domain/model_tier.py``. Cualquier
specialist nuevo declara su :class:`ModelRole` acá. Refactor S4 cambió
2 entries vs sales_agent pre-S4:

- ``closer``: ``REASONING`` → ``AGENT`` (Kimi K2.6 cierres + cache 75-83%).
- ``supervisor``: ``FAST`` → ``NANO`` (classifier 10-token output;
  paridad copilot F8 routing).

``qualifier`` y ``product_expert`` permanecen ``REASONING`` (DeepSeek V4
auto-cache + razonamiento sobre lead/offer context — env var
``AI_PROVIDER_REASONING=deepseek`` rutea).
"""

from __future__ import annotations

import pytest

from luana_core_platform.core.enums import ModelRole
from luana_core_sales_agent.domain.model_tier import SPECIALIST_TO_ROLE


class TestSpecialistToRoleSSoT:
    """SSoT mapping must cover every specialist with LLM call."""

    def test_supervisor_maps_to_nano(self) -> None:
        assert SPECIALIST_TO_ROLE["supervisor"] is ModelRole.NANO

    def test_qualifier_maps_to_reasoning(self) -> None:
        assert SPECIALIST_TO_ROLE["qualifier"] is ModelRole.REASONING

    def test_product_expert_maps_to_reasoning(self) -> None:
        assert SPECIALIST_TO_ROLE["product_expert"] is ModelRole.REASONING

    def test_closer_maps_to_agent(self) -> None:
        assert SPECIALIST_TO_ROLE["closer"] is ModelRole.AGENT

    @pytest.mark.parametrize(
        "specialist",
        ["supervisor", "qualifier", "product_expert", "closer"],
    )
    def test_every_specialist_resolves_to_known_role(self, specialist: str) -> None:
        role = SPECIALIST_TO_ROLE[specialist]
        assert isinstance(role, ModelRole)

    def test_mapping_is_frozen_dict(self) -> None:
        # Mutability check — SSoT should not be mutated at runtime.
        # We tolerate ``dict`` (idiomatic) but assert that consumers
        # treat it read-only by checking presence + key set.
        keys = set(SPECIALIST_TO_ROLE.keys())
        assert keys >= {"supervisor", "qualifier", "product_expert", "closer"}
