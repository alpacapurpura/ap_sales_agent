# Copilot Unified — Audit de Mejoras

**Fecha:** 2026-04-13
**Scope:** Auditoría completa post-Phase 4 (arquitectura, performance, seguridad, testing, polish)
**Estado:** Phases 0-4 completadas, 7 commits de cleanup

---

## Resumen Ejecutivo

El copilot unificado tiene **buena base arquitectónica** (DDD backend, FSD frontend, CSS transitions, SSE streaming correcto). Sin embargo presenta:
- **4 issues críticos** de seguridad/reliability que bloquean producción
- **12 issues importantes** de performance, estado y edge cases
- **8 gaps de testing** que dejan flujos críticos sin cobertura
- **6 items de polish** para UX profesional

---

## CRITICAL (Bloquean producción)

### C1. Sin timeout en streaming LLM
**Backend:** `copilot/application/orchestrator/chat.py:149`
`copilot_graph.astream_events()` no tiene timeout. Si el LLM cuelga, el stream del cliente cuelga indefinidamente consumiendo recursos del servidor.
**Fix:** `asyncio.wait_for(stream, timeout=60)` + SSE error event al frontend.

### C2. Sin verificación de ownership de conversación
**Backend:** `copilot/application/orchestrator/chat.py`
`conversation_id` viene del cliente. Si un atacante adivina el UUID, puede inyectar mensajes en conversaciones ajenas. El repository filtra por `tenant_id` pero no por `user_id`.
**Fix:** Agregar `user_id` al filtro de `ConversationRepository.get_by_id()`.

### C3. Session leak pattern en focus tools
**Backend:** `copilot/application/tools/focus/entity_write.py:53-77`, `entity_read.py`, `entity_undo_all.py`
Todos crean `db = SessionLocal()` pero si `get_persister()` lanza excepción ANTES del bloque try-finally, `db.close()` nunca se ejecuta. Con muchos requests concurrentes → connection pool exhaustion.
**Fix:** Mover `db = SessionLocal()` dentro del try, o usar context manager.

### C4. Race condition en sesiones de interview concurrentes
**Backend:** `copilot/application/services/interview_service.py:92-95`
`get_active_by_domain()` verifica si existe sesión activa, pero requests concurrentes pueden crear duplicados. No hay unique constraint en `(tenant_id, domain)` con `status='active'`.
**Fix:** Agregar unique partial index en DB: `CREATE UNIQUE INDEX ... WHERE status = 'active'`.

---

## IMPORTANT — Performance

### P1. Selectores Zustand sin función (re-renders cascada)
**Frontend:** 4 componentes usan `useCopilotStore()` sin selector — cualquier cambio en el store re-renderiza todo.

| Archivo | Línea | Impacto |
|---------|-------|---------|
| `ProcedureProgress.tsx` | :7 | ALTO — visible siempre |
| `useProactiveNudges.ts` | :38 | ALTO — dispara refetch en cada cambio |
| `section-chat-trigger.tsx` | :26 | MEDIO — multiplicado por N campos |
| `CopilotRail.tsx` | :12 | MEDIO — visible 100% del tiempo |

**Fix:** Reemplazar con `useCopilotStore((s) => s.field)` granular.

### P2. Mensajes sin límite — crecimiento unbounded
**Frontend:** `copilot-store.ts:198-204` — `messages[]` crece indefinidamente sin paginación ni límite.
**Backend:** `conversation_repository.py:91-101` — carga todo el JSONB de mensajes sin límite.
**Impacto:** Conversaciones largas (100+ msgs) → memory bloat, re-renders lentos, DOM pesado.
**Fix:** Limitar a últimos 50 mensajes en store, archivar antiguos, lazy-load al scroll-up.

### P3. Sin virtualización de lista de mensajes
**Frontend:** `CopilotChat.tsx:94-105` — `messages.map()` renderiza TODOS los mensajes en DOM.
**Fix:** Implementar `@tanstack/react-virtual` para conversaciones largas.

### P4. Componentes de mensajes sin memo()
**Frontend:** `AssistantMessage.tsx`, `UserMessage.tsx`, `CopilotInput.tsx`, cards (`AlternativesCard`, `CheckpointCard`, `ClarifyCard`), `NudgeBanner.tsx` — ninguno wrapped en `memo()`.
**Impacto:** Cada mensaje nuevo re-renderiza TODOS los mensajes anteriores.
**Fix:** Wrappear con `memo()` los message components y cards.

### P5. N+1 queries en focus mode
**Backend:** `focus_context_loader.py:45-50`, `entity_read.py:51`
`FocusContextLoader.load()` → `get_persister()` → `OfferRepository` sin `.joins()`. Ofertas con pricing/deliverables generan N+1.
**Fix:** Agregar eager loading (`.options(selectinload(...))`) en los persisters.

