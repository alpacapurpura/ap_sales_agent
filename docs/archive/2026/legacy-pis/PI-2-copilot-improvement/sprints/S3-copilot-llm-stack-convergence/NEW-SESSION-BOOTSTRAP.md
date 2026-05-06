# NEW-SESSION-BOOTSTRAP — S3+S4+S5 PI-2 LLM Stack Convergencia

> **Owner:** PM main thread / sesión nueva. Origen: sesión 2026-04-30 detectó audit failure PR-3 (capa LLM duplicada) + creó este plan completo + procedió cero deuda hasta nueva conversación.
>
> **Misión nueva conversación:** ejecutar 6 PRs (S3 + S4 + S5) hasta cero deuda técnica + arquitectura escalable 1000+ tenants. NO step-by-step approvals — decisión técnica autónoma.

## Bootstrap obligatorio (orden literal)

Pegá en nueva conversación literal:

```
/pm

# MISIÓN — Ejecutar S3+S4+S5 PI-2-copilot-improvement autónomo end-to-end

Sos PM + main thread orchestrator de Nicolify. Vas a ejecutar 3 sprints encadenados (6 PRs total) hasta dejar PI-2 con cero deuda técnica + arquitectura LLM escalable 1000+ tenants. UNA conversación, sin pedir aprobación entre fases salvo bloqueador físico real.

## Lectura obligatoria PRIMERO (orden literal)

1. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S3-copilot-llm-stack-convergence/NEW-SESSION-BOOTSTRAP.md` (este archivo — instrucciones completas)
2. `docs/domains/llm-routing.md` (SSoT explicit)
3. `docs/pm-nico/research/2026-04-30-llm-config-storage-best-practices.md` (patrón hybrid 3-capa research)
4. `docs/pm-nico/research/2026-04-30-llm-landscape-chinese-models.md` (DeepSeek V4-Flash 4-15x cheaper)
5. `docs/pm-nico/pis/active/PI-2-copilot-improvement/PI.md` (PI status + plan S3+S4+S5)
6. `docs/pm-nico/pis/active/PI-2-copilot-improvement/decisions.md` (entrada 2026-04-30 audit failure)
7. `docs/pm-nico/process/process-learnings.md` (entrada 2026-04-30 L-PROC-CROSS-MODULE-AUDIT + 4 lessons)
8. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S3-copilot-llm-stack-convergence/sprint.md`
9. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S3-copilot-llm-stack-convergence/prs/PR-1-cleanup-modeltier-convergence/PR.md`
10. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S3-copilot-llm-stack-convergence/prs/PR-2-litellm-proxy-integration/PR.md`
11. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S4-copilot-model-registry-runtime/sprint.md`
12. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S4-copilot-model-registry-runtime/prs/PR-1-db-registry-admin-ui/PR.md`
13. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S4-copilot-model-registry-runtime/prs/PR-2-growthbook-per-tenant-override/PR.md`
14. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S5-copilot-eval-gate-pre-promote/sprint.md`
15. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S5-copilot-eval-gate-pre-promote/prs/PR-1-eval-gate-admin-wiring/PR.md`
16. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S5-copilot-eval-gate-pre-promote/prs/PR-2-deprecate-legacy-modeltier-final/PR.md`
17. `CLAUDE.md` (Git Workflow INVIOLABLE)
18. `.claude/rules/parallel-safety.md` (M1-M8 rules)

## Criterio decisional AUTORITATIVO (vos decidís 100%)

Orden prioridad:
1. **Escalabilidad** 1000+ tenants sin refactor (Chris: "tenemos pocos clientes hoy, dejaré costos y pérdidas futuras")
2. **Performance** latencia <200ms p99 hot paths
3. **Costo LLM** optimizado (DeepSeek V4-Flash 4-15x cheaper NANO+FAST validado research)
4. **CERO deuda técnica** (Chris explicit: "toda deuda técnica que deje hoy será costos y pérdidas futuras")
5. **Calidad invariantes** (DDD, tenant isolation, response_model, observability best-effort, ratchet copilot→módulo frozen)

## Reglas paralelas INVIOLABLES (otra sesión Claude posiblemente activa)

- PROHIBIDO `git pull`, `git push --force`, `git push -f`, `--force-with-lease`
- PROHIBIDO branches/worktrees/release/hotfix/checkout fuera development
- PROHIBIDO `git revert <hash>` sin aprobación Chris explícita
- PROHIBIDO `git reset --hard` sin aprobación
- PROHIBIDO `git add .` / `git add -A` / `git add -u` (stage por nombre)
- PROHIBIDO `git commit --no-verify`
- Push falla non-fast-forward → STOP, reportar Chris (NO `git pull` para resolver)
- Regla M8: tocar archivos ajenos OK si entendés + extend (no replace)

## Workflow plan (autónomo, ejecutar sin pedir aprobación)

### Phase 0 — Bootstrap + git pre-flight

1. `git status --short && git branch --show-current && git log --oneline -10`
2. Verificar development limpio. Si tree sucio archivos AJENOS → reportar lista, dejar intactos, proceder.
3. Read los 18 archivos listados arriba.

### Phase 1 — Ejecutar S3 (cleanup + LiteLLM)

**S3 PR-1: cleanup-modeltier-convergence** (M-L, ~15 archivos)

1. PM claim `PR-1` Estado: in-progress + commit + push (M4 claim by commit).
2. Spawn `nicolify-architect` con prompt que incluye:
   - Lectura obligatoria PR.md + CONTRACT template + sprint.md + docs/domains/llm-routing.md
   - Skills `copilot-expert` + `sales-agent-expert` (verify NO touch §3)
   - Criterio decisional autoritativo
   - **Sección "Existing systems audit" obligatoria** (audit grep matrix per nuevo CONTRACT template)
   - Restricción NO TOCAR sales_agent (rule sales-agent-brand-voice)
   - Output CONTRACT.md path
   - Última línea EXACTA: `<!-- @pm: CONTRACT.md ready (architect-empowered). -->`
3. Commit + push CONTRACT.
4. Spawn `nicolify-backend` builder con prompt que incluye workflow Phase 1 (TDD strict + IMPL-LOG + commit + push) + Phase 2 (auto-spawn nicolify-backend-auditor) + Phase 3 (auto-fix loop max 3 iter).
5. **Si builder truncate** (probable per L-PROC main thread takeover S2 cementado): PM main thread completa quality gates + REVIEW.md + commits restantes. NO re-spawn parcial.
6. PM cierra PR-1: RESULT.md + lineage current-state/copilot.md + decisions.md + sprint learnings.md + Estado: shipped + commit + push.

**S3 PR-2: litellm-proxy-integration** (M, ~10 archivos)

Mismo workflow PR-1. Architect → builder con auto-loop. Cierre PR.

**Cierre sprint S3:**
- learnings.md + handoff.md
- sprint.md Estado: done
- Update PI.md + roadmap.md

### Phase 2 — Ejecutar S4 (DB registry + GrowthBook)

**S4 PR-1: db-registry-admin-ui** (L, ~12-15 archivos)

Workflow standard. Verificar admin Streamlit page rule + tabla `llm_role_binding` migration idempotente.

**S4 PR-2: growthbook-per-tenant-override** (M, ~10 archivos)

Workflow standard. Docker compose svc visionarias_growthbook + integration GrowthBook SDK Python.

**Cierre sprint S4:** learnings + handoff + Estado done + PI/roadmap updates.

### Phase 3 — Ejecutar S5 (eval gate + cleanup final)

**S5 PR-1: eval-gate-admin-wiring** (M-L, ~12 archivos)

Workflow standard. CI integration GitHub Actions workflow.

**S5 PR-2: deprecate-legacy-modeltier-final** (S, ~5 archivos)

Workflow standard. Audit final cero residual + PI-2 retro + archive.

### Phase 4 — Cierre PI-2 + reporte final

1. Escribir `docs/pm-nico/pis/active/PI-2-copilot-improvement/retro.md` (5 sprints, ~15 PRs total, learnings consolidados).
2. Mover folder a `docs/pm-nico/pis/archive/PI-2-copilot-improvement/`.
3. Update `docs/pm-nico/roadmap.md`: PI-2 Now → Done section.
4. Update `docs/domains/llm-routing.md` sección "Migration timeline" — PI-2 closed.
5. Reporte final a Chris (<500 palabras): outcomes + costos pre/post + escalabilidad validada + deuda residual cero.

## Estado de partida verificable

```bash
# Verificá antes ejecutar (debe estar todo verde):
cd /home/chris/AISALESHT && git log --oneline -5
# Esperado: últimos commits de sesión 2026-04-30 (Bloque A + B + C process prevention + sprints S3+S4+S5 ready)

