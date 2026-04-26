# Prompt arranque FP1

Para iniciar FP1 en una conversación nueva de Claude Code, copiar el siguiente fenced block y pegar:

---

```
Iniciar FP1 plan fpos-2026-04 copilot. Caveman mode full activo (skill `caveman`).

## Misión FP1

Cerrar B22-TP11: ProposalCard "Aplicar" silent no-op cuando `activeBridge` no connected. Garantizar mutation persiste **siempre** — vía bridge si disponible, vía backend `/mutations/apply` endpoint si no — y UI feedback **honesto** (no verde "Aplicado" si nada persistió). Cross-stack FE+BE.

## Pre-lectura obligatoria (orden estricto)

1. `docs/domains/copilot/fpos-2026-04/README.md`
2. `docs/domains/copilot/fpos-2026-04/02-fpos-plan.md`
3. `docs/domains/copilot/fpos-2026-04/04-protocol.md`
4. `docs/domains/copilot/fpos-2026-04/phases/FP1-proposal-card-apply.md`
5. `docs/domains/copilot/testing-2026-04/results/TP11-2026-04-26.md` (origen B22)
6. `docs/domains/copilot/testing-2026-04/04-protocol.md` (protocolo padre)
7. `.claude/rules/copilot-resilience.md` + `.claude/rules/spanish-text.md` + `.claude/rules/backend-ddd.md` + `.claude/rules/frontend-fsd.md` + `.claude/rules/tenant-isolation.md` + `.claude/rules/backend-migrations.md`
8. `frontend/src/features/copilot/components/messages/ProposalCard.tsx` (source actual del bug)
9. `frontend/src/features/copilot/store/copilot-store.ts` (activeBridge logic)
10. `backend/src/modules/copilot/api/` (verificar si existe endpoint mutations apply)
11. `backend/src/modules/copilot/infrastructure/repositories/` (mutation_journal repository si existe)

## Pre-research obligatorio

Mínimo 2 web searches del Research mandate listado en `phases/FP1-proposal-card-apply.md §Research mandate`:
- `react form-runtime bridge pattern 2026 dispatcher subscriber`
- `FastAPI mutation endpoint idempotent apply pattern 2026`
- `optimistic UI rollback strategy 2026 mutation failure`

Tessl tiles: `tessl__fastapi`, `tessl__zod`.

## Setup heredado (NO rehacer — verificado en TP11)

- TP11 cerrado, B23-TP11 voseo system prompts fix vivo (commit `ed18daef`).
- Tenant test primario: visionarias-v4 `9ba0b29a-8507-424f-a48a-896f93218a25` (tenant_profile completo, brand_summary 0).
- Sprint 0 routing: AGENT=Kimi K2.6 (no-thinking, temp 0.6) + REASONING=DeepSeek + NANO/FAST=OpenAI.
- deepagents 0.5.3.
- Span tree B15-TP8 vivo + plan_card B18-TP9 vivo + ROUTE_TOOL_MAP B20-TP10 wired.

## Pre-reqs infra (verificar al arrancar)

```bash
git status --short
docker compose ps
.venv/bin/python -c "import deepagents; print(deepagents.__version__)"
.venv/bin/python scripts/get_clerk_test_token.py | head -c 30
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:3000
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs

# CRÍTICO FP1 — verificar endpoint mutations existe / no existe:
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/copilot/conversations/dummy-id/mutations/apply
# Esperado: 401 si endpoint existe (sin auth), 404 si no existe (must create).

