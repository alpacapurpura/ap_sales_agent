"""Schema-driven guided block generator.

Reads the editable-field catalog (``src.shared.links.ports.editable_fields``)
to build a linear sequence of conversational blocks the copilot uses in
guided mode. No hardcoded config files — adding a new field to a catalog
automatically updates the guided flow.

For domains without a catalog (e.g. ``buyer_persona``) a curated schema
fallback kicks in using ``schema_introspection`` knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from luana_core_platform.links.ports.editable_fields import FieldSpec, get_catalog

Domain = Literal["brand", "offer", "buyer_persona"]


@dataclass(frozen=True, slots=True)
class GuidedBlock:
    """One conversational block in a guided setup flow."""

    id: str
    label: str
    description: str
    field_paths: tuple[str, ...]
    coverage_threshold: float = 0.7


# ── Section labels ────────────────────────────────────────────────────────
# Spanish neutro latam (no voseo) — user-facing.
_SECTION_LABELS: dict[str, str] = {
    # brand
    "identity": "Identidad",
    "story": "Historia y propósito",
    "positioning": "Posicionamiento",
    "narrative": "Narrativa (StoryBrand)",
    "avatars": "Público objetivo",
    "visuals": "Identidad visual",
    "personality": "Personalidad de marca",
    # offer
    "strategy": "Estrategia",
    "psychology": "Psicología de venta",
    "value_stack": "Value stack y entregables",
    "pricing": "Pricing y garantía",
    "closing": "Cierre",
    "onboarding": "Onboarding",
    "classification": "Clasificación",
    # buyer persona
    "demographics": "Demografía y contexto",
    "psychographics": "Psicografía",
    "pain_desire": "Dolores y deseos",
    "objections": "Objeciones y barreras",
    "channels": "Canales y journey",
}


def _humanise(section: str) -> str:
    return _SECTION_LABELS.get(section, section.replace("_", " ").title())


def _coverage_threshold(field_count: int) -> float:
    """Pick a coverage threshold that matches block size.

    Small blocks → high threshold (user should answer almost everything).
    Large blocks → lower threshold (partial coverage is acceptable).
    """
    if field_count <= 3:
        return 0.8
    if field_count <= 6:
        return 0.7
    return 0.6


def build_blocks(domain: Domain) -> list[GuidedBlock]:
    """Return the ordered list of guided blocks for ``domain``.

    Uses the editable-fields catalog when available, falls back to a curated
    schema-based layout otherwise.
    """
    catalog = get_catalog(domain)
    if catalog:
        return _blocks_from_catalog(catalog)
    return _fallback_blocks(domain)


def _blocks_from_catalog(catalog: tuple[FieldSpec, ...]) -> list[GuidedBlock]:
    """Group catalog fields by section, preserving first-appearance order."""
    sections: dict[str, list[FieldSpec]] = {}
    for spec in catalog:
        sections.setdefault(spec.section, []).append(spec)

    blocks: list[GuidedBlock] = []
    for section_name, fields in sections.items():
        label = _humanise(section_name)
        paths = tuple(f.path for f in fields)
        blocks.append(
            GuidedBlock(
                id=section_name,
                label=label,
                description=f"Completar {len(fields)} campo(s) de {label.lower()}.",
                field_paths=paths,
                coverage_threshold=_coverage_threshold(len(fields)),
            ),
        )
    return blocks


def _fallback_blocks(domain: Domain) -> list[GuidedBlock]:
    """Curated fallback for domains without an editable-fields catalog.

    Only ``buyer_persona`` falls here today. BuyerPersona stores dict fields,
    which ``schema_introspection`` doesn't fully resolve into nested Pydantic
    sections, so the block layout is defined explicitly.
    """
    if domain == "buyer_persona":
        return [
            GuidedBlock(
                id="demographics",
                label=_humanise("demographics"),
                description="Edad, ubicación, ocupación, ingresos, educación.",
                field_paths=(
                    "demographics.age_range",
                    "demographics.location",
                    "demographics.occupation",
                    "demographics.income_range",
                    "demographics.education",
                    "demographics.family_status",
                ),
                coverage_threshold=0.6,
            ),
            GuidedBlock(
                id="psychographics",
                label=_humanise("psychographics"),
                description="Valores, creencias, estilo de vida, rasgos.",
                field_paths=(
                    "psychographics.values",
                    "psychographics.beliefs",
                    "psychographics.lifestyle",
                    "psychographics.personality_traits",
                    "psychographics.media_consumption",
                ),
                coverage_threshold=0.6,
            ),
            GuidedBlock(
                id="pain_desire",
                label=_humanise("pain_desire"),
                description="Qué le duele, qué aspira, qué urgencia tiene.",
                field_paths=(
                    "pain_points",
                    "desires",
                    "pain_points.emotional_impact",
                    "desires.urgency",
                ),
                coverage_threshold=0.7,
            ),
            GuidedBlock(
                id="objections",
                label=_humanise("objections"),
                description="Por qué no compraría, qué lo detiene, qué lo dispara.",
                field_paths=("objections", "anti_patterns", "purchase_triggers"),
                coverage_threshold=0.6,
            ),
            GuidedBlock(
                id="channels",
                label=_humanise("channels"),
                description="Dónde vive online y cómo compra.",
                field_paths=(
                    "preferred_channels",
                    "buyer_journey.awareness",
                    "buyer_journey.consideration",
                    "buyer_journey.decision",
                ),
                coverage_threshold=0.6,
            ),
        ]
    return []


def block_by_id(domain: Domain, block_id: str) -> GuidedBlock | None:
    """Return the block with ``block_id`` or ``None`` if it doesn't exist."""
    for block in build_blocks(domain):
        if block.id == block_id:
            return block
    return None


def first_block(domain: Domain) -> GuidedBlock | None:
    """Return the first block of the flow, or ``None`` if the domain is empty."""
    blocks = build_blocks(domain)
    return blocks[0] if blocks else None


def next_block_after(domain: Domain, block_id: str) -> GuidedBlock | None:
    """Return the block that follows ``block_id`` in the flow, or ``None``."""
    blocks = build_blocks(domain)
    for idx, block in enumerate(blocks):
        if block.id == block_id and idx + 1 < len(blocks):
            return blocks[idx + 1]
    return None


__all__ = [
    "GuidedBlock",
    "block_by_id",
    "build_blocks",
    "first_block",
    "next_block_after",
]