ls docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/
# Esperado: S1-... S2-... S3-copilot-llm-stack-convergence S4-copilot-model-registry-runtime S5-copilot-eval-gate-pre-promote

cat docs/domains/llm-routing.md | head -10
# Esperado: doc SSoT existe

cd backend && .venv/bin/pytest tests/architecture/test_llm_routing_ssot.py -v
# Esperado: 3/3 verde (allowlist KNOWN_LEGACY_LLM_FILES con ~19 entries iniciales)
```

## Anti-patrones que NO debes seguir (replicados desde misión original)

- ❌ Preguntar a Chris entre fases salvo bloqueador físico real
- ❌ Pragmatic shortcuts que generen deuda futura — Chris explícito CERO DEUDA
- ❌ Saltar audit cross-module en architect (regla NO NEW LAYER ya enforced en CONTRACT/PR template + skill)
- ❌ git pull / git push --force / git revert sin aprobación
- ❌ Spawn auditor manual yo (lo hace builder en auto-loop)
- ❌ Skip tests TDD para acelerar (RED→GREEN obligatorio)
- ❌ Tocar archivos sesión paralela (regla M8: extend OK, replace NO)
- ❌ Cerrar conversación sin S5 PR-2 shipped + PI-2 archive

## Si bloqueás (escalate Chris)

Solo escala si:
1. Decisión técnica requiere data que solo Chris tiene (DB credentials, business preference fuera criterio listado)
2. Conflicto cross-PR S3+S4+S5 vs sesión paralela activa que rompe el otro work
3. Iter 3 builder fix-loop sin PASS y findings tocan arquitectónico fuera scope
4. Push non-fast-forward (NO git pull — reportar y Chris coordina)

## Inicio

Empezá con Phase 0 (git status + read state archivos listados). NO me confirmes plan, ejecutá todo hasta PI-2 shipped + archived.
```

