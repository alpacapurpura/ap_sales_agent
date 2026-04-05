import json
import uuid

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.domain.enums import FailureCategory
from src.domain.models import Evaluation, EvaluationScore, Simulation
from src.evaluation.rubrics import EVALUATION_DIMENSIONS, render_judge_prompt

logger = structlog.get_logger()


async def evaluate_simulation(
    simulation: Simulation,
    persona: dict,
    scenario: dict,
) -> Evaluation:
    """Run LLM-as-judge evaluation on a completed simulation."""
    turns_data = [
        {
            "turn_number": t.turn_number,
            "role": t.role,
            "content": t.content,
        }
        for t in simulation.turns
    ]

    prompt = render_judge_prompt(
        scenario=scenario,
        persona=persona,
        turns=turns_data,
        finish_reason=simulation.finish_reason.value if simulation.finish_reason else "unknown",
    )

    llm = ChatOpenAI(
        model=settings.evaluator_model,
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=2000,
    )

    messages = [
        SystemMessage(
            content="Eres un evaluador experto de ventas. Respondes ÚNICAMENTE en JSON válido."
        ),
        HumanMessage(content=prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Clean potential markdown wrapping
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        result = json.loads(raw)

        # Build weight lookup
        weight_map = {d["name"]: d["weight"] for d in EVALUATION_DIMENSIONS}

        scores = []
        for s in result.get("scores", []):
            dim = s["dimension"]
            scores.append(
                EvaluationScore(
                    dimension=dim,
                    score=float(s["score"]),
                    weight=weight_map.get(dim, 0.1),
                    reasoning=s.get("reasoning", ""),
                )
            )

        # Weighted average
        total_weight = sum(sc.weight for sc in scores)
        overall = sum(sc.score * sc.weight for sc in scores) / total_weight if total_weight else 0

        # Parse failure categories
        failures = []
        for fc in result.get("failure_categories", []):
            try:
                failures.append(FailureCategory(fc))
            except ValueError:
                logger.warning("unknown_failure_category", category=fc)

        evaluation = Evaluation(
            id=f"eval_{uuid.uuid4().hex[:8]}",
            simulation_id=simulation.id,
            scores=scores,
            overall_score=round(overall, 2),
            summary=result.get("summary", ""),
            failure_categories=failures,
        )

        logger.info(
            "evaluation_completed",
            simulation_id=simulation.id,
            overall_score=evaluation.overall_score,
            failures=len(failures),
        )

        return evaluation

    except json.JSONDecodeError as e:
        logger.error("evaluation_json_error", error=str(e), raw=raw[:500])
        return Evaluation(
            id=f"eval_{uuid.uuid4().hex[:8]}",
            simulation_id=simulation.id,
            overall_score=0,
            summary=f"Error parsing evaluation: {e}",
        )
    except Exception as e:
        logger.error("evaluation_error", simulation_id=simulation.id, error=str(e))
        return Evaluation(
            id=f"eval_{uuid.uuid4().hex[:8]}",
            simulation_id=simulation.id,
            overall_score=0,
            summary=f"Evaluation failed: {e}",
        )
