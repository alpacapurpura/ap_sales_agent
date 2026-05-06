# Manual Test Checklist — S3 MVP Telegram

> Owner: Chris (manual gate). Ejecutar una vez post-merge PR-7+PR-8+PR-9 contra staging real.
> Status: pending Chris execution

## Objetivo

Verificar end-to-end visible que MVP S3 Telegram outbound funciona con:
- 5+ contactos reales reciben mensaje sales_agent personalizado.
- Lead que responde aparece en Inbox con tag `campaña: {name}`.
- Stats endpoint reporta `sent_count >= 5` + `responded_count >= 1`.

## Pre-flight staging

- [ ] dev-app.nicolify.com OR staging URL reachable (Cloudflare tunnel up).
- [ ] Telegram bot connected: `/conexiones/telegram` shows status connected.
- [ ] 5+ contactos staging tenant tienen `telegram_id` valid (verify via `/sales/contactos` o DB query `SELECT id, telegram_id FROM leads WHERE tenant_id = X AND telegram_id IS NOT NULL LIMIT 10;`).
- [ ] Brand Studio personality_profile.system_instruction configurado: verify `/brand-studio/estilo` shows non-empty voice config.
- [ ] Offer activa con title + price + description: verify `/offer-studio` shows at least 1 active offer.
- [ ] BudgetGuard plan_config tier upper-bound suficiente para 5+ outbound LLM calls (~$0.05 each).

## Crear campaña

- [ ] Navigate `/campañas/nuevo` (o usar API directly si UI no existe aún).
- [ ] Name: "Test S3 MVP — {fecha YYYY-MM-DD}"
- [ ] Type: `AGENT_CONVERSATION`
- [ ] Description: brief operacional ("Test smoke MVP S3 — Chris validation").
- [ ] Save campaign as DRAFT.

## Add segment + step

- [ ] Add manual segment con 5+ contactos selected (los pre-flight verificados).
- [ ] Add 1 step `CALL_SUBAGENT_BRIEF` con `step_config.brief`:
  > "Saludá al lead, presentate breve sin sonar guión, ofrecé una reunión de 15 minutos para conocer su negocio. No hables de precio salvo que lo pregunte."

## Schedule

- [ ] Set `scheduled_at` = now + 5min (margen para cron tick).
- [ ] Save → campaign FSM transition DRAFT → SCHEDULED.

## Trigger

- [ ] Wait 5min (cron `run_campaign_scheduler_tick` corre en minute={5,15,25,35,45,55} offset).
- [ ] Monitor backend logs: `docker logs visionarias_brain_dev --tail 200 -f | grep -E "campaign_task|outbound_orchestrator"`.
- [ ] Verify log lines `campaign_orchestrator_launched` + `campaign_task_sent` per lead.

## Verify outbound delivery

- [ ] 5+ contactos reciben Telegram message (verify chat history o pedir confirmación contactos).
- [ ] Mensaje respeta brand voice tenant:
  - [ ] No suena robótico (variación natural turn-by-turn).
  - [ ] No hay tono LiteLLM-default (genérico/inglés).
  - [ ] Tono coherente con personality_profile (verbalidad, formalidad, idiom).
  - [ ] Spanish neutro LATAM (excepto si tenant es AR — voseo permitido per voz tenant).
  - [ ] Brief campaign instructions reflected ("ofrece reunión 15min", "no hables precio").
- [ ] Sin duplicados: cada contacto recibe SOLO 1 mensaje (idempotency).

## Verify inbound recognition (1+ lead responde)

- [ ] Lead responde Telegram message (within 24h window).
- [ ] Conversation aparece en `/inbox` con tag chip "campaña: Test S3 MVP — {fecha}".
- [ ] Click chip → navigate `/campañas/{id}` (placeholder route OK PR-9; actual page S4/PI-3).
- [ ] sales_agent responde al lead con voice fidelity preservada.
- [ ] Si lead score ya >= 40 (campaign fixture pre-seed) → supervisor skip qualifier → directo a closer (verify log `node_sales_supervisor` skip line).

## Verify stats endpoint

- [ ] `curl -H "X-Tenant-ID: <staging>" https://staging-api.nicolify.com/api/v1/campaigns/{id}/stats`
- [ ] Response shape correcto:
  - [ ] `campaign_id` matches.
  - [ ] `total_tasks >= 5`.
  - [ ] `sent_count >= 5`.
  - [ ] `responded_count >= 1` (si lead respondió).
  - [ ] `response_rate >= 0.20` (1/5+).
  - [ ] `currency` reflejando tenant locale (PEN / USD / MXN / ARS / etc).
  - [ ] `converted_count = 0` con `attribution_method = "deferred_pr_followup"` (expected MVP S3 — refine PR follow-up).

## Cleanup

- [ ] Cancelar campaign via UI o API (POST `/api/v1/campaigns/{id}/cancel`).
- [ ] Verify FSM transition → CANCELLED.
- [ ] Reportar resultados al PM con:
  - Screenshots Telegram messages recibidos.
  - Screenshot Inbox tag chip.
  - JSON response stats endpoint.
  - Log lines clave (`campaign_task_sent` count + `inbound_campaign_recognized` count).

## Issues encontrados

(Log durante ejecución manual.)

| ID | Issue | Severity | Fix sprint |
|---|---|---|---|
| - | - | - | - |

## Verdict S3 MVP

- [ ] PASS — MVP S3 Telegram outbound funcional end-to-end. PI-1 cierre.
- [ ] WARN — funcional con friction; sub-issues no bloqueantes (loggeados arriba).
- [ ] FAIL — bug crítico bloquea ship; create follow-up PR pre-merge.