## Estado entregado por sesión 2026-04-30 (este archivo)

| Bloque | Estado | Commits relevantes |
|---|---|---|
| A: Process prevention (CONTRACT/PR template + skill + docs/domains/llm-routing + arch fitness test guard + process-learnings) | ✅ shipped | `7ffd7650` |
| B: S3+S4+S5 sprint folders + 6 PR.md detailed skeletons | ✅ shipped | `1082d9bb` |
| C: PI-2 PI.md + roadmap + decisions update | ✅ shipped | `34023325` |
| D: NEW-SESSION-BOOTSTRAP.md (este archivo) | ✅ shipped | `cf2c822d` |
| **E: S3 PR-1 cleanup-modeltier-convergence shipped end-to-end** | ✅ **shipped 2026-04-30** | `6a3541c5` (claim) → `c9a8cae6` (CONTRACT) → `d079f13b` (refactor 14 archivos) → `773604ab` (deletes + migration 115 + tests + .env.example) → `d1f21725` (RESULT + lineage) |

## Estado verificable post-PR-1 (next session start)

```bash
# Allowlist target alcanzado
cd backend && .venv/bin/pytest tests/architecture/test_llm_routing_ssot.py -v
# 3/3 PASSED — KNOWN_LEGACY_LLM_FILES = set() (0 entries)

cd backend && grep -rn "ModelTier" src/modules/copilot/
# (cero hits)

cd backend && find src/modules/copilot/infrastructure/llm/
# find: 'src/modules/copilot/infrastructure/llm/': No such file or directory

cat .env.example | grep -E "^AI_(MODEL|PROVIDER)_(NANO|FAST)"
# AI_MODEL_NANO=deepseek-v4-flash
# AI_MODEL_FAST=deepseek-v4-flash
# AI_PROVIDER_NANO=deepseek
# AI_PROVIDER_FAST=deepseek
```

