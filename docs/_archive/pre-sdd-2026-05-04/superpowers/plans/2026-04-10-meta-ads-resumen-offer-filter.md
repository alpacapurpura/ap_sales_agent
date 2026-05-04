# Plan — Meta Ads Resumen Offer Filter

**Spec:** `docs/superpowers/specs/2026-04-10-meta-ads-resumen-offer-filter-design.md`
**Branch:** `development`
**Ejecución:** multiagente

## Artefactos compartidos (output de Fase 1, input de Fases 2+)

Ambos se escriben al root del worktree para que backend/frontend los lean:

- `docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/CONTRACT.md` — DTOs, tipos TS, firmas de métodos, queries SQL
- `docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/UI-SPEC.md` — jerarquía visual, tooltips redactados, wireframes por filtro

---

## Fase 1 — Contrato + diseño visual (PARALELO)

### 1A — `nicolify-architect`
**Input:** spec
**Output:** `CONTRACT.md`

Tareas:
1. Leer el spec completo.
2. Verificar empíricamente (con grep/read) si `get_tenant_locale` ya existe como FastAPI dependency. Si no, diseñarlo.
3. Verificar qué campos de `period_metrics` están poblados HOY para `meta-ads` reach (¿channel-level? ¿campaign-level? ambos?). Reportar en CONTRACT.md y ajustar reglas de null si hace falta.
4. Definir:
   - `FunnelStepDTO` (Pydantic v2, CamelModel)
   - Extensiones a `OfferMetricsDTO`, `BrandingAggregateDTO`, `UnassignedAggregateDTO`, `MetricsByOfferDTO`
   - Tipos TypeScript espejo en `frontend/src/features/growth-studio/types/offer-association.ts` (añadir, no romper existentes)
   - Firma exacta de `resolve_period_window(period, tz)` y cadena de DI
   - Firma de `_build_funnel_for_campaigns(rows, campaign_ids) -> list[FunnelStepDTO]`
   - Queries SQL (SQLAlchemy 2.0) que el servicio va a ejecutar sobre `period_metrics`
5. Documentar cualquier decisión no-trivial con "Why" inline.
6. NO escribir código — solo el contrato.

### 1B — `nicolify-ux-designer`
**Input:** spec
**Output:** `UI-SPEC.md`

Tareas:
1. Leer el spec completo + archivos existentes relevantes: `ResumenTab.tsx`, `OfferSegmenter.tsx`, `MetaAdsMiniFunnel.tsx`, `InversionChart.tsx`, `BenchmarkBadge.tsx`.
2. Catálogo Shadcn disponible (leer `frontend/src/components/ui/`).
3. Producir:
   - Jerarquía visual del nuevo layout (orden + spacing + containers)
   - Especificación de cada estado de `OfferSegmenter` (active/hover/disabled, chips branding vs normales vs sin-asignar con warning)
   - Especificación de cada `ResumenKpiCard` por filtro (all/offer/branding/unassigned): label, valor, delta, tooltip placement, estado `—`
   - Tooltips redactados **en español correcto con tildes**, uno por cada KPI y cada paso del funnel, siguiendo plantilla del spec (qué es, por qué importa, rango sano, qué hacer si está mal)
   - Wireframes ASCII/markdown del Resumen bajo los 4 filtros
   - Estados loading, empty, error para cada sección
   - Accesibilidad: aria-labels, contraste, keyboard nav
4. NO escribir código — solo la especificación.

---

## Fase 2 — Implementación core (PARALELO, lee Fase 1)

### 2A — `nicolify-backend`
**Input:** spec + CONTRACT.md

Tareas:
1. Leer CONTRACT.md como source of truth.
2. Implementar DTOs nuevos/extendidos en `metrics_by_offer_dto.py`.
3. Implementar `_build_funnel_for_campaigns()` en `metrics_by_offer_service.py`.
4. Fix de reach: cargar period_metrics, reglas de null según CONTRACT.
5. Implementar/usar `get_tenant_locale` dependency (según lo que el architect haya decidido).
6. Actualizar `resolve_period_window(period, tz)` en `metrics_repository.py`.
7. Wiring de DI en la ruta `/advertising/metrics-by-offer`.
8. Tests nuevos: service tests (8 casos del spec), timezone tests (Lima/Bogota boundary), arch fitness sin regresiones.
9. Correr nativamente:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/pytest tests/modules/advertising/ -x -q --tb=short`
   - `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
10. Reportar diff final + resultados de tests.

### 2B — `nicolify-frontend`
**Input:** spec + CONTRACT.md + UI-SPEC.md

