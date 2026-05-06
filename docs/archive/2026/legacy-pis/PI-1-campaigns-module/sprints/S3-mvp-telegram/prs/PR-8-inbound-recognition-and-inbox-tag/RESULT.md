# RESULT — PR-8-inbound-recognition-and-inbox-tag

> Owner: `/pm`. Cierre del loop PR-8.

## Meta cierre

| Campo | Valor |
|---|---|
| Estado final | shipped |
| Fecha cierre | 2026-04-30 |
| Commits PR-8 | `e5bd8448` (FE Sub-C) `7bed7dea` (BE Sub-A+B+D) |
| Branch | development (push fast-forward) |

## Outcome real vs esperado

| Aspecto | Esperado | Real | Delta |
|---|---|---|---|
| Inbound reply recognition | Lead responde dentro de window → `campaign_id` etiqueta conversación | Sí — `lookup_recent_campaign_task` async + chat.py inject | ✅ |
| Stats endpoint | `GET /campaigns/{id}/stats` con response_model + tenant isolation | Sí — `CampaignStatsResponse` + master-data currency | ✅ |
| Inbox UI tag | Chip "campaña: {name}" clickable | Sí — Shadcn Badge + Link to /campañas/{id} | ✅ |
| Conversion attribution exact | Real payment + scheduling lookup | `converted_count = 0` con attribution_method = "deferred_pr_followup" | ⚠️ defer (1000-clientes MVP simplification, justified) |
| Cero migración nueva | 0 esperadas | 0 entregadas (index ya existía) | ✅ |
| ZERO regresión inbound | outbound_mode=False default preserved | Sí — campaign_id inject NO activates outbound_mode | ✅ |

Veredicto: **✅ cumplido core scope (PR-8 ship-ready);** ⚠️ exact `converted_count` attribution defer documented (no bloqueante MVP).

## Surface entregada

| Tipo | Path | Notas |
|---|---|---|
| Cross-module port NEW | `shared/links/ports/campaigns.py` | `CampaignsLookupPort` ABC + factory |
| Port impl NEW | `campaigns/infrastructure/links/campaigns_lookup_impl.py` | Delegates to repository |
| Service NEW | `campaigns/application/services/campaign_stats_service.py` | sent_count + responded_count proxy |
| Service NEW | `sales_agent/application/services/inbox_campaign_enrichment.py` | Reuse port for tag enrichment |
| FE component NEW | `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` | Shadcn Badge chip clickable |
| API endpoint NEW | `GET /api/v1/campaigns/{campaign_id}/stats` | response_model + tenant isolation |
| ENV NEW | `CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS` default 24 [1,72] | field_validator |
| Source MOD | chat.py inbound recognition + 12 BE files extends | Cero breaking |
| Arch test NEW | `test_campaigns_stats_response_model_currency.py` | response_model + currency + tenant_id + cross-module allowlist |
| FE wire MOD | ConversationItem + ConversationThread render `<CampaignTag>` cuando present | Conversation type extension |

## Capacidades agregadas (lineage current-state)

```md
### Cap: Inbound campaign recognition + Inbox tag (PR-8 PI-1 S3)
- Introducida: PR-8 Sub-A+B+C+D (commits e5bd8448 + 7bed7dea, 2026-04-30)
- Estado: live
- chat.py::process_chat_flow busca CampaignTask SENT últimas 24h (ENV CAMPAIGNS_INBOUND_RECOGNITION_WINDOW_HOURS [1,72]) por (tenant_id, lead_id) → inyecta campaign_id en AgentState (no activa outbound_mode).
- closer_studio inbox endpoints enriquecen conversations con campaign_id + campaign_name optional fields.
- Frontend Inbox renderiza chip "campaña: {name}" clickable a /campañas/{id} (placeholder route post-MVP).
- Best-effort fail-open: lookup error → continue sin tag.

### Cap: Campaign stats endpoint (PR-8 PI-1 S3)
- Introducida: PR-8 Sub-B (commit 7bed7dea, 2026-04-30)
- Estado: live
- GET /api/v1/campaigns/{campaign_id}/stats — response_model CampaignStatsResponse + tenant isolation X-Tenant-ID.
- Live DB query: total_tasks, sent_count, responded_count (proxy: lead messages AFTER sent_at), converted_count (defer = 0 con attribution_method = "deferred_pr_followup"), response_rate, conversion_rate, currency (master-data).
- 1000-clientes MVP simplification: exact converted attribution refined PR follow-up.
```

## Decisiones tomadas

| ID | Decisión | Razón | Origen |
|---|---|---|---|
| D-38 | Inbound recognition window 24h ENV-tunable [1,72] | Lead responde 3 días tarde → fallback no campaign context (window 24h conservador) | CONTRACT §11 |
| D-39 | MOST_RECENT campaign match | Lead responde a múltiples campaigns en window → tomar la más reciente | CONTRACT §11 |
| D-40 | Live DB stats query | Index ya existe; p95 < 200ms con 1000 clientes; MV adds complexity sin beneficio MVP | CONTRACT §11 |
| D-41 | FE chip clickable Shadcn Badge → /campañas/{id} | Reuse design tokens; placeholder route OK pre-S4 | CONTRACT §11 |
| D-42 | campaign_id storage NO migration — lookup on-demand | Single SSoT (campaign_task table); zero migration | CONTRACT §11 |
| D-43 | response_rate = responded / sent (NULL si sent=0) | Standard formula | CONTRACT §11 |
| D-44 | converted_count DEFER = 0 con attribution_method enum | 1000-clientes MVP — exact attribution requiere broad cross-module reads; refine PR follow-up | CONTRACT §11 + IMPL-LOG drift |
| D-45 | Stats endpoint NO paginación | Single-campaign aggregate | CONTRACT §11 |

## Métricas medidas

| Métrica | Baseline | Cierre PR | Delta |
|---|---|---|---|
| Tests PR-8 BE verde | 0 | 52 | +52 |
| Tests PR-8 FE verde | 0 | 7 | +7 |
| Arch tests | 768 (post-PR-7) | 769 (+1 PR-8 currency) | +1 |
| Migrations | 0 | 0 | 0 |
| Endpoints nuevos | 0 | 1 (`GET /campaigns/{id}/stats`) | +1 |
| Sub-deliverables shipped | 0 | 4/4 | 100% |

## Deuda técnica generada

| Item | Razón | Sprint destino |
|---|---|---|
| Exact `converted_count` attribution (cross-module payment + scheduling) | 1000-clientes MVP simplification | PR follow-up post S3 |
| chat.py refactor para reducir PLR0915 (>50 stmts) | Cohesión orchestrator flow > splitting; review legibility | Post PI-1 cleanup |

## Update obligatorios hechos

- [x] IMPL-LOG.md llenado con cronograma + drift + commits
- [ ] `current-state/{campaigns,sales-agent,crm}.md` actualizado (TODO append capability lineage post-PR cierre — pendiente integration con parallel session que también edita estos files)
- [ ] `decisions.md` PI append (TODO PM main session — D-38 to D-45)
- [ ] Sprint `learnings.md` (TODO al cierre S3 post PR-9)

## Próximo paso PM

- Proceder PR-9 E2E Playwright + manual checklist (esfuerzo S).
- Después S3 cierre con learnings + handoff PI-2.
- Si S4 también shipped → PI-1 retro + archive.

---

PR-8 **shipped**. PM cierra archivo. 4/4 sub-deliverables. REVIEW.md verdict: PASS (auditor fallback validation main session: tests verde + lint clean + arch ratchets unchanged + tenant isolation verified).
