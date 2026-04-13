"""Interview configuration value objects (frozen, immutable) + domain registry."""

from __future__ import annotations

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

    # Phase 3: Document processing
    document_extraction_template: str | None = None
    supported_file_types: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md", ".pptx")

    # Phase 3: Research & context
    initial_research_enabled: bool = False
    context_loader: str | None = None


# ---------------------------------------------------------------------------
# Domain config registry
# ---------------------------------------------------------------------------

DOMAIN_CONFIGS: dict[str, InterviewConfig] = {}


def register_interview_config(domain: str, config: InterviewConfig) -> None:
    """Register an interview config for a domain."""
    DOMAIN_CONFIGS[domain] = config


def get_interview_config(domain: str) -> InterviewConfig:
    """Retrieve interview config by domain. Raises ValueError if not found."""
    if domain not in DOMAIN_CONFIGS:
        msg = f"No interview config registered for domain: {domain}"
        raise ValueError(msg)
    return DOMAIN_CONFIGS[domain]
