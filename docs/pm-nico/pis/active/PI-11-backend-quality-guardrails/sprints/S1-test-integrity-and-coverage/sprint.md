# Sprint S1 — Test Integrity Hardening + Anti-Default-Flip + Coverage P0

> Sprint ID: S1-test-integrity-and-coverage
> PI padre: PI-11-backend-quality-guardrails
> Estado: **ready (3 PRs builders pendientes)**
> Owner PM: /pm
> Expanded: 2026-05-04 post-failed-pase-prod

## Objetivo

Restaurar CI backend permanentemente + prevenir recurrencia raíz (default flip side-effect call path change). 0 tests fallidos sin band-aid + regla anti-default-flip cementada en agents/skills/rules + cobertura P0 ≥75%.

## Pre-handoff

- N/A (primer sprint del PI). Origen: failed `/pase-produccion` 2026-05-04 detalle en PI.md.

## Plan PRs

| PR | Folder | Descripción | Agentes/skills | Esfuerzo | Estado |
|---|---|---|---|---|---|
| PR-1 ext | `prs/PR-1-fix-broken-tests-and-arch-snapshots/` | Apply stash 16 archivos + polluter hunt sistemático sin band-aid + singleton fixture exhaustivo conftest + EventBus mocks audit + snapshot helpers outbox-aware + bug fix litellm.py kimi clamp + deprecation runtime warning LegacyEventBus | architect Opus (1 ejecución cubre PR-1+PR-3) → `nicolify-backend` (business) + `nicolify-agentic` (agentic) **paralelos** → auditores cruzados (`nicolify-backend-auditor` + `nicolify-agentic-auditor`) | XL | ready |
| **PR-3 NEW** | `prs/PR-3-anti-default-flip-enforcement/` | Rule `.claude/rules/anti-default-flip-audit.md` + arch fitness `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` | architect Opus (compartido con PR-1) → `nicolify-backend` → `nicolify-backend-auditor` | M | ready |
| **PR-4 NEW** | `prs/PR-4-update-agents-skills-default-flip-audit/` | Updates `nicolify-architect`/`nicolify-backend`/`nicolify-backend-auditor` agent prompts + `pm` SKILL.md template + `tdd-mandatory.md` | **PM directo** (no builder técnico — markdown meta-process) | M | ready |
| PR-2 | `prs/PR-2-coverage-p0-modules/` | Cobertura ≥75% en `crm` y `scheduling` (servicios + repos + DTOs sin test) | `nicolify-backend` → `nicolify-backend-auditor` | L | not-started (después PR-1+3 shipped) |

Detalle de cada PR vive en `prs/PR-*/PR.md`.

## Orden ejecución

1. **PM edits** (este turno) — todos los artifacts ready
2. Bootstrap PR-1 + PR-3 con `nicolify-context-builder` Haiku (paralelo) → CONTEXT-BRIEF.md cada PR
3. **Architect Opus 1 ejecución** — produce CONTRACT.md PR-1 + CONTRACT.md PR-3 (acoplados técnicamente; design singleton fixture + arch fitness test que reflexiona sobre ese fixture)
4. **Builders paralelos PR-1 + PR-3** (regla M1 paths exclusivos):
   - PR-1 business: `nicolify-backend` (Sonnet) → `nicolify-backend-auditor` (Opus)
   - PR-1 agentic: `nicolify-agentic` (Opus) → `nicolify-agentic-auditor` (Opus)
   - PR-3: `nicolify-backend` (Sonnet) → `nicolify-backend-auditor` (Opus)
5. **PM ejecuta PR-4 directo** (markdown edits agents/skills/rules — no builder técnico)
6. PR-1 + PR-3 + PR-4 shipped → PR-2 builder (coverage P0)
7. PI-11 cierre + retro
8. Re-merge `development → main` clean + `/pase-produccion`

## Stash apply timing

