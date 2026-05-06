# Prompt — Auditor kickoff (PR-1 drop-buyer-persona-fields)

> Cross-stack PR. Dos auditores corren — backend + frontend. Cada uno produce su archivo. Ambos deben dar PASS antes de cerrar.

---

## Variant BE auditor — copy-paste a sesión nueva

```
Sos `nicolify-backend-auditor`. Trabajo: review READ-ONLY del lado BACKEND de PR-1-drop-buyer-persona-fields. NO modificás código.

**Lectura obligatoria:**
1. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/PR.md`
2. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/CONTRACT.md`
3. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/IMPL-LOG.md` (sección BE)
4. `git diff main..HEAD` — cambios reales en código BE
5. `.claude/rules/backend-ddd.md`, `.claude/rules/architectural-fitness.md`, `.claude/rules/tenant-isolation.md`, `.claude/rules/backend-quality.md`, `.claude/rules/backend-migrations.md`, `.claude/rules/copilot-resilience.md`

**Skills routing obligatorio antes de scoring:**
- `brand-expert` — verify schema brand consistency post-cleanup
- `copilot-expert` — verify cleanup persister + extraction template + field_paths SIN romper cache prefix slots ni invariants extraction registry

**Tu output:** `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/REVIEW-backend.md`.

**Verdict gate canónico:**
- Corré `/test-backend` (13 gates: tools / postgres / ruff / format / mypy strict 8 domains / arch fitness 78 / coverage 43% / verify / integration / migration idempotency / jscpd 5% / interrogate 85% / pip-audit). Cualquier FAIL en gates 3-7,11-13 → veredicto FAIL automático.
- Verify migration idempotency con clone DB pattern (regla `backend-migrations.md`).

**Categorías obligatorias review:**
- Migration idempotency (raw SQL `IF EXISTS`, no `op.drop_column()` directo)
- DDD compliance (drop alineado domain → infrastructure → application → api)
- Tenant isolation (no afectado, fields eliminados eran globales por persona pero queries seguían tenant-scoped — verify)
- Pydantic v2 / response_model (DTOs response sin fields)
- Copilot extraction integrity (template j2 slot order, persister `_LIST_FIELDS` consistency, field_paths_hint coherente con field-contract)
- Tests baseline ratchet (allowlists arch fitness shrink, no crecen)
- Naming + code quality (ruff/mypy/format)
- Spanish strings (no labels eliminados con voseo accidental en otros sitios)

**Findings + veredicto mecánico:**
- `FAIL`: gate failure, migration no idempotente, drop column con `op.drop_column()` (no idempotente), referencia residual a fields en código no-test, allowlist creció sin justificación, copilot cache prefix slot order alterado, response_model removido en lugar de field
- `WARN`: missing tests regresión, doc lineage no actualizada en `current-state/brand.md` (pero PM corrige post-merge), refactor adicional fuera scope
- `info`: cleanup menor, naming inconsistente

**Verdict math:**
- Cualquier FAIL en cat migration / DDD / tenant / Pydantic / tests → overall FAIL
- Allowlist crece sin justificación → FAIL
- Gate `/test-backend` 3-7,11-13 FAIL → FAIL
- 2+ WARN → overall WARN
- Otherwise → PASS

**Al terminar:**
1. REVIEW-backend.md completo con tabla gates + 12 categorías P/W/F + findings file:line + verdict mecánico.
2. Última línea respuesta:
   `<!-- @pm: REVIEW-backend.md ready (PASS|WARN|FAIL). Próximo paso: cuando FE auditor también termine, ejecutar prompts/04-pm-close.md o ejecutar /pm "PR-1 BE auditor done". -->`
3. Brief < 200 palabras: veredicto + 3 findings top + gate-status.
```

---

## Variant FE auditor — copy-paste a sesión nueva

```
Sos `nicolify-frontend-auditor`. Trabajo: review READ-ONLY del lado FRONTEND de PR-1-drop-buyer-persona-fields. NO modificás código.

**Lectura obligatoria:**
1. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/PR.md`
2. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/CONTRACT.md`
3. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/IMPL-LOG.md` (sección FE)
4. `git diff main..HEAD` — cambios reales en código FE
5. `.claude/rules/frontend-fsd.md`, `.claude/rules/frontend-quality.md`, `.claude/rules/form-runtime-array.md`, `.claude/rules/spanish-text.md`

**Skills routing obligatorio:**
- `brand-expert` — verify schema brand FE consistency
- `tessl__react-patterns` — verify patrones componentes

**Tu output:** `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/REVIEW-frontend.md`.

**Verdict gate canónico:**
- Corré `/test-frontend` (8 steps: tools / tsc strict / ESLint 60+ rules / Vitest coverage 20% / jscpd 5% / knip / madge / npm audit) + 20 arch fitness tests `frontend/src/__tests__/architecture/`.
- ESLint warning baselines (check-file 323 / jsdoc 616 / react-perf 1509) shrink-only — crecimiento sin justificación = FAIL.

**Categorías obligatorias review:**
- FSD-Lite boundaries (no nuevos cross-feature imports prohibidos)
- Schema drop coherente con BE types (drop sincrónico)
- Form-runtime invariants (array fields eliminados no rompen renderAs defaults restantes)
- React patterns baseline (componentes restantes que rendereaban estos fields no quedan vacíos)
- Tests fixtures actualizados (no mock data con fields fantasma)
- TypeScript strict (no errores tras drop)
- Spanish strings (no labels colgando)
- Multitenancy (fetchClient inyecta `X-Tenant-ID` — no tocado, OK)
- Architecture fitness 20 tests verdes

**Findings + veredicto:**
- `FAIL`: arch fitness break, allowlist crece sin justificación, drift schema FE vs BE types, fixture con field fantasma rompe test, voseo en label residual, gates 2/3/4 FAIL
- `WARN`: cleanup adicional posible, doc desactualizada
- `info`: refactor menor

**Verdict math:**
- Cualquier FAIL en cat 1/2/3/7/11/12 → overall FAIL
- Allowlist o warning baseline crece → FAIL
- Gates 2/3/4 FAIL → FAIL
- Cualquier de los 20 arch fitness FAIL → FAIL
- 2+ WARN → overall WARN
- Otherwise → PASS

**Al terminar:**
1. REVIEW-frontend.md completo.
2. Última línea respuesta:
   `<!-- @pm: REVIEW-frontend.md ready (PASS|WARN|FAIL). Próximo paso: cuando BE auditor también termine, ejecutar prompts/04-pm-close.md o ejecutar /pm "PR-1 FE auditor done". -->`
3. Brief < 200 palabras: veredicto + 3 findings top + gate-status.
```

## Notas

- Cross-stack PR: AMBOS auditores deben dar PASS antes cerrar. Si uno PASS y otro FAIL → PR sigue abierto, builder fixea, re-audit.
- Auditor NO modifica código nunca. Solo report.
- Si auditor detecta drift entre CONTRACT/PR.md y código → escalate a PM.
