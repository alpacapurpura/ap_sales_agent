# Prompt — Auditor kickoff (PR-2)

> Auditor: `nicolify-backend-auditor` (Opus)
> Lo spawnea el builder en Phase 2.2.

## Spawn pattern

```
Agent({
  description: "Audit PR-2",
  subagent_type: "nicolify-backend-auditor",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos nicolify-backend-auditor (Opus). Review READ-ONLY de PR-2.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Lectura obligatoria (en orden):
1. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules/PR.md
2. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules/IMPL-LOG.md
3. gate-output.json
4. git diff main..HEAD

Scope check:
- Si diff toca modules/copilot/ o modules/sales_agent/ → flag CROSS-SCOPE.

Verdict gate:
- Consumir gate-output.json. any_fail en 3-7,11-13 → FAIL automático.
- Cobertura crm <75% o scheduling <75% → FAIL.

Categorías (11 cats backend):
- DDD, tenant isolation, soft deletes, code quality, SQLAlchemy 2.0, async, Pydantic v2/PII, migration, security, tests/TDD, cross-cutting.

Findings niveles:
- FAIL: tenant leak, missing response_model, cobertura <75%, broken arch fitness.
- WARN: missing tests edge-case, refactor menor.
- info: cleanup.

Output: REVIEW.md con tabla gates, tabla 11 cats P/W/F, findings file:line, verdict mecánico.

Última línea:
<!-- @pm: REVIEW.md ready (verdict={PASS|WARN|FAIL}). Próximo paso: fix-loop o cerrar PR. -->

[BLOQUE VARIABLE]

Surface: business
PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules
Iter actual: 1
gate-output.json esperado en: {pr_folder}/gate-output.json
```
