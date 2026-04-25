"""F4 — ``url_analyzer`` deepagents subagent.

Wraps the ``fetch_url`` tool in an isolated deepagents subagent so the
main agent can delegate URL analysis via the built-in ``task()`` tool.

Why a subagent (vs. calling ``fetch_url`` directly):

- ``fetch_url`` already returns a short ``llm_content``, but when the
  user pastes 3-4 URLs in a row we don't want the main agent's context
  to grow with one ToolMessage per fetch. The subagent produces a
  combined narrative ("rescaté testimonios de A, CTA de B, paleta de
  C"), keeping the main agent's working set short.
- It enforces a single-purpose flow: when the main agent says
  ``task("url_analyzer", "url=https://...")`` the subagent's bound
  toolset is ONLY ``fetch_url`` (no mutations, no extraction). That
  guarantees pasted URLs cannot accidentally write to brand/offer.

The dict shape matches deepagents 0.5.3's ``SubAgent`` TypedDict
(``{name, description, system_prompt, tools?, model?, middleware?}``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.copilot.application.tools.fetch_url import fetch_url

if TYPE_CHECKING:
    from deepagents import SubAgent


_URL_ANALYZER_PROMPT = """Eres el sub-agente `url_analyzer` del Copilot Nicolify.
Tu única responsabilidad es analizar una o varias URLs que el agente principal
te delega para guardarlas como inspiración de la conversación.

Flujo:
1. Por cada URL recibida, llamá `fetch_url(url, why="...")` con la razón
   que el usuario dio (o "" si no la dio).
2. Si `fetch_url` devuelve `status="error"`, NO insistas: reportá la URL
   problemática y continuá con las restantes.
3. Cuando termines TODAS las URLs, devolvele al agente principal UN
   resumen breve (≤6 líneas) listando lo que aprovechás de cada una.

Reglas:
- Spanish neutro LatAm (tuteo `tú`). Sin voseo.
- No edites campos del studio. No llames otras tools que no sean `fetch_url`.
- No re-pegues el contenido completo de las páginas — el resumen vive en
  el scratchpad y lo pueden referenciar después.
- Si una URL es claramente irrelevante (relevance < 0.3), igual la guardás
  pero sugerís en tu resumen que se descarte.
""".strip()


URL_ANALYZER_SUBAGENT: SubAgent = {
    "name": "url_analyzer",
    "description": (
        "Analiza una o varias URLs como inspiración (no como datos a extraer): "
        "fetchea el contenido, lo destila y lo persiste en la conversación. "
        "Úsalo cuando el usuario pegue links de competencia, ejemplos o swipe "
        "files. NO lo uses para extraer datos hacia Brand/Offer — para eso usá "
        "`extract_from_url` directamente desde el agente principal."
    ),
    "system_prompt": _URL_ANALYZER_PROMPT,
    "tools": [fetch_url],
}


__all__ = ["URL_ANALYZER_SUBAGENT"]
