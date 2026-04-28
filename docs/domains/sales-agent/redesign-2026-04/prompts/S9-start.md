# Handoff prompt · S9 start

> **Refinado al cierre de S8 (2026-04-28).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S9 — Tools: Payment lifecycle + grant access
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S9-tools-payment-access.md
📝 Aprendizajes obligatorios: learnings/S7-brand-voice-integration.md + learnings/S8-tools-scheduler.md.

CONTEXTO:
- S7 + S8 cerradas. Sales_agent habla voz de marca (slot 5 SSoT) + tiene scheduler tools end-to-end.
- enrollment_tools.py ya tiene `generate_payment_link` + `mark_enrollment_paid_manual` básicos (fallback a checkout_page_url estático). NO duplicar — extender via Strategy o refactor cohesivo.
- connections module ya autentica con email/manychat/gmail/calendar. AccessProvider interface NO existe — crear en S9.
- Branch: `development` limpio. Multi-instancia paralela activa (analytics commits coexisten — staging por nombre obligatorio).
- Último commit S8: {HASH-S8}.
- Hooks listos S8 reutilizables:
  * `SchedulerProvider` Strategy + Protocol pattern (mirror para `PaymentProvider`).
  * `WebhookProvider` Protocol + endpoint genérico registry-driven (mirror para payment webhooks).
  * `MeetingStateService` SSoT JSONB (mirror para `PaymentStateService`).
  * `shared/links/ports/scheduling.py` helpers (mirror para `shared/links/ports/payment.py`).
  * `appointment_reminder_engine` voz-de-marca pattern (mirror para payment reminders).
  * `LLM_ROLE_BY_SITE['appointment_reminder_*']=NANO` mental model (NANO + slot 5 cache_key=tenant_id).
  * Webhook dedup table pattern con UNIQUE (provider, tracking_id, event_type, occurred_at).

TECH DEBT EN RADAR (de S8 closeout, ver 05-tech-debt-log.md):
- DEFERRED-S9 — webhook signing secret stub env-var → promover a per-tenant `connections.ChannelConnectionModel.config` lookup en S9 wiring real (MP/Stripe).
- DEFERRED-S11 — `BookingLink.tenant_id` column no declarada en SA model (helper actual lo descarta). NO blocker para S9. NO empeorar.
- DEFERRED-S+1 — Closer Studio FE meetings tab. Coordinar con S9 closeout para diseñar tab conjunto meetings + payments.
- FLAGGED — multi-tenant signing patrón pendiente (S9 lo resuelve para payment + retroalimenta scheduler en S11).

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S7 + learnings/S8 + phases/S9. Re-lectura completa, no salto.
2. Research mandate (queries 2026 obligatorias):
   - Mercado Pago API 2026 webhook signature x-signature header validation.
   - Stripe Payment Links API 2026 + checkout session.
   - Idempotency keys SaaS payment 2026 best practices.
   - LATAM payment providers Pix Brazil / Khipu Chile / Mach (Bcp Peru) / Yape 2026.
   - Digital product access automation (Memberstack / Lemon Squeezy / Whop 2026).
3. Lectura code obligatoria:
   - `src/modules/sales_agent/application/agents/sales/enrollment_tools.py` (NO duplicar).
   - `src/modules/sales_agent/domain/enrollment.py` + `enrollment_service.py` + `enrollment_repository.py`.
   - `src/modules/connections/api/{whatsapp,gmail,manychat}.py` (entry-point para grant_access).
   - `src/modules/offer/domain/` schema (auto_grant_on_payment flag, currency, payment_provider hint).
   - `src/modules/sales_agent/application/tools/scheduling/` (S8 — patrón a mirror).
   - `src/modules/sales_agent/api/scheduler_webhooks.py` (S8 — patrón a mirror).
4. TaskCreate granular (target ≤4h por task).
5. TDD RED→GREEN obligatorio:
   - test_create_payment_link (idempotency + metadata + currency desde offer SSoT).
   - test_verify_payment_status (mapping pending/paid/failed/refunded/expired).
   - test_grant_access_idempotent (natural key (tenant_id, lead_id, offer_id, payment_id) UNIQUE).
   - test_payment_webhook_signature_verify (MP / Stripe signing differences).
   - test_payment_webhook_dedup_replay (UNIQUE constraint on payment_webhook_event).
   - test_verify_pending_payments_task (ARQ cron expira + emite eventos).
   - test_auto_grant_on_paid_subscriber (offer.auto_grant_on_payment=true → fire grant_access).
   - test_payment_audit_immutable (no UPDATE en payment_grant_audit — append-only).
   - test_grant_access_saga_partial_failure (email ok + manychat fail → registra parcial + retry).
   - test_payment_provider_strategy (Protocol compliance via arch test).
   - test_no_hardcoded_payment_provider (arch test bloquea inline branches).
