# RESULT — PR-1-cascade-bugs-recovery

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-cascade-bugs-recovery |
| Sprint padre | S1-cascade-bugs-fix |
| PI padre | PI-7-app-stability-restore |
| Estado final | shipped |
| Cierre | 2026-05-01 |
| Owner cierre | /pm |

## Outcome real vs esperado

| Métrica | Pre-fix | Post-fix target | Post-fix REAL | ✅/❌ |
|---|---|---|---|---|
| Bot responde greeting voice-tenant | NO (error fallback) | SÍ | **SÍ** — "Tenemos dos opciones: el Programa de Propósito a Prosperidad..." | ✅ |
| `sales_agent_trace_event.turn_end.status` | error | ok | **ok** (turn 16:09:16, duration 26968ms) | ✅ |
| `sales_agent_llm_call.cost_usd > 0` | 0 (errors) | >0 | **0.0** (pricing resolution falla — deuda separada) | ⚠️ |
| `sales_agent_llm_call` registrado con tokens reales | 0 input/output | >0 | **gpt-4o-mini 600 in/2 out + deepseek-reasoner 5087 in/1720 out** | ✅ |
| `knowledge_builder.build_identity()` exit | falla AttributeError | success | success (tests + smoke real) | ✅ |
| `visionarias_litellm` container | exited (127) | UP healthy | **Up healthy** (health: starting falso-positivo curl missing) | ✅ |
| `visionarias_litellm:4000` reachable desde brain | unreachable | reachable | **HTTP 200** liveliness | ✅ |

**Métrica única éxito PI-7: ✅ CUMPLIDA.** Chris mandó "Hola, quiero saber el precio" → bot respondió greeting voice-tenant Visionarias correcto.

## Surface entregada

### Bug #7 (backend brand)

| Archivo | Acción | Commit |
|---|---|---|
| `backend/src/modules/brand/application/services/brand_data_adapter.py` | MODIFIED — import `PersonalityProfileDTO` + `model_validate(orm).model_dump()` (4 líneas + 1 import) | `1bdcfdc9` |
| `backend/tests/modules/brand/application/services/test_brand_data_adapter_pr2.py` | MODIFIED — appended `TestGetBrandKnowledgeHandlesORMPersonalityProfile` (2 tests RED→GREEN) | `1bdcfdc9` |

### Bug #9 (infra)

| Archivo | Acción | Commit |
|---|---|---|
| `docker-compose.yml` | MODIFIED — agregar `LITELLM_ENVIRONMENT` propagation + memory limit 768M→1536M (paridad brain) | `d8226cf9` |
| `.env.example` | MODIFIED — agregar `LITELLM_ENVIRONMENT=dev` (gap template) | `d8226cf9` |
| `.env` (gitignored, local) | MODIFIED ad-hoc — 5 vars LITELLM_ agregadas (PM action, no commit) | n/a |

## Capacidades nuevas / restauradas

### Cap: sales_agent end-to-end functional (RESTAURADA)
- **Estado:** live
- **Lineage:** introducida PI-1 sales_agent module · última reparación **PR-1 PI-7 (commit `1bdcfdc9`+`d8226cf9`, 2026-05-01)**
- **Operable copilot:** N/A (es el bot externo)
- **Descripción:** bot Telegram responde con voz tenant — pipeline completo: webhook → buffer → debounce → typing → semantic check → LLM (vía LiteLLM proxy) → response → trace persist

### Cap: BrandDataAdapter ORM→DTO conversion (NUEVA — defensiva)
- **Estado:** live
- **Lineage:** introducida **PR-1 PI-7 (commit `1bdcfdc9`, 2026-05-01)**
- **Descripción:** adapter convierte SQLA ORM `PersonalityProfileModel` a `PersonalityProfileDTO` Pydantic via `model_validate()` antes de serializar. Patrón canonical Pydantic v2 ORM→DTO con `from_attributes=True`. Aplicable a otros adapters brand/offer si encuentran mismo type-mismatch.

### Cap: LiteLLM proxy operacional (RESTAURADA)
- **Estado:** live
- **Lineage:** introducida PI-2 (LLM stack convergencia) · última reparación **PR-1 PI-7 (commit `d8226cf9`, 2026-05-01)**
- **Descripción:** proxy LiteLLM UP healthy con 6 modelos cargados (deepseek-v4-flash, deepseek-reasoner, kimi-k2.6, openai gpt-4o-mini, gpt-4o, text-embedding-3-large). Memory limit 1536M (paridad brain) + `LITELLM_ENVIRONMENT=dev` propagado correctamente.

## Decisiones tomadas durante implementación

