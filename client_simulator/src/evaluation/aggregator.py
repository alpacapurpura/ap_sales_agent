from collections import Counter, defaultdict

from src.domain.models import Evaluation


def aggregate_scores(evaluations: list[Evaluation]) -> dict:
    """Aggregate evaluation scores across multiple simulations."""
    if not evaluations:
        return {"dimensions": {}, "overall": 0, "count": 0}

    dimension_scores: dict[str, list[float]] = defaultdict(list)
    for ev in evaluations:
        for score in ev.scores:
            dimension_scores[score.dimension].append(score.score)

    dimensions = {}
    for dim, scores in dimension_scores.items():
        dimensions[dim] = {
            "mean": round(sum(scores) / len(scores), 2),
            "min": min(scores),
            "max": max(scores),
            "count": len(scores),
        }

    overall_scores = [ev.overall_score for ev in evaluations]
    return {
        "dimensions": dimensions,
        "overall": round(sum(overall_scores) / len(overall_scores), 2),
        "count": len(evaluations),
    }


def count_failures(evaluations: list[Evaluation]) -> dict[str, int]:
    """Count failure categories across all evaluations."""
    counter: Counter = Counter()
    for ev in evaluations:
        for fc in ev.failure_categories:
            counter[fc.value] += 1
    return dict(counter.most_common())


def scores_by_persona(
    evaluations: list[Evaluation],
    simulation_persona_map: dict[str, str],
) -> dict[str, dict]:
    """Group scores by persona."""
    persona_evals: dict[str, list[Evaluation]] = defaultdict(list)
    for ev in evaluations:
        persona_id = simulation_persona_map.get(ev.simulation_id, "unknown")
        persona_evals[persona_id].append(ev)

    return {pid: aggregate_scores(evs) for pid, evs in persona_evals.items()}


def build_heatmap_data(
    evaluations: list[Evaluation],
    simulation_persona_map: dict[str, str],
    persona_names: dict[str, str],
) -> dict:
    """Build data for a persona × dimension heatmap."""
    persona_dim_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for ev in evaluations:
        persona_id = simulation_persona_map.get(ev.simulation_id, "unknown")
        persona_name = persona_names.get(persona_id, persona_id)
        for score in ev.scores:
            persona_dim_scores[persona_name][score.dimension].append(score.score)

    # Average per cell
    personas = sorted(persona_dim_scores.keys())
    dimensions = []
    if evaluations and evaluations[0].scores:
        dimensions = [s.dimension for s in evaluations[0].scores]

    z_data = []
    for persona in personas:
        row = []
        for dim in dimensions:
            scores = persona_dim_scores[persona].get(dim, [])
            avg = round(sum(scores) / len(scores), 1) if scores else 0
            row.append(avg)
        z_data.append(row)

    return {
        "personas": personas,
        "dimensions": dimensions,
        "z": z_data,
    }
