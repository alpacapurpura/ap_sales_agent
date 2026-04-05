import json
from pathlib import Path

from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings


class Base(DeclarativeBase):
    pass


class PersonaRow(Base):
    __tablename__ = "personas"
    id = Column(String, primary_key=True)
    data = Column(Text, nullable=False)  # JSON serialized Persona


class ScenarioRow(Base):
    __tablename__ = "scenarios"
    id = Column(String, primary_key=True)
    data = Column(Text, nullable=False)  # JSON serialized Scenario


class SimulationRow(Base):
    __tablename__ = "simulations"
    id = Column(String, primary_key=True)
    persona_id = Column(String, nullable=False)
    scenario_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    finish_reason = Column(String, nullable=True)
    data = Column(Text, nullable=False)  # JSON serialized full Simulation
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class EvaluationRow(Base):
    __tablename__ = "evaluations"
    id = Column(String, primary_key=True)
    simulation_id = Column(String, nullable=False)
    overall_score = Column(Float, nullable=False, default=0.0)
    data = Column(Text, nullable=False)  # JSON serialized Evaluation


def get_engine():
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session() -> Session:
    engine = get_engine()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