## Continuación PR-2..PR-6 (5 PRs remaining)

S3 PR-2 LiteLLM Proxy → **ready next session** (PR.md + sprint.md updated). Workflow standard: claim → spawn architect → CONTRACT.md commit → spawn builder con expectativa main thread takeover post-truncate → REVIEW + RESULT + close.

S4 PR-1+2 + S5 PR-1+2 = 4 PRs remaining después S3 PR-2. PR.md skeletons completos en sprint folders.

## Stack actual de partida (verificable hoy)

| Layer | Estado |
|---|---|
| `.env` actual | NANO=gpt-4o-mini (openai), FAST=gpt-4o-mini, REASONING=deepseek-reasoner (deepseek), AGENT=kimi-k2.6 (kimi/moonshot), VISION=gpt-4o, EMBEDDING=text-embedding-3-large |
| `Settings.get_model/get_provider_for_role` | ✅ Sistema A activo, multi-provider funcional |
| `shared/infrastructure/llm/router.py + providers/` | ✅ openai + kimi + _openai_compat (DeepSeek) live |
| `copilot/domain/model_tier.py + TIER_METADATA` | ⚠️ DEUDA legacy (decía gpt-5.4-nano hardcoded — desincronizado de .env real) |
| `copilot/infrastructure/llm/{model_config, provider_factory, providers/deepseek}` | ⚠️ DEUDA PR-3 capa duplicada (eliminar S3 PR-1) |
| `copilot/evals/` (golden_dataset + runner + scorers + 100 goldens) | ✅ Mantener (aporte real PR-3) |
| `alembic 114_pricing_deepseek_v4_flash` | ✅ Mantener (migration pricing útil) |
| `tests/architecture/test_llm_routing_ssot.py` | ✅ Shipped Bloque A (allowlist 19 entries actuales, shrinks per S3+S4+S5) |
| Pricing snapshots tabla | ✅ Existing rows + DeepSeek V4-Flash row pendiente migration aplicar Docker |

## Outcome esperado nueva conversación

Post S3+S4+S5 shipped:

| Métrica | Hoy | Post S3+S4+S5 |
|---|---|---|
| SSoT routing LLM | 2 sistemas (ModelTier + ModelRole) | 1 sistema (ModelRole + DB registry) |
| Cambio modelo | edit `.env` + redeploy | admin UI button + <60s sin deploy |
| Per-tenant override | NO | SI (GrowthBook flag) |
| A/B test modelo | NO | SI (GrowthBook bucketing %) |
| Kill-switch instant | NO (revert deploy) | SI (admin UI <30s MTTR) |
| Eval gate pre-promote | NO | SI (≥0.95 score obligatorio) |
| Cost reduction NANO+FAST | 0% | 4-15x (DeepSeek V4-Flash activado) |
| Deuda LLM routing residual | múltiples archivos legacy + capa duplicada PR-3 | 0 (allowlist arch fitness = 0 entries) |
| PI-2 estado | active | archived (retro.md escrito) |

Esto es escalable a 1000+ tenants. Stack ready cero deuda + hot-swap sin deploy + per-tenant + eval gate.
