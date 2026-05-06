# Outbound Conversational (Sales Agent inicia)

## Meta

| Campo | Valor |
|---|---|
| Slug | outbound-conversational |
| Tier legacy | Tier 1A (research `docs/pm/campaigns/00-framework/campaign-types.md`) |
| Estado | priorizada — PI-1 PI-1 MVP 1 (Telegram) |
| Owner módulo | sales_agent + campaigns |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como emprendedor, cuando tengo un grupo de leads que no respondieron en X días, quiero que el Sales Agent les escriba **personalizadamente** sin que yo redacte cada mensaje, para reactivar la conversación y aumentar conversión.

## Dolor user

- Tiene leads warm/cold sin contacto reciente. Re-engagement manual = imposible a escala.
- Templates fijos suenan robóticos. Quiere voz de marca + contexto del lead.
- Hoy NO PUEDE: Sales Agent solo reacciona inbound, no inicia.

## Outcome deseado

- 1 click (o 1 frase a copilot) → Sales Agent envía mensaje personalizado a N contactos por canal preferido.
- Si lead responde → conversación normal en Inbox, taggeada `campaign_id`.
- Attribution: ventas atribuidas a la campaña.

## Solución elegida (FOUNDATION.md decision)

Sales Agent extension non-breaking:
- Nuevo `OutboundOrchestrator` paralelo a `ChatOrchestrator`.
- AgentState: `campaign_id`, `campaign_instructions`, `outbound_mode` opcionales.
- `compose.py` nuevo slot `CAMPAIGN_CONTEXT`.
- Supervisor routing: `outbound_mode=True` → skip qualifier para score≥40.

## Solución alternativa (descartada)

- Reemplazar Sales Agent con "marketing agent" separado → descartado, fragmenta voz de marca y duplica brand voice load.
- Templates hardcoded → descartado, viola D2 (Sales Agent personaliza siempre).

## Canales (priorizados)

1. **Telegram** (MVP 1 — sin aprobación Meta) — PI-1 S3
2. **WhatsApp via ManyChat bridge** — PI-2
3. **WhatsApp WABA directo** — PI-3
4. **Instagram DM** — PI-3
5. **TikTok DM** — PI-2/3 (ver `tiktok-dm-automation.md`)

## Surface impactada

- BE: `sales_agent/application/orchestrator/` (nueva clase), `state.py` (3 fields), `compose.py` (slot), `nodes.py` (routing)
- BE: `campaigns/infrastructure/external/sales_agent_adapter.py` (bridge)
- DB: `campaigns` + `campaign_tasks` (Sprint 1)

## Riesgos

- Inbound reply recognition: ChatOrchestrator necesita detectar lead viene de campaña → buscar CampaignTask SENT últimas 24h. Decisión Sprint 1.
- Voz robotica si campaign_instructions mal escritas: educar emprendedor en copilot subagent (PI-2).

## Métricas

- # mensajes outbound enviados por campaña
- Response rate por campaña / canal
- Conversion attribution

## Links

- Research legacy: `docs/pm/campaigns/00-framework/campaign-types.md` §A
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` §1.2
- PI: `pis/PI-1-campaigns-module/PI.md` Sprint 3 (MVP 1)
