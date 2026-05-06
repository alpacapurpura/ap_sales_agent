# S2-shared-observability — Sprint Learnings

> Append-only. Captured during sprint execution + crystallized at sprint close.

## L1 — 5-layer anti-duplication enforcement WORKS end-to-end

**Situación:** Primer PR (PR-2) bajo el nuevo proceso (commits `b0700be9` + `3e84bb93`) tras la lección dura de PR-1 (turn_envelope mirror duplication).

**Test:** Architect Opus ejecutando Step 0 grep gate del template MANDATORY catched PR.md outdated info — "FXResolver() at lines 116, 168" cuando real es solo 1 sitio en factory.py:78. Sin el bloque grep evidence MANDATORY, el builder hubiera ido a buscar 2 sitios inexistentes.

**Conclusión:** Layer 1 (PR.md mandatory grep evidence) NO ES BUROCRACIA. Catches errors that propagate downstream. Mantenerlo strict.

## L2 — Builder cap maxTurns 150 fits para narrow scope, NOT para large refactor

**Situación:** Builder agentic Opus fue spawned con full PR-2 scope (architect estimó 50-70 turns). Builder hit cap **150** mid-cleanup (`Any` annotation conversation_pipeline). 9 NEW files + 11 modified done en disco, 0 commits.

**Análisis:** Architect estimó conservador 50-70 pero scope real era 150+ turns por:
- Step 0 grep gates per archivo nuevo (5+ files)
- TDD strict: test first then impl per sub-paso
- 6 tests escritos
- 3+ orchestrator wires (chat + outbound + pipeline)
- Quality gates intermedios

**Solución aplicada:** Re-spawn Opus narrow scope ("WIP en disco, solo cleanup + commit + audit"). 67 turns. PASS first pass.

**Conclusión:** Architect estimates DEBEN ser pessimistic en TDD-strict workflows. Default suposición: builder needs 100-200 turns para Refactor LIFT-TO-SHARED. Cap 150 fits si scope is JUST cleanup+commit+audit (~30-70 turns).

**Regla derivada:** Si architect estima >100 turns → architect explicit splittear PR en sub-deliverables OR pre-warn PM que re-spawn narrow scope será necesario post primer pass.

## L3 — Best-effort observability funciona cuando captura errors también

**Situación:** Smoke test Chris-mediated. Bot respondió error técnico por Bug #7+#9 (LLM stack down). Observability ENGÁGE correcto:

| Event | Status | Persisted? |
|---|---|---|
| turn_start | ok | ✅ |
| llm_call deepseek | error | ✅ (cost_usd=0, fx_rate=passthrough) |
| llm_call gpt-4o-mini | error | ✅ |
| turn_end | error (APIConnectionErr) | ✅ |

**Conclusión:** Envelope `__aenter__` commits turn_start ANTES de invoke. Si invoke falla, callback handler captura llm_call rows con cost=0 + turn_end con error_type. **No se pierde turn lifecycle ante fallo LLM.**

**Validación CONTRACT § 2:** "Lifecycle methods: `__aenter__` → turn_start row commit; `__aexit__` → turn_end row commit; exception → set_turn_error row commit" — implementación matchea spec.

## L4 — Cross-session M8 protocol funciona cuando ambas sesiones lo respetan

**Situación:** Sprint S2 y otra sesión PI-5 PR-2 trabajaron simultáneamente sobre `modules/copilot/`. Ambas sesiones modificaron `chat.py` y `observability/recording/turn_envelope.py`.

**Resultado:**
- PI-5 PR-2 commiteó `6bad657b` (PR closure) + `d09799b9` (telegram orchestrator hookup)
- PR-2 SHARED commiteó `d80d15f5` (LIFT shared base)
- M8 verify pre-commit: hunks distintos, no function-level overlap (REVIEW-agentic confirmó)
- Chris-mediated handshake: ambas sesiones avisadas vía `sprint.md` § coordination

**Conclusión:** M8 funciona porque (a) Chris-mediated handshake explícito previo, (b) builder verifica `git diff` pre-commit, (c) auditor confirma no function-level overlap. Sin esos 3 → riesgo collision.

## L5 — Smoke test desbloquea visibilidad de stack faltante

**Situación:** PR-2 fixed Bug #2. Smoke test reveló Bug #7 (brand adapter) + Bug #9 (LiteLLM container) que estaban OCULTOS porque sin observability no había visibilidad ningún error.

**Conclusión:** Observability emerges → cascading bugs visible. Bug #7+#9 estaban presentes pre-PR-2 pero invisible. PR-2 desbloqueó visibilidad. Esos 2 bugs ahora son tractable porque trazas + logs muestran exact failure point.

**Aplica forward:** cuando se ship observability, expect descubrimiento N+1 bugs cascading que estaban ocultos. Plan handoff.

## Summary

PR-2 shipped:
- ✅ Bug #2 traces persistence verified end-to-end
- ✅ Bug #8 FXResolver.default factory cementada
- ✅ 5-layer anti-duplication primer test PASSED
- ✅ Cross-session M8 verified clean
- ❌ Bug #7+#9 cascade descubiertos (out-of-scope, deferred)

Sprint S2 close criteria met. Handoff a `handoff.md`.
