from enum import Enum


class Budget(str, Enum):
    LIMITADO = "limitado"
    MEDIO = "medio"
    ALTO = "alto"


class Urgency(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class Expertise(str, Enum):
    NOVATA = "novata"
    INTERMEDIA = "intermedia"
    EXPERTA = "experta"


class CommunicationStyle(str, Enum):
    DIRECTA = "directa"
    EMOCIONAL = "emocional"
    ANALITICA = "analítica"
    CASUAL = "casual"


class ExpectedOutcome(str, Enum):
    PURCHASE = "purchase"
    SCHEDULE_CALL = "schedule_call"
    ABANDON = "abandon"
    ESCALATE = "escalate"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class FinishReason(str, Enum):
    MAX_TURNS = "max_turns"
    GOAL_ACHIEVED = "goal_achieved"
    CUSTOMER_EXIT = "customer_exit"
    AGENT_ERROR = "agent_error"


class FailureCategory(str, Enum):
    MISSED_OBJECTION = "missed_objection"
    PREMATURE_CLOSE = "premature_close"
    WRONG_TOOL = "wrong_tool"
    STAGE_SKIP = "stage_skip"
    LOST_CONTEXT = "lost_context"
    GENERIC_RESPONSE = "generic_response"
    TONE_MISMATCH = "tone_mismatch"
    STALLED = "stalled"