# CRÍTICO FP1 — mutation_journal table existe:
docker exec visionarias_postgres psql -U postgres -d visionarias_logs -c "\d copilot_mutation_journal" 2>&1 | head -15
# Esperado: schema con id, tenant_id, conversation_id, message_id, domain, entity_id, field_path, old_value, new_value, applied_at, reverted_at.
```

## Acceptance criteria FP1 (de phase doc)

| AC | Descripción |
|---|---|
| AC1 | Click "Aplicar" con bridge connected → bridge.patchField calls + autosave |
| AC2 | Click "Aplicar" sin bridge → fallback POST `/mutations/apply` → row insertada en `copilot_mutation_journal` |
| AC3 | Mutation falla → UI status `failed` (no verde) + mensaje explícito |
| AC4 | Event `proposal_accepted` con `mutation_id` (no solo field_count) |
| AC5 | Idempotency: 2 clicks no duplican rows |
| AC6 | Reload page post-apply → form fields populated end-to-end |

## Anomalías heredadas

### A2.1 (TP9, PARCIAL fix B23-TP11) — voseo en remaining 9 prompts
NO bloquea FP1. FP4 paraleliza si Chris quiere.

### B22 — el bug que cerramos en FP1.

### Heredados sin manifestación esperada en FP1
A1, A3, A4, A5, A6, TP4-B5/B6, TP5-B9/B10, TP6-B11, B12-TP7, B16-TP8, B19-TP9. NO bloquean FP1.

## Reglas non-negotiables

1. Acceptance criteria mandatorio. Sin AC cumplido + before/after evidence, FP NO se cierra.
2. TDD obligatorio: test RED → fix → test GREEN → live verification.
3. Root cause obligatorio. NO `# noqa`, NO `pytest.skip`, NO mock-tape-error.
4. Cross-stack: tocar FE + BE coherente. Schema parity BE↔FE arch test si aplica.
5. Spanish neutro LatAm en cualquier user-facing tocado (regla 11).
6. Native dev tools — lint/tests WSL nativo, NUNCA `docker exec` para lint/tests/type-check.
7. Docker SOLO para runtime + recreate.
8. Stage por nombre en commits (parallel-safety).
9. Idempotent migrations (regla `backend-migrations.md`).
10. Tenant isolation (regla `tenant-isolation.md`) en cualquier nuevo endpoint.
11. PII sanitization — todo endpoint con `response_model=` (Tessl rule).

## Aprendizajes accionables de TP11

- **TDD inline en TP / FP UX live SÍ funciona.** B23-TP11 demostró ciclo completo en 25 min. FP1 puede aplicar mismo: detect bug → test RED → fix → restart api_dev → re-run J1 live.
- **CHECK form-runtime bridge state ANTES de declarar UX flow OK.** B22 = bridge no connected = silent fail. AC2 fallback es defensa principal.
- **Phase doc tenant assumptions outdated rápido.** alpaca-2 redirige a onboarding (tenant_profile vacío). Usar visionarias-v4 con tenant_profile completo + brand_summary 0 — fit natural setup brand scenario.

## Output esperado al cerrar FP1

1. `docs/domains/copilot/fpos-2026-04/results/FP1-{YYYY-MM-DD}.md` con:
   - Pre-research insights
   - AC1-AC6 checklist con before/after evidence (mutation_journal SQL probe + DOM screenshots / network requests)
   - Tests added (count + paths)
   - Sub-bugs descubiertos (si los hubo)
   - Métricas: latency apply endpoint + FE bundle delta
   - **§Aprendizajes para FP2** (1-3 bullets)
   - **§Handoff FP2** referencia a `prompts/FP2-start.md`

2. Si `phases/FP1-proposal-card-apply.md` cambió → commit incluido.

3. **Generar `prompts/FP2-start.md`** (template canónico §Anexo A del `04-protocol.md`).

4. Commits conventional + push origin/development:
   - Backend: `feat(copilot-fpos1): mutations apply endpoint + idempotent journal upsert (B22)`
   - Frontend: `fix(copilot-fpos1): ProposalCard fallback + honest UI feedback (B22)`
   - Tests + arch + docs en su commit propio si crece mucho

5. Reporte al user: 3 líneas resumen + score H6/H8 mejora + paths a results/.

## Anti-patrones (no caer)

- Reportar AC sin evidence concreta (sin SQL probe / sin trace event / sin screenshot).
- Mockear endpoint mutations + skip live integration test.
- Cerrar FP1 con sub-bug abierto sin TDD.
- Spawnear sub-agentes para AC paralelos (FP necesita context completo + fix iteration).
- Skip cross-stack schema parity check (BE shape vs FE TypeScript types).
- Llenar reporte con info no accionable.

## Si te trabás

- Bridge logic confuso → lee `frontend/src/features/copilot/store/copilot-store.ts` + busca dónde se setea `activeBridge`.
- Endpoint mutations apply NO existe → crear bajo `backend/src/modules/copilot/api/mutations.py` siguiendo DDD inside-out.
- Tenant isolation → `tenant_id` desde `X-Tenant-ID` header middleware.
- Mutation journal idempotency → unique constraint via Alembic migration idempotente (raw SQL `ALTER TABLE ADD CONSTRAINT IF NOT EXISTS`).
- Live re-run J1 → tenant visionarias-v4 + clean conversation + setup brand prompt + click Aplicar + SQL probe.

---

**Primera tarea:** pre-lectura paso 1 + pre-research paso 2. Recién después tocás tools.
```
