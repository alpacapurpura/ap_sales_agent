# Prompt — Builder kickoff PR-1-cascade-bugs-recovery (backend negocio)

> **Prerequisitos:** `prompts/00-context-prep.md` ejecutado (CONTEXT-BRIEF.md ready) + `prompts/01-architect-start.md` ejecutado (CONTRACT.md ready).
>
> Builder = `nicolify-backend` (Sonnet). Surface principal = `modules/brand/`.
> Bug #9 (infra litellm) sale de scope `nicolify-backend` por defecto. CONTRACT § 0 dictamina: si infra fix es trivial (mount syntax) → builder lo aplica como ad-hoc; si requiere docker rebuild + litellm config regen → escalate PM para fix manual coordinado.
>
> Builder spawnea auditor automáticamente al terminar — Chris recibe código YA AUDITADO Y CORREGIDO.

## Spawn pattern

```
Agent({
  description: "Build PR-1 cascade-bugs-recovery (backend brand + infra)",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre fix-loop iters]

Sos `nicolify-backend` (Sonnet). Trabajo: implementar PR completo siguiendo CONTRACT.md + auto-spawn gate-runner + auditor + fix loop hasta PASS.

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md — pre-flight Haiku (lee § 7 + § 8 — duplicate detection)
2. {pr_folder}/CONTRACT.md — schemas + interfaces + decisiones (SSoT pre-implementación) — incluye scope decision (single PR vs split) + order of execution
3. {pr_folder}/PR.md — problema + scope (si CONTEXT-BRIEF está incompleto)
4. CLAUDE.md (root) — sección "Git Workflow — INVIOLABLE"
5. .claude/rules/anti-duplication.md — inventario shared abstractions

Skills obligatorios (invoca via Skill tool ANTES de tocar código):
- backend-expert (módulo backend)
- brand-expert (PersonalityProfile schema + adapter pattern + DTO conversion)

Restricciones DURAS:
- Tocás SOLO archivos de tu surface según CONTRACT § 0 mapping. Lista paths permitidos derivada del CONTRACT.
- nicolify-backend NO toca modules/copilot/ ni modules/sales_agent/ (escalate nicolify-agentic). EXCEPCIÓN: si CONTRACT define que sales_agent.knowledge_builder es READ-ONLY consumer y no requiere cambio → OK leer pero no editar.
- NO tocás archivos de otros PRs activos (regla M7). PI-4 S1 toca brand module — verificá CONTEXT-BRIEF § 6 cross-session overlap. Si paths colisionan → STOP y escalate PM.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify, branches/worktrees.
- Push falla non-fast-forward → STOP, reportar Chris. NO git pull para resolver.

Bug #9 infra fix scope (CONTRACT decide):
- Si CONTRACT clasifica "trivial" (mount syntax change docker-compose.yml o regen config.yaml from template) → builder aplica + verifica `docker compose up -d litellm` + `curl http://localhost:4000/health` retorna 200.
- Si CONTRACT clasifica "non-trivial" (litellm config regen with API keys, multi-service rebuild) → builder STOP y escalate PM con findings. PM coordina fix manual.

Step 0 GATE — Anti-duplication grep ANTES de cualquier `Write` que crea archivo nuevo:

> Origen rule: PR-1 PI-1.1 hotfix 2026-05-01 — builder agentic creó `turn_envelope.py` mirror de copilot existing. REVERT obligatorio.

Para CADA archivo nuevo que vas a crear con `Write`:
1. **Verificar inventario shared abstractions:** `cat /home/chris/AISALESHT/.claude/rules/anti-duplication.md` — buscar tu subsystem en tabla. Si listado → SOLO extend desde shared, NO mirror.
2. **Grep nombre similar cross-codebase:**
   ```bash
   find /home/chris/AISALESHT/backend/src -name "<basename>.py" 2>/dev/null
   grep -rn "class <ClassName>" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null
   ```
3. **Si grep encuentra match cross-module:**
   - STOP. Append IMPL-LOG.md sección "Step 0 grep findings" con paths + line numbers.
   - 3 opciones: EXTEND existing | LIFT-TO-SHARED | NEW justificado (escalate PM con evidencia).
4. **Si grep no encuentra match Y subsystem no listado en `rules/anti-duplication.md`:**
   - Procedé. Documentá en IMPL-LOG.md "Step 0 grep clean".

Para Bug #7 NO esperás crear archivos nuevos (es fix in-place de `brand_data_adapter.py:46`). Pero si CONTRACT propone helper nuevo (`_to_json_dict`, `personality_profile_to_dict`, etc.) → Step 0 GATE aplica.

Workflow Phase 1 — IMPLEMENT:
1. TDD strict: tests RED ANTES implementación.
   - `test_brand_data_adapter_handles_orm_personality_profile` — RED reproduce Bug #7 con SQLA model fixture, GREEN post-fix
   - Si CONTRACT pide unit test de helper nuevo → RED primero
2. Implementar Bug #7 fix según CONTRACT (opción A upstream Pydantic conversion | opción B downstream `_to_json_dict` helper | opción C dataclasses.asdict).
3. Implementar Bug #9 fix según CONTRACT (mount syntax o config regen) si scope = trivial.
4. Quality gates locales NATIVE (sin docker exec):
   - cd backend && .venv/bin/{ruff|pytest|mypy}
