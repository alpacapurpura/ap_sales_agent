"""G-Eval style LLM-as-judge grader for brand voice fidelity (S7 Fase C scaffold).

Rubric (research-backed: Confident AI 2025, Langfuse 2025, PersonaGym EMNLP
Findings 2025):

1. tone_match (1-5)              — does the response sound like this preset?
2. lexical_alignment (0.0-1.0)   — target unique_vocabulary present, banned absent
3. banned_vocab_absence (0/1)    — hard fail when forbidden phrases appear
4. example_pair_similarity (0-1) — overlap with stored sample_exchanges

The judge LLM is invoked through ``LLMFactory`` so the harness inherits whatever
model the rest of the brand module uses (typically ``ModelRole.REASONING``). When
the LLM is unavailable (CI without API keys), the grader returns ``judge_skipped``
with deterministic placeholder values so tests don't fail on infrastructure absence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GraderRubric:
    """Inputs the judge needs to score a single response."""

    preset_key: str
    prompt: str  # the prospect message that was sent
    response: str  # the agent's output to judge
    target_dimensions: dict  # {energy: 0.7, ...}
    target_vocabulary: tuple[str, ...]  # unique_vocabulary that should be present
    banned_phrases: tuple[str, ...]  # negative_constraints flattened to phrases
    sample_exchanges: tuple[dict, ...]  # author_response anchors


@dataclass(frozen=True)
class GraderResult:
    """Output of grading a single response against a rubric."""

    tone_match: int  # 1-5
    lexical_alignment: float  # 0.0-1.0
    banned_vocab_absence: bool
    example_pair_similarity: float  # 0.0-1.0
    judge_skipped: bool  # True when LLM was unavailable
    judge_reason: str = ""


_JUDGE_SYSTEM_PROMPT = """\
Eres un evaluador de fidelidad de voz de marca. Recibes:
1. Un perfil de personalidad (dimensions + vocabulario único + frases prohibidas).
2. Un mensaje del prospecto.
3. La respuesta del agente.

Devuelve JSON con estas claves:
- tone_match (entero 1-5): qué tan bien la respuesta refleja las dimensions.
- lexical_alignment (0.0-1.0): proporción del vocabulario único presente.
- banned_vocab_absence (true/false): true si NINGUNA frase prohibida aparece.
- example_pair_similarity (0.0-1.0): similitud con los ejemplos del perfil.
- judge_reason: 1-2 oraciones explicando el puntaje.

Solo devuelve el JSON, sin texto adicional.
"""


def _detect_banned(response: str, banned: tuple[str, ...]) -> bool:
    """Hard check — substring match (case-insensitive)."""
    lower = response.lower()
    return not any(phrase.lower() in lower for phrase in banned if phrase)


def _lexical_alignment(response: str, vocab: tuple[str, ...]) -> float:
    """Fraction of target vocabulary present in the response."""
    if not vocab:
        return 1.0
    lower = response.lower()
    hits = sum(1 for v in vocab if v.lower() in lower)
    return hits / len(vocab)


def grade_response(rubric: GraderRubric) -> GraderResult:
    """Run the G-Eval rubric against ``rubric.response``.

    When the LLM judge is unavailable, returns deterministic banned/lexical
    scores (which can be computed locally) and skips the subjective tone +
    similarity grades by setting ``judge_skipped=True``.
    """
    banned_ok = _detect_banned(rubric.response, rubric.banned_phrases)
    lex = _lexical_alignment(rubric.response, rubric.target_vocabulary)

    try:
        from luana_core_llm.factory import LLMFactory
        from luana_core_platform.core.enums import ModelRole
    except Exception:  # noqa: BLE001 — scaffold tolerates missing infra
        return GraderResult(
            tone_match=0,
            lexical_alignment=lex,
            banned_vocab_absence=banned_ok,
            example_pair_similarity=0.0,
            judge_skipped=True,
            judge_reason="LLMFactory not importable (running without infra).",
        )

    try:
        llm = LLMFactory.get_service()
    except Exception:  # noqa: BLE001 — scaffold tolerates missing API key
        return GraderResult(
            tone_match=0,
            lexical_alignment=lex,
            banned_vocab_absence=banned_ok,
            example_pair_similarity=0.0,
            judge_skipped=True,
            judge_reason="LLMFactory could not initialise (missing credentials).",
        )

    user_payload = json.dumps(
        {
            "preset": rubric.preset_key,
            "dimensions": rubric.target_dimensions,
            "unique_vocabulary": list(rubric.target_vocabulary),
            "banned_phrases": list(rubric.banned_phrases),
            "sample_exchanges": list(rubric.sample_exchanges),
            "prompt": rubric.prompt,
            "response": rubric.response,
        },
        ensure_ascii=False,
    )

    try:
        raw = llm.generate_response(
            messages=[{"role": "user", "content": user_payload}],
            system_prompt=_JUDGE_SYSTEM_PROMPT,
            model_type=ModelRole.REASONING,
            temperature=0.0,
            max_output_tokens=400,
        )
    except Exception as e:  # noqa: BLE001
        return GraderResult(
            tone_match=0,
            lexical_alignment=lex,
            banned_vocab_absence=banned_ok,
            example_pair_similarity=0.0,
            judge_skipped=True,
            judge_reason=f"Judge call failed: {e}",
        )

    json_str = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        return GraderResult(
            tone_match=0,
            lexical_alignment=lex,
            banned_vocab_absence=banned_ok,
            example_pair_similarity=0.0,
            judge_skipped=True,
            judge_reason=f"Judge returned invalid JSON: {e}",
        )

    return GraderResult(
        tone_match=int(parsed.get("tone_match", 0)),
        lexical_alignment=float(parsed.get("lexical_alignment", lex)),
        banned_vocab_absence=bool(parsed.get("banned_vocab_absence", banned_ok)),
        example_pair_similarity=float(parsed.get("example_pair_similarity", 0.0)),
        judge_skipped=False,
        judge_reason=str(parsed.get("judge_reason", "")),
    )
