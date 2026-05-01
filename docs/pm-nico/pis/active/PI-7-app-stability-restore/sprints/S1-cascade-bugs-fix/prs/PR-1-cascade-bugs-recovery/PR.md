# PR-1-cascade-bugs-recovery

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-cascade-bugs-recovery |
| Sprint padre | S1-cascade-bugs-fix |
| PI padre | PI-7-app-stability-restore |
| Estado | in-progress (architect spawn 2026-05-01) |
| Tipo | bug-fix cross-surface (backend negocio + infra) |
| Esfuerzo | M |
| Owner PM | /pm |

## Origen

Handoff PI-1.1 retro. Bugs descubiertos durante smoke real Telegram PR-2-shared-agent-observability cuando observability emergió y desbloqueó visibilidad del LLM stack down.

## Problema (user-facing)

User manda mensaje al `visionarias_bot` Telegram → bot responde "Lo siento, ocurrió un error técnico interno" en lugar de greeting normal voice-tenant.

## Outcome esperado

| Métrica | Pre-fix | Post-fix target |
|---|---|---|
| Bot responde greeting voice-tenant | NO (error fallback) | **SÍ** |
| `sales_agent_llm_call.cost_usd > 0` | 0 (errors) | >0 (functional) |
| `sales_agent_trace_event.turn_end.status` | "error" | "ok" |
| `knowledge_builder.build_identity()` exit | falla AttributeError | success |
| `visionarias_litellm` container | exited (127) | UP healthy |
| `visionarias_litellm:4000` DNS | unreachable | reachable |

## Bugs detallados

### Bug #7 — `PersonalityProfileModel` sin `model_dump`

**Path:** `backend/src/modules/brand/application/services/brand_data_adapter.py:46`

**Stack trace runtime (smoke 2026-05-01 14:15 UTC):**
```
File "/app/src/modules/sales_agent/application/services/knowledge_builder.py", line 71, in build_identity
    brand_knowledge = self.brand_port.get_brand_knowledge(tenant_id)
File "/app/src/modules/brand/application/services/brand_data_adapter.py", line 46, in get_brand_knowledge
    personality_profile=personality_profile.model_dump(mode="json") if personality_profile else None,
AttributeError: 'PersonalityProfileModel' object has no attribute 'model_dump'
```

**Root cause hypothesis:** `personality_profile` está siendo retornado como SQLA ORM `PersonalityProfileModel` en lugar de Pydantic DTO. La línea 46 asume es Pydantic.

**Fix opciones (architect decide):**
- A) Convertir `personality_profile` a Pydantic DTO antes de pass a `get_brand_knowledge` (upstream fix)
- B) Cambiar línea 46 para usar `_to_json_dict(personality_profile)` helper SQLA-aware (downstream fix)
- C) Lazy/dataclass approach con `dataclasses.asdict()` si DTO existe

**Surface:** `modules/brand/application/services/brand_data_adapter.py` + posible upstream caller en sales_agent o brand repository.

### Bug #9 — LiteLLM container exited mount config.yaml conflict

**Container:** `visionarias_litellm` (image: ghcr.io/berriai/litellm-database:main-stable)

**Síntoma:**
```
Status: Exited (127) 11 hours ago

docker start visionarias_litellm:
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error mounting "/run/desktop/mnt/host/wsl/.../app/config.yaml" to rootfs at "/app/config.yaml": create mountpoint for /app/config.yaml mount: cannot create subdirectories in "/var/lib/docker/.../app/config.yaml": not a directory: unknown: Are you trying to mount a directory onto a file (or vice-versa)? Check if the specified host path exists and is the expected type
```

**Root cause hypothesis:** Docker compose mount path conflict. `config.yaml` source path en host es directorio (por error o config bug), target en container espera file. O viceversa.

**Fix opciones (architect decide):**
- A) Verificar host path `config.yaml` existe como FILE, no dir. Recrear si necesario.
- B) docker-compose.yml mount syntax fix (file vs dir)
- C) docker volume rm + recreate

