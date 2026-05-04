# Rubric — Code Quality

```yaml
---
id: code-quality
version: 1
applies_to: [tickets]                          # usado por /auditor en T-{n}-review
type: hybrid                                   # code-checks + LLM-judge
threshold_default: 0.8
---
```

## Propósito

Auditor evalúa code quality post-implementación. NO sustituye gates automáticos (ruff, mypy, coverage) — los complementa con análisis semántico.

## Code-based assertions (auto)

> Auditor corre estos PRIMERO. Si auto-fail aquí → no necesita LLM judge.

### A1. Lint/format passing

```bash
ruff check src/modules/{m}/ tests/modules/{m}/        # 0 errors
ruff format --check src/modules/{m}/ tests/modules/{m}/
```

### A2. Type-check passing

```bash
mypy src/modules/{m}/ --strict                        # si módulo tiene mypy strict
tsc --noEmit                                           # FE
```

### A3. Tests passing

```bash
pytest tests/modules/{m}/ -x -q
```

### A4. Coverage delta

- Coverage del módulo no baja vs baseline
- Idealmente ↑ (test coverage sumado por nuevo código)

### A5. Arch fitness passing

```bash
pytest tests/architecture/ -v --override-ini="addopts="
```

## LLM-judge assertions (semánticas)

### A6. DDD layer respect

- ✅ Domain pure (no FastAPI imports en domain/)
- ✅ Infrastructure implementa domain ports
- ✅ Application services orquestan, no contienen lógica
- ✅ API thin (solo routing + DTO mapping)
- ❌ Cross-layer leak

### A7. Naming consistency

- ✅ Pass: nombres siguen convenciones del proyecto
- ❌ Fail: `getUserById` en proyecto que usa snake_case

### A8. Error handling

- ✅ Pass: excepciones nombradas, no `None` returns para errores
- ❌ Fail: catch-all `except Exception: pass`

### A9. Tenant isolation

- ✅ Pass: cada query filtra `tenant_id`
- ❌ Fail: `repo.get_by_id(id)` sin tenant scoping

### A10. PII safety

- ✅ Pass: response_model exclude PII
- ❌ Fail: raw user data en log/response

### A11. No deuda introducida

- ✅ Pass: sin TODO/FIXME sin contexto
- ❌ Pass: sin `# noqa` sin justificación
- ❌ Pass: sin `any` o `unknown` no justificados (FE)

### A12. Anti-duplication

- ✅ Pass: no mirror code de otros módulos (ver `anti-duplication.md` inventario)
- ❌ Fail: re-implementación local de pattern shared

### A13. Test quality

- ✅ Pass: tests verifican outcome, no implementation detail
- ✅ Pass: usan factories/fixtures, no mocks excesivos
- ✅ Pass: test names descriptivos
- ❌ Fail: test que solo asserta "no exception"

### A14. Spanish neutro UI

- ✅ Pass: strings user-facing sin voseo (salvo sales_agent voz tenant)
- ❌ Fail: voseo en UI labels

### A15. Documentation mínima

- ✅ Pass: docstrings en funciones públicas si non-obvious
- ❌ Fail: docstrings ausentes en API endpoints

## Scoring

```
code_pass = all([A1, A2, A3, A4, A5])           # binario, gate
if not code_pass:
    return 0.0                                   # auto-fail

judge_score = avg([A6..A15])
final_score = judge_score                        # gates ya pasaron
```

Threshold default: **0.8** (8/10 assertions LLM passed).

## Self-fix policy auditor

> Auditor puede auto-fixear ANTES de declarar verdict, SOLO triviales:

| Categoría | Self-fix permitido |
|---|---|
| Lint/format | ✅ |
| Typo en string | ✅ |
| Import ordering | ✅ |
| Comentario eliminar | ✅ |
| Cualquier otra | ❌ → escala |

Cap: 2 iteraciones self-fix. Después → CHANGES_REQUESTED al dev.

## Histórico

- v1 2026-05-04 — initial. Cubre 11 categorías review en `nicolify-backend-auditor.md` legacy + extensiones agentic.
