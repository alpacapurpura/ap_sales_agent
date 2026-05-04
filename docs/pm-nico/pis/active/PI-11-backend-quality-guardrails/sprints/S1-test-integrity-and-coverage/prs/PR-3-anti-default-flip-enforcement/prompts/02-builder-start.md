# Prompt — Builder kickoff (PR-3)

> Builder: `nicolify-backend` (Sonnet)
> Surface: `.claude/rules/`, `tests/architecture/`, `CLAUDE.md`
> Dependency: PR-1 EventBus migration debe estar completa antes que arch fitness test active sin violations baseline.

## Spawn pattern

```
Agent({
  description: "Build PR-3 anti-default-flip enforcement",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <BLOQUE FIJO + BLOQUE VARIABLE abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos `nicolify-backend` (Sonnet). Trabajo: implementar PR-3 anti-default-flip enforcement (rule + arch fitness test + CLAUDE.md update).

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Lectura obligatoria:
1. {pr_folder}/CONTEXT-BRIEF.md
2. {pr_folder}/CONTRACT.md
3. {pr_folder}/PR.md
4. PI-11/PI.md § Decisión arquitectónica clave (D1-D7)
5. .claude/rules/anti-duplication.md (estructura inspiración)
6. backend/tests/architecture/ (patrón existing arch fitness)
7. CLAUDE.md (conditional rules section)

Skills obligatorios:
- backend-expert
- tessl__pytest-api-testing (AST walk patterns)

Restricciones DURAS:
- Tocás SOLO: `.claude/rules/anti-default-flip-audit.md` (NEW), `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` (NEW), CLAUDE.md (conditional rules table append).
- NO tocás source modules (no es scope PR-3).
- NO tocás otros tests (no es scope).
- NO tocás archivos PR-1 ni PR-4.
- PROHIBIDO: git pull, fetch+merge, push --force, revert, reset --hard, add . / -A / -u, commit --no-verify.

Workflow Phase 1 — IMPLEMENT:

Step 1 — Crear `.claude/rules/anti-default-flip-audit.md` siguiendo CONTRACT § 1.
Step 2 — Crear `backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` siguiendo CONTRACT § 2:
  - AST walk para detectar mock targets `LegacyEventBus.publish`, `EventBus.publish` (path legacy)
  - Bypass list (`BYPASS_FILES` + magic comment `# arch-bypass: testing legacy capability`)
  - Failure message linkea regla
  - Performance <2s
Step 3 — CLAUDE.md update: append entry a tabla "Conditional Rules":
  | Tocas | Skill | Stub |
  |---|---|---|
  | `core/config.py` defaults flag | `backend-expert` | `rules/anti-default-flip-audit.md` |
Step 4 — TDD: si arch fitness test rompe baseline (PR-1 incompleto), confirmar PR-1 status:
  - Si PR-1 NOT shipped → STOP, escalate PM (deadlock — PR-3 espera PR-1)
  - Si PR-1 shipped → arch fitness baseline 0 violations esperado
Step 5 — Quality gates locales NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/pytest tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py -v --override-ini="addopts="
   cd backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
Step 6 — IMPL-LOG.md sections:
  - Rule structure rationale (mirror anti-duplication)
  - Arch fitness AST walk implementation notes
  - Bypass mechanism design + tests
  - Performance measurement actual vs budget
  - Skills consulted
  - Quality gates output
Step 7 — STAGE + COMMIT + PUSH:
  git add .claude/rules/anti-default-flip-audit.md
  git commit -m "feat(rules): add anti-default-flip-audit rule (PI-11 PR-3)"
  git add backend/tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py
  git commit -m "test(arch): block tests mocking LegacyEventBus.publish when outbox flag default on"
  git add CLAUDE.md
  git commit -m "docs(claude-md): register anti-default-flip-audit conditional rule"
  git push origin development

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT:

Step 8 — Spawn gate-runner Haiku:
  Agent({ description: "Run /test-backend gates iter-1 PR-3", subagent_type: "nicolify-gate-runner", model: "haiku",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement; <command>: test-backend; <iter>: 1" })

Step 9 — Spawn auditor Opus:
  Agent({ description: "Audit PR-3 iter-1", subagent_type: "nicolify-backend-auditor", model: "opus",
    prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement; <surface>: business; <iter>: 1" })

Workflow Phase 3 — AUTO-FIX LOOP (max 3):
- Findings dentro scope → fix.
- Findings drift CONTRACT → STOP, escalate PM.
- Re-spawn gate-runner + auditor cada iter.

Outputs:
- Code (rule + arch fitness + CLAUDE.md update) committed + pushed
- IMPL-LOG.md
- gate-output.json
- REVIEW.md verdict PASS

Última línea verdict PASS:
<!-- @pm: implementación + gate-runner + auditoría done PR-3 (verdict PASS). Anti-default-flip enforcement cementado. /pm "PR-3 cerrar" -->

Reportar a Chris brief < 250 palabras: rule structure + arch fitness coverage + bypass mechanism + performance measurement + verdict.

[BLOQUE VARIABLE]

PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement
Surface: business + .claude/rules + tests/architecture
Iter actual: 1
Dependency: PR-1 EventBus migration MUST be complete (gate-runner verde) antes de Step 7 push final
```
