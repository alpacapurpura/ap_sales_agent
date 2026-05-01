# PR-8 Inbound recognition and inbox tag

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-8-inbound-recognition-and-inbox-tag |
| Sprint padre | S3-mvp-telegram |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | feature |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | — |

## Problema (user-facing)

Hoy un lead que **responde** a un mensaje outbound de campaña (PR-7) entra al inbox como conversación inbound regular: nada distingue al hilo del resto de leads cold. El owner pierde el contexto "esta conversación arrancó con campaña X". Además no hay forma de medir si la campaña convierte: cero stats endpoint en BE, cero badge "campaña" en FE.

JTBD: cuando un lead responde a un mensaje outbound, quiero ver *en el inbox* de qué campaña vino — y desde la lista de campañas quiero ver tasa de respuesta y conversión por campaña.

## Outcome esperado

- Lead que responde dentro de 24h post-`SENT` → conversación queda etiquetada `campaign_id` (lookup on-demand).
- Inbox FE muestra chip "campaña: {name}" clickable a `/campañas/{id}` (placeholder route OK PR-8).
- `GET /api/v1/campaigns/{id}/stats` retorna `total_tasks / sent_count / responded_count / converted_count / response_rate / conversion_rate` con currency master-data.
- Métrica medible PR-9 manual test: % de leads que respondieron a la campaña en 24h.

## Walking skeleton (mínimo viable cohesivo)

End-to-end visible a Chris en una sola pasada:

1. Lead replica → `process_chat_flow` lookup `campaign_task` (24h window) → inyecta `campaign_id` en `AgentState` (`outbound_mode=False` — no triggerea cache slot 7 — solo enrichment).
2. Inbox endpoint enrichments: `ConversationListItem.campaign_id + campaign_name` + `ConversationDetail.campaign_id + campaign_name`. Lookup mismo helper.
3. Stats endpoint nuevo `GET /campaigns/{id}/stats` consume `count_by_campaign_status` + `responded_count` audit_log proxy + `converted_count = 0` (deferred PR-followup, attribution_method documented).
4. FE `CampaignTag.tsx` chip Shadcn `Badge` clickable. Wire en `ConversationItem.tsx` + `ConversationThread.tsx` (closer-studio inbox SSoT — NO existe `features/inbox/` separado).

Cohesivo Opus 4.7[1M]: BE+DTO+FE+arch tests en una sola PR. NO splitear "lookup helper" como sub-PR.

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| A) Lookup on-demand `campaign_task` SSoT | cero migración · reactive · 1 query con index | requiere index proper para 1000+ tenants | **ELEGIDA** |
| B) Persist `campaign_id` en `agent_state_checkpoint` o nueva column | menos queries runtime | migración + escritura redundante (campaign_task ya tiene la data) · drift potencial entre 2 SSoT | descartada — viola SSoT principle |
| C) MV materialized view stats | sub-100ms p99 | refresh lag · complejidad cron · MVP no necesita | descartada — live query con index alcanza p95<200ms para MVP S3 |

Filosofía Chris "1000 clientes mañana": el index `idx_campaign_tasks_campaign_id_status_sent_at` es el costo-benefit correcto. MV se evalúa en PI-2 si la query escala >200ms p95.

## Validación técnica preliminar

- **Modules afectados**: `sales_agent` (chat orchestrator + closer_studio API + DTOs), `campaigns` (router + repository + DTO + arch test). FE `closer-studio/components/inbox/` (NO `features/inbox/` — drift resuelto en CONTRACT). Cero modificación `crm/api/`.
- **Blockers conocidos**: ninguno. PR-7 SHIPPED, OutboundOrchestrator + AgentState campaign fields disponibles.
- **Tiempo estimado**: 6-9h Opus solo (BE 3h + FE 1.5h + arch tests + IMPL-LOG 1h + buffer).
- **Alternativas técnicas**: descartadas (ver tabla arriba).

## Existing systems audit (NO NEW LAYER rule)

Subsystem que toca: **inbound recognition + stats aggregation + tenant-scoped lookup**.

