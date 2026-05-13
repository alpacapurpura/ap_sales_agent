"""F4 — URL inspiration analyzer (LLM judge + structured output).

Takes the raw markdown produced by ``trafilatura_client.fetch_extract``
plus the (optional) brand lighthouse and asks an LLM to:

1. Summarize the page in ≤500 chars Spanish neutro.
2. Extract sub-elements (testimonials, CTAs, value props, visual cues).
3. Score ``brand_relevance`` 0.0..1.0 against the brand lighthouse.
4. Suggest a kebab-case ``slug`` (used as scratchpad filename + DB key).

Isolated from the ``fetch_url`` tool wrapper so unit tests can drive
the pipeline directly with a stubbed LLM, and so the deepagents
``url_analyzer`` subagent can call it without re-implementing the
prompt logic.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from luana_core_copilot.application.orchestrator.stream_filters import (
    INTERNAL_LLM_CONFIG,
)
from luana_core_platform.core.enums import ModelRole

logger = structlog.get_logger()


# Hard cap on the markdown we send to the LLM. trafilatura already
# strips boilerplate, but a long-form page can still exceed 30K chars
# which inflates cost without changing the summary materially. 12K is
# enough for a long article + sub-elements detection.
_MAX_INPUT_CHARS = 12_000
_SUMMARY_HARD_CAP = 600
_DEFAULT_RELEVANCE = 0.5

_SLUG_RE = re.compile(r"[^a-z0-9-]+")
_VOSEO_RE = re.compile(
    r"\b("
    r"vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|"
    r"mirá|dejá|poné|usá|hacé|seleccioná|empezá|arrancá|agregá|configurá|revisá|"
    r"guardá|cambiá|escribí|subí|abrí|volvé|elegí|seguí|sentí|salí|"
    r"compartí|fijate|acordate"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class InspirationAnalysis:
    """Structured outcome of the LLM analysis pass."""

    slug: str
    summary: str
    sub_elements: dict
    brand_relevance_score: float


_SYSTEM_PROMPT_ES = """Eres un analista de inspiración de marca para Nicolify.
El usuario te entrega una URL como referencia: competencia, ejemplo, swipe file.
Tu trabajo es destilar el contenido en un resumen corto, identificar elementos
reusables (testimonios, CTAs, propuestas de valor, cues visuales) y calificar
qué tan relevante es para la marca del tenant.

Reglas:
- Español latinoamericano neutro tuteo (`tú`). Sin voseo.
- Resumen ≤500 caracteres. Sin pleonasmo.
- ``brand_relevance_score`` 0.0..1.0:
  0.9+ = misma audiencia + misma propuesta + tono compatible
  0.5..0.8 = audiencia parcial o tono útil aunque no idéntico
  < 0.4 = poco aplicable, dudo si vale guardarlo
- Si el contenido es JS-heavy, paywall o no se entiende, devolvé un resumen
  honesto explicando la limitación + score bajo.
- Devuelve SIEMPRE un JSON válido con el shape pedido. Sin markdown, sin
  comillas backtick, sin texto extra.
"""


def _build_user_prompt(
    *,
    url: str,
    why: str,
    brand_lighthouse: str | None,
    page_title: str | None,
    content_md: str,
) -> str:
    """Assemble the user-side payload — keeps the system prompt cacheable."""
    why_block = why.strip() or "(sin razón explícita; el usuario solo pegó la URL)"
    lighthouse_block = (
        brand_lighthouse.strip()
        if brand_lighthouse
        else "(no hay brand lighthouse — usá criterios genéricos: claridad, autoridad, tono humano)"
    )
    title_block = page_title or "(sin título)"
    body = content_md[:_MAX_INPUT_CHARS]
    if len(content_md) > _MAX_INPUT_CHARS:
        body += "\n\n…(truncado para análisis)"

    return f"""URL: {url}
Razón del usuario: {why_block}

## Brand lighthouse del tenant
{lighthouse_block}

## Página (título + contenido en markdown)
**{title_block}**

{body}

## Devolveme JSON
```
{{
  "slug": "kebab-case-corto-derivado-del-domain-y-tema",
  "summary": "≤500 chars en español neutro tuteo describiendo el ángulo aprovechable",
  "brand_relevance_score": 0.0,
  "sub_elements": {{
    "testimonials": ["frase corta o nombre + frase, máximo 3"],
    "ctas": ["copy del CTA, máximo 3"],
    "value_props": ["propuesta de valor o promesa, máximo 3"],
    "visual_cues": ["palette / fotografía / tipografía, máximo 3"]
  }}
}}
```
"""


def _slugify(raw: str, fallback_domain: str) -> str:
    """Best-effort kebab-case slug. Falls back to ``fallback_domain`` parts."""
    candidate = (raw or "").strip().lower()
    candidate = _SLUG_RE.sub("-", candidate).strip("-")
    if not candidate:
        candidate = _SLUG_RE.sub("-", fallback_domain.lower()).strip("-") or "inspiracion"
    return candidate[:80]


def _coerce_score(raw: object) -> float:
    """Clamp ``raw`` to 0..1; return ``_DEFAULT_RELEVANCE`` on parse fail."""
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return _DEFAULT_RELEVANCE
    return max(0.0, min(1.0, value))


def _coerce_sub_elements(raw: object) -> dict:
    """Normalize ``sub_elements`` to ``{key: list[str]}`` shape."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for key in ("testimonials", "ctas", "value_props", "visual_cues"):
        value = raw.get(key)
        if isinstance(value, list):
            out[key] = [str(item).strip() for item in value if str(item).strip()][:5]
        else:
            out[key] = []
    return out