5. Si bloqueado arquitectónicamente → STOP, append a IMPL-LOG.md, devolver control a PM (NO inventar solución).
6. Llenar IMPL-LOG.md completo (sub-deliverables, decisiones, skill consultations, tests, gates, commits, EXTEND-vs-NEW decision si aplica).
7. Stage por nombre + conventional commit + push origin development.
   - Bug #7 commit: `fix(brand): convert ORM PersonalityProfileModel to dict in brand_data_adapter (Bug #7)`
   - Bug #9 commit: `fix(infra): docker-compose litellm mount config.yaml (Bug #9)`

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT (obligatorio):

Phase 2.1 — Spawn gate-runner Haiku:
8. Agent({
     description: "Run /test-backend gates iter-{N}",
     subagent_type: "nicolify-gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery; <command>: test-backend; <iter>: {N}"
   })
9. Esperá gate-output.json. Si overall.any_fail = true → fix scope findings, re-stage + re-commit + re-spawn gate-runner. NO sigas a Phase 2.2 hasta gates green.

Phase 2.2 — Spawn auditor Opus:
10. Agent({
      description: "Audit PR-1 backend",
      subagent_type: "nicolify-backend-auditor",
      model: "opus",
      prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery; iter: {N}"
    })
11. Esperá REVIEW.md output. Lee verdict.
12. Si verdict = PASS → terminás. Última línea respuesta:
    <!-- @pm: implementación + gate-runner + auditoría done (verdict PASS). PR-1 listo para /pm "PR-1 cerrar" -->
13. Si verdict = WARN o FAIL → entra Phase 3.

Workflow Phase 3 — AUTO-FIX LOOP (max 3 iteraciones):
14. Lee findings file:line del REVIEW. Filtrá findings que tocan paths de TU surface (regla M7).
15. Para cada finding FAIL/WARN dentro scope:
    - Si finding == drift CONTRACT vs código → STOP fix, NO inventes solución. Append IMPL-LOG bloqueador "Drift CONTRACT — escalate PM". Devuelve control con verdict actual + nota.
    - Si finding == missing test/typo/hardcoded value/refactor menor → fixá.
    - Si finding == arquitectónico (cambia design CONTRACT) → STOP, escalate PM.
    - Si finding == NO-NEW-LAYER violation → STOP, escalate PM.
16. Quality gates locales re-run NATIVE.
17. Stage por nombre + conventional commit `fix(brand|infra): address auditor findings iter-{N}` + push.
18. Re-spawn gate-runner Haiku → produce gate-output.iter-{N}.json (preserva el anterior).
19. Re-spawn auditor Opus. Iter ++.
20. Si iter == 3 y verdict aún ≠ PASS → STOP. Append IMPL-LOG "Max iterations reached, escalate PM". Última línea:
    <!-- @pm: implementación done, auditoría WARN/FAIL tras 3 iter. Findings pendientes: {lista}. Escalate /pm "PR-1 fix-loop maxed" -->

Outputs:
- Code + tests + (posible docker-compose fix) en codebase (committed + pushed)
- IMPL-LOG.md completo (Skills consulted, EXTEND-vs-NEW decision si aplica, Auto-fix iterations si entró Phase 3)
- gate-output.json final (Haiku) + gate-output.iter-N.json preserved si hubo iteraciones
- REVIEW.md final (output último auditor run)
- Commits conventional: fix(brand): ..., fix(infra): ..., test(brand): ..., fix(brand): address auditor findings iter-N

Reportar a Chris brief < 300 palabras: qué se implementó + tests verdes + iteraciones gate-runner + iteraciones audit + verdict final + bloqueadores escalados a PM (si los hay) + estado litellm container post-fix.

[BLOQUE VARIABLE — específico de este PR]

Surface a implementar: business (módulo brand) + infra (docker-compose / litellm config) — según CONTRACT § 0 scope decision
PR folder: docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery
Modules touched: brand
Iter actual: {1 si primera invocación; 2-3 si fix-loop}

Smoke verify post-fix (Chris-mediated, NO builder):
1. `docker compose ps visionarias_litellm` → Status: Up healthy
2. `curl -s http://localhost:4000/health` → 200 OK
3. Chris manda "hola" desde Telegram al @visionarias_bot
4. Esperar respuesta voice-tenant Visionarias
5. Query: `SELECT status, error_type FROM sales_agent_trace_event WHERE conversation_id IN (SELECT id FROM sales_agent_conversations WHERE lead_id='cb711aea-e0a5-42c0-b276-7a63570207bd' ORDER BY created_at DESC LIMIT 1) AND event_type='turn_end';` → status='ok'
6. Query: `SELECT cost_usd FROM sales_agent_llm_call WHERE tenant_id='6347e21e-8112-4aa1-80d3-6adaa73bf6f9' ORDER BY created_at DESC LIMIT 1;` → cost_usd > 0
```

## Cómo usar

1. Spawn vía Agent tool con `model: "sonnet"`.
2. Builder maneja todo el loop end-to-end — Chris no interviene salvo escalation.
3. Si Sonnet builder paused → SendMessage con agentId previo. Sonnet OK re-spawn fresh.
