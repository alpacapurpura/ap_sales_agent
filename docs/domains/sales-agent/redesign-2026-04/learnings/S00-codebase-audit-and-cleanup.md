# Learnings · S00 · codebase-audit-and-cleanup

> Doc para S0. Snapshot estado limpio antes de tocar arquitectura.

---

## Resumen (3 líneas)

- **Entregado**: borrado limpio `/sales/resumen` + 6 componentes orphan (SalesDashboard + ConversionCommandCenter + 3 lanes + SalesInboxSheet); sidebar consolidado (3 entries: Studio/Contactos/Inscripciones); audit map + admin migration plan persistidos; spanish neutro scan = 0 hits sales_agent + closer-studio (baseline limpia); arch test ratchet `test_no_resumen_deprecated_references.py` verde.
- **Decisión no obvia**: cleanup en cascada (borrar route + 6 componentes + types/registry purge) en lugar de solo route+sidebar+redirect — anti-parche `04-principles.md §1.4` justifica eliminar dead code consecuencia directa.
- **Listo para S0**: branch development limpio post-commit, audit map verifica callers, admin plan documenta cutover S1→S6, ratchet activo.

---

## Decisiones clave

- **Cleanup en cascada vs scope estricto**:
  - Tomada: borrar también `SalesDashboard` + `ConversionCommandCenter` + `SalesLane` + `AgendaLane` + `OpportunityLane` + `SalesInboxSheet` + types orphan.
  - Razón: post `/sales/resumen` deletion los 6 archivos quedan con 0 callers (verificado por grep) + types orphan (`SalesMetrics`, `SalesConversation`, `Appointment`, `SalesDashboardState`). Anti-parche: dejar dead code = ruido para AI auto-complete + falsifica el `lib/design-system/registry-sales.ts` (catálogo).
  - Alternativa descartada: borrar sólo el route + sidebar + redirect, log orphans como DEFERRED. Rechazada porque "leave it better" + cascade es local al cleanup actual.

- **NO borrar `ActivityFeedWidget` / `CalendarWidget` / `AppointmentSheet` / `AvailabilityModal`**:
  - Tomada: dejarlos como orphans pre-existentes (NO consecuencia de S00).
  - Razón: scope strict S00. Estos archivos ya estaban orphan ANTES del cleanup (sólo aparecen en `registry-sales.ts`). Borrarlos = scope creep no justificado por el delete del route.
  - Alternativa: borrar ahora todo orphan. Rechazada — debt log con DEFERRED-S0 deja la decisión a la siguiente fase.

- **Arch test es Python (BE) escaneando FE**:
  - Tomada: `tests/architecture/test_no_resumen_deprecated_references.py` en BE pytest, escanea `frontend/src/` con regex.
  - Razón: paridad con `test_copilot_anchors.py` etc — BE arch tests ya scan-ean FE files. Único framework de ratchet en el monorepo.
  - Alternativa: FE Vitest arch test (`src/__tests__/architecture/`). Rechazada — FE arch tests son para FSD/naming, no contenido textual cross-stack.

- **E2E test split por slug en lugar de loop iter**:
  - Tomada: 5 tests separados (uno por slug) en lugar de 1 test con loop.
  - Razón: Next.js dev compila route en primer hit (15-20s). Loop con 5 routes excede el timeout 60s default.
  - Alternativa: increase test timeout 300s. Rechazada — ocultaría regresiones de compilación lenta + test individual = error claro por slug.

---

## Sorpresas / gotchas críticos

- **Audit agent reportó `follow_up_engine` 400+ LOC, real 230 LOC**: agent estimó. Verificar siempre con `wc -l` antes de citar.
- **`features/sales/components/dashboard/lanes/` quedó vacío** post borrado de los 3 lanes — `rmdir` lo limpió. Si querés que git track el dir vacío usar `.gitkeep`. Decisión: dejarlo borrado (cohesión: dir vacío = ruido).
- **Branch al iniciar = `main`**, no `development`. Tree dirty con docs S00 pre-existentes. Resuelto vía stash → checkout development → fast-forward merge main → pop. La sesión tuvo que sincronizar `development` con 3 commits avanzados de main (last `379f4f92`).
- **No hay voseo en sales_agent prompts**: scan returned 0 hits — parece que los prompts ya están en español neutro o el LLM los regeneró así. Validar baseline en S7 cuando brand voice integration entre.
- **`features/sales/index.ts` barrel re-exportaba `SalesDashboard` directamente** — barrel reduce a 1 línea (`export * from "./types"`) tras cleanup. Considerá si el barrel sigue siendo útil o si features/sales/ entera debería desaparecer en S0/S6 cleanup.

---

## Recomendaciones accionables para S0

