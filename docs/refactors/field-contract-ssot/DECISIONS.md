# Decisiones arquitectónicas (ADR log)

Cada decisión: fecha + contexto + decisión + razón + alternativas rechazadas.

Formato ADR minimalista. Append-only. No editar decisiones viejas — si invalidás, nueva entry marca la vieja como superseded.

---

## ADR-001 — Separación de capas estructura vs presentación

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Offer studio schemas FE conflate `path` (estructural) + `label/hint/placeholder` (UX). Esto causó Capa A (9 paths huérfanos) y drift silencioso.

**Decisión**: Dos capas explícitas:
- Layer 1 — `FieldContract` BE-owned. Estructural: path, type, owner, required, section, archetype filter, enum values, array item.
- Layer 2 — Schemas FE-owned. UX: label, hint, placeholder, icon, formula, examples, downstream_uses, lengthHint.

**Razón**:
- Estructura originada por modelo de datos (BE). Pydantic ya es SSoT.
- Copy/UX iteración rápida (FE) — no bloquear con deploy backend.
- Validación en compile-time FE via codegen path union.
- Industria confirma patrón: Sanity/Strapi/Stripe/GitHub todos separan estructura de presentación.

**Alternativas rechazadas**:
- Todo BE (Strapi-clone): mata velocidad UX iteration. Over-engineering.
- Todo FE (status quo): drift silencioso. Bug repetible.
- JSON Schema shared package: codegen Python+TS pesado. Asimetría natural BE↔FE no calza.
- Generar Pydantic desde Zod: inversión de causalidad incorrecta.

---

## ADR-002 — `OFFER_FIELDS_BY_FE_SECTION` reemplazado por derivación

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `OFFER_FIELDS_BY_FE_SECTION` es mapping parcial (7/21 secciones). Divergente de `Offer` domain.

**Decisión**: En Fase 04, eliminar dict. Reemplazar por util `fields_by_section(contract, section_key)` derivado puro de `FieldContract`.

**Razón**: single source. Imposible drift. Nuevo field en contract aparece auto en grouping.

**Alternativas rechazadas**: llenar el dict con los 21 slugs completos → mantener duplicación.

---

## ADR-003 — Section catalog BE como SSoT, FE consume

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: `backend/.../section_catalog.py::SECTION_CATALOG` (21 secciones + label_es + subtitle_es + help_text_es + icon_name + scope + weight + required_to_publish) duplicado por `frontend/.../section-catalog.ts::OFFER_SECTIONS` (21 secciones + label + icon + kind).

**Decisión**: BE es SSoT. FE consume endpoint catalog + mapea `icon_name` a componente Lucide via `icon-name-resolver.ts`. `kind` se mueve a BE `SectionMetadata`.

**Razón**: section ontology es estructural, no puramente UX. Affects completion weight + scope persistence.

**Alternativas rechazadas**: dejar duplicado porque "es solo display" — `label_es` diverge de `label` en cualquier momento.

---

## ADR-004 — Workspace refactor `docs/refactors/field-contract-ssot/`

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: Refactor multi-sprint, riesgo de perder contexto entre sessions Claude.

**Decisión**: Crear workspace estructurado con STATE.md atomic + protocolo RESUME/PRE_FLIGHT/POST_FLIGHT + per-fase dir. Patrón reutilizable para futuros refactors grandes.

**Razón**: crash recovery, no-drift, trazabilidad, learnings compuestos.

**Alternativas rechazadas**:
- Un solo doc largo: no survive session reset.
- Jira/GitHub issues: fuera de repo, no versionable.
- `docs/projects/`: ok pero `refactors/` más semántico.

---

## ADR-005 — Golden fixture desde Fase 00

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: user quiere asegurar base funcional no rompa durante refactor.

**Decisión**: Capturar snapshot de `a96403b5...` (DB state + rendered prompt + landing output) en Fase 00. Golden test valida paridad cada PR.

**Razón**: data-level regression catching. Automatizable.

**Alternativas rechazadas**:
- Visual regression (Playwright screenshots): overhead alto. Rechazado explícito por user.
- Solo manual check: no escalable.

---

## ADR-006 — Tech debt arreglada en la misma fase

**Fecha**: 2026-04-24
**Estado**: accepted
**Contexto**: user preferencia: no posponer deuda descubierta.

**Decisión**: Tech debt encontrada durante fase **relacionada al scope** se arregla en PR de la fase (o PR vecina). Tangencial va a TODO.md + `docs/mejoras-proceso/to-do.md`.

**Razón**: compounding debt es el problema original (Capa A = deuda aplazada).

**Alternativas rechazadas**: "fix forward" tangenciales — crean scope creep y mergeadas en batch tardías.
