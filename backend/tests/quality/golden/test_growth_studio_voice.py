# voseo-allowed: this file's _VOSEO_REGEX is the *blocklist* applied to golden
# expected_output strings — the verbs cited verbatim are the ones we forbid in
# user-facing copilot UI (per .claude/rules/spanish-text.md R2 + R25 magic
# comment escape for technical references to the glossary).
"""T-4 Story 2B — voice fidelity goldens for Growth Studio actions.

# [GROWTH-STUDIO-VOICE-T4] -> docs/product/stories/growth-studio-actions-schemas-real/03-arch.md § 4.4

3 deterministic eval goldens that lock in 3 invariants for the new
analytics tools registered by T-3 (commit 12962e0d):

* ``stage-query-happy.json`` — voice fidelity (Spanish neutro tuteo)
  for ``get_stage_metrics`` happy path.
* ``etl-refresh-confirm.json`` — tool dispatch correctness +
  polite confirm copy for ``trigger_etl_refresh`` requires_confirmation.
* ``etl-refresh-rate-limited.json`` — no retry loop guarantee for
  ``trigger_etl_refresh`` rate_limit_exceeded.

Pattern mirrors :mod:`tests.quality.golden.test_golden_conversations_semantic`
(F9 + S10 cementado): stub default returns 4.0/dim → pipeline plumbing test;
``RUN_LLM_JUDGE=1`` flips to real NANO judge for weekly cron + ad-hoc
inspection. Threshold ≥3.5 (DEFAULT_THRESHOLD) — same as canonical 20
goldens.

Deterministic invariants (no LLM dependency, run on every CI):

1. **Tool registration check** — each golden's ``expected_tool_call.name``
   must exist in ``ANALYTICS_TOOLS`` (would catch a regression where T-3
   accidentally drops a tool from the list).
2. **Voice constraints** — voseo glossary regex applied to
   ``expected_output``; tildes / max_length / max_lines enforced.
3. **No retry loop** — goldens flagged ``no_retry_loop=True`` MUST NOT
   contain phrases like "intento de nuevo", "vuelvo a intentar" in the
   *same response* (only retry-time copy is allowed).
4. **Polite confirm copy** — goldens flagged ``polite_confirm_required``
   MUST include an interrogative question mark ``?`` and a verb of
   confirmation (e.g. ``confirma``, ``continúo``, ``confirmo``).

LLM-dependent (opt-in via ``RUN_LLM_JUDGE=1``):

5. ``CopilotJudge.evaluate(...)`` returns ``passes_threshold=True`` for
   each golden's ``expected_output`` against the rubric.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from luana_core_copilot.application.observability.judge import (
    DEFAULT_THRESHOLD,
    CopilotJudge,
)
from luana_core_copilot.application.tools.analytics_tools import ANALYTICS_TOOLS

GOLDEN_DIR: Path = Path(__file__).parent / "growth_studio_actions"

# Voseo glossary — defensive subset matching .claude/rules/spanish-text.md
# R2. The pre-commit hook covers files at commit time; this assertion
# covers golden expected_output regression at test time.
_VOSEO_REGEX = re.compile(
    r"\b("
    r"vos|sos|tenés|podés|querés|sabés|hacés|venís|decís|"
    r"mirá|dejá|dejalo|poné|ponelo|usá|usalo|hacé|hacelo|"
    r"elegí|elegilo|seleccioná|arrancá|empezá|agregá|configurá|"
    r"revisá|escribí|guardá|subí|bajá|abrí|volvé|andá|"
    r"cambiá|cambialo|ofrecés|cobrás|ejecutás|acompañás|"
    r"activás|desactivás|linkeá|despublicala|reactivá|cancelala|"
    r"validá|considerá|formulala|marcá|referís|atendés|integrás|"
    r"listá|probá|mostrá|compartí|contá|explicá|fijate|acordate|"
    r"refrescá"
    r")\b",
    re.IGNORECASE,
)

# Confirmation verbs that satisfy "polite_confirm_required". The golden
# must use at least one of these in the expected_output to surface a
# clear yes/no decision to the user (no ambiguous "yo veo si" hedge).
_CONFIRM_VERBS_REGEX = re.compile(
    r"\b(confirmas?|confirmo|continúo|sigo|procedo|adelante)\b",
    re.IGNORECASE,
)

# Phrases that imply "I will retry now" — forbidden when no_retry_loop
# is asserted. Retry-time copy ("Próximo intento en 31 min") is allowed
# because it's *informational*, not "I'm retrying".
_FORBIDDEN_RETRY_PHRASES_REGEX = re.compile(
    r"\b("
    r"intento\s+de\s+nuevo|vuelvo\s+a\s+intentar|reintento|"
    r"lo\s+intento\s+otra\s+vez|reintentar\s+ahora"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class GrowthStudioGolden:
    """Loaded golden ready for assertion."""

    id: str
    category: str
    user_input: str
    expected_output: str
    expected_tool_name: str
    expected_tool_args: dict[str, Any]
    expected_block_kind: str
    expected_tool_response_shape: dict[str, Any] | None
    brand_summary: str
    context: str
    voice_constraints: dict[str, Any]
    source_path: Path


def _load_golden(path: Path) -> GrowthStudioGolden:
    raw = json.loads(path.read_text(encoding="utf-8"))
    tool_call = raw["expected_tool_call"]
    return GrowthStudioGolden(
        id=raw["id"],
        category=raw["category"],
        user_input=raw["user_input"],
        expected_output=raw["expected_output"],
        expected_tool_name=tool_call["name"],
        expected_tool_args=tool_call.get("args", {}),
        expected_block_kind=raw["expected_block_kind"],
        expected_tool_response_shape=raw.get("expected_tool_response_shape"),
        brand_summary=raw["brand_summary"],
        context=raw["context"],
        voice_constraints=raw["voice_constraints"],
        source_path=path,
    )


def _all_goldens() -> tuple[GrowthStudioGolden, ...]:
    files = sorted(GOLDEN_DIR.glob("*.json"))
    return tuple(_load_golden(f) for f in files)


GOLDENS: tuple[GrowthStudioGolden, ...] = _all_goldens()


# ── 1. dataset shape sanity ──────────────────────────────────────────────


def test_growth_studio_goldens_dataset_has_three_entries() -> None:
    """T-4 spec mandates exactly 3 voice fidelity goldens."""
    assert len(GOLDENS) == 3, (
        f"Expected exactly 3 goldens under {GOLDEN_DIR.relative_to(Path.cwd()) if GOLDEN_DIR.is_relative_to(Path.cwd()) else GOLDEN_DIR}, "
        f"got {len(GOLDENS)}: {[g.source_path.name for g in GOLDENS]}"
    )


def test_growth_studio_goldens_ids_unique() -> None:
    ids = [g.id for g in GOLDENS]
    assert len(ids) == len(set(ids)), f"Duplicate golden ids: {ids}"


def test_growth_studio_goldens_cover_three_categories() -> None:
    """One golden per category: tool_dispatch_correctness, polite_confirm, no_retry_loop."""
    found_categories = {g.category for g in GOLDENS}
    expected = {
        "tool_dispatch_correctness",
        "tool_dispatch_polite_confirm",
        "no_retry_loop",
    }
    assert found_categories == expected, (
        f"Expected categories {expected}, got {sorted(found_categories)}. Each golden must lock a distinct invariant."
    )


# ── 2. tool dispatch correctness (deterministic, no LLM) ─────────────────


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_tool_is_registered_in_analytics_tools(
    golden: GrowthStudioGolden,
) -> None:
    """Every golden's expected_tool_call.name must exist in ANALYTICS_TOOLS.

    Regression detector: if T-3 (or any future change) drops a tool from
    ``ANALYTICS_TOOLS``, this test fails and points the dev at the
    affected golden id.
    """
    registered_tool_names = {getattr(t, "name", "") for t in ANALYTICS_TOOLS}
    assert golden.expected_tool_name in registered_tool_names, (
        f"Golden {golden.id!r} expects tool {golden.expected_tool_name!r}, "
        f"but ANALYTICS_TOOLS only registers {sorted(registered_tool_names)}. "
        "Either fix the golden or re-register the missing tool in analytics_tools.py."
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_tool_args_are_well_formed(golden: GrowthStudioGolden) -> None:
    """Tool args dict must be non-empty (no naked tool calls without args)."""
    assert isinstance(golden.expected_tool_args, dict), (
        f"Golden {golden.id!r}: expected_tool_call.args must be a dict; got {type(golden.expected_tool_args).__name__}"
    )
    assert golden.expected_tool_args, (
        f"Golden {golden.id!r}: expected_tool_call.args is empty — every "
        "tool call in scope of T-4 takes at least 1 arg (stage / channel)."
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_block_kind_is_growth_namespaced(
    golden: GrowthStudioGolden,
) -> None:
    """Block kinds must be ``growth.*`` (action registry namespace per T-2)."""
    assert golden.expected_block_kind.startswith("growth."), (
        f"Golden {golden.id!r}: expected_block_kind must start with 'growth.' "
        f"(matches frontend action registry GROWTH_STUDIO_ACTION_KEYS); "
        f"got {golden.expected_block_kind!r}"
    )


# ── 3. Spanish neutro voice constraints (deterministic, no LLM) ──────────


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_output_has_no_voseo(golden: GrowthStudioGolden) -> None:
    """Spanish neutro tuteo only — the voseo glossary is forbidden in copilot UI.

    Per .claude/rules/spanish-text.md R2 + voseo glossary. Sales agent
    OUTPUT can have voseo (it respects tenant voice — feature, not bug),
    but copilot UI is always Spanish neutro.
    """
    matches = _VOSEO_REGEX.findall(golden.expected_output)
    assert not matches, (
        f"Golden {golden.id!r} expected_output uses voseo: {matches}. "
        f"Copilot UI must use Spanish neutro tuteo per .claude/rules/spanish-text.md R2. "
        f"Output: {golden.expected_output!r}"
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_output_respects_max_length(
    golden: GrowthStudioGolden,
) -> None:
    """Length cap: prevents verbose responses that confuse user + bloat tokens."""
    max_len = golden.voice_constraints.get("max_length_chars", 800)
    assert len(golden.expected_output) <= max_len, (
        f"Golden {golden.id!r} expected_output is {len(golden.expected_output)} chars, "
        f"exceeds voice_constraints.max_length_chars={max_len}. Trim the response."
    )


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_expected_output_respects_max_lines(golden: GrowthStudioGolden) -> None:
    """Line cap: matches CHANNEL_FORMATS expectations for chat surfaces."""
    max_lines = golden.voice_constraints.get("max_lines", 12)
    line_count = len(golden.expected_output.splitlines()) or 1
    assert line_count <= max_lines, (
        f"Golden {golden.id!r} expected_output has {line_count} lines, exceeds voice_constraints.max_lines={max_lines}."
    )


# ── 4. polite confirm + no retry loop (deterministic, no LLM) ────────────


@pytest.mark.parametrize(
    "golden",
    [g for g in GOLDENS if g.voice_constraints.get("polite_confirm_required")],
    ids=lambda g: g.id,
)
def test_polite_confirm_uses_explicit_question(
    golden: GrowthStudioGolden,
) -> None:
    """When confirm is required, the response MUST surface a yes/no question."""
    assert "?" in golden.expected_output or "¿" in golden.expected_output, (
        f"Golden {golden.id!r}: polite_confirm_required → "
        "expected_output must surface a question mark (¿…?) so the user "
        f"sees an explicit yes/no decision. Got: {golden.expected_output!r}"
    )
    assert _CONFIRM_VERBS_REGEX.search(golden.expected_output), (
        f"Golden {golden.id!r}: polite_confirm_required → expected_output "
        "must use a confirmation verb (confirmas / confirmo / continúo / "
        f"sigo / procedo / adelante). Got: {golden.expected_output!r}"
    )


@pytest.mark.parametrize(
    "golden",
    [g for g in GOLDENS if g.voice_constraints.get("no_retry_loop")],
    ids=lambda g: g.id,
)
def test_no_retry_loop_phrases_in_expected_output(
    golden: GrowthStudioGolden,
) -> None:
    """Reject phrases that imply 'I'm retrying right now' (transcript_constraint max_turns=2).

    Allowed: informational retry copy ("Próximo intento en 31 min").
    Forbidden: action retry copy ("intento de nuevo", "vuelvo a intentar").
    """
    matches = _FORBIDDEN_RETRY_PHRASES_REGEX.findall(golden.expected_output)
    assert not matches, (
        f"Golden {golden.id!r}: no_retry_loop=True but expected_output "
        f"contains action-retry phrases {matches}. Use informational copy "
        "('Próximo intento en X min') instead — agent must NOT re-invoke "
        "the tool in the same turn (per spec scenario 2 transcript_constraint)."
    )


@pytest.mark.parametrize(
    "golden",
    [g for g in GOLDENS if g.voice_constraints.get("max_tool_invocations_per_turn") is not None],
    ids=lambda g: g.id,
)
def test_max_tool_invocations_per_turn_is_one_for_no_retry_loop(
    golden: GrowthStudioGolden,
) -> None:
    """Anti-loop guarantee: single-shot dispatch (≤1 invocation per turn)."""
    cap = golden.voice_constraints["max_tool_invocations_per_turn"]
    assert isinstance(cap, int) and cap == 1, (
        f"Golden {golden.id!r}: max_tool_invocations_per_turn must be exactly 1 "
        f"to enforce single-shot dispatch (no retry loop). Got: {cap!r}"
    )


@pytest.mark.parametrize(
    "golden",
    [g for g in GOLDENS if g.voice_constraints.get("retry_copy_required")],
    ids=lambda g: g.id,
)
def test_retry_copy_present_when_rate_limited(
    golden: GrowthStudioGolden,
) -> None:
    """Rate-limited golden must surface retry-time copy so user knows when to come back."""
    has_retry_copy = any(
        token in golden.expected_output.lower()
        for token in (
            "próximo intento",
            "intenta de nuevo en",
            "intenta nuevamente en",
            "disponible en",
            "vuelve a intentar en",
            "minutos",
        )
    )
    assert has_retry_copy, (
        f"Golden {golden.id!r}: retry_copy_required=True → expected_output "
        f"must include retry-time copy (e.g. 'Próximo intento disponible en 31 min'). "
        f"Got: {golden.expected_output!r}"
    )


# ── 5. CopilotJudge LLM scoring (stub default, opt-in real LLM) ──────────


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_growth_studio_golden_judges_above_threshold(golden: GrowthStudioGolden, judge_llm: object) -> None:
    """Pipeline test — every golden must be judged ≥3.5/5 by the active LLM.

    In stub mode (default — every CI run) the judge returns 4.0/dim → all
    pass; this proves the wiring is correct. In real mode (RUN_LLM_JUDGE=1
    weekly cron + ad-hoc) a genuine voice regression fails the build.
    """
    judge = CopilotJudge(llm=judge_llm)
    result = judge.evaluate(
        user_input=golden.user_input,
        assistant_output=golden.expected_output,
        brand_summary=golden.brand_summary,
        context=golden.context,
    )
    assert result.passes_threshold, (
        f"Golden {golden.id!r} judged below threshold {DEFAULT_THRESHOLD}: "
        f"avg={result.avg_score} dims={[(d.name, d.score) for d in result.dimensions]} "
        f"meta={result.metadata}"
    )
