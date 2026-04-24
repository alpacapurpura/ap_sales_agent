# Fase 05 — Downstream unify

## Objetivo

Sales-agent prompt + landing builder + completion service + extraction schemas derivan de `FieldContract`. Agregar nuevo field al contract = aparece downstream sin tocar templates.

## Scope

**Dentro**:
- `backend/src/modules/sales_agent/application/services/knowledge_builder.py` consume `FieldContract` para enumerar user-facing fields a prompt
- `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` refactor data-driven:
  - En lugar de `{% if offer.X %}` por cada field, recibir estructura data-driven y render loop
  - Preservar bloques narrative-style existentes (no todo es `key: value`)
- `backend/src/modules/landing/application/landing_content_builders.py`:
  - Cada builder consume `FieldContract` para saber qué fields están disponibles
  - Proyección a `LandingPageConfig` usa contract para saber qué campos son requeridos vs opcionales
- `backend/src/modules/offer/application/services/offer_completion_service.py`:
  - `_SECTION_VALIDATORS` derivado de `FieldContract.required` ≟ true
  - Percentage real incluye Capa A fields
- `backend/src/modules/offer/application/extraction_schemas.py` wave outputs: field list derivada (o al menos validada) contra contract

**Fuera**:
- Nuevos providers ETL
- Templates landing nuevos (solo refactor existentes)
- Sales-agent behavior change (solo estructura prompt, tono intacto)

## Análisis requerido al abrir fase

Extensivo — es la fase más impactante:

1. Leer full `knowledge_builder.py` y `agent_identity.j2` — cómo generar prompt
2. Leer full `landing_content_builders.py` — flujo 6 builders
3. Snapshot completo prompt rendered para `a96403b5...` PRE cambio
4. Snapshot completo landing output PRE cambio
5. Diseñar estructura data-driven que preserve tono narrativo (no convertir todo a `<ul><li>key: value</li></ul>`)
6. Research: prompt engineering patterns para data-driven templates LLM (knowledge bases, RAG prompts)
7. Feature flag opcional para comparar prompt antes/después en runtime (proof paridad)

## Duración estimada

1 sprint (~5 días efectivos, ~8-10 commits atómicos).

## Riesgo

Medio-alto. Tocamos corazón sales-agent + landing. Golden fixture protege outputs. Rollback atómico por commit.

## Invariantes críticos

- Output sales-agent prompt: additive only. Si offer no tiene field nuevo, prompt byte-identical.
- Output landing: additive only. Mismo principio.
- Completion % puede cambiar (ahora contar Capa A), pero solo subir o mantener para offers con data. Nunca bajar para offer que ya estaba completo.

## DoD

Al abrir fase, escribir ACCEPTANCE.md.
