# Prompt — Auditor kickoff (PR-1 business surface)

> Auditor: `nicolify-backend-auditor` (Opus)
> Lo spawnea el business builder en Phase 2.2.

## Spawn pattern

```
Agent({
  description: "Audit PR-1 business",
  subagent_type: "nicolify-backend-auditor",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos nicolify-backend-auditor (Opus). Review READ-ONLY de PR-1 business surface.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Lectura obligatoria (en orden):
1. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots/PR.md
2. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots/IMPL-LOG.md
3. gate-output.json (del gate-runner Haiku)
4. git diff main..HEAD — cambios reales

Scope check:
- Si diff toca modules/copilot/ o modules/sales_agent/ → flag CROSS-SCOPE, NO scorear esos files.

Verdict gate:
- Consumir gate-output.json (13 gates BE). any_fail en 3-7,11-13 → FAIL automático.

Categorías (11 cats backend):
- DDD, tenant isolation, soft deletes, code quality, SQLAlchemy 2.0, async, Pydantic v2/PII, migration, security, tests/TDD, cross-cutting.

Findings niveles:
- FAIL: tenant leak, missing response_model, broken arch fitness, allowlist creció sin justificación.
- WARN: missing tests, refactor menor.
- info: cleanup.

Output: REVIEW-backend.md con tabla gates, tabla 11 cats P/W/F, findings file:line, verdict mecánico.

Última línea:
<!-- @pm: REVIEW-backend.md ready (verdict={PASS|WARN|FAIL}). Próximo paso: fix-loop iter-N+1 o cerrar PR. -->

[BLOQUE VARIABLE]

Surface: business
PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots
Iter actual: 1
gate-output.json esperado en: {pr_folder}/gate-output.json
```
