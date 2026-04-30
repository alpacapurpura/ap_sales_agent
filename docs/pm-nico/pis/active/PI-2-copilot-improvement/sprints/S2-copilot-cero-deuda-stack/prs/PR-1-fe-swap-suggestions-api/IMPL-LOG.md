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
