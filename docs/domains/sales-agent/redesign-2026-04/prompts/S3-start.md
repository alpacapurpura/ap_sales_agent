# Handoff prompt · S3 start

> **Refinado al cierre de S2 (y S4 si fue paralelo).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S3 — Prompt cache_boundary refactor
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
📝 Aprendizajes: learnings/S1-*, learnings/S2-*, learnings/S4-* (si cerrada).

CONTEXTO:
- S1 + S2 + S4 cerradas (S4 idealmente).
- Cache hit rate sales_agent actual: ~0% (Jinja render fresh per turn).
- Target post-S3: ≥60%.
- Branch: development limpio.
- Último commit: {HASH}
- Hooks: SalesAgentCallbackHandler captura cached_read_tokens, model_tier definido (S4), CHAT_MODEL_SPEC per provider.
- Tech debt en radar: {LIST}

PROTOCOLO:
1. Lee README + 00 (§3) + 01 + 02 + 03 + 04 + 05 (DEFERRED-S3) + learnings/S1, S2, S4 + phases/S3.
2. Research mandate: OpenAI prompt caching threshold 1024 tokens 2026, Anthropic cache_control blocks 2026, LangChain SystemMessage cache compatibility cross-provider, prompt engineering progressive disclosure.
3. Lectura: copilot graph.py build_system_prompt (F8 implementación), specialist *.j2 actuales, PromptLoader, learnings/F8 de copilot.
4. TaskCreate.
5. TDD:
   - test_compose_system_prompt: 2 SystemMessages, slot order correcto.
   - test_no_volatile_in_cacheable.
   - test_prompt_version_override_placement.
   - test_cache_prefix_size ≥1024 tokens (con tiktoken).
   - tests/architecture/test_sales_agent_system_prompt_order.
6. Refactor specialists nodes.py para usar compose_system_prompt(state).
7. Quality gates nativos.
8. Deploy dev + medir 24h: cached_read_tokens / input_tokens en sales_agent_llm_call.
9. §3 sigue funcionando.
10. Tech debt log.
11. learnings/S3-* + prompts/S4-start.md (si S4 no cerró aún) o S5-start.md refinado.

PRINCIPIOS: TDD, anti-parche. Si goldens existentes fallan tras refactor, investiga root cause antes de regenerar UPDATE_GOLDEN=1 — pueden estar revelando bug real.

Empieza con paso 1.
```
