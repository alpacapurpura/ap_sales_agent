"""Buyer-persona FieldContract — declarative section map + overrides.

Post field-contract-platform refactor (Fase 07), this module declares
the semantic metadata Pydantic cannot express (section, copilot meta,
lifecycle, can_propose flags) for the BuyerPersona domain and delegates
derivation to ``src.shared.domain.field_contract``.

The derived :data:`BUYER_PERSONA_FIELD_CONTRACTS` is the single source
of truth for every buyer-persona consumer that needs to iterate fields:

- ``brand/domain/copilot_editable_fields_buyer_persona.py`` (proyección)
- (futuro) sales-agent / landing builders consumiendo persona vars

BuyerPersona surfaces three JSONB ``dict`` fields (``demographics``,
``psychographics``, ``buyer_journey``) with no Pydantic sub-models —
their sub-keys live in :data:`BUYER_PERSONA_DICT_SUBKEYS` and are
walked by the platform walker into synthetic TEXT contracts (Patrón B
per Fase 06 LEARNINGS).

Adding a new BuyerPersona JSONB sub-key requires:

1. Add ``"<dict_field>": (<existing_subkeys>, "<new_subkey>")`` to
   :data:`BUYER_PERSONA_DICT_SUBKEYS`.
2. Add ``"<dict_field>.<new_subkey>": "section_slug"`` to
   :data:`BUYER_PERSONA_SECTION_MAP`.
3. (Optional) ``Override(label_es=..., notes=..., can_propose=...)``
   en :data:`BUYER_PERSONA_FIELD_OVERRIDES` para meta semántica.

Lives under ``brand/domain/`` (BuyerPersona aggregate co-resides with
brand) but registers under module key ``"buyer_persona"`` — consistente
con port editable_fields y schema_introspection.

See ``docs/refactors/field-contract-platform/DESIGN.md`` and
``phases/07-buyer-migration/`` for rationale.
"""

from __future__ import annotations

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.shared.domain.field_contract import FieldContractOverride as Override
from src.shared.domain.field_contract import (
    derive_contracts_from_pydantic,
    register_module_contracts,
)

# ---------------------------------------------------------------------------
# Dict sub-keys — JSONB containers exposed via declared sub-keys
#
# Mirrors the FE schema (frontend/src/features/brand-studio/schemas/
# buyer-persona.schema.ts) — the canonical user-facing surface. The
# walker emits one synthetic TEXT contract per (parent, subkey) pair.
# ---------------------------------------------------------------------------

BUYER_PERSONA_DICT_SUBKEYS: dict[str, tuple[str, ...]] = {
    "demographics": ("age_range", "location", "occupation", "income"),
    "psychographics": ("values", "aspirations", "lifestyle"),
    "buyer_journey": ("awareness", "consideration", "decision"),
}

# ---------------------------------------------------------------------------
# Ignore paths — system / lifecycle / internal-only fields
#
# id/tenant_id/user_id are PK-/FK-style identifiers. scope/offer_id/
# is_primary are persona metadata managed by BuyerPersonaService, not
# user-facing. completeness_score is derived. is_active/deleted_at/
# created_at/updated_at are audit/lifecycle.
# ---------------------------------------------------------------------------

BUYER_PERSONA_IGNORE_PATHS: frozenset[str] = frozenset(
    {
        "id",
        "tenant_id",
        "user_id",
        "scope",
        "offer_id",
        "is_primary",
        "completeness_score",
        "is_active",
        "deleted_at",
        "created_at",
        "updated_at",
    }
)


# ---------------------------------------------------------------------------
# Section map — path → FE section slug
#
# Sections inline (no buyer_persona/domain/section_catalog.py). Mirrors
# the legacy 12-entry catalog plus contract-only paths for list fields
# the copilot does not propose (form-runtime CRUD UX).
# ---------------------------------------------------------------------------

BUYER_PERSONA_SECTION_MAP: dict[str, str] = {
    # ── identity ─────────────────────────────────────────────────────
    "name": "identity",
    "tagline": "identity",
    # ── demographics (JSONB sub-keys) ────────────────────────────────
    "demographics.age_range": "demographics",
    "demographics.location": "demographics",
    "demographics.occupation": "demographics",
    "demographics.income": "demographics",
    # ── psychographics (JSONB sub-keys) ──────────────────────────────
    "psychographics.values": "psychographics",
    "psychographics.aspirations": "psychographics",
    "psychographics.lifestyle": "psychographics",
    # ── buyer journey (JSONB sub-keys) ───────────────────────────────
    "buyer_journey.awareness": "journey",
    "buyer_journey.consideration": "journey",
    "buyer_journey.decision": "journey",
    # ── list[dict] surfaces (form-runtime CRUD; copilot can't propose) ─
    "pain_points": "pain_points",
    "desires": "desires",
    "objections": "objections",
    "preferred_channels": "channels",
    # ── list[str] surfaces (no UX hoy, contract-only) ────────────────
    "purchase_triggers": "triggers",
    "anti_patterns": "anti_patterns",
}


# ---------------------------------------------------------------------------
# Field overrides — semantic metadata Pydantic cannot express
#
# Two groups:
# 1. ``can_propose=False`` for list fields the copilot must not replace
#    wholesale (UX edita item-by-item via form-runtime). Plus list[str]
#    fields with no current UX surface.
# 2. Curated Spanish labels + notes for the 12 catalog-exposed paths,
#    preserving byte-identical system prompt enumeration.
# ---------------------------------------------------------------------------