`git stash@{0}` (label "WIP PI-11 PR-1 partial — 16 tests/source fixes from paused pase-produccion 2026-05-04") **se aplica en builder PR-1 Phase 1 (Step 1)**, no antes. Builder revisa cada archivo del stash y commitea como parte de PR-1.

Razón: pop antes de tener PR.md/prompts ready genera conflict workflow paralelo + sin contexto de fixture exhaustivo. Builder Phase 1 = momento correcto.

## Criterio éxito sprint

- [ ] `pytest` pasa 100% (0 failed, 0 deselected obligatorios, 0 `@pytest.mark.flaky` permanentes)
- [ ] Arch fitness 78/78 + 1 nuevo (test_no_legacy_eventbus_mock_when_outbox_on) verde
- [ ] Polluter snapshot test fixed at source (no band-aid)
- [ ] Singleton fixture exhaustivo cubre TODOS class-level singletons identificados via grep `_instance =`
- [ ] Tests legacy `EventBus.publish` mocks: 100% migrados a `adapter_bus` o outbox table probe
- [ ] `_chat_flow_snapshot_helpers.py` outbox-aware (captura real)
- [ ] `LegacyEventBus.publish` runtime warning emitted
- [ ] Cobertura `crm` ≥75%, `scheduling` ≥75% (PR-2)
- [ ] `.claude/rules/anti-default-flip-audit.md` existe + arch fitness test enforza
- [ ] Agents `nicolify-architect`/`nicolify-backend`/`nicolify-backend-auditor` actualizados con default-flip audit (PR-4)
- [ ] `pm` SKILL.md template incluye bloque "Default flips audited" (PR-4)
- [ ] `tdd-mandatory.md` extendido con sección "Default flag flips" (PR-4)
- [ ] Todos los PRs tienen `RESULT.md`
- [ ] `/test-backend` + `/test-frontend` verde end-to-end nativos WSL

## Out of scope

| Item | Razón | Sprint destino |
|---|---|---|
| Cobertura `sales_agent`/`copilot` ≥80% | Scope limitado a P0 primero | S2 |
| Cobertura `shared/links/ports` | Transversal, mejor en batch S2 | S2 |
| Tests integración con DB real (verify/integration markers) | Requieren Postgres up; gate separado existente | No programado |
| Eliminación final `LegacyEventBus.publish` capability | Deprecation gradual; ahora solo runtime warning + tests migration | post PI-12 si decide |

## Riesgos

| Riesgo | Mitigación | Owner |
|---|---|---|
| Builders paralelos tocan mismo archivo (`tests/conftest.py`) | Builder business owns conftest.py (singleton fixture). Builder agentic NO toca conftest. PR-3 builder lee conftest pero NO lo modifica (solo arch fitness test new file) | PM |
| PR-1 business + agentic tocan ambos `tests/architecture/` | Asignar archivos exclusivos: business owns `test_ddd_boundaries.py` + `test_folder_naming.py`; agentic owns `test_sales_agent_anchors.py` + `test_sales_agent_system_prompt_order.py` | PM |
| Polluter hunt no resuelve en presupuesto Opus | Sin budget cap explícito (decisión Chris 2026-05-04 "lo más robusto cueste lo que cueste"); si supera 6h Opus → PM escalate Chris budget extra. **NO ship con band-aid permanente** | PM |
| Singleton fixture incompleto | Grep `_instance =` cross-codebase obligatorio en IMPL-LOG; lista exhaustiva validada por architect CONTRACT § Singleton inventory; auditor Cat review verifica | builder + auditor |
| Architect 1-ejecución produce CONTRACT inconsistente PR-1 vs PR-3 | Architect produce CONTRACT.md PR-1 (singleton fixture design + EventBus migration strategy) + CONTRACT.md PR-3 (arch fitness test referencia singleton fixture). Cross-link explícito entre ambos | architect |

## Cierre

Al cerrar:
1. Llenar `learnings.md`
2. Llenar `handoff.md`
3. Marcar sprint `done`
4. Verificar `RESULT.md` de PR-1, PR-2, PR-3, PR-4