Tareas:
1. Leer los tres documentos.
2. Añadir tipos TS espejo del CONTRACT en `types/offer-association.ts` y `types/metrics.ts`.
3. Crear `hooks/useResumenViewData.ts` con la lógica de derivación contextual.
4. Crear `copy/tooltips.ts` con los textos del UI-SPEC (exactamente como los redactó el ux-designer, verificando tildes).
5. Refactor de `ResumenTab.tsx`:
   - Mover `OfferSegmenter` entre Health Check y KPIs
   - Usar `useResumenViewData` para alimentar KPIs, chart, funnel
   - Pasar funnel reactivo a `MetaAdsMiniFunnel`
6. Actualizar `MetaAdsMiniFunnel.tsx` si hace falta aceptar data dinámica (muy probable que ya lo haga — verificar).
7. Tests:
   - `useResumenViewData.test.ts` (casos del spec)
   - Actualizar/añadir `ResumenTab.test.tsx` para cubrir cambio de filtro
   - E2E smoke test nuevo en `e2e/specs/smoke/meta-ads-resumen.smoke.spec.ts` (opcional si ya existe uno general para meta-ads)
8. Correr nativamente:
   - `cd frontend && npx tsc --noEmit`
   - `cd frontend && npx eslint src/features/growth-studio/`
   - `cd frontend && npx vitest run src/features/growth-studio/`
9. NO polishear charts visualmente — solo funcionalidad. Fase 3 los pule.
10. Reportar diff + resultados.

---

## Fase 3 — Polish visual por especialista (PARALELO × 4)

Cada agente corre con `subagent_type: general-purpose` + instrucciones de "data-viz senior" + permiso de escribir solo su archivo y tests.

### 3A — KPI Cards polish
- Files: `ResumenTab.tsx` (solo sección de KPI cards), posiblemente un nuevo `components/ResumenKpiCard.tsx` extraído
- Polish: tipografía, jerarquía visual delta/label/valor, color semáforo según benchmark, estado `—` con indicador visual distintivo, tooltip con Shadcn `Tooltip` componente, aria-label completo
- Verificar: `tsc --noEmit`, vitest del feature

### 3B — InversionChart polish
- Files: `InversionChart.tsx` y tests
- Polish: subtítulo narrativo contextual ("Cada $1 en [Offer] generó $X"), colores break-even, tooltip del chart con contexto multi-métrica, leyenda clara, respuesta al cambio de filtro (transición suave si trivial)
- Verificar: tsc, vitest

### 3C — MetaAdsMiniFunnel polish
- Files: `MetaAdsMiniFunnel.tsx` y tests
- Polish: tasa de conversión visible entre pasos sin hover, color ramp por tasa (verde > amarillo > rojo), estado cero (¿qué se muestra cuando todos los pasos son 0?), tooltip por paso con explicación + rango sano
- Verificar: tsc, vitest

### 3D — OfferSegmenter polish
- Files: `OfferSegmenter.tsx` y tests
- Polish: active state más fuerte, spacing horizontal responsive, chip "Sin asignar" con warning visual (rojo suave), chip "Branding" con icon ✨ o similar, chip de offer con emoji del archetype (ya existe), aria-pressed correcto
- Verificar: tsc, vitest

**Coordinación:** cada agente trabaja en archivos diferentes o en secciones claramente delimitadas. Si 3A y 3C necesitan tocar `ResumenTab.tsx`, se ejecutan secuencial (3A primero).

---

## Fase 4 — Auditoría (secuencial)

### 4A — `nicolify-backend-auditor`
- Review del diff backend contra `.claude/rules/` (DDD, tenant isolation, SA 2.0, response_model, soft deletes, arch tests)
- Output: `REVIEW.md` con findings puntuados CRITICAL/HIGH/MEDIUM/LOW
- Si hay CRITICAL o HIGH → main thread corrige antes de Fase 5

---

## Fase 5 — Verificación completa nativa (secuencial, main thread)

Correr en orden y fixear hasta que todos pasen:

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/ruff format --check src/ tests/
cd backend && .venv/bin/pytest tests/modules/advertising/ -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/features/growth-studio/
cd frontend && npx vitest run src/features/growth-studio/
```

**NO correr** Playwright local (feedback_playwright_local.md — crashes WSL). E2E smoke se corre en GitHub Actions al push.

---

## Fase 6 — Commit y reporte

1. Verificar working tree: `git status --short`
2. Commit(s) convencionales en `development`:
   - `feat(meta-ads): unified offer filter on Resumen tab (KPIs + chart + funnel)`
   - Mensaje detallado con referencias al spec y fix de reach
3. NO push — el usuario decide cuándo.
4. Reporte final con:
   - Resumen de cambios por módulo
   - Lista de tests que pasan
   - Screenshots si es posible (no es crítico)
   - Cualquier deuda nueva descubierta → anotar en `docs/mejoras-proceso/to-do.md`
