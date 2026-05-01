# PI-7-app-stability-restore

## Meta

| Campo | Valor |
|---|---|
| PI ID | PI-7-app-stability-restore |
| Inicio | 2026-05-01 |
| Estado | active |
| Tipo | mini-PI hotfix cascade recovery |
| Owner PM | /pm |
| Origen | Handoff PI-1.1 retro — Bugs #7 + #9 descubiertos durante smoke PR-2 |

## Outcome esperado (user-facing)

**Sales agent (todos canales: Telegram, IG, FB, futuro WA) responde correcto al usuario** en lugar del actual "Lo siento, ocurrió un error técnico interno".

Métrica única éxito: Chris manda mensaje "hola" al `visionarias_bot` Telegram → bot responde con greeting normal voice-tenant + traces persisten + LLM call exitoso (no APIConnectionError).

## Problema (raíz cascading bugs)

PR-2-shared-agent-observability shipped Bug #2 fix (sales_agent traces persistence) y al testear smoke desbloqueó visibilidad de **2 bugs CRÍTICOS pre-existentes** que estaban ocultos por falta de observability:

### Bug #7 — `PersonalityProfileModel.model_dump` AttributeError

**Path:** `backend/src/modules/brand/application/services/brand_data_adapter.py:46`

**Síntoma:** `'PersonalityProfileModel' object has no attribute 'model_dump'`

**Análisis:** SQLA ORM `PersonalityProfileModel` está siendo tratada como Pydantic model. Línea hace `personality_profile.model_dump(mode="json")` pero `personality_profile` es ORM model, no DTO Pydantic.

**Impacto:** `knowledge_builder.build_identity()` falla → sales_agent identity NO se construye → agent prompt sin context tenant → fallback error.

**Surface:** `modules/brand/application/services/brand_data_adapter.py` (backend negocio).

### Bug #9 — LiteLLM container exited (mount config.yaml conflict)

**Path:** `docker-compose.yml` o equivalente — mount config

**Síntoma:**
```
visionarias_litellm: Exited (127) 11 hours ago
docker start visionarias_litellm:
Error: failed to mount "/run/desktop/mnt/host/wsl/.../app/config.yaml" to "/var/lib/docker/.../app/config.yaml": create mountpoint for /app/config.yaml mount: cannot create subdirectories in "...overlayfs/.../app/config.yaml": not a directory
```

**Análisis:** Docker compose intenta montar config.yaml como FILE pero target path existe como DIRECTORY (o viceversa). Docker mount path mismatch.

**Impacto:** `visionarias_litellm:4000` DNS unreachable → APIConnectionError en TODOS LLM calls del sales_agent + copilot. Sin LLM funcional → bot no puede responder.

**Surface:** infra (docker-compose mount fix) + posible litellm config.yaml regen.

## Outcome alcanzado vs hipótesis

### H1 — Bug #7 + #9 fix end-to-end restaura sales_agent funcional
**Test:** Chris manda "hola" al bot → respuesta correcta voice-tenant (no error fallback).

### H2 — Single sprint con 2 PRs paralelos surface distinta es scope right-sized
**Test:** PR-1 backend negocio + PR-2 infra commit independent + ambos PASS audit.

## Sprints + PRs plan

### Sprint S1-cascade-bugs-fix (single sprint per Chris preference)

**Scope:** ambos bugs fixed + smoke verified end-to-end. Single sprint cohesivo.

**PR plan:**

| PR | Scope | Surface | Builder | Auditor |
|---|---|---|---|---|
| **PR-1-cascade-bugs-recovery** | Bug #7 brand_data_adapter PersonalityProfileModel fix + Bug #9 LiteLLM container restart + mount config fix + smoke verify Chris-mediated Telegram | Cross-scope: backend negocio (módulo brand) + infra (docker-compose / litellm) | Single PR cohesivo cross-surface — `nicolify-backend` (Sonnet) + ad-hoc infra fix por PM | `nicolify-backend-auditor` (Opus) |

**Decisión PR sizing:** 1 PR cohesivo en lugar de 2 paralelos porque:
- Bugs son cascade interdependientes (sin Bug #9 fix no podemos verificar Bug #7 fix end-to-end)
- Smoke test único Chris-mediated valida ambos
- Architect mandatory para verificar scope cross-surface — sí, regla nueva 5-layer enforcement aplica si PR toca shared/

Si architect dictamina splittear → 2 PRs paralelos.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Bug #7 fix puede requerir cambio downstream (DTOs, otros callers de `personality_profile`) | Architect Step 0 grep cross-codebase verifica callers |
| Bug #9 mount fix puede requerir docker-compose modify + container rebuild — quizás otros tenants/services impactados | Validar config.yaml correcto + restart secuencial |
| LiteLLM config.yaml regen puede invalidar API keys configurados | Backup config pre-fix + restore si rompe |
| Sales_agent puede tener N+1 cascade post-fix (más bugs ocultos) | Smoke test profundo Chris-mediated post-fix antes cerrar PI |

## Out of scope

- Bug #5 max update depth FE — defer hasta repro
- Bug #6 Clerk tenant switch persist — PR dedicado FE Clerk session (PI distinto)
- Backfill traces históricos sales_agent pre-PR-2 — discusión Chris post-PI-7
- Refactor brand_data_adapter más allá del fix mínimo (NO scope creep)

## Aceptación PI

- [ ] PR-1 shipped con verdict PASS auditor
- [ ] Smoke real Telegram Chris-mediated → bot respond correct (no error fallback)
- [ ] `sales_agent_trace_event` post-smoke con `turn_end status='ok'` (no error)
- [ ] `sales_agent_llm_call` post-smoke con `cost_usd > 0` (LLM call exitoso)
- [ ] `current-state/sales-agent.md` status "LLM call functional" → live
- [ ] `current-state/brand.md` (si existe) lineage Bug #7 fix
- [ ] retro.md PI-7 + archive

## Cross-references

- PI-1.1 retro.md (origen): `pis/archive/PI-1.1-pi1-post-mortem/retro.md`
- PR-2 RESULT.md (descubrimiento bugs): `pis/archive/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/RESULT.md`
- Anti-duplication rule: `.claude/rules/anti-duplication.md`
- Process learning: `docs/pm-nico/process/process-learnings.md`
