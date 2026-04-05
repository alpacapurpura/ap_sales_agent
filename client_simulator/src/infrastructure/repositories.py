import json

from sqlalchemy.orm import Session

from src.domain.models import Evaluation, Persona, Scenario, Simulation
from src.infrastructure.database import EvaluationRow, PersonaRow, ScenarioRow, SimulationRow


class PersonaRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, persona: Persona) -> None:
        row = self.session.get(PersonaRow, persona.id)
        if row:
            row.data = persona.model_dump_json()
        else:
            row = PersonaRow(id=persona.id, data=persona.model_dump_json())
            self.session.add(row)
        self.session.commit()

    def get(self, persona_id: str) -> Persona | None:
        row = self.session.get(PersonaRow, persona_id)
        if not row:
            return None
        return Persona.model_validate_json(row.data)

    def list_all(self) -> list[Persona]:
        rows = self.session.query(PersonaRow).all()
        return [Persona.model_validate_json(r.data) for r in rows]

    def delete(self, persona_id: str) -> bool:
        row = self.session.get(PersonaRow, persona_id)
        if row:
            self.session.delete(row)
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        return self.session.query(PersonaRow).count()


class ScenarioRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, scenario: Scenario) -> None:
        row = self.session.get(ScenarioRow, scenario.id)
        if row:
            row.data = scenario.model_dump_json()
        else:
            row = ScenarioRow(id=scenario.id, data=scenario.model_dump_json())
            self.session.add(row)
        self.session.commit()

    def get(self, scenario_id: str) -> Scenario | None:
        row = self.session.get(ScenarioRow, scenario_id)
        if not row:
            return None
        return Scenario.model_validate_json(row.data)

    def list_all(self) -> list[Scenario]:
        rows = self.session.query(ScenarioRow).all()
        return [Scenario.model_validate_json(r.data) for r in rows]

    def delete(self, scenario_id: str) -> bool:
        row = self.session.get(ScenarioRow, scenario_id)
        if row:
            self.session.delete(row)
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        return self.session.query(ScenarioRow).count()


class SimulationRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, simulation: Simulation) -> None:
        row = self.session.get(SimulationRow, simulation.id)
        if row:
            row.persona_id = simulation.persona_id
            row.scenario_id = simulation.scenario_id
            row.status = simulation.status.value
            row.finish_reason = simulation.finish_reason.value if simulation.finish_reason else None
            row.data = simulation.model_dump_json()
            row.started_at = simulation.started_at
            row.completed_at = simulation.completed_at
        else:
            row = SimulationRow(
                id=simulation.id,
                persona_id=simulation.persona_id,
                scenario_id=simulation.scenario_id,
                status=simulation.status.value,
                finish_reason=simulation.finish_reason.value if simulation.finish_reason else None,
                data=simulation.model_dump_json(),
                started_at=simulation.started_at,
                completed_at=simulation.completed_at,
            )
            self.session.add(row)
        self.session.commit()

    def get(self, simulation_id: str) -> Simulation | None:
        row = self.session.get(SimulationRow, simulation_id)
        if not row:
            return None
        return Simulation.model_validate_json(row.data)

    def list_all(self) -> list[Simulation]:
        rows = self.session.query(SimulationRow).order_by(SimulationRow.started_at.desc()).all()
        return [Simulation.model_validate_json(r.data) for r in rows]

    def list_by_status(self, status: str) -> list[Simulation]:
        rows = (
            self.session.query(SimulationRow)
            .filter(SimulationRow.status == status)
            .order_by(SimulationRow.started_at.desc())
            .all()
        )
        return [Simulation.model_validate_json(r.data) for r in rows]

    def delete(self, simulation_id: str) -> bool:
        row = self.session.get(SimulationRow, simulation_id)
        if row:
            self.session.delete(row)
            self.session.commit()
            return True
        return False

    def count(self) -> int:
        return self.session.query(SimulationRow).count()


class EvaluationRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, evaluation: Evaluation) -> None:
        row = self.session.get(EvaluationRow, evaluation.id)
        if row:
            row.simulation_id = evaluation.simulation_id
            row.overall_score = evaluation.overall_score
            row.data = evaluation.model_dump_json()
        else:
            row = EvaluationRow(
                id=evaluation.id,
                simulation_id=evaluation.simulation_id,
                overall_score=evaluation.overall_score,
                data=evaluation.model_dump_json(),
            )
            self.session.add(row)
        self.session.commit()

    def get(self, evaluation_id: str) -> Evaluation | None:
        row = self.session.get(EvaluationRow, evaluation_id)
        if not row:
            return None
        return Evaluation.model_validate_json(row.data)

    def get_by_simulation(self, simulation_id: str) -> Evaluation | None:
        row = (
            self.session.query(EvaluationRow)
            .filter(EvaluationRow.simulation_id == simulation_id)
            .first()
        )
        if not row:
            return None
        return Evaluation.model_validate_json(row.data)

    def list_all(self) -> list[Evaluation]:
        rows = self.session.query(EvaluationRow).all()
        return [Evaluation.model_validate_json(r.data) for r in rows]

    def count(self) -> int:
        return self.session.query(EvaluationRow).count()