BUYER_PERSONA_FIELD_OVERRIDES: dict[str, Override] = {
    # ── list[dict] fields the copilot must not replace wholesale ─────
    "pain_points": Override(can_propose=False),
    "desires": Override(can_propose=False),
    "objections": Override(can_propose=False),
    "preferred_channels": Override(can_propose=False),
    # ── list[str] fields without UX surface today ────────────────────
    "purchase_triggers": Override(can_propose=False),
    "anti_patterns": Override(can_propose=False),
    # ── identity ─────────────────────────────────────────────────────
    "name": Override(
        label_es="Nombre",
        priority=100,
        is_required_semantic=True,
        human_question_es="¿Qué nombre interno le pones a este buyer persona?",
        expects="palabra o frase corta (ej. María Profesional)",
        notes="Nombre interno del avatar. Identifica la persona, no aparece al cliente.",
    ),
    "tagline": Override(
        label_es="Tagline",
        priority=85,
        gate="name",
        human_question_es="En una línea, ¿quién es esta persona?",
        expects="frase descriptiva corta",
        notes="Una línea que describe quién es esta persona.",
    ),
    # ── demographics ─────────────────────────────────────────────────
    "demographics.age_range": Override(
        label_es="Rango etario",
        priority=80,
        is_required_semantic=True,
        human_question_es="¿Cuál es el rango de edad de este buyer persona?",
        expects="rango como '25-35' o '30-45'",
        notes="Rango de edades del cliente ideal.",
    ),
    "demographics.location": Override(
        label_es="Ubicación",
        priority=70,
        is_required_semantic=True,
        human_question_es="¿En qué ciudad o región vive principalmente?",
        expects="ciudad/país (ej. Lima, Perú)",
        notes="Ciudad o región principal del avatar.",
    ),
    "demographics.occupation": Override(
        label_es="Ocupación",
        priority=75,
        is_required_semantic=True,
        human_question_es="¿Cuál es la profesión u ocupación principal de este avatar?",
        expects="profesión específica",
        notes="Profesión o rol del cliente ideal.",
    ),
    "demographics.income": Override(
        label_es="Nivel de ingresos",
        priority=60,
        human_question_es="¿Cuál es su rango de ingresos aproximado?",
        expects="rango monetario mensual o anual",
        notes="Rango de ingresos aproximado del avatar.",
    ),
    # ── psychographics ───────────────────────────────────────────────
    "psychographics.values": Override(
        label_es="Valores centrales",
        priority=70,
        is_required_semantic=True,
        human_question_es="¿Cuáles son los valores que guían las decisiones de este avatar?",
        expects="lista de 3-5 valores",
        notes="Principios que guían las decisiones del avatar.",
    ),
    "psychographics.aspirations": Override(
        label_es="Aspiraciones",
        priority=65,
        is_required_semantic=True,
        human_question_es="¿A dónde quiere llegar este avatar? ¿Cuáles son sus aspiraciones?",
        expects="2-3 aspiraciones concretas",
        notes="A dónde quiere llegar este avatar.",
    ),
    "psychographics.lifestyle": Override(
        label_es="Estilo de vida",
        priority=55,
        human_question_es="¿Cómo organiza su día? ¿Qué consume y dónde pasa el tiempo?",
        expects="2-3 oraciones",
        notes="Cómo organiza su día y qué consume.",
    ),
    # ── buyer journey ────────────────────────────────────────────────
    "buyer_journey.awareness": Override(
        label_es="Etapa de awareness",
        priority=70,
        human_question_es="¿Cómo descubre este avatar que tiene un problema o que tu marca existe?",
        expects="2-3 oraciones",
        notes="Cómo descubre que tiene un problema o que existes.",
    ),
    "buyer_journey.consideration": Override(
        label_es="Etapa de consideración",
        priority=65,
        human_question_es="¿Cómo evalúa este avatar las opciones antes de decidir?",
        expects="2-3 oraciones",
        notes="Cómo evalúa opciones antes de decidir.",
    ),
    "buyer_journey.decision": Override(
        label_es="Etapa de decisión",
        priority=60,
        human_question_es="¿Qué lo lleva finalmente al sí?",
        expects="2-3 oraciones",
        notes="Qué lo lleva al sí final.",
    ),
}


# ---------------------------------------------------------------------------
# Derived registry — the SSoT for the buyer-persona domain
# ---------------------------------------------------------------------------

BUYER_PERSONA_FIELD_CONTRACTS = derive_contracts_from_pydantic(
    model=BuyerPersona,
    owner_module="buyer_persona",
    section_map=BUYER_PERSONA_SECTION_MAP,
    overrides=BUYER_PERSONA_FIELD_OVERRIDES,
    ignore_paths=BUYER_PERSONA_IGNORE_PATHS,
    dict_subkeys=BUYER_PERSONA_DICT_SUBKEYS,
)

register_module_contracts("buyer_persona", BUYER_PERSONA_FIELD_CONTRACTS)


__all__ = [
    "BUYER_PERSONA_DICT_SUBKEYS",
    "BUYER_PERSONA_FIELD_CONTRACTS",
    "BUYER_PERSONA_FIELD_OVERRIDES",
    "BUYER_PERSONA_IGNORE_PATHS",
    "BUYER_PERSONA_SECTION_MAP",
]
