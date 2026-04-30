# IMPL-LOG — PR-8-inbound-recognition-and-inbox-tag

> Owner: builders (nicolify-backend Sub-A+B+D; nicolify-frontend Sub-C). Append-only.

## Sesión 2026-04-30 — backend (Sub-A + Sub-B + Sub-D) + frontend (Sub-C)

### Contexto cargado

- `PR.md` ✓
- `CONTRACT.md` ✓ 832 líneas
- Skills consultados: `backend-expert` (DDD ports, AsyncSession, response_model), `frontend-expert` (FSD-Lite + Shadcn), `sales-agent-expert` (chat.py insertion point + outbound_mode invariant)

### Decisiones implementación

- **Lazy import en chat.py**: `from src.shared.links.ports.campaigns import create_campaigns_lookup_port` dentro de `process_chat_flow` para preservar boundary DDD y evitar coupling startup. Test patch target debe ser `src.shared.links.ports.campaigns.create_campaigns_lookup_port` (lazy origin). Drift inicial: test patcheaba también `chat.create_campaigns_lookup_port` que no existe — removido.
- **PLR0915 noqa en chat.py::process_chat_flow**: orchestrator composition crossed 50-stmt limit con PR-8 inbound recognition block agregado on top de S11B carve-out. Refactor agresivo a sub-funciones queda follow-up — preservamos cohesión flow para review legibility.
- **`converted_count_attribution_method = "deferred_pr_followup"` enum**: 1000-clientes MVP simplification. Exact attribution (cross-module payment + scheduling lookup) requeriría broad cross-table reads; deferred a PR follow-up. responded_count proxy via `sales_agent.messages` post sent_at queda documentado en `KNOWN_CROSS_MODULE_TABLE_READS` allowlist.
- **CampaignsLookupPort ABC + factory pattern**: matches `crm_repos.py` lazy port pattern; no direct cross-module import sales_agent → campaigns.

### Sub-deliverables completados

| Sub | Commit | Builder | Resumen |
|---|---|---|---|
| Sub-A | `7bed7dea` | backend | CampaignsLookupPort ABC + factory + impl + chat.py inbound recognition + ENV [1,72] validator + tests |
| Sub-B | `7bed7dea` | backend | CampaignStatsResponse + GET /campaigns/{id}/stats endpoint + CampaignStatsService + closer_studio DTO/endpoint extension + inbox_campaign_enrichment service |
| Sub-C | `e5bd8448` | frontend | CampaignTag.tsx Shadcn Badge chip clickable to /campañas/{id} + ConversationItem/ConversationThread wire + Conversation type extension |
| Sub-D | `7bed7dea` | backend | test_campaigns_stats_response_model_currency.py arch test (response_model + currency + tenant_id filter + KNOWN_CROSS_MODULE_TABLE_READS allowlist entry) |

### Files affected (real count post-build)

#### NEW source (4)

| Path | Sub |
|---|---|
| `backend/src/modules/campaigns/application/services/campaign_stats_service.py` | B |
| `backend/src/modules/campaigns/infrastructure/links/__init__.py` + `campaigns_lookup_impl.py` | A |
| `backend/src/modules/sales_agent/application/services/inbox_campaign_enrichment.py` | B |
| `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` | C |

#### MODIFY source

| Path | Sub | Cambio |
|---|---|---|
| `backend/src/core/config.py` | A | + `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` ENV + validator |
| `backend/src/modules/campaigns/api/_service_factories.py` | B | + `_get_locale` async helper |
| `backend/src/modules/campaigns/api/routers/campaigns_router.py` | B | + GET /campaigns/{id}/stats endpoint |
| `backend/src/modules/campaigns/application/dtos/campaign_dtos.py` | B | + `CampaignStatsResponse` Pydantic v2 |
| `backend/src/modules/campaigns/domain/repositories.py` | A | + ABC method `get_recent_sent_for_lead` |
| `backend/src/modules/campaigns/infrastructure/repositories/campaign_task_repository_impl.py` | A | + impl method |
| `backend/src/modules/sales_agent/api/dto/closer_studio.py` | B | + `campaign_id`, `campaign_name` optional fields |
| `backend/src/modules/sales_agent/application/orchestrator/chat.py` | A | + inbound recognition block + PLR0915 noqa |
| `backend/src/shared/links/ports/campaigns.py` | A | + `CampaignsLookupPort` ABC + `create_campaigns_lookup_port` factory + `CampaignTaskLookupResult` |
| `frontend/src/features/closer-studio/components/inbox/ConversationItem.tsx` | C | + render `<CampaignTag>` when present |
| `frontend/src/features/closer-studio/components/inbox/ConversationThread.tsx` | C | + render in detail header |
| `frontend/src/features/closer-studio/types/index.ts` | C | + `campaign_id?` `campaign_name?` |

