"""F5 — ``data_query`` deepagents subagent.

Wraps the ``ask_tenant_data`` tool in an isolated deepagents subagent so the
main agent can delegate Q&A about the tenant's own data via the built-in
``task()`` tool.

Why a subagent (vs. calling ``ask_tenant_data`` directly):

- ``ask_tenant_data`` already returns a short ``llm_content`` answer, but a
  user power-question may chain several follow-ups ("y la semana anterior?",
  "y por telegram?"). The subagent isolates those iterative calls so the main
  agent's working set keeps the final answer only — not the intermediate
  intent/plan/result payloads.
- It enforces a single-purpose toolset: the subagent's ``tools`` is only
  ``ask_tenant_data``. No mutations, no URL fetching, no extraction. That
  guarantees a Q&A delegation cannot accidentally write tenant data even if
  the LLM hallucinates a different tool call.

Mirrors the F4 ``URL_ANALYZER_SUBAGENT`` pattern. The dict shape matches
deepagents 0.5.3's ``SubAgent`` TypedDict.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.copilot.application.tools.ask_tenant_data import ask_tenant_data

if TYPE_CHECKING:
    from deepagents import SubAgent


_DATA_QUERY_PROMPT = """Eres el sub-agente `data_query` del Copilot Nicolify.
Tu única responsabilidad es responder preguntas del usuario sobre los datos del
tenant: ofertas, leads inbound, conversaciones del copilot.

Flujo:
1. Recibís UNA pregunta natural del agente principal.
2. Llamá `ask_tenant_data(question, output_channel)` con la pregunta tal como te
   llega y el canal que el agente principal te indique (default `chat`).
3. Si la respuesta es `status="ok"`, devolvele al agente principal el campo
   `answer` tal cual (ya viene en español neutro LatAm y adaptado al canal).
4. Si la respuesta es `status="error"`, reportá el `message` honestamente —
   no inventes datos.

Reglas:
- Spanish neutro LatAm (tuteo `tú`). Sin voseo.
- No edites datos del tenant. No llames otras tools que no sean `ask_tenant_data`.
- No reformules la pregunta antes de pasársela a la tool — el clasificador de
  intención dentro de la tool es quien la interpreta.
- Si recibís múltiples preguntas en una misma delegación, llamá la tool una vez
  por cada pregunta y combiná las respuestas en un único mensaje breve.
""".strip()


DATA_QUERY_SUBAGENT: SubAgent = {
    "name": "data_query",
    "description": (
        "Responde preguntas naturales sobre los datos del tenant (ofertas, leads "
        "inbound, conversaciones del copilot). Úsalo cuando el usuario pregunta "
        "'cuántos / cuántas / dame resumen de / qué ofertas tengo'. NO lo uses "
        "para mutar datos ni para responder sobre método/doctrina."
    ),
    "system_prompt": _DATA_QUERY_PROMPT,
    "tools": [ask_tenant_data],
}


__all__ = ["DATA_QUERY_SUBAGENT"]