def _truncate_summary(text: str) -> str:
    """Cap ``text`` to the summary hard cap. Adds an ellipsis when truncated."""
    cleaned = text.strip()
    if len(cleaned) <= _SUMMARY_HARD_CAP:
        return cleaned
    return cleaned[: _SUMMARY_HARD_CAP - 1].rstrip() + "…"


def _strip_voseo(text: str) -> str:
    """Soft-replacement: voseo lexemes → neutral copy.

    Last-ditch defense if the LLM ignored the prompt rule. We do NOT
    retry the call — the summary is short enough that a small lexical
    swap costs nothing and never makes the copy worse than passing it
    through. Reuses the same regex shape as ``judge_summary`` so the
    voseo glossary stays single-source.
    """

    def _replace(match: re.Match[str]) -> str:
        word = match.group(0).lower()
        return _VOSEO_REPLACEMENTS.get(word, word)

    return _VOSEO_RE.sub(_replace, text)


# Tiny inline dictionary — the catch-all regex above; this map only
# needs the high-frequency forms the LLM emits when it slips. Anything
# not listed falls through unchanged (still better than failing).
_VOSEO_REPLACEMENTS: dict[str, str] = {
    "vos": "tú",
    "sos": "eres",
    "tenés": "tienes",
    "querés": "quieres",
    "podés": "puedes",
    "sabés": "sabes",
    "hacés": "haces",
    "venís": "vienes",
    "decís": "dices",
    "mirá": "mira",
    "dejá": "deja",
    "poné": "pon",
    "usá": "usa",
    "hacé": "haz",
    "seleccioná": "selecciona",
    "empezá": "empieza",
    "arrancá": "empieza",
    "agregá": "agrega",
    "configurá": "configura",
    "revisá": "revisa",
    "guardá": "guarda",
    "cambiá": "cambia",
    "escribí": "escribe",
    "subí": "sube",
    "abrí": "abre",
    "volvé": "vuelve",
    "elegí": "elige",
    "seguí": "sigue",
    "sentí": "siente",
    "salí": "sal",
    "compartí": "comparte",
    "fijate": "ten en cuenta",
    "acordate": "recuerda",
}


def parse_llm_output(raw: str, *, fallback_domain: str) -> InspirationAnalysis:
    """Best-effort parse of the LLM JSON response.

    Tolerates fenced code blocks (```json ... ```) and stray prose by
    locating the first/last brace. Falls back to neutral defaults when
    a field is missing — the tool never raises on parse failure; it
    surfaces the row with a low relevance score so the user can still
    pin it manually if useful.
    """
    cleaned = raw.strip()
    # Pull JSON out of fenced code blocks.
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # Or out of prose: take from first { to last }.
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last > first:
        cleaned = cleaned[first : last + 1]

    try:
        payload = json.loads(cleaned)
    except (TypeError, ValueError):
        logger.warning("url_inspiration_llm_parse_failed", preview=raw[:200])
        return InspirationAnalysis(
            slug=_slugify("", fallback_domain),
            summary="No se pudo analizar la URL automáticamente. Revisá el contenido manualmente.",
            sub_elements={},
            brand_relevance_score=0.3,
        )

    if not isinstance(payload, dict):
        return InspirationAnalysis(
            slug=_slugify("", fallback_domain),
            summary="Respuesta inesperada del análisis.",
            sub_elements={},
            brand_relevance_score=0.3,
        )

    summary = _truncate_summary(_strip_voseo(str(payload.get("summary", "")).strip()))
    if not summary:
        summary = "Inspiración guardada sin resumen."

    return InspirationAnalysis(
        slug=_slugify(str(payload.get("slug", "")), fallback_domain),
        summary=summary,
        sub_elements=_coerce_sub_elements(payload.get("sub_elements")),
        brand_relevance_score=_coerce_score(payload.get("brand_relevance_score")),
    )


def analyze(
    *,
    url: str,
    why: str,
    brand_lighthouse: str | None,
    page_title: str | None,
    content_md: str,
    fallback_domain: str,
    llm: object | None = None,
) -> InspirationAnalysis:
    """Run the LLM analysis pass and return an ``InspirationAnalysis``.

    ``llm`` defaults to ``LLMFactory.get_service().get_client(FAST)`` so
    the tool can call ``analyze(...)`` without arguments in production.
    Tests pass a stub object exposing ``invoke([messages])``.
    """
    user_prompt = _build_user_prompt(
        url=url,
        why=why,
        brand_lighthouse=brand_lighthouse,
        page_title=page_title,
        content_md=content_md,
    )

    if llm is None:
        from luana_core_llm.factory import LLMFactory

        llm = LLMFactory.get_service().get_client(ModelRole.FAST)
        llm = llm.bind(temperature=0.3)

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT_ES),
        HumanMessage(content=user_prompt),
    ]
    # TP3 B1 — tag the call so chat orchestrator drops the
    # intermediate JSON tokens instead of streaming them as block_delta.
    response = llm.invoke(messages, config=INTERNAL_LLM_CONFIG)  # type: ignore[attr-defined]
    text = getattr(response, "content", None) or str(response)
    if isinstance(text, list):
        text = "\n".join(str(part) for part in text)

    return parse_llm_output(str(text), fallback_domain=fallback_domain)


__all__ = [
    "InspirationAnalysis",
    "analyze",
    "parse_llm_output",
]
