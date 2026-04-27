# Handoff prompt · S5 start

> **Refinado al cierre de S0 + S4.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S5 — Channel format registry (shared)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
📝 Aprendizajes: learnings/S0-*.md, learnings/S4-*.md.

CONTEXTO:
- S0 cerrada: shared/agent_observability/ existe.
- Copilot ya tiene output_channels.py + format_for_channel + channel_intent_detector — extraer a shared.
- Sales_agent OutputManager hardcoded por canal — refactor.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: shared/agent_observability/ módulo.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S0, S4 + phases/S5.
2. Research mandate: WhatsApp Business API limits 2026, IG DM markdown 2026, Telegram parse_mode 2026, SMS GSM-7 LATAM accents.
3. Lectura: copilot output_channels.py, format_for_channel.py, channel_intent_detector.py, sales_agent OutputManager.py, channel_resolver.py.
4. TaskCreate.
5. TDD:
   - test_channel_registry: register dup, fallback, bootstrap channels.
   - test_format_for_channel: WA/Telegram/IG/SMS.
   - test_output_manager_uses_registry.
   - test_no_hardcoded_channel_in_output_manager (AST).
6. Implementar shared channels module + bootstrap.
7. Refactor OutputManager.
8. Wire format_for_channel como always-available tool en sales_agent.
9. Quality gates.
10. Smoke webhook real Telegram dev: mensaje generado respeta MarkdownV2.
11. §3 sigue funcionando.
12. Tech debt log.
13. learnings/S5-* + prompts/S6-start.md refinado.

PRINCIPIOS: Strategy pattern (channels), DRY (extract a shared), single responsibility (registry no mezcla auth/signature).

Empieza con paso 1.
```