- `grep -rn "campaign_task" backend/src/modules/campaigns/`: `CampaignTaskRepository.count_by_campaign_status` YA existe (línea 291 `campaign_task_repository_impl.py`) — explicitly designed for "GET /campaigns/{id}/stats (S3)" comment.
- `grep -rn "from src.modules.campaigns" backend/src/modules/sales_agent/`: cero imports. PR-8 abre nuevo cross-module read **via `shared/links/ports/`** (NO direct import — DDD arch test enforce).
- `grep -rn "tenant_locale\|get_tenant_locale" backend/src/shared/`: `TenantLocale` VO en `shared/domain/locale.py` existe. PR-8 reusa el patron PR-7 Sub-F (`get_tenant_locale()` DI).
- `grep -rn "AuditRepository\|messages.role" backend/src/modules/sales_agent/`: `AuditRepository` + `messages` table existen — `responded_count` proxy reusa esto sin nueva tabla.

**Decisión por sistema**:
1. `CampaignTaskRepository` → **EXTEND**: agregar 1 método `find_recent_for_lead(tenant_id, lead_id, window_hours)` ABC + impl. Reusa `count_by_campaign_status` para stats.
2. `shared/links/ports/` → **EXTEND**: nuevo port `campaigns.py` con `find_recent_campaign_task_for_lead` + `count_campaign_tasks_by_status` + `count_responded_leads`. NO importar `campaigns.domain` directo desde `sales_agent`.
3. `TenantLocale` flow → **EXTEND** (reuse PR-7 Sub-F): `currency` en `CampaignStatsResponse` derivado de `get_tenant_locale(tenant_id)`.
4. `AuditRepository.messages` → **READ-ONLY query** desde stats service: `SELECT COUNT(DISTINCT user_id) FROM messages WHERE tenant_id=X AND role='user' AND created_at > campaign_task.sent_at AND user_id IN (lead_ids of campaign tasks SENT)`. Cero nuevo modelo.
5. **Index `idx_campaign_tasks_campaign_id_status_sent_at`**: incluido como migración idempotente `CREATE INDEX IF NOT EXISTS` en PR-8 (Sub-B). Justificado: query stats + query lookup ambos usan filter `(tenant_id, campaign_id, status, sent_at)`. Sin index → seq scan a 1000 clientes × N campaigns × M tasks = inaceptable. CON index → p95 < 50ms.

NO NEW LAYER detectado. Todo EXTEND.

## Decisiones diferidas (explícitas)

- **`converted_count` exact attribution** (cross-module: payments + scheduling) → `converted_count = 0` + `converted_count_attribution_method: "deferred_pr_followup"` en CampaignStatsResponse. PR-followup post-S3 lo refina.
- **`campaign_archetype` filter en inbox list** (filter por campaña) → backlog post-MVP. PR-8 solo enriquece, no agrega filter UI.
- **MV stats refresh** (sub-100ms aggregation) → PI-2 si live query supera p95 200ms.

## Out of scope

- ❌ Modificar `agent_state_checkpoint` schema (decisión 42).
- ❌ Persistir `campaign_id` en `messages` o `leads` (lookup on-demand SSoT).
- ❌ Nueva ruta `/campañas/{id}` real (placeholder OK — PR follow-up wires real page).
- ❌ Filter inbox por campaña (solo enrichment).
- ❌ `RESPONDED`/`CONVERTED` enum status nuevo (proxy via audit_log + flags downstream).
- ❌ ETL/MV stats (live query con index).
- ❌ Voice/sales_agent prompt change (PR-7 cubrió outbound voice; PR-8 inbound es regular conversation).

## Copilot-first checklist

