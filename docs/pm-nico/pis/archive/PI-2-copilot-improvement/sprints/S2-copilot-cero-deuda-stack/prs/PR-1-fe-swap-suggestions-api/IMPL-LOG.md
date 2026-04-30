# IMPL-LOG — PR-1-fe-swap-suggestions-api

> Owner: `nicolify-backend`. Append-only. Diario de decisiones implementación.

## Sesión 2026-04-30 — nicolify-backend (BE scope)

### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (architect-empowered, 16 decisiones, ZERO open questions)
- Skills: `copilot-expert` ✓, `backend-expert` ✓, `tessl__fastapi` ✓, `tessl__pytest-api-testing` ✓

### Decisiones implementación

- **asyncio.to_thread (D-3)**: implementado como especifica CONTRACT. Engine sync + wrapping async evita bloquear event loop.
- **noqa N812**: `adapter_bus as EventBus` requiere `# noqa: N812` — mismo patrón que `chat.py:79`.
- **SuggestionDTO incluye source_module**: D-6 override final — slug público no PII. metadata excluido.
- **best-effort doble**: engine try/except + EventBus.publish try/except independientes (D-10/D-11).
- **Anchor reutilizado**: `[COPILOT-SUGGESTIONS-ENGINE]` en header. Cap 36/37 no bumpeado (D-15).
- **Ratchet 22 frozen**: solo imports dentro de `copilot.*` + `iam.api.dependencies` + `shared.domain_events.*`.

### Sub-deliverables completados
- [x] DTOs Pydantic v2: `suggestions_dto.py`
- [x] Router: `suggestions.py` (2 endpoints)
- [x] main.py: +1 import + include_router
- [x] Tests RED-GREEN TDD: 16 tests (8 unit + 5 unit accept + 3 integration)

### Quality gates

- [x] Ruff lint verde
- [x] Ruff format verde
- [x] Mypy strict verde (0 errors)
- [x] Pytest unit verde (13/13)
- [x] Arch fitness verde (34 passed — ratchets intactos)
- [x] Migration N/A (sin schema changes)

### Pre-existing failures (parallel session campaigns — NO de este PR)
- `test_master_data.py::test_no_new_usd_defaults` — `campaigns/infrastructure/channels/shared.py`
- `test_folder_naming.py::test_all_python_files_snake_case` — `campaigns/api/_*.py`
- `test_ddd_boundaries.py::test_no_new_cross_module_imports` — `campaigns/api/_service_factories.py`

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| API router | `backend/src/modules/copilot/api/suggestions.py` | live |
| DTOs | `backend/src/modules/copilot/api/suggestions_dto.py` | live |
| main.py wiring | `backend/src/main.py` | live |
| Unit tests suggestions | `backend/tests/modules/copilot/api/test_suggestions_endpoint.py` | 8/8 green |
| Unit tests accept | `backend/tests/modules/copilot/api/test_suggestions_accept_endpoint.py` | 5/5 green |
| Integration tests | `backend/tests/modules/copilot/api/test_suggestions_endpoint_integration.py` | 3 tests mark.integration |

---

<!-- @pm: implementación BE done. Próximo paso: ejecutar prompts/03-auditor-start.md. -->

---

## 2026-04-30 — FE builder (nicolify-frontend)

### Contexto cargado
- `PR.md` ✓
- `CONTRACT.md` ✓ (16 decisiones architect-empowered)
- Skills: `copilot-expert` ✓, `frontend-expert` ✓
- Reglas: `frontend-fsd.md`, `frontend-quality.md`, `tdd-mandatory.md`, `parallel-safety.md`, `git-safety.md`, `spanish-text.md`
- Archivos existentes leídos: `voice-api.ts`, `use-suggestions.ts`, `types/suggestions.ts`, `SuggestedChips.tsx`, `SuggestedActions.tsx`, `copilot-store.ts`

### Decisiones implementación

