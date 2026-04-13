# Phase 4 Handoff: Cleanup + Polish

**Date:** 2026-04-13
**Previous Phases:** Phase 0 + 1 + 2 + 3 — ALL COMPLETE
**Next Phase:** Phase 4 (Final cleanup, dead code removal, polish)

---

## Resumen ejecutivo de Phases 0-3

### Phase 0 (8 commits) — Foundations
Backend: `ClientContext` extendido con `focus` + `interview_session_id`, system prompt por capas (`build_system_prompt()`), `extract_structured` global con validación de field_path via `schema_introspection`, context budget con `truncate_history()`, tool `revert_to_block`, dead code cleanup.
Frontend: Zustand store extendido (`sidebarState`, `focusEntity`, `focusSnapshot`, `previewData`, `interviewProgress`), `CopilotInput` unificado, preview registry refactorizado a lazy imports.

### Phase 1 (10 commits) — Unified Input + Interview Fix
Backend: `FocusContextDTO` + `ClientContextDTO` con focus/interview, orchestrator carga interview session, tool selection por modo, `UIAction` extendido con interview cards + `preview_update`, `entity_id` en `StartInterviewRequest`.
Frontend: `useCopilotChat` unificado (mode-aware send, `_handleUIAction` dispatcher, `sendCardAction`), `AssistantMessage` renderiza interview cards, `useInterviewChat` deprecado a thin wrapper.

### Phase 2 (13 commits) — Expandable Sidebar + Focus Mode
Backend: `FocusContextLoader`, focus tools (`entity_write`, `entity_read`, `entity_undo_all`), tool registry con focus mode selection, orchestrator carga `focus_entity_data`.
Frontend: Dashboard layout refactorizado (flex push, sin padding-right hacks), `CopilotSidebar` reemplaza `CopilotPanel` (3 width states: 60/380/780px), `CopilotHeader` mode-aware, `CopilotPreviewPane` lazy-loaded, `FocusBar` (entity label, progress dots, undo all), `FocusModeButton`, `CopilotStatusBar` reemplaza `InterviewBanner`, left sidebar auto-collapse a viewport <1280px.

### Phase 3 (9 commits) — Interview in Sidebar + Offer Creation with IA
Backend: Config dinámica por arquetipo (`get_offer_interview_config()` con 7 bloques: 3 universales + 1 específico + 3 universales finales), interview service carga arquetipo de la oferta, 7 reglas de inteligencia en template de entrevista.
Frontend: Card callbacks wired (AlternativesCard, ClarifyCard, CheckpointCard → `sendCardAction`), `InterviewCompleteCard` sidebar-aware y domain-generic, wizard "Crear con asistente IA" (crea oferta → activa interview en sidebar), interview pages redirigen a studio con query param, `WithCopilot` muestra badge "IA" en focus mode.

**Test count after Phase 3:** 2404 backend, 1048 frontend, 62 arch.

---

## Deuda técnica acumulada

### 1. Archivos legacy todavía importados (NO borrar sin migrar)

| Archivo | Importado por | Bloquea borrado |
|---|---|---|
| `copilot/components/interview/interview-split-view.tsx` | **buyer-persona interview page** (`brand-studio/interview/buyer-persona/page.tsx`) | La página buyer-persona aún usa el split view viejo |
| `copilot/components/interview/interview-chat-panel.tsx` | `interview-split-view.tsx` | Cadena de dependencia |
| `copilot/components/interview/interview-input.tsx` | `interview-split-view.tsx` | Cadena de dependencia |
| `copilot/components/interview/interview-header.tsx` | `interview-split-view.tsx` | Cadena de dependencia |
| `copilot/components/interview/interview-message.tsx` | `interview-chat-panel.tsx` + `interview-split-view.tsx` | Cadena de dependencia |
| `copilot/components/interview/session-restore-modal.tsx` | `interview-split-view.tsx` | Cadena de dependencia |
| `copilot/hooks/useInterviewChat.ts` | `interview-split-view.tsx` + tests | Deprecated wrapper |
| `brand/components/interview/interview-split-view.tsx` | brand-studio interview page (ahora redirector, pero buyer-persona aún vive) | Wrapper legacy |
| `brand/components/interview/session-restore-modal.tsx` | `brand/interview-split-view.tsx` | Duplicado del copilot |
| `brand/components/interview/interview-header.tsx` | `brand/interview-split-view.tsx` | Wrapper legacy |
| `brand/components/interview/register-brand-preview.ts` | Side-effect import en brand interview page | Registro de preview |
| `offer-studio/components/interview/register-offer-preview.tsx` | Side-effect import (ya no usado — interview page redirige) | Puede borrarse |
| `components/shared/interview-banner.tsx` | **Nadie lo importa** (ya reemplazado por `CopilotStatusBar`) | Puede borrarse |

### 2. CopilotPanel.tsx — ya muerto

