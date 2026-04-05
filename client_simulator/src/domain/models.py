from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.enums import (
    Budget,
    CommunicationStyle,
    Difficulty,
    ExpectedOutcome,
    Expertise,
    FailureCategory,
    FinishReason,
    SimulationStatus,
    Urgency,
)


class Persona(BaseModel):
    id: str
    name: str
    demographics: str
    budget: Budget
    urgency: Urgency
    expertise: Expertise
    communication_style: CommunicationStyle
    objection_tendency: list[str] = Field(default_factory=list)
    hidden_goal: str
    pain_points: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    personality_traits: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    id: str
    name: str
    entry_channel: str
    campaign_name: str | None = None
    initial_message: str
    expected_outcome: ExpectedOutcome
    max_turns: int = 20
    difficulty: Difficulty = Difficulty.MEDIUM
    context_instructions: str = ""


class ConversationTurn(BaseModel):
    turn_number: int
    role: str  # "customer" | "agent"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict | None = None


class Simulation(BaseModel):
    id: str
    persona_id: str
    scenario_id: str
    status: SimulationStatus = SimulationStatus.PENDING
    turns: list[ConversationTurn] = Field(default_factory=list)
    finish_reason: FinishReason | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class EvaluationScore(BaseModel):
    dimension: str
    score: float  # 0-10
    weight: float
    reasoning: str


class Evaluation(BaseModel):
    id: str
    simulation_id: str
    scores: list[EvaluationScore] = Field(default_factory=list)
    overall_score: float = 0.0
    summary: str = ""
    failure_categories: list[FailureCategory] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
