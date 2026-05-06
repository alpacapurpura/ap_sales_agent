# S1-cascade-bugs-fix — Sprint plan

## Meta

| Campo | Valor |
|---|---|
| Sprint ID | S1-cascade-bugs-fix |
| PI padre | PI-7-app-stability-restore |
| Inicio | 2026-05-01 |
| Estado | in-progress (PR-1 architect spawn 2026-05-01) |

## Objetivo

Restaurar sales_agent funcional end-to-end fixing Bug #7 (brand_data_adapter PersonalityProfileModel.model_dump) + Bug #9 (LiteLLM container exited mount conflict). Métrica única éxito: Chris manda "hola" al bot → respuesta correcta voice-tenant.

## PR plan

| PR | Scope | Estado |
|---|---|---|
| PR-1-cascade-bugs-recovery | Bug #7 brand_data_adapter fix + Bug #9 LiteLLM mount fix + smoke verify Chris-mediated | discovery → architect spawn |

## Criterio éxito sprint

- ✅ Bug #7 fix: `knowledge_builder.build_identity()` no falla con AttributeError model_dump
- ✅ Bug #9 fix: `visionarias_litellm` container UP (healthy) + `:4000` reachable
- ✅ LLM call sales_agent successful: `cost_usd > 0` en `sales_agent_llm_call` post-smoke
- ✅ Bot respond user-facing voice-tenant correct (no fallback "error técnico")
- ✅ `sales_agent_trace_event` `turn_end status='ok'` post-smoke

## Hipótesis sprint

**H1: Bug #7 + #9 son los únicos bloqueadores LLM stack functional sales_agent.**
- Test: post-fix, LLM call exitoso end-to-end. Si más bugs cascade descubiertos → handoff sprint S2 o PI separado.

**H2: Single PR cohesivo (cross-surface) es right-sized vs 2 PRs paralelos.**
- Test: architect dictamina. Si scope demasiado grande → split.

## Riesgos sprint

| Riesgo | Mitigación |
|---|---|
| Bug #7 fix tiene cascade callers (más sitios con `personality_profile.model_dump`) | Architect Step 0 grep cross-codebase obligatorio |
| Bug #9 mount fix invalida otros services en docker-compose | Backup pre-fix + restart secuencial |
| Bot N+1 bugs post-fix (más cascade ocultos) | Smoke profundo post-fix; si más bugs → handoff PI dedicado |
| Architect Opus paused mid-CONTRACT cap caché | Re-spawn fresh per "Opus paused → resume Opus" rule |

## Próximos pasos

1. Spawn `nicolify-architect` Opus con `prompts/01-architect-start.md` (PR-1) → produce CONTRACT.md
2. PM revisa CONTRACT, valida scope (split en 2 PRs si necesario)
3. Spawn `nicolify-backend` builder con `prompts/02-builder-start.md` (template + Step 0 grep gate)
4. Builder auto-spawn auditor backend (Cat 12 mirror detection — no aplica scope, pero check)
5. Smoke real Telegram Chris-mediated post-PASS
6. PM cierra PR + RESULT.md + lineage
7. Sprint S1 close + retro.md PI-7 → archive