### P6. Estimación de tokens naïve
**Backend:** `context_budget.py:31` usa `len(text) // 4` — Claude tokeniza ~1.3 chars/token, no 4. Con entity snapshots grandes, puede exceder la ventana de contexto del modelo.
**Fix:** Usar `tiktoken` o al menos `len(text) // 2` como heurística más segura.

---

## IMPORTANT — Reliability & Edge Cases

### R1. SSE sin lógica de reconexión
**Frontend:** `copilot-api.ts:98-167` — si WiFi se cae mid-stream, el mensaje queda stuck en "streaming" sin recovery.
**Fix:** Retry con backoff (max 3), callback `onReconnect` para UI.

### R2. Race condition al enviar mensajes rápidos
**Frontend:** `useCopilotChat.ts:26-56` — si el usuario envía 2 mensajes rápido, el segundo sobreescribe `abortRef` pero el primero sigue streaming. Deja mensajes huérfanos.
**Fix:** Deshabilitar send a nivel del hook (no solo UI) mientras streaming. Abortar ALL in-flight requests.

### R3. FocusModeButton captura entityData stale
**Frontend:** `focus-mode-button.tsx:12,30` — `entityData` se pasa como prop al render. Si la entity cambia entre render y click, focus captura snapshot desactualizado.
**Fix:** Fetch fresh entity data al momento de activar focus (callback), no al render.

### R4. Focus exit no valida que la entity siga existiendo
**Frontend:** `focus-bar.tsx:27-31` — `handleExitFocus()` llama `clearFocus()` sin verificar si la entity fue borrada entre activación y exit.
**Fix:** Validar entity before/after focus.

### R5. Interview sessions sin expiración
**Backend:** `interview_session.py` — sesiones `ACTIVE` persisten indefinidamente. Sin auto-abandon por inactividad.
**Fix:** TTL de 7 días. Job periódico que marque como `ABANDONED`.

### R6. DOM manipulation con timing fijo (flaky)
**Frontend:** `useCopilotNavigator.ts:33-47` — `setTimeout(800ms)` asume que la navegación completa en 800ms. Si el render es lento, el scroll falla.
**Fix:** Hook en router completion event en lugar de timer fijo.

---

## IMPORTANT — Seguridad

### S1. Sin rate limiting en `/copilot/chat`
**Backend:** `chat.py` — sin throttle. Un usuario puede saturar el endpoint con requests (y consumir tokens LLM sin límite).
**Fix:** SlowAPI o middleware Redis: 30 msgs/min por user.

### S2. Prompt injection vía campos de usuario
**Backend:** `copilot_system.j2:16-18` — `selected_fields` valores insertados raw en el prompt. Contenido malicioso podría inyectar instrucciones.
**Fix:** Sanitizar/escapar valores de usuario antes de insertar en templates.

### S3. Conversaciones sin política de retención PII
**Backend:** `copilot_conversations.messages` (JSONB) — mensajes persisten indefinidamente sin redacción de PII. Email, teléfono, direcciones pueden quedar en historial.
**Fix:** Política de retención (90 días), auto-redacción de PII patterns.

---

## TESTING — Gaps Críticos

### T1. 0 E2E tests para copilot
**Riesgo:** CRÍTICO. Ningún flujo de usuario del copilot está cubierto por Playwright.
**Necesario:**
- `e2e/specs/smoke/copilot-chat.smoke.spec.ts` — enviar mensaje, ver respuesta
- `e2e/specs/smoke/copilot-interview.smoke.spec.ts` — iniciar interview, seleccionar alternativa
- `e2e/specs/smoke/copilot-focus.smoke.spec.ts` — activar focus, ver preview
- `e2e/pages/copilot.pom.ts` — Page Object Model

### T2. Hook principal sin tests (useCopilotChat)
**Frontend:** `useCopilotChat.ts` — 0% cobertura. Es el hook más crítico del feature.
**Necesario:** Tests para send, streaming, error handling, abort.

### T3. API layer sin tests
**Frontend:** `copilot-api.ts`, `interview-api.ts`, `document-api.ts`, `voice-api.ts` — 0% cobertura.

### T4. Card interactions sin tests
**Frontend:** `alternatives-card.tsx`, `checkpoint-card.tsx` — el usuario clickea opciones, confirma, revierte. Sin tests de interacción.

### T5. Backend: sin tests de streaming SSE
Ningún test verifica el flujo completo de streaming del chat endpoint.

### T6. Backend: test vacío
`test_offer_ladder_tools.py` — 236 bytes, sin tests.

### T7. 70% de componentes copilot sin unit tests
21 de 30 componentes sin tests. 5 de 6 hooks sin tests.

### T8. Infraestructura E2E faltante
- No existe `copilot.pom.ts` (Page Object Model)
- No existe `copilot-interview.fixture.ts` (datos mock)
- No existe mock de SSE streaming para tests

---

## POLISH — UX Profesional

