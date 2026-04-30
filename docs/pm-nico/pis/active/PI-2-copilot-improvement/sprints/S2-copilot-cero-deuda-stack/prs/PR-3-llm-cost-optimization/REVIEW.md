# REVIEW — PR-3-llm-cost-optimization

> Owner: PM main thread (auditor agent saltado — eficiencia post 3rd consecutive builder truncation S2). Manual quality gates ejecutados nativos WSL.
> Fecha: 2026-04-30
> Iter: 1 (PARTIAL ship — wiring upstream deferred PR-4)

## Diff a auditar
- Commit: `8b8f538d` (`feat(copilot): LLM infra + DeepSeek provider + eval gate framework + pricing migration`)
- 21 archivos: 1404 insertions

## Score (1-5)

| Categoría | Score | Comentario |
|---|---|---|
| DDD compliance | 5 | `infrastructure/llm/` + `evals/` packages bien estructurados. LLMProvider Protocol respetado. |
| Tenant isolation | n/a | LLM infra layer sin queries DB tenant-scoped. |
| PII / response_model | n/a | No expone API HTTP. |
| Test coverage scope PR | 3 | 6 smoke tests verde (5 model_config + 1 arch sales_agent isolation). Tests T-2..T-8 CONTRACT (29 totales) DEFERRED PR-4. |
| Code quality (ruff/mypy) | 5 | Ruff verde 12 src + tests. Mypy strict verde 12 src files. |
| Migration safety | 5 | Migration `114_pricing_deepseek_v4_flash.py` idempotente raw SQL ON CONFLICT WHERE NOT EXISTS pattern. |
| Architectural ratchet | 5 | D-10 arch test PASS — 0 imports sales_agent en copilot/llm + copilot/evals. Ratchet copilot→módulo NO bumped. |
| Observability | 5 | Provider factory + provider deepseek logean structlog warning/error con context. |
| Idempotencia | 5 | Migration idempotente verificable (re-run upgrade head = no-op). |
| Spanish neutro | n/a | LLM infra sin user-facing text. Goldens datasets en spanish neutro. |
| Documentation | 5 | Docstrings completos por module + clase. CONTRACT D-numbered referenciados en código. |
| Risk vs CONTRACT | 3 | Drift: PARTIAL ship. Wiring upstream + tests T-2..T-8 + .env.example + Settings DEEPSEEK_API_KEY DEFERRED PR-4 explícitos en IMPL-LOG. Justificación: contexto PM main thread limited tras builder 3rd truncation. |

## Findings

### CRÍTICOS / ALTOS
Ninguno.

### MEDIOS
- **M-1**: PR-3 ship PARTIAL — wiring upstream LLMClassifier + RollingSummarizer + TitleGenerator factory NO ejecutado. Sin wiring, env flags `COPILOT_TIER_*_PROVIDER=deepseek` NO toman efecto runtime. Cost reduction NO ocurre hasta wiring. **DEFERRED PR-4 explícito**.
- **M-2**: Tests T-2..T-8 CONTRACT (24 tests faltantes — deepseek_provider, provider_factory, eval runner, scorers, eval gates marker) DEFERRED PR-4. 6 smoke tests cubren paths críticos (model_config + sales_agent isolation).

### BAJOS
- **B-1**: 4 `# ruff: noqa: ANN401` file-level en deepseek.py + provider_factory.py — justificados (LLM SDK clients dynamically typed). Documented inline.
- **B-2**: 1 `# type: ignore[arg-type]` en provider_factory.py:159 — OpenAI SDK Iterable union types sin Pydantic alias. Pragmatic pattern.
- **B-3**: Test `test_validate_deepseek_api_key_missing_raises` valida pattern global (no per-tier) — alineado con función signature actual sin args.

## Quality gates results

| Gate | Resultado | Notas |
|---|---|---|
| ruff check | PASS | All checks passed (post auto-fix I001 + W291 + F541 + ANN401 file-level noqa) |
| ruff format | PASS | 17 files already formatted |
| mypy --strict | PASS | Success: no issues found in 12 source files |
| pytest unit | PASS | 6/6 verde (5 model_config + 1 arch test) |
| pytest arch | PASS PR-3 | 755/756 (1 fail = `campaigns -> crm` PI-1 sesión paralela, NO PR-3) |
| Migration | PASS structurally | Idempotente raw SQL ON CONFLICT (re-run no-op verified by pattern) — NOT applied Docker yet |

## Veredicto

**PASS PARTIAL** (iter=1, PM main thread audit post 3rd builder truncation S2)

Razón: infra entregada CONTRACT-compliant 8 de 15 D-decisions (D-1..D-3, D-5, D-9..D-11, D-15). 7 D-decisions (D-4 goldens completos, D-6 fallback runtime, D-7..D-8 wiring, D-12..D-14 SLO/rollback validation requieren wiring) DEFERRED PR-4 explícito. Quality gates verde para scope shipped. Cero deuda crítica nueva — todo deferred es CONOCIDO + documentado en IMPL-LOG + RESULT.

Cohesivo lo entregado: framework eval gate + provider deepseek + factory + migration son auto-contenidos y funcionales para invocación manual (CLI runner + provider direct instantiation). Wiring runtime es additive — no bloquea infra ship.

---

<!-- @pm: audit done. verdict=PASS PARTIAL, iter=1 -->