**Surface:** `docker-compose.yml` + posible `config/litellm.config.yaml` regen + container restart secuencial.

**Impacto cascade:**
- Sales_agent: APIConnectionError todos LLM calls
- Copilot: posible mismo (depende si copilot routea via litellm-proxy o direct)
- Verificar afecta solo sales_agent o también copilot

## Walking skeleton

Mínimo cohesivo entrega:
1. Bug #7 fix con grep evidence callers cross-codebase (architect Step 0 GATE)
2. Bug #9 fix docker-compose mount + container UP healthy
3. Smoke real Telegram Chris-mediated → bot respond correct voice-tenant
4. Tests:
   - Unit test `brand_data_adapter.get_brand_knowledge` con SQLA model fixture
   - Smoke verify `sales_agent_llm_call.cost_usd > 0` post turn

## Soluciones consideradas

### Bug #7 fix approach

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Upstream convert a Pydantic DTO antes pass | Cleaner separation. Pydantic DTO en API boundary | Más cambios cross-callers | architect decide |
| B) Línea 46 usar `_to_json_dict(personality_profile)` SQLA-aware helper | Fix mínimo. 1 line | Inconsistente con resto adapter | architect decide |
| C) `dataclasses.asdict()` si DTO existe | Estándar | Requiere DTO existing — verificar | architect decide |

### Bug #9 fix approach

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Host path verify + recreate config.yaml as file | Direct fix raíz | Requiere docker-compose rebuild | architect decide |
| B) docker-compose mount syntax change | Compose-only | No fix si root cause es host fs | architect decide |
| C) docker volume rm + restart | Nuclear | Pierde state si litellm tenía DB persistente | descartada (riesgo) |

## Validación técnica preliminar