### D-1 — Single PR cross-surface vs split
**Resolución:** SPLIT scope dictaminado por architect. Bug #7 = builder Sonnet; Bug #9 = PM ad-hoc (restart + .env + compose edit).
**Razón:** Bug #9 root cause cambió mid-flight (architect dijo WSL2 stale bind-mount; logs reveal `LITELLM_ENVIRONMENT` missing + OOM 768M). PM ad-hoc agile vs builder con CONTRACT pre-definido.

### D-2 — Bug #7 fix approach
**Resolución:** Opción B downstream EXTEND existing `PersonalityProfileDTO` (vs A upstream repository, vs C dataclasses).
**Razón:** EXTEND existing DTO con `from_attributes=True` ya disponible. Fix mínimo (4 líneas + 1 import) en deepest layer. Anti-duplication satisfied.

### D-3 — Bug #9 fix approach
**Resolución:** Multi-causa fix (LITELLM_ENVIRONMENT propagation + memory 768M→1536M).
**Razón:** Architect/CONTEXT-BRIEF missed ambas causas reales. Logs runtime revelaron `ValueError: LITELLM_ENVIRONMENT` (causa #1) + exit code 137 SIGKILL OOM (causa #2). Memory paridad con brain (1536M) safe sin sobre-provisioning.

### D-4 — Cost_usd=0 deferred
**Resolución:** Aceptar `cost_usd=0` post-fix como deuda separada (NO bloquea PI-7).
**Razón:** Métrica única éxito = `turn_end status='ok'`, no cost > 0. Pricing resolution falla en provider mapping (`provider="openai"` para deepseek+gpt-4o-mini). Backlog separado en handoff.

## Métricas

| Métrica | Valor |
|---|---|
| Turns successful post-fix | 1 (Chris-mediated smoke) |
| Duration turn_end | 26968ms (gpt-4o-mini 3908ms + deepseek-reasoner 22872ms + overhead) |
| Tokens consumed | gpt-4o-mini: 600 in / 2 out · deepseek-reasoner: 5087 in / 1720 out |
| Container LiteLLM uptime post-fix | stable (no restart count growth) |
| Builder iter | 1 (PASS sin fix loop) |
| Auditor iter | 1 (PASS sin findings) |
| Files touched | 4 (1 src + 1 test + docker-compose + .env.example) |
| LOC delta | +12/-4 (fix #7) + +5/-2 (fix #9) |

## Deuda técnica generada / detectada

| # | Deuda | Severidad | Acción propuesta |
|---|---|---|---|
| 1 | `cost_usd=0` en `sales_agent_llm_call` post-fix — pricing resolution falla por `provider="openai"` mapping incorrecto para deepseek+kimi | MEDIUM | PR follow-up: corregir provider tag en LiteLLM-aware cost recorder |
| 2 | `BrandDataAdapter` sin try/except graceful-degradation fallback (Iron Rule `tessl__graceful-degradation`) | LOW | PR follow-up: wrap repo calls + fallback `BrandKnowledgeDTO()` vacío |
| 3 | LiteLLM healthcheck CMD usa `curl` que NO existe en imagen Chainguard wolfi-base — health: starting falso-positivo perpetuo | LOW | PR follow-up: cambiar a `wget` o Python one-liner |
| 4 | Architect/CONTEXT-BRIEF missed ambas causas reales Bug #9 (proceso learning) | LEARNING | Process improvement: architect debe correr `docker logs <container>` + `docker events` cuando container exited (no solo `docker inspect`) |
| 5 | Telegram Web typing indicator inconsistente vs apps nativas (no es bug nuestro — backend dispara `sendChatAction` correctamente, 11 calls 200 OK) | INFO | NO ACCIÓN — cliente issue conocido |

## Cross-references

- IMPL-LOG: `IMPL-LOG.md` (Sonnet builder)
- REVIEW: `REVIEW-backend.md` (verdict PASS iter=1)
- CONTRACT: `CONTRACT.md` (Opus architect)
- CONTEXT-BRIEF: `CONTEXT-BRIEF.md` (Haiku pre-flight)
- gate-output: `gate-output.json`
- Smoke real Chris-mediated: 2026-05-01 16:09 UTC ("Hola, quiero saber el precio" → bot respond voice-tenant)
- Origen handoff: `pis/archive/PI-1.1-pi1-post-mortem/retro.md`

## Lineage commit chain

| # | Commit | Descripción |
|---|---|---|
| 1 | `aec00ede` | feat(pm): claim PR-1 in-progress + bake prompts |
| 2 | `1bdcfdc9` | fix(brand): convert ORM PersonalityProfileModel via DTO in brand_data_adapter (Bug #7) |
| 3 | `427ef43a` | docs(pr-1-cascade-bugs-recovery): gate-output.json + REVIEW-backend.md verdict PASS iter=1 |
| 4 | `d8226cf9` | fix(infra): litellm container OOM + missing LITELLM_ENVIRONMENT (Bug #9) |