### UX1. Sidebar sin animaciones de contenido
**Estado actual:** CSS `transition-[width]` smooth para el sidebar width. Pero el contenido interno (chat, preview) aparece/desaparece abruptamente sin fade.
**Mejora:** Agregar `opacity` transition al contenido del chat y preview pane. Fade-in cuando aparecen, fade-out cuando colapsan.

### UX2. Sin soporte mobile
**Estado actual:** Widths hardcoded (60/380/780px) sin breakpoints responsive. En mobile, el sidebar de 780px desborda.
**Mejora:** Mobile overlay sheet — full-screen en `<768px` con toggle chat/preview. Auto-collapse sidebar en mobile.

### UX3. Sin prefetch de preview data
**Estado actual:** Preview data se carga al activar focus mode. Hay un flash de "loading" antes de ver el preview.
**Mejora:** Prefetch on hover del FocusModeButton. Precarga entity data al hovering, activación instantánea al click.

### UX4. Sin feedback visual durante streaming
**Estado actual:** El mensaje del asistente se va llenando de texto pero no hay indicador visual explícito de que está pensando/escribiendo.
**Mejora:** Typing indicator animado (3 dots bounce) antes del primer chunk. Cursor parpadeante al final del texto durante streaming.

### UX5. Cards sin transiciones
**Estado actual:** Interview cards (AlternativesCard, CheckpointCard) aparecen instantáneamente en el chat.
**Mejora:** Slide-in animation para cards. Feedback visual al seleccionar opción (scale + check). Transición del status de card (pending → resolved).

### UX6. Focus bar sin micro-interacciones
**Estado actual:** Progress dots estáticos. Exit button plano.
**Mejora:** Dots con animación de fill al completar block. Tooltip en hover mostrando nombre del block. Exit button con confirmación si hay cambios unsaved.

---

## DDD & Mantenibilidad

### D1. Domain importa infrastructure
**Backend:** `copilot/domain/schema_introspection.py:47-50` — domain importa `OfferPersister` (infrastructure) via `TYPE_CHECKING`. Viola regla de dependencia.
**Fix:** Mover type hints a `shared/` o usar Protocol.

### D2. Tools con SessionLocal() directa
**Backend:** `copilot/application/tools/focus/` — todos los focus tools instancian `SessionLocal()` directamente, bypaseando dependency injection.
**Fix:** Inyectar sesión vía contexto del graph, no instanciar manualmente.

### D3. Async/sync mismatch en offer_ladder_tools
**Backend:** `offer_ladder_tools.py:246` — `OfferContextLoader` es async pero se llama desde contexto sync de tool. `db.close()` en AsyncSession puede no liberar conexión correctamente.
**Fix:** Refactorizar a interface sync o usar async tool context.

### D4. Archivos frontend grandes (>200 líneas)
| Archivo | Líneas | Acción sugerida |
|---------|--------|-----------------|
| `copilot-store.ts` | 320 | OK — state definition coherente |
| `copilot-input.tsx` | 243 | Extraer voice + file a subcomponentes |
| `useCopilotChat.ts` | 205 | Extraer streaming + event routing |
| `useVoiceRecorder.ts` | 204 | Extraer recording + transcription |
| `copilot-api.ts` | 197 | Extraer streaming + headers |
| `AssistantMessage.tsx` | 171 | Extraer card renderer switch |
| `WithCopilot.tsx` | 160 | OK pero denso — documentar |

---

## Priorización Recomendada

### Sprint 1: Hardening (bloquea producción)
1. C1 — Timeout en streaming LLM
2. C2 — Ownership check en conversaciones
3. C3 — Session leak en focus tools
4. C4 — Unique constraint en interview sessions
5. S1 — Rate limiting `/copilot/chat`
6. P1 — Fix 4 selectores Zustand bare

### Sprint 2: Reliability + Performance
7. R1 — SSE reconnection
8. R2 — Race condition en send rápido
9. R3 — Fresh entity data en focus activation
10. P2+P3 — Message limits + virtualización
11. P4 — memo() en message components
12. P5 — N+1 queries en focus

### Sprint 3: Testing Foundation
13. T1 — 3 smoke E2E tests (chat, interview, focus)
14. T2 — Tests para useCopilotChat
15. T4 — Tests de interacción para cards
16. T8 — Infraestructura E2E (POM + fixtures)

### Sprint 4: Polish + UX
17. UX1 — Animaciones de contenido sidebar
18. UX4 — Typing indicator durante streaming
19. UX5 — Card transitions
20. UX2 — Mobile responsive overlay
21. UX3 — Prefetch on hover
22. UX6 — Micro-interacciones focus bar

### Backlog
23. S2 — Sanitización prompt injection
24. S3 — Retención PII
25. R5 — Interview session expiry
26. P6 — Token estimation accuracy
27. D1-D3 — DDD compliance fixes
28. D4 — File splitting
29. T3, T5-T7 — Gaps de testing restantes