1. **TDD estricto**: Tests RED escritos antes de implementación. 4 archivos de test creados/actualizados. 21 tests nuevos, todos verdes. Suite copilot completa: 285/285.

2. **Mock paths en tests de componentes**: Tests en `components/composer/__tests__/` requieren paths `../../../hooks/...` (relativos al test), no `../../hooks/...` (relativos al componente). Detectado al verificar RED state.

3. **D-9 voice adapter**: URL swap + shape adapter en `voice-api.ts`. Firma pública `TranscriptionResponse` intacta — consumers (composer voice button) sin cambios necesarios.

4. **useSuggestions rewrite**: ROUTE_SUGGESTIONS map eliminado completamente. React Query con `queryKey: ["copilot", "suggestions", currentRoute, conversationId]`, `staleTime: 5min`, `retry: false` (D-10), `gcTime: 10min`.

5. **useSuggestionAccept**: Fire-and-forget, NO invalida queries (D-13). `onError` = `console.warn`, no re-throws.

6. **react-perf warnings**: 3 warnings en archivos modificados son patrones pre-existentes en los componentes originales (inline style maskImage, onClick arrow functions). No incrementan baseline.

7. **Deuda D-14 verificada**: `grep -rn "ROUTE_SUGGESTIONS" frontend/src/` = 0 definiciones de map. `grep -rn "voice/transcribe" frontend/src/` = 0 llamadas activas.

### Sub-deliverables completados

- [x] `types/suggestions.ts` extendido con Request/Response types
- [x] `api/suggestions-api.ts` (nuevo): fetchSuggestions + acceptSuggestion
- [x] `api/voice-api.ts` modificado: D-9 URL swap + shape adapter
- [x] `hooks/use-suggestions.ts` reescrito: React Query, drop ROUTE_SUGGESTIONS
- [x] `hooks/use-suggestion-accept.ts` (nuevo): fire-and-forget mutation
- [x] `components/composer/SuggestedChips.tsx`: accept mutation wired onClick
- [x] `components/SuggestedActions.tsx`: ROUTE_SUGGESTIONS eliminado, consume hooks

### Tests escritos (TDD RED-first)

- `hooks/__tests__/use-suggestions.test.ts` — 6 tests: chips from API, graceful on failure, no token, re-fetch on route/convId change, correct body params
- `hooks/__tests__/use-suggestion-accept.test.ts` — 4 tests (nuevo): payload, ISO UTC, no query invalidation, onError warning
- `api/__tests__/voice-api.test.ts` — 5 tests (nuevo): URL adapter, shape adapter, null fields, non-ok throws, Authorization
- `components/composer/__tests__/SuggestedChips.test.tsx` — 6 tests (nuevo): renders, null when empty, null when loading, accept+onClick, order, stable keys

### Quality gates

- [x] ESLint verde (0 errors; 3 warnings react-perf pre-existentes)
- [x] TSC verde (0 errors)
- [x] Vitest verde (285/285 copilot, 39/39 arch fitness)
- [x] Arch fitness 20 tests verde

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| FE types | `frontend/src/features/copilot/types/suggestions.ts` | MODIFICADO |
| FE api | `frontend/src/features/copilot/api/suggestions-api.ts` | NUEVO |
| FE api | `frontend/src/features/copilot/api/voice-api.ts` | MODIFICADO (D-9) |
| FE hook | `frontend/src/features/copilot/hooks/use-suggestions.ts` | REESCRITO |
| FE hook | `frontend/src/features/copilot/hooks/use-suggestion-accept.ts` | NUEVO |
| FE component | `frontend/src/features/copilot/components/composer/SuggestedChips.tsx` | MODIFICADO |
| FE component | `frontend/src/features/copilot/components/SuggestedActions.tsx` | MODIFICADO |
| FE tests | 4 test files (21 tests nuevos) | TODOS VERDE |

---

<!-- @pm: FE builder done. Tanto BE como FE implementaciones completas para PR-1. -->