Spawn `nicolify-architect` Opus → produce CONTRACT.md con:
- Step 0 GATE grep evidence Bug #7 callers cross-codebase
- Bug #9 mount path investigation (host path inspect + docker inspect existing)
- Migration plan sequenced (Bug #9 first — sin LLM no podemos verify Bug #7 end-to-end; o Bug #7 first — sin identity build no llega al LLM call)
- Tests strategy
- Risk + rollback plan

## Existing systems audit (MANDATORY — bloque grep evidence)

Architect ejecuta sección 1-5 del template. Subsistemas tocados:
- `personality_profile.model_dump` callers — grep cross-codebase
- LiteLLM proxy config — config.yaml location + docker-compose mount syntax
- `brand_data_adapter` callers — sales_agent + copilot consumers
- Anti-duplication inventory `.claude/rules/anti-duplication.md`: brand adapter NO listed (módulo-specific). LiteLLM proxy infra NO listed.

## Decisiones diferidas

- Bug #5 max update depth FE — defer hasta repro
- Bug #6 Clerk tenant switch persist — PR dedicado FE (PI distinto, NO scope PI-7)
- Backfill traces históricos sales_agent pre-PR-2 — discusión Chris post-PI-7
- Refactor brand_data_adapter más allá fix mínimo (NO scope creep)

## Out of scope

- Refactor general brand adapter
- Re-arquitectura LiteLLM proxy (sigue patrón actual)
- Cambios FE
- Cambios sales_agent module (ya fixed PR-2)

## Copilot-first checklist

- [x] Operable copilot? **NO** — bug fix infra/backend invisible al user (excepto resolver el problema raíz)
- [x] Tools nuevos: ninguno
- [x] Cards/UI nueva: ninguna
- [x] Razón NO copilot: hotfix técnico restaurar funcionalidad existente

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt | Entregable |
|---|---|---|---|
| Pre-flight context | `nicolify-context-builder` (Haiku) | architect spawn auto | `CONTEXT-BRIEF.md` |
| Pre-design | `nicolify-architect` (Opus) | `prompts/01-architect-start.md` | `CONTRACT.md` con scope decision (1 PR cross-surface vs 2 paralelos) |
| Implementation | `nicolify-backend` (Sonnet) + ad-hoc infra fix por PM si Bug #9 docker-only | `prompts/02-builder-backend.md` | code + tests + IMPL-LOG.md |
| Audit | `nicolify-backend-auditor` (Opus, auto-spawn) | builder dispara | `REVIEW-backend.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/sales-agent.md` lineage update |

**Skills mandatory:**
- Architect + builder: `backend-expert` + `brand-expert` (Bug #7 brand surface) + `tessl__graceful-degradation` (LLM resilience)
- Auditor: `backend-expert` + `brand-expert` + `sales-agent-expert` (verifica que sales_agent stack functional)

## Surface impactada (preliminary — architect refines)

| Tipo | Path | Cambio |
|---|---|---|
| BE módulo brand | `backend/src/modules/brand/application/services/brand_data_adapter.py` | Bug #7 fix (line 46) |
| BE posible upstream | `backend/src/modules/brand/infrastructure/repositories/personality_profile_repository.py` | Verificar return type ORM vs Pydantic |
| Infra | `docker-compose.yml` o `config/litellm.config.yaml` | Bug #9 mount fix |
| Tests BE | `backend/tests/modules/brand/application/services/test_brand_data_adapter.py` | Unit test SQLA fixture |
| Tests BE | `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py` | Append assertion `turn_end status='ok'` post-fix |
| current-state | `docs/pm-nico/current-state/sales-agent.md` | Status "LLM call functional" → live |
| current-state | `docs/pm-nico/current-state/brand.md` | Append note Bug #7 fix lineage si existe |

## Tests requeridos (TDD)

- `test_brand_data_adapter_handles_orm_personality_profile` — RED reproduce Bug #7 con SQLA model fixture, GREEN post-fix
- `test_litellm_proxy_reachable` — health check `:4000/v1/health` retorna 200 (ad-hoc smoke)
- `test_real_trace_persistence` (existing) — extender assertion `turn_end.status == 'ok'` post-LLM-functional

## Aceptación

- [ ] CONTRACT.md producido por architect Opus con grep evidence + scope decision (1 PR vs 2 paralelos)
- [ ] Bug #7 fix shipped + tests verdes
- [ ] Bug #9 fix shipped + container UP healthy
- [ ] Smoke real Telegram Chris-mediated → bot respond correct voice-tenant (NO error fallback)
- [ ] `sales_agent_llm_call.cost_usd > 0` post-smoke
- [ ] `sales_agent_trace_event.turn_end.status='ok'` post-smoke
- [ ] IMPL-LOG.md con Step 0 grep findings + RCA
- [ ] REVIEW-backend.md verdict PASS
- [ ] RESULT.md escrito por PM
- [ ] `current-state/sales-agent.md` lineage update
- [ ] retro.md PI-7 + archive

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Bug #7 fix tiene cascade callers más allá de adapter:46 | Architect Step 0 grep obligatorio |
| Bug #9 mount fix rompe otros services docker-compose | Backup pre-fix + restart secuencial uno-por-uno |
| LiteLLM config.yaml regen invalida API keys | Backup config + restore si rompe |
| Sales_agent N+1 cascade post-fix (más bugs ocultos) | Smoke profundo Chris-mediated. Si más bugs → handoff sprint S2 |
| Architect Opus paused mid-CONTRACT cap caché | Re-spawn fresh per "Opus paused → resume Opus" rule |
| Cross-session collision (PI-3 sales improvement, PI-5 telegram, PI-4 brand maintenance) | Architect Step 0.4 verifica overlap pre-CONTRACT |

## Estado lifecycle

`discovery` → architect ejecuta CONTRACT.md → estado `ready` → builder spawn → estado `in-progress` → PASS audit → estado `review` → smoke verify → PM cierra → estado `shipped`
