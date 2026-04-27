# Handoff prompt · S9 start

> **Refinado al cierre de S8.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S9 — Tools: Payment lifecycle + grant access
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S9-tools-payment-access.md
📝 Aprendizajes: learnings/S7-*.md, learnings/S8-*.md.

CONTEXTO:
- S7 + S8 cerradas.
- enrollment_tools.py ya tiene generate_payment_link + mark_paid básicos. Refactor a strategy pattern + extender.
- connections module entrega acceso (email, manychat, lms).
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: compose_system_prompt slot 4 brand voice, scheduler tools (S8 patrón).
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S7, S8 + phases/S9.
2. Research mandate: Mercado Pago API 2026 webhook signature, Stripe Payment Links 2026, idempotency keys SaaS 2026, LATAM payment providers (Pix, Khipu, Mach), digital product access automation.
3. Lectura: enrollment_tools.py + enrollment.py + enrollment_service.py + connections/ + offer/ schema.
4. TaskCreate.
5. TDD:
   - test_create_payment_link (idempotency + metadata)
   - test_grant_access_idempotent (natural key)
   - test_payment_webhooks (signature + replay)
   - test_verify_pending_payments
   - test_auto_grant_on_paid (offer.auto_grant_on_payment flag)
   - test_payment_audit_immutable (no UPDATE)
6. Strategy pattern: PaymentProvider Protocol + MercadoPago / Stripe impls.
7. Migración: payment_link, payment_grant_audit (con unique index natural key).
8. Tools create_payment_link / verify_payment_status / grant_access.
9. Webhook handlers con signature MANDATORY.
10. ARQ task verify_pending_payments.
11. Subscriber auto_grant_on_paid (opt-in per offer).
12. Extender connections para AccessProvider interface.
13. UI Closer Studio: payment + access tabs.
14. Quality gates.
15. Smoke live: MP sandbox → pagar → verify auto-grant + acceso entregado.
16. §3 sigue funcionando.
17. Tech debt log: si enrollment_tools.py duplica funcionalidad → DRY refactor o flag.
18. learnings/S9-* + prompts/S10-start.md refinado.

PRINCIPIOS:
- Idempotency natural key (tenant_id, lead_id, offer_id, payment_id) UNIQUE.
- Auditoría append-only (no UPDATE en payment_grant_audit).
- Saga pattern para grant_access multi-channel (email + manychat + lms).
- PII sanitization en webhooks (CC last4, etc.).
- Currency desde offer SSoT, no inferir.

Empieza con paso 1.
```