`frontend/src/features/copilot/components/CopilotPanel.tsx` NO está importado por ningún componente activo. Solo referenciado en:
- `design-system/registry.ts` (como descripción textual)
- `MetricSidebar.tsx` (como comentario, no import)
- `detail-panel-test/page.tsx` (playground, no prod)

**Acción:** Borrar directamente.

### 3. Backward-compat aliases en copilot store (4 aliases)

Usados SOLO por archivos legacy y sus tests:

| Alias | Source of truth | Usado por (fuera del store) |
|---|---|---|
| `interviewMode: boolean` | `interviewSessionId` | `interview-split-view.tsx`, `brand-preview-sections.tsx`, `brand-preview-summary.tsx`, `copilot-sidebar.test.tsx`, `useInterviewChat.test.ts` |
| `setInterviewMode(active, sessionId)` | `setInterviewSession` + `clearInterview` | `interview-split-view.tsx`, tests |
| `interviewPreviewData` | `previewData` | `brand-preview-sections.tsx`, `brand-preview-summary.tsx`, tests |
| `updateInterviewPreview(delta)` | `updatePreviewData(delta)` | tests |

**Acción:** Borrar los 4 aliases DESPUÉS de borrar los archivos legacy que los usan.

### 4. SmartFill dialogs — activos, reemplazados por Focus Mode

| Archivo | Importado por | Reemplazo |
|---|---|---|
| `offer-studio/components/container/autocompletar-ia-button.tsx` | `offer-shell-header-row2.tsx` | `FocusModeButton` |
| `offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx` | `autocompletar-ia-button.tsx` + `offer-editor-content.tsx` | Focus mode + extract tools |
| `brand/components/smart-fill/smart-fill-dialog.tsx` | `brand-studio/layout.tsx` | Focus mode + extract tools |

**Acción:** Reemplazar imports en `offer-shell-header-row2.tsx` y `offer-editor-content.tsx` con `FocusModeButton`, luego borrar SmartFill files. Brand SmartFill necesita migrar `brand-studio/layout.tsx`.

### 5. ESLint errors en archivos de copilot (5 errors, 1 warning)

| Archivo | Error | Causa |
|---|---|---|
| `brand/interview/brand-preview-sections.tsx:65` | setState in effect | `setActiveTab` llamado directamente en useEffect |
| `copilot/components/copilot-preview-pane.tsx:22` | Memoization can't be preserved | `useMemo` deps no coinciden con inferred |
| `copilot/components/copilot-preview-pane.tsx:23` | Missing dependency `focusEntity` | En dependency array de useMemo |
| `copilot/components/copilot-preview-pane.tsx:46,47` | Cannot create components during render | `lazy()` llamado dentro del componente |

**Acción:** Fix `copilot-preview-pane.tsx` (mover `lazy()` fuera del componente, corregir deps). El error de `brand-preview-sections.tsx` se resuelve al borrar el archivo.

### 6. Buyer-persona interview page — NO fue migrada

`frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/buyer-persona/page.tsx` aún usa `InterviewSplitView` directamente. Este es el **único bloqueante real** para borrar toda la cadena de archivos legacy.

**Acción:** Migrar buyer-persona interview al sidebar (igual que brand/offer), luego borrar.

### 7. Backend deprecated endpoints

Per spec Phase 4:
- `POST /copilot/actions/brand/extract-full` — reemplazado por focus mode + `extract_from_document` tool
- `POST /copilot/actions/offer/psychology` — reemplazado por interview
- `research.py` tool — revisar si sigue usado por algún tool registry

### 8. Rate limiting pendiente

Spec Phase 4 requiere: 30 msgs/min por usuario en `/copilot/chat`.

---

## Plan Phase 4: Cleanup + Polish

### Orden de ejecución

```
1. Fix ESLint errors (copilot-preview-pane.tsx)
2. Migrar buyer-persona interview al sidebar
3. Borrar cadena de archivos legacy interview
4. Borrar SmartFill dialogs + autocompletar-ia-button
5. Borrar CopilotPanel.tsx
6. Borrar InterviewBanner
7. Borrar backward-compat aliases del store
8. Borrar/deprecar endpoints backend
9. Rate limiting
10. Polish (animaciones, mobile, prefetch)
11. Full test suite verification
```

### Task 1: Fix ESLint errors en copilot-preview-pane.tsx

**Archivo:** `frontend/src/features/copilot/components/copilot-preview-pane.tsx`

**Problemas:**
- `lazy()` llamado dentro del componente body → mover afuera
- `useMemo` con deps `[focusEntity?.domain]` → cambiar a `[focusEntity]`

### Task 2: Migrar buyer-persona interview al sidebar

**Archivo:** `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/interview/buyer-persona/page.tsx`

**Cambio:** Convertir a redirector (igual que brand-studio/interview y offer-studio/interview):
```tsx
import { redirect } from "next/navigation";
// Redirect to brand-studio with interview query param
redirect(`/${tenantId}/brand-studio?interview=${session}&domain=buyer_persona`);
```

