# S00 · Codebase audit + cleanup deprecated + admin prep

## Objetivo

Pre-fase. **Snapshot estado limpio del codebase ANTES de tocar arquitectura.** Borrar feature `resumen` deprecated, fix sidebar + redirect. Identificar callers obsoletos. Auditar Streamlit admin para post-S1 migration. Mapear superficie de cohesión/acoplamiento sales_agent. Garantizar S0..S10 no rompan integraciones existentes.

## Dependencias

- Ninguna (foundation pre-fase).

## Criterios de éxito

1. **Resumen deprecated borrado** (cero referencias activas):
   - `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/resumen/page.tsx` borrado.
   - `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/page.tsx` redirige a `/sales/studio/inbox` (no a deprecated).
   - `frontend/src/components/shared/layout/AppSidebar.tsx` línea 118 entry "Resumen" eliminado.
   - **NO TOCAR** `growth-studio/.../meta-ads/.../Resumen*` (feature distinta y activa).
2. **Sidebar consolidado**: "Closer Studio" parent con 3 hijos máximo (Studio, Contactos, Inscripciones). Sin duplicados.
3. **Smoke FE**: Playwright smoke test cubre `/sales`, `/sales/studio/inbox`, `/sales/contactos`, `/sales/enrollments`. Sin 404 ni 500.
4. **Audit map** (entregable doc) `docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md`:
   - Inventario callers cross-module a sales_agent (frontend + backend).
   - Inventario imports `from src.modules.sales_agent` (cross-module reads).
   - Inventario tablas DB que sales_agent toca (lectura/escritura).
   - Inventario endpoints `/api/v1/sales/*` consumidos por FE (qué hooks llaman cuáles).
   - Inventario Streamlit admin pages que leen sales_agent legacy tables (`agent_trace_model`, `agent_log_model`).
5. **Streamlit admin migration prep**: doc `docs/domains/sales-agent/redesign-2026-04/audit/admin-migration-plan.md` con:
   - `sales_audit.py` migración path desde `agent_trace_model` → `sales_agent_trace_event` (post-S1).
   - Nuevas pages requeridas post-S1: `/sales-audit-v2`, `/sales-cost`, `/sales-quality`.
   - Cambios a `_shared.py` para queries cross-agent.
6. **Tech debt entries** sembrados en `05-tech-debt-log.md` para items detectados durante audit.
7. **Spanish neutro check**: scan strings hardcoded user-facing sales_agent — flagear voseo encontrado (loggear, no fix masivo en S00 — eso lo hará S7 con voz de marca).
8. Quality gates verdes.
9. §3 sigue funcionando.

## Research mandate

### Queries WebSearch

1. `Next.js App Router safe route deletion strategy redirects 2026` — best practice para borrar rutas sin 404 a usuarios bookmarked.
2. `dependency cruiser Python imports cross-module audit 2026` — herramientas auto-mapping.
3. `Streamlit admin page deprecation strategy zero-downtime` — patrones.

### Tessl tiles

- N/A directa.

### Lectura obligatoria

- `00-vision-and-objectives.md`, `01-master-plan.md`, `02-architecture-target.md`, `03-phase-protocol.md`, `04-principles.md`, `05-tech-debt-log.md`.
- `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/` (entero).
- `frontend/src/components/shared/layout/AppSidebar.tsx`.
- `frontend/src/features/closer-studio/` (entero — confirmar estructura).
- `backend/src/admin/modules/sales_audit.py`.
- `backend/src/admin/app.py` PAGE_SPECS.
- `.claude/rules/admin-panel.md`.
- `.claude/rules/parallel-safety.md`.

### Hallazgos research

> COMPLETAR.

---

## Diseño

### Strategy de borrado seguro `/sales/resumen`

Opción A (recomendada): borrar página + redirigir 301 servidor.
- Borrar `app/(main)/[tenantId]/(dashboard)/sales/resumen/`.
- En `app/(main)/[tenantId]/(dashboard)/sales/page.tsx`:
  ```tsx
  redirect(`/${tenantId}/sales/studio/inbox`);
  ```
- Sidebar: borrar entry. Estructura final:
  ```
  Sales (parent)
    ├─ Studio        → /sales/studio/inbox
    ├─ Contactos     → /sales/contactos
    └─ Inscripciones → /sales/enrollments  (NEW badge si aplica)
  ```

Opción B (rechazada): redirect interno temporal. Razón rechazada: codebase ya tiene 8 commits de fixes admin/CI; deuda nueva = ruido. Borrar limpio.

### Audit map structure

