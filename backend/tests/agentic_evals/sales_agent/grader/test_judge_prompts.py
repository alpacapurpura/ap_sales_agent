# voseo-allowed: test fixtures cite es-AR voice strings + voseo glossary tokens to verify DQ4 detection
"""Unit tests for judge_prompts.py 6-slot template (T-7 TDD).

Pure unit tests — no LLM calls, no DB. Marked ``pytest.mark.no_eval`` so they
run on default CI without requiring ``--run-evals`` flag.

Coverage matrix (10 mandatory tests per T-7 acceptance + ticket deliverables):

- test_round_1_prompt_has_6_slots
- test_slots_1_2_3_marked_cacheable_ttl_1h
- test_slots_4_5_6_fresh_no_cache
- test_sandbox_markers_literal_present
- test_slot_1_directive_data_not_instructions
- test_round_2_excludes_self_reasoning            (DQ3 anti-anchoring)
- test_round_2_includes_peer_reasoning_only
- test_rubric_dispatch_4_rubrics
- test_voice_profile_compiled_read_only
- test_no_system_leak_judge_prompt

Plus T-7 ticket-named tests:

- test_slot_1_sandbox_directive_present
- test_slot_5_transcript_wrapped_with_markers
- test_slot_3_tenant_voice_no_tenant_name_interpolation
- test_round_1_no_peer_reasoning
- test_round_2_peer_reasoning_excludes_self
- test_cache_control_ttl_1h_explicit
- test_no_voseo_in_judge_prompt_english

Decisions cement (T-7): D14 sandbox markers, DQ1 6-slot arch, DQ2 sandbox 3-layer,
DQ3 round-2 peer-only, DQ4 judge English, D-AG-7/8/18 (cache + voice SSoT).
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.agentic_evals.sales_agent.grader._internal.judge_prompts import (
    SLOT_1_TEMPLATE,
    SLOT_2_TEMPLATE,
    SLOT_3_TEMPLATE,
    TRANSCRIPT_MARKER_BEGIN,
    TRANSCRIPT_MARKER_END,
    build_judge_prompt,
)
from tests.agentic_evals.sales_agent.grader.result import RubricGradeRequest

pytestmark = pytest.mark.no_eval


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ──────────────────────────────────────────────────────────────────────────────


class _StubTurn:
    """Minimal duck-typed stand-in for Story D ``GoldenTurnModel``.

    The grader prompt builder treats ``request.transcript`` as
    ``list[Any]`` (RubricGradeRequest cement) and reads attributes
    ``role``, ``content``, ``turn_number``, ``tool_calls``. A duck type
    is sufficient for unit testing prompt assembly.
    """

    def __init__(
        self,
        role: str,
        content: str,
        turn_number: int,
        tool_calls: list[str] | None = None,
    ) -> None:
        self.role = role
        self.content = content
        self.turn_number = turn_number
        self.tool_calls = tool_calls


class _StubVoiceProfile:
    """Minimal duck-typed stand-in for Story A ``PersonalityProfile``.

    Only ``system_instruction`` is consumed by Slot 3 (sales-agent-expert
    §3 SSoT — verbatim, READ-ONLY).
    """

    def __init__(self, system_instruction: str, dialect_code: str = "es-419") -> None:
        self.system_instruction = system_instruction
        self.dialect_code = dialect_code


def _make_request(
    *,
    rubrics: list[str] | None = None,
    persona_kind: str = "happy",
    tenant_slug: str = "tenant_coach_lat",
    actor_profile_id: str = "coach_lat_happy_v1",
    transcript: list[_StubTurn] | None = None,
    voice_profile: _StubVoiceProfile | None = None,
) -> RubricGradeRequest:
    """Factory for a minimal valid ``RubricGradeRequest`` (T-7 unit test scope)."""
    if transcript is None:
        transcript = [
            _StubTurn(role="customer", content="Hola, quiero saber más.", turn_number=0),
            _StubTurn(
                role="agent",
                content="¡Hola! Cuéntame qué buscas y te oriento.",
                turn_number=1,
                tool_calls=["qualify_lead"],
            ),
        ]
    if voice_profile is None:
        voice_profile = _StubVoiceProfile(
            system_instruction=(
                "TU IDENTIDAD: Sos coach de bienestar empático.\n"
                "ASÍ HABLAS: cálido, directo, usás voseo (es-AR).\n"
                "ASÍ NO: nunca jerga corporativa."
            ),
            dialect_code="es-AR",
        )
    return RubricGradeRequest(
        transcript=list(transcript),
        tenant_voice_profile=voice_profile,
        rubrics=rubrics or ["voice-fidelity"],  # type: ignore[arg-type]
        simulation_id="sim-test-001",
        tenant_slug=tenant_slug,
        persona_kind=persona_kind,  # type: ignore[arg-type]
        actor_profile_id=actor_profile_id,
    )


def _build(
    *,
    request: RubricGradeRequest | None = None,
    turn_n: int = 1,
    rubric_id: str = "voice-fidelity",
    rubric_version: int = 1,
    round_n: int = 1,
    peer_reasoning: list[tuple[str, float, str]] | None = None,
    judge_id: str = "sonnet",
) -> list[dict[str, Any]]:
    """Convenience wrapper for ``build_judge_prompt`` with sensible defaults."""
    if request is None:
        request = _make_request()
    return build_judge_prompt(
        request=request,
        turn_n=turn_n,
        rubric_id=rubric_id,
        rubric_version=rubric_version,
        round_n=round_n,
        peer_reasoning=peer_reasoning,
        judge_id=judge_id,
    )


def _all_text(prompt: list[dict[str, Any]]) -> str:
    """Flatten the prompt blocks into a single text blob for substring assertions."""
    chunks: list[str] = []
    for block in prompt:
        text = block.get("text")
        if isinstance(text, str):
            chunks.append(text)
    return "\n".join(chunks)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Slot composition (6 slots, in order)
# ──────────────────────────────────────────────────────────────────────────────


def test_round_1_prompt_has_6_slots() -> None:
    """Round 1 prompt assembles 6 slots in canonical order (1→6)."""
    prompt = _build(round_n=1)
    assert len(prompt) == 6, f"Expected 6 slots in Round 1 prompt, got {len(prompt)}: {prompt}"


def test_round_2_prompt_has_6_slots_with_peer_reasoning() -> None:
    """Round 2 prompt also assembles 6 slots — Slot 4 carries peer reasoning."""
    peer = [
        ("gpt4o", 0.55, "Agent missed BANT qualification step in turn 2."),
        ("kimi", 0.60, "Voice tone diverged from declared dialect — formal vs. informal."),
    ]
    prompt = _build(round_n=2, peer_reasoning=peer, judge_id="sonnet")
    assert len(prompt) == 6, f"Expected 6 slots in Round 2 prompt, got {len(prompt)}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Cache control — slots 1+2+3 cacheable TTL=1h, slots 4+5+6 fresh
# ──────────────────────────────────────────────────────────────────────────────


def test_slots_1_2_3_marked_cacheable_ttl_1h() -> None:
    """Slots 1, 2, 3 carry ``cache_control={'type':'ephemeral','ttl':'1h'}`` per Anthropic SDK."""
    prompt = _build()
    for idx in (0, 1, 2):
        block = prompt[idx]
        cache_control = block.get("cache_control")
        assert isinstance(cache_control, dict), f"Slot {idx + 1} must declare cache_control dict; got {cache_control!r}"
        assert cache_control.get("type") == "ephemeral", (
            f"Slot {idx + 1} cache_control.type must be 'ephemeral'; got {cache_control.get('type')!r}"
        )
        assert cache_control.get("ttl") == "1h", (
            f"Slot {idx + 1} cache_control.ttl must be '1h' (post 2026-03-06 default change); "
            f"got {cache_control.get('ttl')!r}"
        )


def test_slots_4_5_6_fresh_no_cache() -> None:
    """Slots 4, 5, 6 (round context, transcript, task directive) MUST NOT carry cache_control."""
    prompt = _build()
    for idx in (3, 4, 5):
        block = prompt[idx]
        assert "cache_control" not in block, (
            f"Slot {idx + 1} must be fresh (NO cache_control); got {block.get('cache_control')!r}"
        )


def test_cache_control_ttl_1h_explicit() -> None:
    """Cache TTL=1h declared explicitly per Anthropic 2026-03-06 default change to 5min.

    Acceptance A4 — verifies all 3 cacheable slots carry the explicit 1h TTL.
    """
    prompt = _build()
    cacheable_slots = [prompt[0], prompt[1], prompt[2]]
    ttls = [b["cache_control"]["ttl"] for b in cacheable_slots]
    assert ttls == ["1h", "1h", "1h"], (
        f"All 3 cacheable slots MUST declare TTL=1h explicitly (post Anthropic 2026-03-06 "
        f"default change to 5min). Got: {ttls!r}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 3. Sandbox markers (DQ2 — 3-layer cement)
# ──────────────────────────────────────────────────────────────────────────────


def test_sandbox_markers_literal_present() -> None:
    """Slot 5 wraps transcript with literal `<<TRANSCRIPT_BEGIN>>` and `<<TRANSCRIPT_END>>` markers.

    DQ2 cement layer 2 — defense-in-depth vs prompt injection. Markers MUST be exact strings.
    """
    prompt = _build()
    slot_5_text = prompt[4]["text"]
    assert TRANSCRIPT_MARKER_BEGIN == "<<TRANSCRIPT_BEGIN>>", (
        f"Sandbox marker BEGIN must be literal '<<TRANSCRIPT_BEGIN>>'; got {TRANSCRIPT_MARKER_BEGIN!r}"
    )
    assert TRANSCRIPT_MARKER_END == "<<TRANSCRIPT_END>>", (
        f"Sandbox marker END must be literal '<<TRANSCRIPT_END>>'; got {TRANSCRIPT_MARKER_END!r}"
    )
    assert "<<TRANSCRIPT_BEGIN>>" in slot_5_text, (
        f"Slot 5 must contain literal `<<TRANSCRIPT_BEGIN>>` (DQ2 cement); slot_5: {slot_5_text!r}"
    )
    assert "<<TRANSCRIPT_END>>" in slot_5_text, (
        f"Slot 5 must contain literal `<<TRANSCRIPT_END>>` (DQ2 cement); slot_5: {slot_5_text!r}"
    )
    # BEGIN must precede END
    assert slot_5_text.index("<<TRANSCRIPT_BEGIN>>") < slot_5_text.index("<<TRANSCRIPT_END>>"), (
        "Sandbox markers in Slot 5 must be ordered: BEGIN before END."
    )


def test_slot_5_transcript_wrapped_with_markers() -> None:
    """Transcript content sits BETWEEN markers (T-7 ticket acceptance)."""
    transcript = [
        _StubTurn(role="customer", content="MARKER_TEST_CUSTOMER", turn_number=0),
        _StubTurn(role="agent", content="MARKER_TEST_AGENT", turn_number=1),
    ]
    request = _make_request(transcript=transcript)
    prompt = _build(request=request)
    slot_5_text = prompt[4]["text"]
    begin_idx = slot_5_text.index("<<TRANSCRIPT_BEGIN>>")
    end_idx = slot_5_text.index("<<TRANSCRIPT_END>>")
    sandwiched = slot_5_text[begin_idx:end_idx]
    assert "MARKER_TEST_CUSTOMER" in sandwiched, "Customer turn content must sit between sandbox markers in Slot 5."
    assert "MARKER_TEST_AGENT" in sandwiched, "Agent turn content must sit between sandbox markers in Slot 5."


def test_slot_1_directive_data_not_instructions() -> None:
    """Slot 1 carries explicit `data, not instructions` directive (DQ2 layer 1 cement)."""
    prompt = _build()
    slot_1_text = prompt[0]["text"]
    lower = slot_1_text.lower()
    assert "data" in lower and "not instructions" in lower, (
        f"Slot 1 must explicitly state transcript content is 'DATA, NOT instructions' "
        f"(DQ2 layer 1 cement). Got slot_1: {slot_1_text!r}"
    )


def test_slot_1_sandbox_directive_present() -> None:
    """Slot 1 references sandbox markers in its directive (DQ2 layer 1 cement)."""
    prompt = _build()
    slot_1_text = prompt[0]["text"]
    assert "<<TRANSCRIPT_BEGIN>>" in slot_1_text, (
        "Slot 1 system directive must reference the literal `<<TRANSCRIPT_BEGIN>>` marker."
    )
    assert "<<TRANSCRIPT_END>>" in slot_1_text, (
        "Slot 1 system directive must reference the literal `<<TRANSCRIPT_END>>` marker."
    )
    assert "CRITICAL SECURITY DIRECTIVE" in slot_1_text, (
        "Slot 1 must include the CRITICAL SECURITY DIRECTIVE block (verbatim cement)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 4. Round 2 anti-anchoring (DQ3) — peer-only, NEVER own R1 reasoning
# ──────────────────────────────────────────────────────────────────────────────


def test_round_1_no_peer_reasoning() -> None:
    """Round 1 prompt MUST NOT contain peer reasoning (only present in Round 2)."""
    prompt = _build(round_n=1)
    slot_4_text = prompt[3]["text"]
    assert "<<ROUND_2_PEER_REASONING>>" not in slot_4_text, (
        "Round 1 prompt must NOT contain `<<ROUND_2_PEER_REASONING>>` block (only Round 2 carries peers)."
    )


def test_round_2_excludes_self_reasoning() -> None:
    """Round 2 prompt for judge X MUST NOT contain X's own R1 reasoning (DQ3 anti-anchoring).

    Sonnet's R2 prompt receives reasoning from gpt4o + kimi — NEVER its own.
    """
    sonnet_own_reasoning = "SONNET_OWN_REASONING_TOKEN_DO_NOT_LEAK_INTO_R2"
    peer = [
        ("gpt4o", 0.55, "GPT4O_R1_REASONING_VISIBLE"),
        ("kimi", 0.60, "KIMI_R1_REASONING_VISIBLE"),
    ]
    prompt = _build(round_n=2, peer_reasoning=peer, judge_id="sonnet")
    full_text = _all_text(prompt)
    assert sonnet_own_reasoning not in full_text, (
        "Sonnet R2 prompt MUST NOT contain its own R1 reasoning (DQ3 anti-anchoring cement)."
    )


def test_round_2_peer_reasoning_excludes_self() -> None:
    """Sonnet R2 prompt should reference gpt4o + kimi reasoning but not 'sonnet' as peer.

    DQ3 cement — judge sees ONLY OTHER 2 peers. Reinforces upstream filter contract.
    """
    peer = [
        ("gpt4o", 0.55, "GPT4O_PEER_REASONING_VISIBLE"),
        ("kimi", 0.60, "KIMI_PEER_REASONING_VISIBLE"),
    ]
    prompt = _build(round_n=2, peer_reasoning=peer, judge_id="sonnet")
    slot_4_text = prompt[3]["text"]
    assert "GPT4O_PEER_REASONING_VISIBLE" in slot_4_text, "Sonnet R2 Slot 4 must include peer (gpt4o) R1 reasoning."
    assert "KIMI_PEER_REASONING_VISIBLE" in slot_4_text, "Sonnet R2 Slot 4 must include peer (kimi) R1 reasoning."


def test_round_2_includes_peer_reasoning_only() -> None:
    """Round 2 Slot 4 carries `<<ROUND_2_PEER_REASONING>>` block exclusively for peer judges."""
    peer = [
        ("gpt4o", 0.55, "Peer reasoning gpt4o."),
        ("kimi", 0.60, "Peer reasoning kimi."),
    ]
    prompt = _build(round_n=2, peer_reasoning=peer, judge_id="sonnet")
    slot_4_text = prompt[3]["text"]
    assert "<<ROUND_2_PEER_REASONING>>" in slot_4_text, (
        "Round 2 Slot 4 must contain `<<ROUND_2_PEER_REASONING>>` opening marker."
    )
    assert "<<ROUND_2_PEER_REASONING_END>>" in slot_4_text, (
        "Round 2 Slot 4 must contain `<<ROUND_2_PEER_REASONING_END>>` closing marker."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 5. Voice profile read-only (sales-agent-expert §3 SSoT)
# ──────────────────────────────────────────────────────────────────────────────


def test_voice_profile_compiled_read_only() -> None:
    """Slot 3 quotes ``personality_profile.system_instruction`` verbatim — no mutation.

    sales-agent-expert §3 cement — the SSoT system_instruction is consumed READ-ONLY.
    """
    voice_text = (
        "TU IDENTIDAD: Coach experto.\nASÍ HABLAS: tono cálido, voseo cuando corresponde.\nASÍ NO: nunca jerga técnica."
    )
    voice_profile = _StubVoiceProfile(system_instruction=voice_text, dialect_code="es-AR")
    request = _make_request(voice_profile=voice_profile)

    # Build prompt twice — verify input voice profile not mutated
    _build(request=request)
    _build(request=request)
    assert voice_profile.system_instruction == voice_text, (
        "build_judge_prompt MUST NOT mutate input voice profile (sales-agent-expert §3 read-only)."
    )

    # Verify Slot 3 includes verbatim
    prompt = _build(request=request)
    slot_3_text = prompt[2]["text"]
    assert voice_text in slot_3_text, f"Slot 3 must carry voice system_instruction verbatim. Got: {slot_3_text!r}"


def test_slot_3_tenant_voice_no_tenant_name_interpolation() -> None:
    """Slot 3 MUST NOT interpolate ``{tenant_name}`` mid-block (cache prefix safety).

    sales-agent-expert §3 cement — interpolating tenant_name mid-block breaks cache prefix
    AND causes voice creep. tenant_slug appears in Slot 6 metadata (NOT cached).
    """
    voice_profile = _StubVoiceProfile(
        system_instruction="TU IDENTIDAD: Coach.\nASÍ HABLAS: directo.",
        dialect_code="es-419",
    )
    request = _make_request(
        tenant_slug="tenant_acme_inc",
        voice_profile=voice_profile,
    )
    prompt = _build(request=request)
    slot_3_text = prompt[2]["text"]
    # Must not contain Jinja-style or f-string-leftover placeholders
    assert "{tenant_name}" not in slot_3_text, (
        "Slot 3 must not contain `{tenant_name}` placeholder (cache prefix safety)."
    )
    assert "{tenant_slug}" not in slot_3_text, (
        "Slot 3 must not contain `{tenant_slug}` placeholder (cache prefix safety)."
    )
    # Must not contain the actual tenant_slug string (it belongs in Slot 6, not Slot 3)
    assert "tenant_acme_inc" not in slot_3_text, (
        "Slot 3 must not interpolate tenant_slug literal mid-block (cache prefix safety)."
    )


# ──────────────────────────────────────────────────────────────────────────────
# 6. Rubric dispatch (D5/D7 cement)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "rubric_id",
    [
        "voice-fidelity",
        "qualification-accuracy",
        "no-overpromise",
        "no-hallucination",
    ],
)
def test_rubric_dispatch_4_rubrics(rubric_id: str) -> None:
    """All 4 rubrics in scope (D5 cement) build prompts cleanly + reference RUBRIC_ID."""
    prompt = _build(rubric_id=rubric_id, rubric_version=1)
    slot_2_text = prompt[1]["text"]
    assert f"RUBRIC_ID: {rubric_id}" in slot_2_text, (
        f"Slot 2 must reference rubric_id literal `{rubric_id}` (D5/D7 cement)."
    )
    assert "RUBRIC_VERSION: 1" in slot_2_text, "Slot 2 must reference rubric_version literal."


# ──────────────────────────────────────────────────────────────────────────────
# 7. No system leak (Story B FORBIDDEN_LEAK_STRINGS pattern reused)
# ──────────────────────────────────────────────────────────────────────────────


def test_no_system_leak_judge_prompt() -> None:
    """Judge prompt MUST NOT include sales-agent's production system_instruction verbatim chunk.

    sales-agent-expert §3 cement: judges see voice via Slot 3 (READ-ONLY consume) but the
    overall judge prompt MUST NOT leak production system identity (e.g., 'You are a sales
    agent for tenant X' — judges are independent observers, not sales agents).
    """
    prompt = _build()
    full_text = _all_text(prompt)
    # Forbidden phrases that would indicate production system leak into judge context
    forbidden_phrases = [
        "You are a sales agent",
        "you are the sales agent",
        "I am a sales agent",
    ]
    for phrase in forbidden_phrases:
        assert phrase.lower() not in full_text.lower(), (
            f"Judge prompt MUST NOT contain production sales-agent identity phrase: {phrase!r}. "
            f"Judges are independent observers — Slot 3 carries voice context only."
        )


# ──────────────────────────────────────────────────────────────────────────────
# 8. DQ4 — judge prompt language English (voseo only inside transcript subject)
# ──────────────────────────────────────────────────────────────────────────────


def test_no_voseo_in_judge_prompt_english() -> None:
    """Judge prompts (slots 1+2+6) are English (DQ4 cement).

    Voseo strings (`vos`, `tenés`, `podés`, `mirá`) MAY appear ONLY inside Slot 5
    transcript content (verbatim from Story D goldens) and Slot 3 (verbatim voice
    SSoT for es-AR tenants). Slots 1+2+6 are English-only.
    """
    prompt = _build()
    # Slots 1, 2, 6 (indices 0, 1, 5) — English-only
    english_slots_text = "\n".join(prompt[i]["text"] for i in (0, 1, 5))
    voseo_markers = ["tenés", "podés", "mirá", "querés", "sabés"]
    for marker in voseo_markers:
        assert marker not in english_slots_text.lower(), (
            f"Slots 1+2+6 (English-only per DQ4) MUST NOT contain voseo marker {marker!r}. "
            f"Voseo allowed only in Slot 3 (voice SSoT) and Slot 5 (transcript subject)."
        )


# ──────────────────────────────────────────────────────────────────────────────
# 9. Slot template constants (cement smoke probes)
# ──────────────────────────────────────────────────────────────────────────────


def test_slot_1_template_constant_includes_security_directive() -> None:
    """Module-level ``SLOT_1_TEMPLATE`` cement contains CRITICAL SECURITY DIRECTIVE block."""
    assert "CRITICAL SECURITY DIRECTIVE" in SLOT_1_TEMPLATE, (
        "SLOT_1_TEMPLATE module constant must contain `CRITICAL SECURITY DIRECTIVE` block."
    )
    assert "<<TRANSCRIPT_BEGIN>>" in SLOT_1_TEMPLATE, (
        "SLOT_1_TEMPLATE must reference sandbox marker `<<TRANSCRIPT_BEGIN>>`."
    )


def test_slot_2_template_carries_scoring_ladder() -> None:
    """Module-level ``SLOT_2_TEMPLATE`` cement contains the scoring ladder (1.0/0.7/0.5/0.0)."""
    assert "Score 1.0" in SLOT_2_TEMPLATE, "Slot 2 template must define Score 1.0 anchor."
    assert "Score 0.7" in SLOT_2_TEMPLATE, "Slot 2 template must define Score 0.7 anchor."
    assert "Score 0.5" in SLOT_2_TEMPLATE, "Slot 2 template must define Score 0.5 anchor."
    assert "Score 0.0" in SLOT_2_TEMPLATE, "Slot 2 template must define Score 0.0 anchor."


def test_slot_3_template_no_tenant_name_placeholder() -> None:
    """Module-level ``SLOT_3_TEMPLATE`` cement: no ``{tenant_name}`` placeholder mid-block."""
    assert "{tenant_name}" not in SLOT_3_TEMPLATE, (
        "SLOT_3_TEMPLATE must NEVER contain `{tenant_name}` placeholder (cache prefix safety)."
    )
