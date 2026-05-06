# Prompt — Builder kickoff (PR-2)

> Builder: `nicolify-backend` (Sonnet)
> Surface: `crm`, `scheduling`

## Spawn pattern

```
Agent({
  description: "Build PR-2 backend",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos nicolify-backend (Sonnet). Trabajo: aumentar cobertura de tests en crm y scheduling a ≥75%.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Restricciones DURAS:
- Tocás SOLO tests/ y src/modules/crm/ + src/modules/scheduling/.
- NO tocás otros módulos.
- NO tocás archivos de otros PRs activos.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify.
- Push falla non-fast-forward → STOP, reportar.

Skills obligatorios:
- backend-expert
- pytest-api-testing (si disponible en skills)

Workflow Phase 1 — IMPLEMENT:
1. TDD strict: tests RED primero, luego verificar que pasan.
2. Escribir tests unitarios para servicios de aplicación sin cobertura:
   - crm: lead_query_service, nps_service, referral_service, ig_profile_enricher
   - scheduling: availability_service, event_type_service (gaps), public_links
3. Escribir tests de integración liviana (mock repo) para:
   - crm: lead_repository, lead_metrics_repository
   - scheduling: appointment_repository
4. Quality gates locales NATIVE:
   cd backend && .venv/bin/ruff check src/ tests/ --no-cache
   cd backend && .venv/bin/pytest tests/modules/crm/ tests/modules/scheduling/ --cov=src/modules/crm --cov=src/modules/scheduling --cov-report=term-missing -v --timeout=60
5. Verificar cobertura ≥75% para cada módulo.
6. Stage + conventional commit + push origin development.
7. IMPL-LOG.md completo.

Workflow Phase 2 — AUTO-AUDIT:
8. Spawn nicolify-gate-runner Haiku:
   Agent({ description: "Run gates iter-1", subagent_type: "nicolify-gate-runner", model: "haiku",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules; <command>: test-backend; <iter>: 1" })
9. Esperá gate-output.json. Si any_fail en gates 3-7,11-13 → fix, re-commit, re-spawn.
10. Spawn nicolify-backend-auditor Opus:
    Agent({ description: "Audit PR-2", subagent_type: "nicolify-backend-auditor", model: "opus",
      prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules; <surface>: business; <iter>: 1" })
11. Si verdict ≠ PASS → fix loop max 3 iter.

Outputs:
- Code + tests committed + pushed
- IMPL-LOG.md
- gate-output.json final
- REVIEW.md

Reportar a Chris brief < 300 palabras: qué se implementó, cobertura antes/después, tests nuevos count, verdict final.

[BLOQUE VARIABLE]

Módulos: crm, scheduling
Cobertura objetivo: crm ≥75%, scheduling ≥75%
Cobertura actual (baseline): crm 59.3%, scheduling 59.9%

Archivos sin cobertura (prioridad):
- src/modules/crm/application/services/lead_query_service.py (0%)
- src/modules/crm/application/services/nps_service.py (0%)
- src/modules/crm/application/services/referral_service.py (0%)
- src/modules/crm/infrastructure/repositories/lead_metrics_repository.py (15.8%)
- src/modules/crm/application/services/ig_profile_enricher.py (25.0%)
- src/modules/crm/infrastructure/repositories/lead_repository.py (36.6%)
- src/modules/scheduling/api/public_links.py (23.6%)
- src/modules/scheduling/application/services/availability_service.py (60.2%)

PR folder: docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules
Surface: business
Iter actual: 1
```