```
docs/domains/sales-agent/redesign-2026-04/audit/
├── sales-agent-current-state.md
│   ├── §1 Cross-module callers (FE → BE endpoints)
│   ├── §2 Backend imports `from src.modules.sales_agent`
│   ├── §3 DB tables touched (read/write per repo)
│   ├── §4 Endpoints `/api/v1/sales/*` con consumer FE
│   ├── §5 Streamlit admin reads (agent_trace_model + agent_log_model)
│   ├── §6 Domain events emitidos/consumidos
│   ├── §7 Workers (follow_up_engine + frozen_detection) schedule
│   └── §8 Cohesion/coupling heatmap (alta cohesión / alto acoplamiento detected)
└── admin-migration-plan.md
    ├── §1 sales_audit.py current shape
    ├── §2 Migration path post-S1 (dual-read window)
    ├── §3 Nuevas pages requeridas (/sales-audit-v2, /sales-cost, /sales-quality)
    └── §4 _shared.py extensions
```

### Cohesion/coupling heatmap

Per archivo en `sales_agent/`:
- Cohesion score (0-1): cuántas responsabilidades distintas tiene (1 = única).
- Coupling score (0-1): cuántos módulos externos importa (0 = nadie).
- Flag: archivos con cohesion <0.5 o coupling >0.5 → candidatos a refactor (DEFERRED al S6 ratchet o S0 si crítico).

### Spanish neutro scan

Grep `vos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|configurá|elegí|seleccioná|arrancá|empezá|agregá|escribí|guardá|subí|bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|integrás|listá|probá|mostrá|compartí|contá|explicá|fijate|acordate|dale` en:
- `backend/src/modules/sales_agent/infrastructure/prompts/templates/*.j2`
- `backend/src/modules/sales_agent/infrastructure/prompts/*.py`
- `frontend/src/features/closer-studio/**/*.tsx`

Loggear hits en `05-tech-debt-log.md`. **NO fixear en S00** — voz de marca real entra en S7. Solo logueamos.

---

## Plan TDD

### RED tests

1. `frontend/e2e/specs/smoke/sales-routes.spec.ts`:
   - `/sales/resumen` retorna 404 (post-cleanup).
   - `/sales` redirige a `/sales/studio/inbox`.
   - Sidebar no contiene texto "Resumen" en sección sales.
   - Routes activas siguen renderizando: studio/inbox, studio/pipeline, studio/frozen, contactos, enrollments.

2. `tests/architecture/test_no_resumen_deprecated_references.py`:
   - AST scan: cero imports/refs a `/sales/resumen` en frontend.
   - Excluir `growth-studio/**/Resumen*` del scan (whitelist).

3. `tests/architecture/test_admin_pages_smoke.py` (extend existing):
   - Todas las pages renderizan post-changes.
   - `sales_audit.py` flagged como "uses legacy table" (deferred metadata).

---

## Implementación step-by-step

1. **Audit map** — generar `docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md`.
   - Use `Explore` agent thorough con prompt específico.
2. **Admin migration plan** — generar `audit/admin-migration-plan.md`.
3. **Tests RED primero**:
   - Smoke FE Playwright para rutas.
   - Arch test no-resumen-refs.
4. **Cleanup FE**:
   - Borrar `app/.../sales/resumen/` directorio.
   - Update `app/.../sales/page.tsx` redirect.
   - Update `AppSidebar.tsx` entry.
5. Smoke local FE:
   - `cd frontend && npm run dev` → navegar manual.
   - skill `chrome-devtools-verify` para confirmar flujo.
6. **Spanish neutro scan**:
   - Loggear hits en `05-tech-debt-log.md` con severity LOW.
   - Si hits >50 → flag DEFERRED-S7 cluster.
7. **Quality gates**:
   - `cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run`
   - `cd backend && .venv/bin/ruff check src/ tests/ && .venv/bin/pytest tests/admin/ tests/architecture/ -x -q`
   - `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke`
8. **Code review final** (Paso 11 protocol):
   - Verificar callers no rotos.
   - Verificar no introdujimos nuevo coupling.
   - Verificar audit docs son útiles (no template vacío).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Borrar `/sales/resumen` rompe bookmarks usuarios | Server-side redirect en `sales/page.tsx`; web archive shows route gone limpio. |
| Audit map se vuelve doc muerto | Persistir como referencia para S1+; cada fase puede referenciarlo (paths + queries). |
| Spanish neutro scan trae miles hits → noise | Cap inicial 50 hits; si más → cluster DEFERRED-S7. |
| Sales_audit.py legacy admin queda colgada hasta S1 cutover | OK — page sigue leyendo `agent_trace_model` legacy hasta S1 dual-write cierre. Plan migración explícito. |
| Confundir growth-studio Resumen con sales resumen | Arch test whitelist `growth-studio/**/Resumen*` — no eliminar. |

---

## Tech debt watchpoints

Sembrar (durante audit) entradas en `05-tech-debt-log.md`:

- [HIGH] `sales_audit.py` lee `agent_trace_model` legacy → DEFERRED-S1 (cutover post-S1).
- [HIGH] `sales/page.tsx` redirige a deprecated → FIXED en S00.
- [HIGH] `AppSidebar.tsx` entry "Resumen" → FIXED en S00.
- [MEDIUM] Posible duplicación FE-BE de KPIs entre `closer_studio_service.py` y `use-kpis.ts` → review.
- [LOW] Voseo encontrado en N templates Jinja → DEFERRED-S7.
- Cualquier otra detected.

---

## Ajustes vs plan original

> COMPLETAR si audit revela algo que cambia el plan S0..S10 (ej. coupling no esperado entre sales_agent y otro módulo que requiere `shared/links/` antes de S0).