- [ ] S0 Paso 1: re-leer `audit/sales-agent-current-state.md` §2 (cross-module imports). Validar lista vs realidad antes de extraer `shared/agent_observability/`. Si el lazy-import de brand+offer en `style_anchor_retriever.py` y `business_repository.py` requiere ports formales en `shared/links/`, decidir antes de empezar S0.
- [ ] S0 Paso 11.5 cleanup oportunista: si tocás archivos en `features/sales/components/dashboard/` o `overlay/`, considerar borrar los 4 orphans pre-existentes (`ActivityFeedWidget`, `CalendarWidget`, `AppointmentSheet`, `AvailabilityModal`) — registrados como DEFERRED-S0 en `05-tech-debt-log.md`.
- [ ] S0: extender `test_no_resumen_deprecated_references.py` si emergen nuevas refs no esperadas. Allowlist `_ALLOWED_LEGACY_REFS` está vacío — solo crece con justificación.
- [ ] S1: implementar dual-read en `sales_audit.py` ANTES de cualquier cutover legacy. Plan completo en `audit/admin-migration-plan.md §2`.
- [ ] S1: nueva tabla `sales_agent_trace_event` debe poblar el sidebar admin "Ver Último Estado" con el mismo shape que hoy lee `AgentTrace.output_state` (compat con `_legacy_compat_keys` projection es opción).

---

## Hooks listos

- `backend/tests/architecture/test_no_resumen_deprecated_references.py` — ratchet activo. `_ALLOWED_LEGACY_REFS = frozenset()` vacío. S0+ NO debe agregar refs.
- `frontend/e2e/specs/smoke/sales-routes.smoke.spec.ts` — smoke test 8 cases (3 cleanup-verification + 5 active routes). Corre en `--project=smoke`.
- `docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md` — re-leer en Paso 1 de cada fase. Sección §10 protege `00-vision §3`.
- `docs/domains/sales-agent/redesign-2026-04/audit/admin-migration-plan.md` — checklist S1+ (§6).

---

## Riesgos abiertos

- `frontend/src/features/sales/` queda con feature mixto: live (atoms, scheduling settings, mock view) + 4 orphans pre-S00. Nombre del feature es `sales` pero la mayoría del UI activo está en `features/closer-studio/`. Riesgo de confusión: `02-architecture-target.md` ya alerta "sales studio FE vive en `features/closer-studio/` (NO `sales-studio`)". S0+ debe respetar.
- `audit.py` admin queries siguen leyendo `AgentTrace` legacy. Si alguien rebana el módulo sales_agent en S0 antes de que S1 implemente dual-read, el admin rompe.
- E2E suite usa Clerk auth state cacheado 168h+. Renovar antes de pase prod (ya warn en preflight).

---

## Tech debt detectado (NO arreglado)

- [LOW] FE orphans pre-existentes en `features/sales/components/dashboard/` y `overlay/` → `05-tech-debt-log.md` sección "Orphans pre-existentes" — DEFERRED-S0.
- [HIGH] `sales_audit.py` lee `agent_trace_model` legacy → `05-tech-debt-log.md` sección "Admin migration" — DEFERRED-S1.
- [MEDIUM] `chat.py` 1082 LOC, `closer_studio_service.py` 623 LOC, `semantic_router.py` 328 LOC — DEFERRED-post-S6.
- [MEDIUM] `knowledge_builder.py` 217 LOC con lazy imports cross-module → `05-tech-debt-log.md` — DEFERRED-S0 (re-evaluar al cierre).
- [LOW] Lazy imports brand+offer en sales_agent services → DEFERRED-S0.
- [LOW] Tilde scan: `legacy/state_transition.j2:33` palabra inglesa "Expansion" → WONT-FIX.

---

## Fuentes research útiles

- [Next.js docs · `redirects` config + `redirect()` server action] — confirmó que `redirect()` de `next/navigation` es la forma server-side correcta para apuntar `/sales` → `/sales/studio/inbox`. Permanente=308 cached, default 307. Decisión: dejar redirect del route handler (default) ya que es navegación interna, no SEO-critical.
- [Streamlit 2026 release notes · `st.Page` `visibility` param] — informativo: existe pero NO se usa en S00. `auditoria` page sigue visible. Posible uso en S6 si necesitamos hide pages legacy temporalmente.
- (Dependency-cruiser para Python NO existe — usar AST + grep como ya hace `tests/architecture/`.)

---

## Métricas medidas

- BE quality gates: `ruff check src/ tests/` 0 errors. `pytest tests/architecture/ tests/admin/` = 633 passed.
- FE quality gates: `tsc --noEmit` 0 errors. `eslint src/` 0 errors / 3181 warnings (baseline). `vitest run` 1824 tests passed (238 files).
- E2E smoke `sales-routes`: 10 tests (incluye setup) passed en 37.6s.
- LOC borradas (FE): ~700 (estimado por archivos eliminados + edits).
- LOC añadidas (test + docs): audit map ~250 lines, admin migration plan ~190 lines, RED arch test ~80 lines, RED smoke spec ~50 lines, learnings ~140 lines.
- Voseo hits: 0 (sales_agent + closer-studio).
