from jinja2 import Template

EVALUATION_DIMENSIONS = [
    {
        "name": "task_completion",
        "display": "Task Completion",
        "weight": 0.20,
        "description": "¿El agente logró el resultado esperado del escenario?",
    },
    {
        "name": "qualification_quality",
        "display": "Qualification Quality",
        "weight": 0.15,
        "description": "¿Hizo preguntas de descubrimiento adecuadas? ¿Calificó bien al lead?",
    },
    {
        "name": "objection_handling",
        "display": "Objection Handling",
        "weight": 0.20,
        "description": "¿Manejó las objeciones del cliente de forma efectiva y empática?",
    },
    {
        "name": "tone_naturalness",
        "display": "Tone & Naturalness",
        "weight": 0.10,
        "description": "¿Suena humano, empático y natural? ¿Evita sonar robótico?",
    },
    {
        "name": "product_knowledge",
        "display": "Product Knowledge",
        "weight": 0.10,
        "description": "¿La información del producto fue precisa y relevante?",
    },
    {
        "name": "stage_progression",
        "display": "Stage Progression",
        "weight": 0.15,
        "description": "¿Siguió un flujo lógico rapport→discovery→presentation→closing?",
    },
    {
        "name": "tool_usage",
        "display": "Tool Usage",
        "weight": 0.10,
        "description": "¿Usó las herramientas correctas en el momento adecuado?",
    },
]

JUDGE_PROMPT_TEMPLATE = Template("""Eres un evaluador experto de conversaciones de ventas. Analiza la siguiente conversación entre un agente de ventas IA y un cliente simulado.

## Contexto del Escenario
- Nombre: {{ scenario_name }}
- Canal de entrada: {{ entry_channel }}
- Resultado esperado: {{ expected_outcome }}
- Dificultad: {{ difficulty }}
{% if context_instructions %}- Contexto: {{ context_instructions }}{% endif %}

## Perfil del Cliente (oculto al agente)
- Nombre: {{ persona_name }}
- Presupuesto: {{ budget }}
- Urgencia: {{ urgency }}
- Estilo: {{ communication_style }}
- Objetivo oculto: {{ hidden_goal }}
- Objeciones típicas: {{ objection_tendency }}

## Conversación
{% for turn in turns %}
**{{ turn.role | upper }}** (turno {{ turn.turn_number }}): {{ turn.content }}
{% endfor %}

## Resultado de la simulación
- Turnos totales: {{ total_turns }}
- Razón de fin: {{ finish_reason }}

## Instrucciones de Evaluación
Evalúa al AGENTE DE VENTAS (no al cliente) en estas 7 dimensiones. Para cada una, da un score de 0 a 10 y una justificación breve.

### Dimensiones
{% for dim in dimensions %}
{{ loop.index }}. **{{ dim.display }}** (peso: {{ (dim.weight * 100)|int }}%): {{ dim.description }}
{% endfor %}

### Categorías de fallo
Identifica si aplica alguna de estas categorías:
- missed_objection: No abordó una objeción del cliente
- premature_close: Intentó cerrar sin suficiente rapport/discovery
- wrong_tool: Usó una herramienta incorrecta o innecesaria
- stage_skip: Saltó etapas del flujo de ventas
- lost_context: Olvidó algo que el cliente ya dijo
- generic_response: Respuesta genérica que no atendió lo específico
- tone_mismatch: Tono inadecuado para el contexto/cliente
- stalled: La conversación se estancó sin progreso

## Formato de Respuesta (JSON estricto)
Responde ÚNICAMENTE con JSON válido, sin texto adicional:
{
  "scores": [
    {"dimension": "task_completion", "score": 8, "reasoning": "..."},
    {"dimension": "qualification_quality", "score": 7, "reasoning": "..."},
    {"dimension": "objection_handling", "score": 6, "reasoning": "..."},
    {"dimension": "tone_naturalness", "score": 9, "reasoning": "..."},
    {"dimension": "product_knowledge", "score": 7, "reasoning": "..."},
    {"dimension": "stage_progression", "score": 8, "reasoning": "..."},
    {"dimension": "tool_usage", "score": 5, "reasoning": "..."}
  ],
  "failure_categories": ["missed_objection", "generic_response"],
  "summary": "Resumen de 2-3 oraciones sobre el desempeño general del agente."
}""")


def render_judge_prompt(
    scenario: dict,
    persona: dict,
    turns: list[dict],
    finish_reason: str,
) -> str:
    """Render the evaluation prompt with conversation data."""
    return JUDGE_PROMPT_TEMPLATE.render(
        scenario_name=scenario["name"],
        entry_channel=scenario["entry_channel"],
        expected_outcome=scenario["expected_outcome"],
        difficulty=scenario.get("difficulty", "medium"),
        context_instructions=scenario.get("context_instructions", ""),
        persona_name=persona["name"],
        budget=persona["budget"],
        urgency=persona["urgency"],
        communication_style=persona["communication_style"],
        hidden_goal=persona["hidden_goal"],
        objection_tendency=", ".join(persona.get("objection_tendency", [])),
        turns=turns,
        total_turns=len(turns),
        finish_reason=finish_reason,
        dimensions=EVALUATION_DIMENSIONS,
    )
