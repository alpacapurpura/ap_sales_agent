# Sprint S4 — Mini CRM Hub (lite view)

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S4-crm-hub-lite |
| PI padre | PI-1-campaigns-module |
| Estado | done |
| Inicio | 2026-04-30 |
| Cierre estimado | +1 sem post-S3 inicio (paralelo, no serial) |
| Cierre real | 2026-04-30 (mismo día — Opus 4.7[1M] sprint sizing) |
| Owner PM | /pm |

## Objetivo (1 línea)

Vista lite de contactos + creación de segmento manual con **arquitectura forward-compatible**: PI-3 expande por agregación (nuevos componentes / endpoints / páginas), no por reescritura.

## Pre-handoff (input desde S0+S1+S2 + paralelo S3)

- Domain `crm/` existente (CustomerProfile, lifecycle, scoring) — usable directo.
- Domain `campaigns/Segment` con type=STATIC|DYNAMIC + filters list (S1 ya lo entrega).
- API `campaigns/segments` create endpoint base (S1 cubre).
- Stub FE `/sales/contactos/page.tsx` existe vacío.
- UX session previa: `docs/ux-sessions/2026-04-29-crm-module-proposal/` (FLOW-SPEC + DECISIONS + prototype HTML).

## Principio arquitectónico clave (forward-compat)

> **API contracts FINALES desde día 1. UI compone subset hoy. PI-3 agrega componentes/páginas que CONSUMEN la misma API y mismos primitives FE. Cero refactor.**

### Ejes de extensibilidad

| Eje | S4 lite | PI-3 expand | Refactor PI-3? |
|---|---|---|---|
| API filters | `lifecycle_stage`, `score_min/max`, `channel`, `search` | + `traits.{key}`, `last_activity_at`, `source_campaign_id` ranges | NO — query params ya extensibles |
| API endpoints | GET /contacts (list), GET /contacts/{id} (detail), POST /segments (STATIC con contact_ids) | + GET /contacts/{id}/journey (timeline), GET /contacts/{id}/campaigns, POST /segments (DYNAMIC con filters), POST /audience-exports | NO — endpoints nuevos, no modifican existentes |
| Detail UI | Drawer con `ContactDetailContent` component | Página completa `/contactos/{id}` USANDO mismo `ContactDetailContent` | NO — content reusable |
| Filter UI | Panel básico (`ContactFiltersPanel`) | Filter builder visual drag-drop | NO — ambos producen mismos `FilterParams` types |
| Segment creation | Botón "crear segmento" desde selección múltiple → POST type=STATIC | Segment Builder Visual page → POST type=DYNAMIC con filters | NO — backend ya soporta ambos types desde S1 |
| Bulk actions bar | "Crear segmento" único | + "Exportar Meta", "bulk update", "agregar a campaña existente" | NO — `SelectedContactsBar` extensible vía slot pattern |

## Plan PRs

| PR | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|
| PR-S4.1 | CRM contacts API forward-compatible. Endpoints GET /contacts + GET /contacts/{id} + extension stubs (`/journey`, `/campaigns`) documentados aunque deferred PI-3. ContactListDTO + ContactDetailDTO + FilterParams (Pydantic schema soporta TODOS los filters desde día 1, lite UI usa subset) | `nicolify-architect` (CONTRACT.md) → `nicolify-backend` → `nicolify-backend-auditor` | M | not-started |
| PR-S4.2 | UX session refinada: cargar `ux-sessions/2026-04-29-crm-module-proposal/FLOW-SPEC.md` → adaptar a UI-SPEC.md específico mini view (subset documentado). Define component primitives + responsive + interaction. | `ux-flow-architect` | S | not-started |
| PR-S4.3 | FE primitives + types + hooks. `features/crm-hub/`: api/, hooks/, components/ (DataTable wrapper, ContactFiltersPanel, ContactDetailContent, ContactDetailDrawer, IdentityList, ScoreBadge, LifecycleStageChip, SelectedContactsBar). Types compartidos (`Contact`, `ContactDetail`, `FilterParams`, `Segment`). FilterParams ya soporta TODOS los filters; UI expone básicos | `nicolify-frontend` | M | not-started |
| PR-S4.4 | `/sales/contactos` page implementación. Server Component default. ContactsPageClient con DataTable + FilterPanel + paginación + búsqueda + Drawer detail. Selección múltiple. | `nicolify-frontend` | M | not-started |
| PR-S4.5 | Segment manual creation flow. SelectedContactsBar → "Crear segmento" → form name → POST /segments STATIC con contact_ids → toast + navigate. | `nicolify-frontend` | S | not-started |
| PR-S4.6 | Wire MVP 1: launch campaign desde segment manual creado. Botón "lanzar campaña Telegram" en segment detail (lite). Consume API S3. | `nicolify-frontend` | S | not-started |

