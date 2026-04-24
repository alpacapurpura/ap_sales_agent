"""Buyer persona editable-field catalog — single source of truth for the copilot.

# [COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  IMPORTANTE PARA AGENTES / DEVS                                      ║
# ║                                                                      ║
# ║  Esta es la fuente de verdad de los campos de buyer_persona que el   ║
# ║  copilot puede proponer editar vía ``propose_field_updates``.        ║
# ║                                                                      ║
# ║  Cuando AGREGUES, ELIMINES, RENOMBRES o MUEVAS un campo en:          ║
# ║  - frontend/src/features/brand-studio/schemas/buyer-persona.schema.ts║
# ║  - el modelo BuyerPersona en                                         ║
# ║    backend/src/modules/brand/domain/buyer_persona.py                 ║
# ║                                                                      ║
# ║  TAMBIÉN ACTUALIZA ESTE ARCHIVO. Sin esta actualización el LLM       ║
# ║  alucinará ``field_id``s obsoletos o ignorará campos nuevos.         ║
# ║                                                                      ║
# ║  Independiente de ``_build_buyer_persona_paths`` en                  ║
# ║  schema_introspection.py: aquel valida cualquier path del schema     ║
# ║  (incluye campos legacy todavía en el modelo). Este catálogo refleja ║
# ║  SOLO lo que el FE renderiza hoy en buyer-persona.schema.ts —        ║
# ║  propose_field_updates no debe sugerir cambios a campos no visibles. ║
# ╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

from src.shared.links.ports.editable_fields import FieldSpec, register_catalog

# ── identity ─────────────────────────────────────────────────────────────
# Form-runtime: brand.buyer-persona — campos top-level que identifican al avatar.
_IDENTITY = (
    FieldSpec(
        "name",
        "Nombre",
        "identity",
        "Nombre interno del avatar. Identifica la persona, no aparece al cliente.",
    ),
    FieldSpec(
        "tagline",
        "Tagline",
        "identity",
        "Una línea que describe quién es esta persona.",
    ),
)

# ── demographics ─────────────────────────────────────────────────────────
# Sub-claves persistidas en BuyerPersona.demographics (JSONB).
_DEMOGRAPHICS = (
    FieldSpec(
        "demographics.age_range",
        "Rango etario",
        "demographics",
        "Rango de edades del cliente ideal.",
    ),
    FieldSpec(
        "demographics.location",
        "Ubicación",
        "demographics",
        "Ciudad o región principal del avatar.",
    ),
    FieldSpec(
        "demographics.occupation",
        "Ocupación",
        "demographics",
        "Profesión o rol del cliente ideal.",
    ),
    FieldSpec(
        "demographics.income",
        "Nivel de ingresos",
        "demographics",
        "Rango de ingresos aproximado del avatar.",
    ),
)

# ── psychographics ───────────────────────────────────────────────────────
_PSYCHOGRAPHICS = (
    FieldSpec(
        "psychographics.values",
        "Valores centrales",
        "psychographics",
        "Principios que guían las decisiones del avatar.",
    ),
    FieldSpec(
        "psychographics.aspirations",
        "Aspiraciones",
        "psychographics",
        "A dónde quiere llegar este avatar.",
    ),
    FieldSpec(
        "psychographics.lifestyle",
        "Estilo de vida",
        "psychographics",
        "Cómo organiza su día y qué consume.",
    ),
)

# ── journey ──────────────────────────────────────────────────────────────
# Listas de items compuestos (pain_points, desires, objections,
# preferred_channels) se editan vía form-runtime split-mode o vía guided
# extract item-by-item (persistido por BuyerPersonaPersister wave-based).
# No las exponemos en el catálogo editable porque ``propose_field_updates``
# reemplazaría la lista entera, lo cual es UX pobre frente a la edición
# granular del form-runtime. Además ``objections`` colisionaría con offer.
_JOURNEY = (
    FieldSpec(
        "buyer_journey.awareness",
        "Etapa de awareness",
        "journey",
        "Cómo descubre que tiene un problema o que existes.",
    ),
    FieldSpec(
        "buyer_journey.consideration",
        "Etapa de consideración",
        "journey",
        "Cómo evalúa opciones antes de decidir.",
    ),
    FieldSpec(
        "buyer_journey.decision",
        "Etapa de decisión",
        "journey",
        "Qué lo lleva al sí final.",
    ),
)


BUYER_PERSONA_EDITABLE_FIELDS: tuple[FieldSpec, ...] = (
    *_IDENTITY,
    *_DEMOGRAPHICS,
    *_PSYCHOGRAPHICS,
    *_JOURNEY,
)


# Register at import time so the copilot sees the catalog via the port
# without importing this module directly.
register_catalog("buyer_persona", BUYER_PERSONA_EDITABLE_FIELDS)


__all__ = ["BUYER_PERSONA_EDITABLE_FIELDS"]
