# Handoff — S1-copilot-maintenance-batch → próximo sprint

> Owner: `/pm`. Producido al cerrar sprint. Input para sprint siguiente o cierre PI.

## Estado cierre

| Campo | Valor |
|---|---|
| Sprint | S1-copilot-maintenance-batch |
| Cierre | 2026-04-29 |
| PRs shipped | 3/3 (PR-1 voice-media-hardening · PR-2 suggestions-engine · PR-3 backfill-content-blocks) |
| Verdicts | PR-1 PASS (1 iter) · PR-2 PASS (1 WARN cat 12 partial Q1) · PR-3 PASS (0 WARN) |
| Commits totales | 9 PRs commits + 3 cierres = 12 |

## Surface entregada al PI

### Backend infra
- **Tenant rate limit voice/media** (PR-1): `copilot_tenant_limits` + audit tables. Admin Streamlit `/admin/copilot-limits` CRUD overrides per-tenant. Defaults voice 6 RPM / media 25 MiB / upload 30 RPM. Cap upper 100 MiB editable post planes.
- **Suggestion engine** (PR-2): provider registry pattern (`provider_priority` weight tie-breaker). `OfferSuggestionProvider` con 6 heurísticas. Subscriber `SuggestionAccepted` forward-compat sin producer (FE futuro).
- **Backfill content→blocks** (PR-3): script CLI idempotente con triple safety (dry-run/apply/confirm-prod). Audit table `copilot_backfill_runs`. Codec v1 warning sampled 1/100.

### API endpoints modificados
- `/voice/upload-and-transcribe`: rate limit + per-tenant override
- `/voice/transcribe` (legacy): 410 Gone + `X-Deprecation-Notice`
- `/media/upload`: rate limit bucket separado + tenant-scoped max_bytes

### Tests agregados
- 42 tests PR-1 (domain, repo, resolver, voice, media, admin smoke)
- 50 tests PR-2 (suggestions engine, providers, registry, tool refactor contract, trace events)
- 25 tests PR-3 (codec sampling + backfill dry-run, apply, idempotent, batch, tenant filter, corrupt, audit)
- **Total nuevos: 117 tests** (todos verde)

### current-state/copilot.md updates
- Cap "Rate limit voice + per-tenant media/voice limits"
- Cap "Suggestion engine + provider registry"
- Cap "Backfill content→blocks (data migration v1→v2)"

## Decisiones cross-PR (para decisions.md PI-2)

| ID | Decisión | Origen |
|---|---|---|
| D-1 | Reuse `core/rate_limit.py` (no `shared/rate_limit/` nuevo) | PR-1 architect |
| D-2 | Tabla audit separada `copilot_tenant_limits_audit` (Q2 PM) | PR-1 |
| D-3 | Default voice 6 RPM cost-based ($0.036/min/tenant cap Whisper) | PR-1 Q3 PM |
| D-4 | Cap upper media 100 MiB (industry standard SaaS microempresarios) | PR-1 Q4 PM |
| D-5 | Legacy `/voice/transcribe` → 410 Gone (FE migration → cross-stack PR siguiente) | PR-1 auto-fix iter 1 |
| D-6 | Heurística simple suggestions (no LLM ranking) — latencia <10ms cost cero | PR-2 architect |
| D-7 | Reuse `copilot_trace_event` (no tabla nueva suggestions) — zero migración | PR-2 architect |
| D-8 | `provider_priority: int` explicit weight tie-breaker (Q3 PM) | PR-2 |
| D-9 | Q1 expansion vs additive: builder híbrido pragmático aceptado deuda S2+ | PR-2 |
| D-10 | Patrón Nicolify data migrations: marker + script externo (NO Python-in-alembic) | PR-3 D6 |
| D-11 | Triple safety dry-run/apply/confirm-prod regex DATABASE_URL | PR-3 D8 |
| D-12 | Filosofía paralelas relajada (M8 nueva): tocar archivos ajenos OK con "extend no destroy" | Chris 2026-04-29 |

## Riesgos abiertos al sprint siguiente

| Riesgo | Mitigación propuesta | Sprint destino |
|---|---|---|
| FE call `voice-api.ts:26` rompe con 410 Gone backend | Cross-stack PR FE migration `/voice/transcribe` → `/voice/upload-and-transcribe` | S2 (cross-stack) o pase prod previo |
| Suggestion engine FE consume stub `useSuggestions` (no real BE) | Cross-stack PR FE swap stub → GET endpoint + producer `SuggestionAccepted` | S2 |
| Backfill prod-clone test diferido | Chris docker exec antes pase prod | Pre-pase prod |
| `campaigns/domain/repositories.py` arch fail | Fix sesión PI-1 sub-G (regla M8 — no PI-2 responsabilidad) | PI-1 sub-G follow-up |

## Skills/agentes recomendados S2

- Si S2 incluye FE swap suggestions/voice → `nicolify-architect` + `nicolify-frontend` + `nicolify-frontend-auditor` + `copilot-expert`
- Si S2 incluye providers nuevos suggestions (brand, sales_agent) → `nicolify-backend` + skill correspondiente (`brand-expert` / `sales-agent-expert`) + `copilot-expert`
- Si S2 incluye discovery formal Bloque C copilot → PM solo + `Explore` agent

## Pase a producción

Sprint S1 acumula:
- 3 migraciones nuevas (`085_copilot_tenant_limits`, `111_copilot_blocks_backfill_marker`)
- 117 tests nuevos
- 5 endpoints API modificados (rate limit + 410 Gone)
- 1 admin Streamlit page nueva

**Recomendación PM**: pase a producción factible post-handoff. Pre-requisitos:
- `/test-all` pase
- Migration prod-clone test (`085` y `111`)
- `make ci-parity` antes `git push origin main`
- Smoke E2E voice + media post-deploy

Auto-spawn agent PASE-PRODUCCION → 2 semanas (cleanup post-deploy verification) opcional.

## Próximo sprint sugerencia

Opción A (recomendada): **S2-copilot-fe-swap** — cross-stack FE swap del stub suggestions + voice migration. Cierra deuda PR-2/PR-1.
Opción B: **Cerrar PI-2** y mover a archive. Razón: 3 PRs S1 estabilizaron core copilot. PI-2 S2+ puede esperar discovery formal Bloque C.
Opción C: **S2-copilot-providers** — agregar `BrandSuggestionProvider` + `SalesAgentSuggestionProvider`. Habilita pure expansion `offer_section_tools.py` (cierra deuda PR-2 Q1).

PM recomienda **A** primero (urge cerrar deuda visible cross-stack), después decidir B vs C según métricas adopción copilot.