Dependencias:
- PR-S4.1 (BE) bloquea PR-S4.3 (FE types).
- PR-S4.2 (UX) paraleliza con PR-S4.1.
- PR-S4.3 paraleliza con PR-S4.4 conceptualmente; PR-S4.4 importa de PR-S4.3.
- PR-S4.5 → PR-S4.4 done.
- PR-S4.6 → PR-S4.5 done + S3 done.

## Criterio éxito sprint

- [ ] Chris navega `/sales/contactos`, ve sus contactos reales (al menos 5 cargados manual o desde ManyChat webhook test).
- [ ] Filtros básicos funcionan (lifecycle_stage + score range + channel).
- [ ] Búsqueda por nombre/email/teléfono funciona.
- [ ] Drawer detail muestra identidades + score + traits + source + link a Inbox conversación.
- [ ] Selección múltiple → "crear segmento" → segment STATIC creado en BD.
- [ ] Desde segment lite → "lanzar campaña Telegram" → conecta con S3 OutboundOrchestrator.
- [ ] Tests FE: ContactsTable + filters + drawer (Vitest).
- [ ] **Arch test forward-compat:** API contract documenta TODOS los endpoints PI-3 con `# deferred` flag. Test arquitectura valida que tipos `FilterParams`/`ContactDetailDTO` no rompen al extenderse.
- [ ] PI-3 plan documentado en `current-state/crm.md` (qué se agrega, qué NO se reescribe).

## Out of scope S4 (movido a PI-3)

| Item | Razón |
|---|---|
| Segment Builder Visual (drag-drop con filtros) | UX complejo, PI-3 |
| Página completa `/contactos/{id}` (vs drawer) | Drawer cubre 80% casos en lite |
| Timeline rico de journey events | Endpoint deferred PI-3, drawer solo muestra count + link |
| Bulk actions avanzadas (export Meta, bulk update) | PI-3 retargeting |
| Campaign Dashboard (`/sales/campañas` performance view) | PI-3 |
| Export segment a Meta Ads | PI-3 retargeting |

## Decisiones a tomar durante sprint

| Fecha | Decisión | PR |
|---|---|---|
| (append durante implementación) | | |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| FE primitives no respetan FSD-Lite | `nicolify-frontend` consulta `.claude/rules/frontend-fsd.md` antes implementación. Audit post-S4.3 | nicolify-frontend |
| API contracts cambian en PI-3 forzando refactor | Architect-led design en PR-S4.1: definir TODOS los filters/endpoints aunque solo subset implementado. Documentar `# deferred` en stubs | nicolify-architect |
| `DataTable` como primitive shared termina en `features/crm-hub` y luego PI-3 quiere usar en `campañas` y `segmentos` | Decisión PR-S4.3: DataTable wrapper genérico va a `components/shared/data-table/`. Solo lo crm-específico (filtros + columnas) en `features/crm-hub/` | nicolify-architect |
| UX session previa no encaja con scope lite | UX flow architect refina. UI-SPEC.md S4 = subset documentado del FLOW-SPEC original | ux-flow-architect |
| Mini drawer hoy → página completa después → mismo content debe vivir | Crear `ContactDetailContent` aislado en S4.3. Drawer y future page lo importan | nicolify-frontend |

## Cierre

Al cerrar S4:
1. `learnings.md` — qué primitives terminaron usándose, qué overdesigned, qué quedó corto.
2. `handoff.md` para PI-3:
   - Surface entregada (endpoints + types + components).
   - Lista exhaustiva: qué AGREGA PI-3 vs qué EXTIENDE.
   - Arch test forward-compat permite PI-3 sin refactor.
3. Update `current-state/crm.md` — vista contactos lite operativa.
4. Update `current-state/campaigns.md` — segment manual creation operativo.
