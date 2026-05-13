"""Integration tests for ``build_specialist_system_prompt`` — S3.

Validates the high-level builder that takes an AgentState + role and returns
the composed system prompt with cache_boundary marker. Mirrors the copilot
``build_system_prompt`` integration but for sales specialists.

# [SALES-AGENT-CACHE-PREFIX-S3]
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from luana_core_sales_agent.application.orchestrator.state import create_initial_state
from luana_core_sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    SpecialistRole,
    build_specialist_system_prompt,
)

# Approximation: 1 token ≈ 4 chars (per OpenAI tokenizer rule of thumb).
# Test threshold uses char count to avoid tiktoken dependency in test path.
MIN_CACHE_PREFIX_CHARS = 1024 * 3  # conservative — assumes ≥1024 tokens at 3 chars/token.


def _realistic_state(**overrides: Any) -> dict[str, Any]:
    state = create_initial_state(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        agent_identity=(
            "# IDENTIDAD DEL AGENTE\n\n"
            "## Quién Eres\n"
            "Eres el asistente de ventas de **Test Brand**.\n"
            'Tu lema: "Test tagline"\n'
            "**Misión:** Test mission line.\n\n"
            "## Tu Voz y Tono\n"
            "Profesional, cercano, directo, sin floreo. Tuteo neutro latam.\n\n"
            "## Catálogo de Ofertas\n\n"
            "### Programa Insignia\n"
            "- **Tipo:** Programa formativo de 8 semanas\n"
            "- **Promesa:** Resultado X en plazo Y\n"
            "- **Resultado Principal:** transformación medible\n"
            "- **Tiempo al Resultado:** 8 semanas\n"
            "- **Precios:** $597 USD pago único / 3 cuotas $220 USD\n"
            "- **Garantía:** 14 días devolución total\n"
            "- **Incluye:** 8 módulos de video, comunidad activa, 4 mentorías grupales\n"
            "- **Dolores que resuelve:** falta de método, soledad, sin claridad\n"
            "- **Deseos que satisface:** autonomía, ingreso predecible, clientes mejores\n"
            "- **Objeciones comunes y cómo manejarlas:**\n"
            "  - **PRECIO** [aikido]: Validar la inversión. Conectar a outcome.\n"
            "  - **TIEMPO** [aikido]: Reframe — 1h diaria vs años de prueba/error.\n"
            "- **Por qué actuar ahora:** próximo cohorte cierra en 5 días\n"
            "- **Resultados medibles:**\n"
            "  - 3-5 clientes nuevos en 60 días\n"
            "  - sistema documentado replicable\n\n"
            "## Reglas por Canal\n"
            "- Mensajes claros y conversacionales (3-4 oraciones)\n"
            "- Tono profesional y cercano\n"
        ),
        tenant_config={"brand_name": "Test Brand"},
        channel_type="whatsapp",
    )
    state.update(overrides)
    return state


class TestCachePrefixSizeAtLeast1024Tokens:
    """OpenAI / Kimi / DeepSeek require ≥1024 tokens of stable prefix."""

    def test_qualifier_prefix_meets_1024_token_floor(self) -> None:
        state = _realistic_state()
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        prefix = prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert len(prefix) >= MIN_CACHE_PREFIX_CHARS, (
            f"Cacheable prefix is only {len(prefix)} chars (~{len(prefix) // 4} tokens). "
            f"Expected ≥{MIN_CACHE_PREFIX_CHARS} chars (~1024 tokens) per S3 §3.4."
        )

    def test_closer_prefix_meets_1024_token_floor(self) -> None:
        state = _realistic_state()
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        prefix = prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert len(prefix) >= MIN_CACHE_PREFIX_CHARS

    def test_product_expert_prefix_meets_1024_token_floor(self) -> None:
        state = _realistic_state()
        prompt = build_specialist_system_prompt(state, SpecialistRole.PRODUCT_EXPERT)
        prefix = prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert len(prefix) >= MIN_CACHE_PREFIX_CHARS


class TestNoVolatileInCacheable:
    """Cacheable bytes must be byte-identical regardless of volatile state."""

    def _prefix(self, prompt: str) -> str:
        return prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]

    def test_lead_score_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(lead_score=0),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(lead_score=99),
            SpecialistRole.QUALIFIER,
        )
        assert self._prefix(a) == self._prefix(b)

    def test_buying_signals_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(buying_signals=[{"type": "price_question", "turn": 1}]),
            SpecialistRole.CLOSER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(
                buying_signals=[
                    {"type": "price_question", "turn": 1},
                    {"type": "logistics_question", "turn": 2},
                    {"type": "objection_resolved", "turn": 3},
                ],
            ),
            SpecialistRole.CLOSER,
        )
        assert self._prefix(a) == self._prefix(b)

    def test_qualification_answers_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(qualification_answers={}),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(qualification_answers={"name": "Ana", "budget": "low"}),
            SpecialistRole.QUALIFIER,
        )
        assert self._prefix(a) == self._prefix(b)

    def test_current_state_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(current_state="rapport"),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(current_state="closing"),
            SpecialistRole.QUALIFIER,
        )
        assert self._prefix(a) == self._prefix(b)

    def test_session_gap_hours_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(session_gap_hours=None),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(session_gap_hours=72.0),
            SpecialistRole.QUALIFIER,
        )
        assert self._prefix(a) == self._prefix(b)

    def test_consecutive_questions_change_does_not_alter_prefix(self) -> None:
        a = build_specialist_system_prompt(
            _realistic_state(consecutive_questions=0),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _realistic_state(consecutive_questions=4),
            SpecialistRole.QUALIFIER,
        )
        assert self._prefix(a) == self._prefix(b)


class TestVolatileFragmentsCarryState:
    """Volatile slots SHOULD reflect state changes."""

    def _suffix(self, prompt: str) -> str:
        if CACHE_BOUNDARY_MARKER not in prompt:
            return prompt
        return prompt.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[1]

    def test_stage_change_appears_in_suffix(self) -> None:
        a_suffix = self._suffix(
            build_specialist_system_prompt(
                _realistic_state(current_state="rapport"),
                SpecialistRole.QUALIFIER,
            ),
        )
        b_suffix = self._suffix(
            build_specialist_system_prompt(
                _realistic_state(current_state="closing"),
                SpecialistRole.QUALIFIER,
            ),
        )
        assert a_suffix != b_suffix

    def test_lead_score_appears_in_suffix(self) -> None:
        a_suffix = self._suffix(
            build_specialist_system_prompt(
                _realistic_state(lead_score=10),
                SpecialistRole.CLOSER,
            ),
        )
        b_suffix = self._suffix(
            build_specialist_system_prompt(
                _realistic_state(lead_score=85),
                SpecialistRole.CLOSER,
            ),
        )
        assert "10" in a_suffix or "lead_score" in a_suffix.lower()
        assert a_suffix != b_suffix


class TestSpecialistRoleAffectsPlaybookSlot:
    """Different specialist roles produce different playbook content (cacheable per-role)."""

    def test_qualifier_and_closer_have_different_playbooks(self) -> None:
        q = build_specialist_system_prompt(_realistic_state(), SpecialistRole.QUALIFIER)
        c = build_specialist_system_prompt(_realistic_state(), SpecialistRole.CLOSER)
        # Both meet the floor independently, but the playbook differs.
        assert q != c

    def test_product_expert_has_distinct_playbook(self) -> None:
        q = build_specialist_system_prompt(_realistic_state(), SpecialistRole.QUALIFIER)
        p = build_specialist_system_prompt(_realistic_state(), SpecialistRole.PRODUCT_EXPERT)
        assert q != p


class TestEmptyAgentIdentityFallsBackGracefully:
    """If tenant has no agent_identity rendered, prefix may still meet floor via static + playbook."""

    def test_no_agent_identity_does_not_crash(self) -> None:
        state = _realistic_state(agent_identity=None)
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert prompt
        # Prefix may not meet 1024 tokens without tenant content — that is OK.
        # Test only asserts no exception + non-empty.


class TestTimestampNotPresentInCacheable:
    """Anti-cache poison: no datetime.now() in cacheable slots."""

    def test_two_consecutive_renders_have_identical_prefix(self) -> None:
        state = _realistic_state()
        a = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        b = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        prefix_a = a.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        prefix_b = b.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert prefix_a == prefix_b


@pytest.mark.parametrize(
    "role",
    [SpecialistRole.QUALIFIER, SpecialistRole.PRODUCT_EXPERT, SpecialistRole.CLOSER],
)
class TestEachRoleEmitsCacheBoundary:
    def test_marker_present(self, role: SpecialistRole) -> None:
        state = _realistic_state()
        prompt = build_specialist_system_prompt(state, role)
        assert CACHE_BOUNDARY_MARKER in prompt
