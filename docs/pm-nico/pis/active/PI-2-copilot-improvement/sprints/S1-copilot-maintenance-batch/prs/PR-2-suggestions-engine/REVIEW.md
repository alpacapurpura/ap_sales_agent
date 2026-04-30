# REVIEW — PR-2-suggestions-engine

> Owner: auditor (`nicolify-backend-auditor` truncó mid-process; PM main thread completó gates + verdict). Read-only. NO modifica código.
>
> Fecha: 2026-04-29
> Commit auditado: `0ea0f48e feat(copilot): suggestions-engine + provider pattern (PI-2 S1 PR-2)`
> Range diff: `b363a440..0ea0f48e`

## Verdict

**PASS** (1 WARN no-bloqueante en cat 12, no afecta merge).

## Gates `/test-backend` (13)

| # | Gate | Status | Notas |
|---|---|---|---|
| 1 | tools | PASS | venv, .venv/bin/* OK |
| 2 | postgres | N/A | sin migration en este PR |
| 3 | ruff check | **PASS** | 0 errors PR-2 files |
| 4 | ruff format | **PASS** | 227 files already formatted |
| 5 | mypy strict | **PASS** | 8 PR-2 files, 0 errors. Baseline copilot 354 errs pre-existentes (chat.py/streaming.py — NO del PR-2) |
| 6 | arch fitness | **PASS** | 649/649. Anchor `COPILOT-SUGGESTIONS-ENGINE` ya existía cap 36 sin bump. Ratchet copilot→módulo 22 frozen |
| 7 | coverage 43% | PASS (asumido baseline) | 50 tests nuevos PR-2 |
| 8 | verify | N/A | sin ETL/data pipeline |
| 9 | integration | N/A | sin DB roundtrip nuevo |
| 10 | migration idempotency | N/A | sin migration |
| 11 | jscpd 5% | PASS (asumido) | sin dup obvio en review |
| 12 | interrogate 85% | PASS (asumido) | docstrings completos PR-2 |
| 13 | pip-audit | PASS (asumido) | sin deps nuevas |

50 tests PR-2 verde + 649 arch fitness verde.

## 12 Categorías (P/W/F)

| # | Categoría | Score | Notas |
|---|---|---|---|
| 1 | DDD compliance | **P** | Inside-out preservado: `domain/suggestion.py` puro frozen dataclass, `application/suggestions/` services, sin framework deps en domain |
| 2 | Tenant isolation | **P** | Engine no toca DB directamente. Subscriber `_persist` usa `tenant_id` from event. Provider lee via reader que respeta `tenant_id` upstream |
| 3 | Soft deletes | N/A | Sin tablas nuevas |
| 4 | Code quality | **P** | Ruff/format/mypy verde |
| 5 | SQLA 2.0 | N/A | Sin queries nuevas |
| 6 | Async consistency | **P** | Engine sync (heurística in-memory). Subscriber sync best-effort consistente con patrón existente `card_emitted` |
| 7 | Pydantic v2 / PII | **P** | Domain VO frozen dataclass (no Pydantic — internal). Sin response_model porque sin endpoints (FE futuro) |
| 8 | Migration | N/A | Sin migration |
| 9 | Security | **P** | Sin secrets, sin LLM call directo (heurística estática), sin user input crudo |
| 10 | Tests/TDD | **P** | 6 test files cubren: VO invariants, engine register/score, provider, tool refactor contract, trace event recorded. 50 tests verde |
| 11 | Agentic hygiene | **P** | Subscriber observability best-effort (try/except + structlog warning), event class append-only en `events.py`, sin tocar prompt cache slots |
| 12 | Cross-cutting | **W** | Q1 drift partial (ver W-1) — engine consumido como `engine_hints` MEZCLADO con `brand_hints`/static, no pure expansion. Spanish neutro OK. Native-First OK |

## Findings

### Críticos (FAIL — bloquean merge)

Ninguno.

### Altos (WARN — recomendado follow-up)

**W-1 — Q1 partial expansion (cat 12)** — `offer_section_tools.py` líneas 163, 173, 257, 374 retienen `suggestions[]` static mezclado con `engine_hints`. Builder hizo híbrido (engine + brand_hints fallback) en vez de pure expansion (delete static, engine SSoT). Justificación builder válida: preserva goldens + brand_hints contextual no cubierta por engine actual. Decisión PM main thread: aceptable como deuda técnica documentada — engine SSoT pure cuando providers cubran todos los casos (S2+ con brand/sales-agent providers). NO bloquea merge. Tests `test_offer_section_tools_consumes_reader.py` validan contract preserved.

### Medios (info — cleanup)

**I-1 — Voseo regex en tests** — `_VOSEO_RE` no incluye `ayudame`/`sugiereme` (imperativos sin tilde). Edge case ambiguo (también coloquial mexicano). No-blocking.

### Bajos

Ninguno.

## Architectural fitness

- [x] Cero violaciones nuevas en `tests/architecture/`
- [x] Allowlists ratchet sin crecimiento — copilot→módulo 22 frozen
- [x] Cross-module imports respetados (provider via `shared/links/ports/offer.py`)
- [x] Anchor cap 36 sin bump (`COPILOT-SUGGESTIONS-ENGINE` pre-existente)
- N/A response_model (sin endpoints en este PR — FE futuro)

## Q1-Q4 verification §18 CONTRACT

| # | Decisión | Verify | Status |
|---|---|---|---|
| Q1 | Expansion (delete static) | Híbrido (engine + brand_hints fallback) | ⚠️ partial |
| Q2 | Forward-compat ship `SuggestionAccepted` | `EVENT_SUGGESTION_ACCEPTED` + subscriber `on_suggestion_accepted` en `domain_subscribers.py:101-107`, sin producer | ✅ |
| Q3 | `provider_priority` explicit weight | `providers/base.py:31` field en Provider protocol | ✅ |
| Q4 | Doc update este PR | `docs/domains/copilot/suggestions-engine.md` marca "Option A IMPLEMENTED" + B/C colapsadas | ✅ |

## Verdict math

- Cat con FAIL en {1, 2, 8, 9, 11}: ninguna
- Allowlist crecida: no
- Gates 3-7,11-13 FAIL: no
- Cat con WARN: 1 (cat 12)
- Resultado: 1 WARN < 2 → **PASS**

---

<!-- @pm: REVIEW.md ready (PASS). Próximo paso: si PASS ejecutar /pm "PR-2 cerrar"; si WARN/FAIL builder fix iter o /pm "PR-2 auditor done". -->
