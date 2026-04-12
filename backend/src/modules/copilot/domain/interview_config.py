"""Interview configuration value objects (frozen, immutable)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewBlock:
    """A thematic block within an interview."""

    id: str
    label: str
    campos_objetivo: list[str]
    prompt_context: str
    coverage_threshold: float = 0.8


@dataclass(frozen=True)
class InterviewConfig:
    """Immutable configuration for an interview session."""

    domain: str
    objetivo: str
    bloques: list[InterviewBlock]
    output_schema_path: str
    datos_previos_fields: list[str]
    tono: str
    expertise_template: str
    max_mensajes: int = 60
    rag_collection: str | None = None