6. Strategy pattern obligatorio:
   - `PaymentProvider` Protocol + dataclasses (`PaymentLinkOutput`, `PaymentStatus`, `RefundReceipt`).
   - `MercadoPagoPaymentProvider` impl (LATAM primary).
   - `StripePaymentProvider` impl (international).
   - `SCHEDULER_PAYMENT_PROVIDERS` registry + `payment_provider_for_tenant(db, tenant_id)`.
   - `WebhookProvider` mirror para signing verify per-provider.
7. Migración Alembic idempotente (raw SQL `IF NOT EXISTS`):
   - `payment_link` table (id, tenant_id, lead_id, offer_id, provider, external_id, url, status, currency, amount, expires_at, metadata JSONB, created_at).
   - `payment_grant_audit` (id, tenant_id, lead_id, offer_id, payment_id, channels JSONB, granted_at, append-only). UNIQUE natural key.
   - `payment_webhook_event` (id, provider, external_id, event_type, occurred_at, tenant_id, lead_id, payload_raw, received_at). UNIQUE natural key.
   - `agent_state_checkpoints.payment_state` JSONB column.
8. Tools en `src/modules/sales_agent/application/tools/payment/`:
   - `create_payment_link` (idempotency: re-fire en mismo turn → reuse).
   - `verify_payment_status`.
   - `grant_access` (delega a AccessProvider per offer.access_channels).
9. Webhook handler `POST /api/v1/sales-agent/webhooks/payment/{provider}` con signature MANDATORY (no skip env-var). Per-tenant secret lookup `connections.ChannelConnectionModel.config`.
10. ARQ task `verify_pending_payments` (cron 15min, offset de scheduler crons para no stackear).
11. Subscriber `auto_grant_on_paid` opt-in via `offer.auto_grant_on_payment` flag — saga pattern para multi-channel access (email + manychat + lms). Partial failure logged + retry.
12. AccessProvider interface en `shared/links/ports/access.py` — adapters concretos en connections module.
13. Extender `STAGE_TOOL_SCOPE` (closing): create_payment_link, grant_access. verify_payment_status → ALWAYS_AVAILABLE.
14. Reminder engine extension (T-2h post-link sin pagar): nuevo template `payment_pending_reminder.j2` + LLM call NANO + `prompt_cache_key=tenant_id` (S7 rule). Mismo `appointment_reminder_engine` o nuevo `payment_reminder_engine` separado (decidir por cohesión — recomiendo separado).
15. Cron retry `grant_access_retry_task` para casos saga partial failure persistentes.
16. UI Closer Studio: agregar tabs `payments` + `access_grants` (coordinar con DEFERRED-S+1 meetings tab — diseñar tab conjunto meetings/payments/grants).
17. Quality gates obligatorios:
   - Native: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache` (S9 files clean).
   - Native: `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/architecture/ -x -q --tb=short`.
   - Migration verify clone + re-run idempotency.
   - PII sanitize webhook payloads (CC last4, expiration date, CVV blocked).
18. Smoke live MP sandbox: lead reserva → paga → webhook recibido + dedup activo + grant_access auto + audit row + acceso real entregado (email + manychat).
19. §3 sigue funcionando: smoke `/sales/studio/inbox` + closer_studio + buffer + output_manager + enrollment + agent_state_checkpoint + webhooks Telegram/WhatsApp/IG + follow_up_engine + frozen_detection. Verify después de cada commit.
20. Tech debt log: si enrollment_tools.py duplica functionality (`generate_payment_link`, `mark_enrollment_paid_manual`, `check_payment_status`) → DRY refactor + deprecation o FLAG con plan migración. NO ignorar.
21. learnings/S9-tools-payment-access.md (denso, accionable, sin filler) + prompts/S10-start.md refinado con hooks listos para quality eval loop.

PRINCIPIOS NO NEGOCIABLES:
- Strategy pattern para payment providers (NO hardcodear MP/Stripe).
- Idempotency natural key UNIQUE en `payment_grant_audit` — append-only, no UPDATE.
- Saga pattern para multi-channel grant_access — partial failure registrada + retry.
- PII sanitization en webhook payloads (CC last4, expiration, CVV blocked).
- Currency desde `offer` SSoT, NO inferir desde provider.
- Webhook signature verify MANDATORY (no skip por env var faltante — fail-closed con 401).
- Brand voice slot 5 SSoT — payment messages heredan voz tenant via `prompt_cache_key=tenant_id`.
- Tenant isolation en cada query — `tenant_id` filter obligatorio.
- Anti-parche: si enrollment_tools.py duplica → DRY refactor + plan deprecación. NO ignorar.
- Spanish neutro LATAM en mensajes default; respeta voz tenant.
- Stage scoping: payment tools primarily closing — verify_status ALWAYS_AVAILABLE.
- Coordinación S+1 FE: meetings tab (S8 deferred) + payments tab (S9) diseñar conjunto.

Empieza con Paso 1 (re-lectura completa), reportá hallazgos críticos antes de codear.
```