### Task 3: Borrar cadena legacy interview (16+ archivos)

**Frontend files to delete:**
```
frontend/src/features/copilot/components/interview/interview-split-view.tsx
frontend/src/features/copilot/components/interview/interview-chat-panel.tsx
frontend/src/features/copilot/components/interview/interview-input.tsx
frontend/src/features/copilot/components/interview/interview-header.tsx
frontend/src/features/copilot/components/interview/interview-message.tsx
frontend/src/features/copilot/components/interview/session-restore-modal.tsx
frontend/src/features/copilot/components/interview/__tests__/ (toda la carpeta)
frontend/src/features/copilot/hooks/useInterviewChat.ts
frontend/src/features/copilot/hooks/__tests__/useInterviewChat.test.ts
frontend/src/features/brand/components/interview/interview-split-view.tsx
frontend/src/features/brand/components/interview/session-restore-modal.tsx
frontend/src/features/brand/components/interview/interview-header.tsx
frontend/src/features/brand/components/interview/register-brand-preview.ts
frontend/src/features/brand/components/interview/brand-preview-sections.tsx
frontend/src/features/brand/components/interview/brand-preview-summary.tsx
```

**Verificar antes de borrar:** `grep -rn` cada archivo para confirmar que no hay imports activos.

### Task 4: Borrar SmartFill + AutocompletarIA

**Archivos:**
```
frontend/src/features/offer-studio/components/container/autocompletar-ia-button.tsx
frontend/src/features/offer-studio/components/editor/components/smart-fill/offer-smart-fill-dialog.tsx
frontend/src/features/offer-studio/components/interview/register-offer-preview.tsx
```

**Migrar primero:**
- `offer-shell-header-row2.tsx:38` — reemplazar `<AutocompletarIAButton>` con `<FocusModeButton domain="offer" entityId={offer.id} label={offer.public_name} />`
- `offer-editor-content.tsx:135` — quitar `<OfferSmartFillDialog>` (ya no necesario con Focus mode)

**Brand SmartFill** (`brand/components/smart-fill/smart-fill-dialog.tsx`): mantener por ahora si aún se usa desde `brand-studio/layout.tsx` con refine mode. Evaluar si Focus mode lo reemplaza completamente.

### Task 5: Borrar CopilotPanel.tsx

```
frontend/src/features/copilot/components/CopilotPanel.tsx
```

Actualizar `design-system/registry.ts` si lo referencia.

### Task 6: Borrar InterviewBanner

```
frontend/src/components/shared/interview-banner.tsx
```

Ya reemplazado por `CopilotStatusBar`. Verificar que no hay imports.

### Task 7: Borrar backward-compat aliases del store

En `frontend/src/features/copilot/store/copilot-store.ts`:
- Borrar: `interviewMode`, `setInterviewMode`, `interviewPreviewData`, `updateInterviewPreview`
- Actualizar `CopilotState` interface
- Actualizar tests que usaban aliases

### Task 8: Deprecar endpoints backend

En `backend/src/modules/copilot/api/actions.py`:
- Marcar o borrar endpoints `/copilot/actions/brand/extract-full` y `/copilot/actions/offer/psychology`
- Verificar si `research.py` tool sigue en uso en `registry.py`

### Task 9: Rate limiting

Agregar rate limiting a `POST /copilot/chat`: 30 msgs/min por usuario.
Opciones: middleware FastAPI con Redis counter, o SlowAPI.

### Task 10: Polish

- Animaciones en transiciones de sidebar (expand/collapse)
- Mobile: full-screen overlay sheet con toggle preview/chat
- Prefetch: precargar preview data al hover sobre FocusModeButton

### Task 11: Full verification

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest -x -q --tb=short
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
```

---

## Archivos clave para la nueva sesión

| Propósito | Path |
|---|---|
| Design spec completo | `docs/superpowers/specs/2026-04-13-unified-copilot-design.md` |
| Phase 3 handoff | `docs/superpowers/specs/2026-04-13-phase3-handoff.md` |
| Phase 3 plan ejecutado | `docs/superpowers/plans/2026-04-13-phase3-interview-sidebar-offer-ia.md` |
| **Este documento** | `docs/superpowers/specs/2026-04-13-phase4-handoff.md` |
| Copilot store (source of truth) | `frontend/src/features/copilot/store/copilot-store.ts` |
| Copilot sidebar (3 states) | `frontend/src/features/copilot/components/CopilotSidebar.tsx` |
| Interview template (7 rules) | `backend/src/modules/copilot/infrastructure/prompts/templates/copilot_interview.j2` |
| Dynamic config factory | `backend/src/modules/copilot/domain/interview_configs/offer_config.py` |

---

## Start command para nueva sesión

```
lee docs/superpowers/specs/2026-04-13-phase4-handoff.md, luego crea el plan detallado para Phase 4 y ejecútalo con subagent-driven-development
```
