# S1 Learnings — Test Integrity Hardening

> Append durante sprint, congela al cerrar.

## PR-1 (shipped 2026-05-04)

### Polluter hunt — qué funcionó, qué no

| Hipótesis investigada | Iter | Resultado |
|---|---|---|
| uuid4() x2 calls en `OutboxEntry.from_event` lines 65/69 — flag `_is_outbox_enabled` turn OFF (monkeypatch leak) | iter 1 (agente original) | **DESCARTADA** — uuid4 era síntoma no causa |
| `ChatOrchestrator._instance.buffer_service` + `SemanticRouter._instance` leak cross-test | iter 2 (agente continuación) | **CONFIRMADA** — fix at source vía singleton fixture business iter 1 ya cubrió |

Lección: el primer iter Opus puede mid-investigation tirar hipótesis prematuras. iter 2 con prompt enriquecido + estado actual + insight previo descartó hipótesis y confirmó real root cause.

### Singleton fixture exhaustive pattern

5 class-level singletons + 2 module-level caches identificados via grep `_instance =` + `@lru_cache|@cache`:
- LLMFactory._instance
- ChatOrchestrator._instance (cleanup buffer_service first, then reset)
- SemanticRouter._instance
- EventBus._handlers (clear)
- EventBusAdapter @cache (_reset_module_inference_cache)
- ChannelRouterRegistry: EXCLUDED (bootstrap-once, romperíamos campaigns tests)
- MetaAPI._api_instance: EXCLUDED (per-instance, NOT class-level)

Lección: NO TODOS los singletons resetean cleanly. Algunos (bootstrap-once) requieren EXCLUDE explícito + documentación reason en fixture.

### Default flip = side-effect call path change

Commit `64738354` (PR-1 Sub-E PI-2) flipeó `USE_OUTBOX_PATTERN_*=False→True` sin auditar tests que mockean path legacy. 25 BE failures + 1 polluter no identificable. PR-1 PI-11 reparó. PR-3 enforza.

Patrón: cualquier flag default flip que cambia call path real DEBE incluir audit grep tests + migración mocks pre-merge.

### Cost real PR-1

| Phase | Tokens (approx) | Notes |
|---|---|---|
| Context-builders Haiku x2 (PR-1 + PR-3) | ~145k total | Pre-flight ahorra 30-50k Opus downstream |
| Architect Opus 1 ejecución (CONTRACT PR-1 + PR-3) | ~223k | 51KB CONTRACT PR-1 + 28KB PR-3 |
| Business builder Sonnet (iter 1) | ~66k | Stash apply + singleton fixture + LegacyEventBus dep + litellm clamp + EventBus migration brand |
| Agentic builder Opus (iter 1) | ~303k | Mid-investigation polluter hunt — terminó incompleto |
| Agentic builder Opus (iter 2 continuación) | ~198k | Completó workflow + polluter root cause confirmado |
| Gate-runner Haiku iter 1 | killed | Machine crashed mid-pytest 79% |
| Gate-runner Haiku iter 2 (subset) | ~34k | Lightweight: lint/format/mypy/jscpd/interrogate/pip-audit |
| Backend auditor Opus (iter 1) | killed (stalled 600s) | Agent crashed |
| Backend auditor Opus (iter 1 continuación) | ~136k | Scoring ágil — completó PASS verdict |
| Agentic auditor Opus | ~163k | PASS verdict + 3 findings info-only |
| **Total approx** | **~1.27M tokens** | Investigación profunda + 2 crashes recovered |

Lección: agentic Opus polluter hunts son CAROS por iteraciones pytest run + análisis exhaustivo. Cuando builder termina mid-thought (no pause sino completion sin verdict) = re-spawn enriched.

### Process meta-learnings

1. **Re-spawn Opus enriched > pause+resume cuando agent dies sin verdict.** Iter 1 + iter 2 continuación combined = ~501k pero PR-1 entregado completo + verificado.
2. **Subset gate-runner válido cuando full /test-backend riesgo crash.** Reducir a lint/mypy/jscpd/interrogate/pip-audit + pytest NATIVE_VALIDATED por evidencia builder.
3. **Self-audit por builder NO sustituye auditor Opus oficial.** Builder agentic iter 2 hizo "self-audit checklist" pero PM SIEMPRE spawn auditor Opus real.
4. **Auditor Opus puede stallear con prompts grandes.** Solución = prompt "scoring ágil" (focused diffs only, NO re-read full sources, consume gate-output.json + IMPL-LOG nativos).
5. **Otra sesión Claude paralela puede tocar archivos durante PR.** Detected playwright-expert skill setup mid-sprint. Regla M8 respetada.

## PR-3 (shipped 2026-05-04)

### Anti-default-flip enforcement cementado

| Layer | Mecanismo |
|---|---|
| Rule docs | `.claude/rules/anti-default-flip-audit.md` 4-step workflow + 6 flags inventario + 7 enforcement layers |
| Arch fitness | `test_no_legacy_eventbus_mock_when_outbox_on.py` AST walk Pattern 1+2 |
| Bypass 3-tier | BYPASS_FILES (10 permanent) + KNOWN_LEGACY (3 D9 ratchet shrink-only) + magic comment |
| Meta-test | 8 casos coverage |
| CLAUDE.md | Conditional rule entry |

### Lección AST walk arch fitness

Sibling pattern existing `test_no_legacy_event_bus_publish.py` reusable. Pattern 1 (string `@patch("X")`) + Pattern 2 (`patch.object(EventBus, "publish")` synthesized) — cubre 90%+ casos. Edge cases (computed string variables, alias imports) → magic comment cubre.

Performance: ~220 test files scan < 2s wall-time (rglob + ast.parse).

### Lección Self-audit por builder ≠ Auditor Opus oficial

Builder PR-3 hizo self-audit completo (REVIEW.md por Sonnet). PM REJECTED + spawn auditor Opus oficial (D13). Razón: regla cardinal "PR no se cierra sin Opus output". Auditor Opus oficial validó independientemente + 0 findings nuevos = self-audit era correcto, pero formalmente requerido Opus REVIEW.md.

Trade-off: +145k tokens Opus extra. Costo aceptable vs riesgo aprobar PR sin Opus eyes.

### Deviation CONTRACT § 2 justificada

CONTRACT estimó BYPASS_FILES=7 pre-impl. Builder grep real reveló 10 legítimos + 3 violators reales (deferred D9). Auditor Opus validó deviation. Lección: architect specs allowlist sizes son estimaciones — builders ajustan en realidad + auditor valida.

## Pendiente sprint S1

- PR-4: PM directo (markdown agents/skills/rules updates) — NEXT
- PR-2: coverage P0 crm/scheduling

## Pendiente cerrar sprint

- handoff.md → S2
- Roadmap update si aplica
