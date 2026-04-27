# Handoff prompt · S8 start

> **Refinado al cierre de S7.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S8 — Tools: Scheduler integration (booking link + verify + follow-up)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S8-tools-scheduler.md
📝 Aprendizajes: learnings/S7-*.md.

CONTEXTO:
- S7 cerrada: agente habla voz de marca via brand_voice_summary lighthouse en slot 4.
- Sales_agent ya tiene tool_check_schedule básico (scheduling check).
- scheduling module existe. connections module ya autentica con calendar providers.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: compose_system_prompt slot 4 con brand voice, ChannelFormat registry, callback handler con cost.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S7 + phases/S8.
2. Research mandate: Cal.com API booking link tracking 2026, Google Calendar API 2026 auth, Calendly webhooks 2026, LATAM time zones meeting UX, sales reminder cadence T-24h/T-1h.
3. Lectura: scheduling module entero, connections (calendar auth), follow_up_engine, closer_studio_service, sales tools.py + enrollment_tools.py (patrones existentes).
4. TaskCreate.
5. TDD:
   - test_create_booking_link (provider strategy + idempotency)
   - test_verify_booking_status
   - test_scheduler_webhooks (signature + idempotency replay)
   - test_verify_pending_bookings_task
   - test_follow_up_reminders_with_brand_voice (mensaje contiene summary_text)
   - test_scheduler_provider_strategy (Protocol compliance)
6. Strategy pattern: SchedulerProvider Protocol + Cal.com / Google Calendar / Calendly impls.
7. Migración: lead_meeting o JSONB en agent_state_checkpoint.scheduled_meetings.
8. Tools en sales_agent/application/tools/scheduling/.
9. Webhook handlers con signature verification.
10. ARQ task verify_pending_bookings (cada 15min).
11. Extender follow_up_engine para reminders T-24h/T-1h/T+1h.
12. Stage scoping en tools/registry.py.
13. UI Closer Studio: meetings tab.
14. Quality gates.
15. Smoke live: lead reserva en provider sandbox → event + reminders.
16. §3 sigue funcionando.
17. Tech debt log.
18. learnings/S8-* + prompts/S9-start.md refinado.

PRINCIPIOS:
- Strategy pattern para providers (NO hardcodear Cal.com).
- Idempotency natural key.
- Anti-parche: si scheduling no expone semantic correcta → coordinar con dueño módulo, NO shadow API.

Empieza con paso 1.
```
