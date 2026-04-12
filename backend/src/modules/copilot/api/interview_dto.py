"""Request and response DTOs for Interview API."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StartInterviewRequest(BaseModel):
    domain: str = "brand"
    resume_session_id: UUID | None = None


class StartInterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    conversation_id: UUID
    config: dict
    initial_message: str


class ActiveInterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    domain: str
    domain_label: str
    bloque_actual: str
    bloques_completados: list[str]
    total_bloques: int


class InterviewStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: UUID
    mapa_global: dict
    bloque_actual: str
    bloques_completados: list[str]
    config: dict
    messages_count: int


class InterviewStatusResponse(BaseModel):
    """Generic status response for pause/abandon operations."""

    status: str
