"""B23-TP11 — System prompts de deep_agent + subagents NO contienen voseo.

Lección TP11 J4: Kimi K2.6 (AGENT) arrastra el voseo del system prompt al
output user-facing (B11-TP6 phrasing-sensitive). El ``output_sanitizer``
B7-TP6 corrige tokens en post-procesado pero el user los ve durante el
streaming SSE token-a-token. Defensa raíz = system prompts en tuteo
neutro LatAm.

Esta es la 4a capa de defensa contra A2.1 voseo leak:
  1. ``output_sanitizer`` (B7-TP6) — runtime correction.
  2. Spanish-text rule .claude/rules/spanish-text.md — convention.
  3. Schema/UI catalogs neutro-checked en arch tests.
  4. **System prompts neutro-checked aquí** (B23-TP11).
"""

from __future__ import annotations

import re

import pytest

from src.modules.copilot.application.orchestrator import deep_agent
from src.modules.copilot.application.orchestrator.subagents import (
    url_analyzer as url_analyzer_module,
)

# Tokens voseo prohibidos en system prompts. Formas más comunes que Kimi
# K2.6 arrastra al output. Match case-insensitive con boundary \b.
_VOSEO_TOKENS = (
    # imperativos voseo
    "anotá",
    "anotá",
    "marcá",
    "configurá",
    "revisá",
    "guardá",
    "cambiá",
    "delegá",
    "dejá",
    "usá",
    "elegí",
    "seleccioná",
    "empezá",
    "arrancá",
    "agregá",
    "subí",
    "bajá",
    "abrí",
    "volvé",
    "andá",
    "probá",
    "compartí",
    "contá",
    "explicá",
    "fijate",
    "acordate",
    "respondé",
    "escribí",
    "llamá",
    "reportá",
    "continuá",
    "devolvele",
    "ofrecé",
    "marca",  # OK as noun, false positives manage via boundary check
    # presente voseo
    "querés",
    "tenés",
    "podés",
    "sabés",
    "hacés",
    "venís",
    "decís",
    "ofrecés",
    "cobrás",
    "aprovechás",
    "guardás",
    "sugerís",
    "atendés",
    "ejercés",
    "vendés",
    "acompañás",
    "enseñás",
    "reunís",
    "producís",
    "entregás",
    "manejás",
    "avanzás",
    "seguís",
    # pronombre/copula
    "vos",
    "sos",
    # léxico marcado
    "mirá",
    "dale",
    "che",
    "bárbaro",
    "fijate",
    "laburo",
    "quilombo",
)

# False positives — palabras que terminan en "vos" o "sos" pero NO son
# voseo. "marca" y "queres" están descartados via word boundary.
_FALSE_POSITIVE_WORDS = {
    "marca",
    "marcas",
    "vamos",
    "estamos",
    "somos",
    "soluciones",
    "asocios",
    "negocios",
    "valores",
    "videos",
    "estados",
    "datos",
    "llamados",
    "mensajes",
    "ejemplos",
    "todos",
    "modos",
    "campos",
    "casos",
    "objetivos",
    "asuntos",
}


def _scan_voseo(text: str) -> list[str]:
    """Return list of voseo tokens found in ``text`` (case-insensitive).

    Uses word boundary to avoid matching ``marca`` (noun) when checking
    for ``marcá`` (imperativo voseo) — they differ only by accent.
    """
    found: list[str] = []
    for token in _VOSEO_TOKENS:
        # Escape the literal token (it may contain accents) and require
        # word boundary so e.g. "marcá" does not match "marcaba".
        pattern = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            matched = match.group(0)
            if matched.lower() in _FALSE_POSITIVE_WORDS:
                continue
            # Skip if the bare token (no accent) accidentally matches a
            # neutral form (e.g. "marca" the noun). The accent is the
            # discriminator: voseo imperativos always carry the accent on
            # the last vowel.
            if "á" not in token and "é" not in token and "í" not in token:
                # tokens like "vos", "sos", "che", "mirá" still carry
                # voseo signature. Allow.
                pass
            found.append(matched)
    return found


def test_deep_agent_suffix_es_has_no_voseo() -> None:
    """``_DEEP_AGENT_SUFFIX_ES`` is the per-turn system prompt suffix.

    Kimi K2.6 (AGENT tier) tends to mirror the linguistic register of
    the system prompt. Voseo here = voseo in user-facing output.
    """
    suffix = deep_agent._DEEP_AGENT_SUFFIX_ES
    found = _scan_voseo(suffix)
    assert not found, (
        f"_DEEP_AGENT_SUFFIX_ES contains voseo tokens: {sorted(set(found))}. "
        "Switch to tuteo neutro LatAm (regla 11) — Kimi K2.6 arrastra el "
        "voseo del system prompt al output user-facing."
    )


def test_url_analyzer_prompt_has_no_voseo() -> None:
    """The url_analyzer subagent system prompt must be tuteo neutro."""
    prompt = url_analyzer_module._URL_ANALYZER_PROMPT
    found = _scan_voseo(prompt)
    assert not found, (
        f"_URL_ANALYZER_PROMPT contains voseo tokens: {sorted(set(found))}. Convert to tuteo neutro LatAm (regla 11)."
    )


def test_url_analyzer_subagent_description_has_no_voseo() -> None:
    """The subagent ``description`` is also visible to the parent agent
    when the deepagents router decides to delegate. Must be neutro."""
    description = url_analyzer_module.URL_ANALYZER_SUBAGENT["description"]
    found = _scan_voseo(description)
    assert not found, f"URL_ANALYZER_SUBAGENT description contains voseo: {sorted(set(found))}."


def test_deep_agent_suffix_has_subagent_delegation_rules() -> None:
    """El suffix DEBE incluir reglas explícitas de delegación a sub-agentes.

    Sin estas reglas el modelo:
    - lee la misma data en paralelo via tools del parent (gasto x2);
    - re-resume verbatim el ToolMessage del sub-agente (output x2 + duplicación
      visible en pantalla, ver bug en conv ``795cdfbb...``).

    Bloquea regresión si alguien borra la sección.
    """
    suffix = deep_agent._DEEP_AGENT_SUFFIX_ES.lower()
    assert "delegación a sub-agente" in suffix or "task(subagent_type" in suffix, (
        "El suffix debe documentar el contrato de delegación a sub-agente "
        "(prohibición de doble lectura + obligación de no re-redactar el reporte)."
    )
    assert "no leas la misma data" in suffix or "lecturas paralelas" in suffix, (
        "Falta la regla anti-doble-lectura — el modelo invoca task + tools del parent en paralelo y duplica costo."
    )
    assert "no re-escrib" in suffix or "no re-redact" in suffix or "sin re-redact" in suffix, (
        "Falta la regla anti-re-resumen — el modelo re-frasea el ToolMessage "
        "del sub-agente y duplica el contenido en pantalla."
    )


@pytest.mark.parametrize(
    "voseo,neutro",
    [
        ("anotá", "anota"),
        ("avanzás", "avanzas"),
        ("querés", "quieres"),
        ("podés", "puedes"),
        ("respondé", "responde"),
        ("delegá", "delega"),
        ("llamá", "llama"),
        ("guardás", "guardas"),
    ],
)
def test_voseo_scanner_detects_canonical_pairs(voseo: str, neutro: str) -> None:
    """Sanity: scanner detects the voseo form but NOT the neutro form."""
    assert _scan_voseo(f"Lorem {voseo} ipsum"), f"Scanner missed {voseo!r}"
    assert not _scan_voseo(
        f"Lorem {neutro} ipsum",
    ), f"Scanner false positive on {neutro!r}"
