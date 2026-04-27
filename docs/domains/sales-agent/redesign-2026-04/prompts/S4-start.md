# Handoff prompt · S4 start

> **Refinado al cierre de S1 (S4 puede ir paralelo a S2/S3 si recursos).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S4 — ChatModelSpec + tier adoption
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S4-chatmodelspec-tier.md
📝 Aprendizajes: learnings/S1-*.md.

CONTEXTO:
- S1 cerrada: callback handler graba provider/model_responded.
- Ya existe en codebase: providers/_kwargs.py (post-incidente 2026-04-27), CHAT_MODEL_SPEC en copilot.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: providers/_kwargs.py::normalize_openai_protocol_kwargs SSoT.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 + learnings/S1 + phases/S4.
2. Research mandate: OpenAI o3/o4 reasoning kwargs 2026, Anthropic Claude 4.7 max_tokens cache, DeepSeek protocol diff 2026, Gemini maxOutputTokens.
3. Lectura: shared/infrastructure/llm/factory.py, providers/_kwargs.py, providers/openai_compat.py, copilot/domain/model_tier.py, commits 7dcc5db4, c60197fa, dfc57716, 222bd54a.
4. TaskCreate.
5. TDD:
   - test_model_tier_resolution.
   - test_kwargs_normalizer_sales (cross-provider).
   - test_no_hardcoded_models_in_sales_agent (AST scan).
   - test_provider_agnostic_kwargs.
6. Implementar domain/model_tier.py + ROLE_TO_TIER mapping.
7. Refactor specialists para usar tier semantic.
8. Quality gates.
9. §3 sigue funcionando.
10. Tech debt log.
11. learnings/S4-* + prompts/S3 / S5 refinado según orden ejecución.

PRINCIPIOS: SSoT (CHAT_MODEL_SPEC en provider, no per-agent), DRY, TDD.

Empieza con paso 1.
```
