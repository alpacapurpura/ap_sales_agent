# Handoff prompt · S7 start

> **Refinado al cierre de S3 + S6.**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S7 — Brand voice integration ("Estilo Comunicacional")
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S7-brand-voice-integration.md
📝 Aprendizajes: learnings/S3-*.md, learnings/S6-*.md.

CONTEXTO:
- S3 cerrada: compose_system_prompt con cache_boundary y slot 4 reservado para lighthouse.
- S6 cerrada: ratchet evita drift.
- Brand Studio: campo "Estilo Comunicacional" {EXISTE? — verificar nombre exacto en research}.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: slot 4 reservado en compose.py, brand domain events bus.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S3, S6 + phases/S7.
2. Research mandate: brand voice prompt eng style transfer 2026, prompt cache invariance per-tenant, do/don't list LLM.
3. Lectura PRIMERO: brand domain schema completo + frontend brand-studio schemas — VERIFICAR nombre exacto del campo "Estilo Comunicacional". Si NO existe → ESCALAR al usuario (puede requerir fase Brand Studio extra), NO crear campo en S7.
4. Lectura: copilot brand_summary.py + F3 implementation + skill brand-expert.
5. TaskCreate.
6. TDD:
   - test_brand_voice_summary_regen (hash short-circuit)
   - test_lighthouse_in_slot_4
   - test_brand_voice_differentiation (tenant A vs B)
   - test_voseo_respected_per_tenant (excepción documented)
   - test_brand_voice_summary_cache_invalidation
7. Migración: brand_voice_summary table idempotente.
8. ARQ task regenerate_brand_voice_summary + subscriber a BrandVoiceUpdatedEvent.
9. Implementar _agent_identity_lighthouse en compose.py slot 4.
10. Goldens nuevos: tenant fixture formal vs casual con voseo.
11. Quality gates.
12. §3 sigue funcionando.
13. Tech debt log.
14. learnings/S7-* + prompts/S8-start.md refinado.

PRINCIPIOS: SSoT (brand_voice vive en brand/, no en sales_agent/), alta cohesión, anti-parche (NO crear campo si no existe → escalar).

Empieza con paso 1.
```
