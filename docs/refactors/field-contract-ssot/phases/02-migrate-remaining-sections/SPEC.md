# Fase 02 — Migrate remaining sections

## Objetivo

Aplicar patrón `FieldContract` validado en Fase 01 a las secciones restantes. Cierra Capa A + Capa B (gaps de extraction coverage).

## Bloques semánticos (una PR por bloque)

1. **Authority block**: `authority_positioning_for_sales`, `authority_notes` (Offer top-level, section=instructors)
2. **Value-stack anchor**: `total_perceived_value_anchor`, `stack_positioning_statement` (Offer top-level, section=value_stack)
3. **Program narratives**: `specific_details.weekly_time_commitment_hours`, `specific_details.prerequisites_text` (ProgramDetails)
4. **Formalizar secciones sin Capa A**: identity, promise, strategy, psychology, closing — ya tienen domain, solo registran `FieldContract` entries
5. **Extraction coverage gap cleanup** (Capa B residual): `deliverables[].fulfillment_note` en `value_stack` prompt y otros gaps detectados

## Análisis requerido al abrir fase

Pre-bloque (revisar cada vez):
- Releer LEARNINGS.md Fase 01 — aplicar lessons
- Verificar estado allowlist (debe haber shrunk)
- Revisar si otros archetypes necesitan field similar (product_details, service_details, event_details, subscription_details)

Per-bloque:
- ¿Migration necesaria? (authority + value-stack sí; program narratives no — JSONB)
- ¿Sales-agent prompt bloque? (authority sí — pieza central SDR; value-stack anchor sí — pieza landing)
- ¿Landing builder consume? (authority no directamente; value-stack sí)
- Prompt LLM tiene framing marketing-expert (drafts ya en LEARNINGS/conversación previa; releer)

## Duración estimada

2 sprints (~10 días efectivos, ~15-20 commits atómicos).

## Riesgo

Bajo (patrón ya validado).

## Out of scope

- Drop de `OFFER_FIELDS_BY_FE_SECTION` (Fase 04)
- Section catalog dedup (Fase 03)

## DoD

Al abrir fase, escribir ACCEPTANCE.md con checklist per-bloque.