- [x] **NO copilot operable PR-8**. Razón: feature es enrichment del inbox owner-facing y stats endpoint de campaigns admin. Copilot no necesita exponer "ver stats de campaña" como tool en MVP S3 — owner ya tiene `/campañas` page (futuro). Si PI-2 quiere "preguntale al copilot por stats de mi última campaña" → tool nuevo `get_campaign_stats(campaign_id)` que consume el endpoint PR-8 ya hecho.
- [ ] Tools nuevos: ninguno.
- [ ] Cards/UI copilot nueva: ninguna.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` (este PR) | `prompts/01-architect-start.md` (este task) | `CONTRACT.md` |
| Implementation | `nicolify-backend` (Sub-A + Sub-B + Sub-D) | `prompts/02-builder-start.md` | code + tests + IMPL-LOG (cronograma A → B → D) |
| Implementation | `nicolify-frontend` (Sub-C) | `prompts/02-builder-start.md` | code + Vitest + IMPL-LOG (Sub-C cronograma) |
| Audit | `nicolify-backend-auditor` + `nicolify-frontend-auditor` | `prompts/03-auditor-start.md` | `REVIEW.md` (consolidado) |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + current-state{campaigns,sales-agent,crm}.md |

Surface mapping (PM spawnea estos agentes):

| Surface | Builder | Auditor |
|---|---|---|
| `backend/src/modules/sales_agent/{api/closer_studio.py, api/dto/closer_studio.py, application/orchestrator/chat.py}` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/src/modules/campaigns/{api/routers/campaigns_router.py, api/dto/, application/services/, infrastructure/repositories/, domain/repositories.py}` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/src/shared/links/ports/campaigns.py` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/alembic/versions/{NN}_add_campaign_task_stats_index.py` | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/tests/architecture/test_campaigns_stats_response_model_currency.py` | `nicolify-backend` (Sub-D) | `nicolify-backend-auditor` |
| `backend/tests/modules/sales_agent/application/orchestrator/test_inbound_campaign_recognition.py` | `nicolify-backend` (Sub-A) | `nicolify-backend-auditor` |
| `backend/tests/modules/campaigns/api/test_campaigns_stats_endpoint.py` | `nicolify-backend` (Sub-B) | `nicolify-backend-auditor` |
| `backend/tests/modules/sales_agent/api/test_inbox_campaign_tag.py` | `nicolify-backend` (Sub-B) | `nicolify-backend-auditor` |
| `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` | `nicolify-frontend` (Sub-C) | `nicolify-frontend-auditor` |
| `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` | `nicolify-frontend` (Sub-C) | `nicolify-frontend-auditor` |
| `frontend/src/features/closer-studio/types/index.ts` (extend) | `nicolify-frontend` (Sub-C) | `nicolify-frontend-auditor` |

## Surface impactada

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Tabla DB | `campaign_tasks` | índice nuevo `idx_campaign_tasks_campaign_id_status_sent_at` (migración idempotente) |
| API endpoint | `GET /api/v1/campaigns/{campaign_id}/stats` | NEW |
| API endpoint | `GET /api/v1/closer-studio/conversations` + `GET /api/v1/closer-studio/conversations/{lead_id}` | extended response (add `campaign_id` + `campaign_name`) |
| Domain port | `shared/links/ports/campaigns.py::CampaignsLookupPort` | NEW (3 métodos) |
| Domain repo | `CampaignTaskRepository.find_recent_for_lead` | NEW método ABC + impl |
| Domain repo | `CampaignTaskRepository.count_responded_leads` | NEW método ABC + impl |
| Application service | `CampaignStatsService` (campaigns) | NEW |
| DTO | `CampaignStatsResponse` (campaigns) | NEW |
| DTO | `ConversationListItem.campaign_id/name` + `ConversationDetail.campaign_id/name` | extend (additive optional) |
| FE component | `CampaignTag.tsx` (closer-studio inbox) | NEW |
| FE wire | `ConversationItem.tsx` + `ConversationThread.tsx` | extend |
| FE types | `closer-studio/types/index.ts` | extend (campaign_id + campaign_name optional) |
| Arch test | `test_campaigns_stats_response_model_currency.py` | NEW |
| ENV | `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` | NEW (default 24, max 72) |
| current-state | `current-state/{campaigns,sales-agent,crm}.md` | append capability lineage PR-8 |

## Tests requeridos (TDD)

Backend (RED → GREEN por capa, conforme `.claude/rules/tdd-mandatory.md`):

- `tests/modules/sales_agent/application/orchestrator/test_inbound_campaign_recognition.py` — happy path + lookup miss + lookup error fail-open + window boundary (sent_at = now-23h59m → hit; sent_at = now-24h01m → miss) + most-recent ordering.
- `tests/modules/campaigns/api/test_campaigns_stats_endpoint.py` — happy path + zero tasks (rates=null) + tenant isolation 403/404 + currency from tenant_locale + converted_count_attribution_method literal.
- `tests/modules/sales_agent/api/test_inbox_campaign_tag.py` — list + detail enrichment (lead with campaign hit, lead without campaign null, lookup error fail-open).
- `tests/modules/campaigns/infrastructure/test_campaign_task_repository_lookup.py` — `find_recent_for_lead` happy + tenant scope + most-recent + window boundary; `count_responded_leads` happy + zero responded.
- `tests/architecture/test_campaigns_stats_response_model_currency.py` — `response_model=CampaignStatsResponse` declared; `currency: str | None` field present; AST grep `tenant_id` filter en stats query.

Frontend (Vitest + RTL):

- `frontend/src/features/closer-studio/components/inbox/__tests__/CampaignTag.test.tsx` — render con campaign_id + campaign_name → chip Badge texto correcto; click → router push `/campañas/{id}`; sin campaign_id → render null.
- Update `ConversationItem.test.tsx` + `ConversationThread.test.tsx` (si existen) para ensamblar CampaignTag — extend baseline.

## Aceptación

- [ ] Tests verdes BE + FE
- [ ] `cd backend && .venv/bin/pytest tests/architecture/ -x -q` verde (allowlist no crece)
- [ ] `cd backend && .venv/bin/ruff check src tests` + `ruff format --check` verde
- [ ] `cd frontend && npx tsc --noEmit && npx eslint . && npx vitest run` verde
- [ ] IMPL-LOG.md completo (cronograma Sub-A → B → C → D + commit hashes)
- [ ] REVIEW.md sin findings críticos
- [ ] RESULT.md escrito por PM
- [ ] `current-state/{campaigns,sales-agent,crm}.md` updated con capability lineage PR-8
- [ ] Decisiones 38-45 registradas (CONTRACT.md las cubre)

## Reglas duras

- `response_model=` OBLIGATORIO en stats endpoint y en extended inbox endpoints.
- Tenant isolation cada query (`WHERE tenant_id = :t`).
- AsyncSession código nuevo (`AsyncSession`) — chat.py ya usa sync `Session`, helper Sub-A debe ser async-friendly via wrapper que respete actual session lifecycle.
- `structlog` (no `print`/`logging`).
- `currency: str \| None` field en `CampaignStatsResponse` (master-data invariante).
- Spanish neutro LATAM en docstrings + UI strings ("campaña", "tasa de respuesta", "tasa de conversión").
- `tenant_id` mandatory en CADA método nuevo del port + repo.
- Inbound recognition fail-open (try/except graceful — agent resilience pattern de chat.py:208).
- Cero `from src.modules.campaigns` en `sales_agent` — solo via `shared/links/ports/campaigns.py`.
- Migration idempotente raw SQL (`CREATE INDEX IF NOT EXISTS`).
- TDD: RED por capa (domain repo → port → service → API → orchestrator → FE).

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Cross-module import `sales_agent → campaigns` rompe DDD arch test | Port en `shared/links/ports/campaigns.py` (igual patrón a `tenant_profile`, `offer`, `brand`) |
| Window 24h muy corto en LATAM (lead responde día 2-3) | ENV `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` ajustable per-tenant futuro · max 72h hard cap valida ENV |
| Lookup query slow a 1000+ tenants | Index `(tenant_id, lead_id, status, sent_at DESC)` + `LIMIT 1` |
| `responded_count` proxy false-positives (lead respondió por canal distinto al outbound) | MVP acepta proxy; PR follow-up afina con `channel_used` filter |
| Postgres no levantado durante validación pre-deploy | migration `IF NOT EXISTS` idempotente — crea index la primera vez sin romper si ya existe |
| FE `features/inbox/` no existe (drift task description) | CampaignTag.tsx en `closer-studio/components/inbox/` SSoT real (resuelto CONTRACT) |
| `outbound_mode` activado por error inyectando slot 7 cache cuando no corresponde | helper inyecta SOLO `campaign_id`; `outbound_mode` queda False default. Test arch valida slot 7 ausente cuando outbound_mode=False |