#### NEW tests (committed)

| Path | Sub |
|---|---|
| `backend/tests/architecture/test_campaigns_stats_response_model_currency.py` | D |
| `backend/tests/modules/campaigns/api/test_campaigns_stats_endpoint.py` | B |
| `backend/tests/modules/campaigns/infrastructure/test_campaign_task_repository_lookup.py` | A |
| `backend/tests/modules/sales_agent/api/test_inbox_campaign_tag.py` | B |
| `backend/tests/modules/sales_agent/application/orchestrator/test_inbound_campaign_recognition.py` | A |
| `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` | C |

### Tests count post-build

- BE: 52 tests verde (unit + arch) native WSL.
- FE: 7 nuevos CampaignTag tests + 1846 total Vitest passing (242 test files).

### Quality gates

- [x] Ruff verde (28 errores auto-fixed via `--fix --unsafe-fixes`; 3 manual fixes — D104 + PLR0915 noqa + BLE001 ValidationError-only)
- [x] Ruff format verde (10 files reformatted)
- [x] Pytest verde 52/52 backend
- [x] Vitest verde 7/7 frontend (CampaignTag suite) + suite global
- [x] Pre-commit hooks verde
- [x] Migrations: 0 nuevas (index `idx_campaign_tasks_campaign_id_status_sent_at` ya existía)

### Drift detectado durante implementación

1. **FE inbox real path** = `frontend/src/features/closer-studio/components/inbox/` (sprint.md decía `features/inbox/` que no existe). Resolved en CONTRACT.md by architect — confirmed durante FE build.
2. **Test patch target redundante** — `chat.create_campaigns_lookup_port` (lazy import inside function = no module-level symbol). Removed; patch al port location funciona.
3. **chat.py PLR0915 (>50 statements)** — pre-existing borderline; PR-8 inbound recognition block lo cruzó. noqa with reason "orchestrator composition (S11B carve-out + PR-8 inbound recognition)".
4. **`converted_count` exact attribution** — defer a PR follow-up. Cross-module payment + scheduling lookups requieren broad reads; MVP S3 prioriza ship visible. Field `converted_count_attribution_method = "deferred_pr_followup"` documenta explícito.

### Bloqueadores encontrados

Ninguno crítico. `get_async_session_factory` no existe pero short-lived AsyncSession pattern de PR-7 OutboundOrchestrator suficiente para Sub-A.

### Decisiones diferidas

| Item | Por qué diferido | Sprint destino |
|---|---|---|
| Exact `converted_count` attribution (payment + scheduling cross-lookup) | 1000-clientes MVP simplification; broad cross-module reads complejos | PR follow-up post S3 |
| chat.py refactor para reducir PLR0915 | Cohesión orchestrator flow > splitting; review legibility | Post PI-1 cleanup |

### Surface real entregada

| Tipo | Path | Estado |
|---|---|---|
| Source NEW | `campaigns/application/services/campaign_stats_service.py` | shipped |
| Source NEW | `campaigns/infrastructure/links/campaigns_lookup_impl.py` | shipped |
| Source NEW | `sales_agent/application/services/inbox_campaign_enrichment.py` | shipped |
| Source NEW | `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` | shipped |
| API endpoint NEW | `GET /api/v1/campaigns/{campaign_id}/stats` | shipped |
| Source MOD | `chat.py` inbound recognition + 12 BE files extends | shipped |
| Test NEW | 5 BE tests + 1 FE test | shipped |
| Doc MOD | `current-state/{campaigns,sales-agent,crm}.md` | TODO Sub-K cierre PR-8 |

### Commits (chronological)

- `e5bd8448` — feat(frontend-inbox): PR-8 Sub-C campaign tag chip + click navigation
- `7bed7dea` — feat(campaigns): PR-8 Sub-A+B+D inbound recognition + stats endpoint + inbox tag

---

<!-- @pm: implementación PR-8 done. Próximo paso: REVIEW.md auditor + RESULT.md cierre. Después PR-9 E2E test. -->
