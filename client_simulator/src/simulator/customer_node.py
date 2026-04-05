from datetime import datetime

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.simulator.state import SimulationState

logger = structlog.get_logger()

PERSONA_SYSTEM_PROMPT = """Eres un cliente potencial en una conversación de ventas por chat.

## Tu Identidad
Nombre: {name}
Demografía: {demographics}
Presupuesto: {budget}
Urgencia: {urgency}
Estilo de comunicación: {communication_style}

## Tus Dolores
{pain_points_formatted}

## Tu Objetivo Oculto (nunca lo reveles directamente)
{hidden_goal}

## Tus Objeciones Naturales
Tiendes a objetar sobre: {objection_tendency_formatted}

## Tus Rasgos de Personalidad
{personality_traits_formatted}

## Contexto de Llegada
Canal: {entry_channel}
{campaign_line}
{context_line}

## Reglas ESTRICTAS
1. Siempre en español latinoamericano
2. Mensajes cortos (1-3 oraciones, como chat real de WhatsApp/Instagram)
3. Reacciona auténticamente a lo que dice el vendedor
4. Si te convence Y tu objetivo es comprar, muestra interés genuino
5. Si la conversación no avanza o se repite tras varios turnos, escribe exactamente [EXIT]
6. Nunca rompas personaje
7. No uses emojis excesivos — solo los naturales para tu estilo
8. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios"""


def _build_system_prompt(persona: dict, scenario: dict) -> str:
    pain_points = "\n".join(f"- {p}" for p in persona.get("pain_points", []))
    objections = ", ".join(persona.get("objection_tendency", []))
    traits = ", ".join(persona.get("personality_traits", []))
    campaign = f"Campaña: {scenario['campaign_name']}" if scenario.get("campaign_name") else ""
    context = scenario.get("context_instructions", "")

    return PERSONA_SYSTEM_PROMPT.format(
        name=persona["name"],
        demographics=persona["demographics"],
        budget=persona["budget"],
        urgency=persona["urgency"],
        communication_style=persona["communication_style"],
        pain_points_formatted=pain_points,
        hidden_goal=persona["hidden_goal"],
        objection_tendency_formatted=objections,
        personality_traits_formatted=traits,
        entry_channel=scenario["entry_channel"],
        campaign_line=campaign,
        context_line=f"Contexto: {context}" if context else "",
    )


def _build_conversation_messages(turns: list[dict]) -> list[HumanMessage]:
    """Build conversation history as alternating messages for the LLM."""
    messages = []
    for turn in turns:
        role = turn["role"]
        content = turn["content"]
        if role == "customer":
            # Customer messages = assistant perspective (we're generating customer)
            messages.append(HumanMessage(content=f"[Tú dijiste]: {content}"))
        else:
            # Agent messages = what the vendedor said
            messages.append(HumanMessage(content=f"[Vendedor]: {content}"))
    return messages


async def customer_node(state: SimulationState) -> dict:
    """Generate the next customer message based on persona and conversation history."""
    persona = state["persona"]
    scenario = state["scenario"]
    turns = state["turns"]
    current_turn = state["current_turn"]

    # Turn 0: use initial_message from scenario
    if current_turn == 0:
        customer_turn = {
            "turn_number": 0,
            "role": "customer",
            "content": scenario["initial_message"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"generated": False},
        }
        return {
            "turns": turns + [customer_turn],
            "current_turn": current_turn,
        }

    # Subsequent turns: LLM generates response
    llm = ChatOpenAI(
        model=settings.simulator_model,
        api_key=settings.openai_api_key,
        temperature=0.8,
        max_tokens=200,
    )

    system_prompt = _build_system_prompt(persona, scenario)
    conversation = _build_conversation_messages(turns)

    messages = [
        SystemMessage(content=system_prompt),
        *conversation,
        HumanMessage(
            content="Genera tu siguiente mensaje como cliente. Solo el mensaje, nada más."
        ),
    ]

    try:
        response = await llm.ainvoke(messages)
        customer_message = response.content.strip()

        customer_turn = {
            "turn_number": current_turn,
            "role": "customer",
            "content": customer_message,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"generated": True},
        }

        logger.info(
            "customer_message_generated",
            simulation_id=state["simulation_id"],
            turn=current_turn,
            message_preview=customer_message[:80],
        )

        return {
            "turns": turns + [customer_turn],
            "current_turn": current_turn,
        }

    except Exception as e:
        logger.error(
            "customer_node_error",
            simulation_id=state["simulation_id"],
            error=str(e),
        )
        return {
            "is_finished": True,
            "finish_reason": "agent_error",
        }
