# Handoff prompt · S5 start

> **Refinado al cierre de S4 (2026-04-28).**

---

```
Continuamos redesign sales_agent.

📋 Plan: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S5 — Channel format registry (shared)
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
📝 Aprendizajes previos: learnings/S0, S1, S2, S3, S4.

CONTEXTO post-S4 (cerrado 2026-04-28):
- S4 cerrada: `domain/model_tier.py::SPECIALIST_TO_ROLE` (SSoT mapping). Closer→AGENT (Kimi K2.6 cache 75-83%), supervisor→NANO, qualifier/product_expert REASONING (DeepSeek V4 auto-cache disk-based). Arch test ratchet `tests/architecture/test_no_hardcoded_models_sales_agent.py` bloquea wire-name strings (`gpt-*`, `o3`, `o4-mini`, `claude-*`, `deepseek-*`, `kimi-*`, `moonshot-*`, `qwen*`, `gemini-*`) en `application/agents/sales/`. Sin allowlist.
- Hot wins activos via env vars: `AI_PROVIDER_AGENT=kimi` rutea closer; `AI_PROVIDER_REASONING=deepseek` rutea qualifier+product_expert.
- Branch: development limpio. Último commit S4: {HASH}
- Tests: 1639 verde (sales_agent + arch + admin + shared + copilot/observability).
- `MultiRoleLLMRouter` (singleton) + `ChatModelSpec` + `_kwargs.py::normalize_openai_protocol_kwargs` con `reasoning_token_reserve` ya activo cross-provider — S5 NO toca.

HOOKS LISTOS PARA S5:
- `shared/agent_observability/` módulo cohesivo (S0). Path target para S5 = `shared/agent_observability/channels/`.
- Copilot tiene `copilot/domain/output_channels.py` + `copilot/application/format_for_channel.py` + `channel_intent_detector` — primer movimiento S5 = decidir si se mueven a shared o se reescriben (anti-parche §2).
- Sales_agent `infrastructure/external/output_manager.py` (166 LOC, §3 protected `process_response` chunking + CPM_SPEED) — S5 puede refactor el lookup de canal sin tocar `process_response`.
- `compose_system_prompt` (S3) reserva slot 6 `CHANNEL_FORMAT_HINT` vacío — S5 lo puebla con registry data.

DEUDA REMANENTE para S5:
- DEFERRED-S5 (S3 learning): `agent_identity.j2` mezcla offer + channel rules. S5 extrae channel rules a `CHANNEL_FORMAT_HINT` slot via registry. Despois S7 extrae offer summary.
- DEFERRED-S5: `OutputManager` hardcoded por canal (chunk size, CPM, emoji policy en if-else) — refactor consume registry.
- DEFERRED-post-S6: `safety_service.py` + `chat.py:550` (summary) + `follow_up_engine.py:83` (nudge) NO consumen `SPECIALIST_TO_ROLE` SSoT — S5 NO los toca; S6 ratchet pass formaliza `LLM_ROLE_BY_SITE` expandido.
- DEFERRED-pre-Jul-2026: DeepSeek alias `deepseek-chat`/`deepseek-reasoner` retiran 2026-07-24 → tenant overrides `AI_MODEL_REASONING=deepseek-reasoner` rompen post-deadline. Sweep prod env vars + tenant configs antes.
- FLAGGED-S4: closer temp 0.4 declarado, Kimi clamp 0.6 server-side. Watchpoint conversion rate post-deploy.

PROTOCOLO:

1. Lee:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - 00-vision-and-objectives.md (§3 lo que NO se toca — `OutputManager.process_response` + webhooks NO se tocan)
   - 01-master-plan.md
   - 02-architecture-target.md (§3.5 channel registry shape)
   - 03-phase-protocol.md (10 pasos + Paso 11 code review)
   - 04-principles.md (§1.1 Strategy, §1.2 DRY, §1.4 acoplamiento)
   - 05-tech-debt-log.md (entradas DEFERRED-S5)
   - learnings/S0, S1, S2, S3, S4
   - phases/S5-channel-registry.md
   - audit/sales-agent-current-state.md (§3.5 OutputManager LOC + §3 protected)
   - .claude/rules/copilot-resilience.md (channel intent + output_channels patterns)

2. Research mandate S5 (mínimo 3 queries):
   - `WhatsApp Business API max message length 2026 markdown formatting`
   - `Telegram Bot API parse_mode MarkdownV2 escape characters 2026`
   - `Instagram Graph API DM message length emoji limit 2026`
   - `SMS GSM-7 character set Latin America accents segments 2026`
   - `Evolution API v2 message format payload 2026`

3. Documenta hallazgos en phases/S5-*.md sección "Hallazgos research".

4. TaskCreate granular.

5. TDD: tests RED primero.
   - `test_channel_registry`: `register_channel` idempotent + dup detection + `get_channel(unknown)` raises + bootstrap channels (`whatsapp`, `telegram`, `instagram_dm`, `web`, `evolution`) presentes.
   - `test_channel_format_dataclass_invariants`: frozen + slots + max_chars > 0 + chunk_size <= max_chars + typing_cpm cuando applicable.
   - `test_format_for_channel`: per channel — Telegram MarkdownV2 escape correct, WhatsApp markdown subset, IG DM no markdown, web markdown full, SMS pure ASCII fallback.
   - `test_output_manager_consumes_registry`: AST scan que verifica `OutputManager` invoca `get_channel(channel_id)` no hardcoded if-else.
   - `tests/architecture/test_no_hardcoded_channel_in_output_manager.py` (ratchet sin allowlist, mirror de `test_no_hardcoded_models_sales_agent`).
   - `test_compose_system_prompt_populates_channel_format_hint`: cuando `state.channel_type` set, slot 6 `CHANNEL_FORMAT_HINT` no vacío y aparece en cacheable prefix (antes de CACHE_BOUNDARY_MARKER).

6. Decisión clave (anti-parche): primero leer copilot/domain/output_channels.py + format_for_channel.py — decidir si se mueven a shared/agent_observability/channels/ (preferred) o se diseñan de cero. Si copilot tiene shape suficiente, mover; si tiene tech debt copilot-specific, abstract pattern + dejar copilot consumer.

7. Implementación step-by-step:
   - `shared/agent_observability/channels/format.py`: `ChannelFormat` dataclass frozen + slots (campos: id, label, max_chars, chunk_size, markdown_allowed, emoji_allowed, typing_simulation_cpm, structure_hint, parse_mode).
   - `shared/agent_observability/channels/registry.py`: `register_channel(fmt)` + `get_channel(channel_id)` + `CHANNELS: dict`.
   - `shared/agent_observability/channels/format_for_channel.py`: pure function (no LLM call) que aplica reglas del ChannelFormat al output text.
   - Bootstrap from `shared/infrastructure/agent_observability_bootstrap.py` (extender registry pasivo S2).
   - `OutputManager._lookup_channel_format(channel_id)` consume registry — NO hardcoded if-else.
   - `compose_system_prompt` Jinja `_channel_format_hint` builder lee `state.channel_type` + `get_channel(...).structure_hint`.

8. Quality gates nativos:
   - `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
   - `cd backend && .venv/bin/ruff format --check src/ tests/`
   - `cd backend && .venv/bin/pytest tests/modules/sales_agent/ tests/architecture/ tests/admin/ tests/shared/ tests/modules/copilot/observability/ -x -q --tb=short`

9. Verificación funcional:
   - 1 conversación dev sales_agent en canal Telegram. Output respeta MarkdownV2 escape (no `*` raw, no `_` raw — todos escaped).
   - WhatsApp dev: chunks <= max_chars; emoji_allowed honored.
   - §3 NO roto: `OutputManager.process_response` typing simulation + chunking intactos. Smart_debounce, follow_up, frozen_detection sin cambios.
   - Cache hit rate sales_agent_llm_call.cached_read_tokens segundo turn ≥60% mantenido (slot 6 ahora populado per-tenant cacheable, NO debería bajar hit rate; si baja → root cause).

10. Tech debt log: entrada para cualquier provider channel con quirk no documentado (ej. Evolution API v2 payload differente vs v1).

11. Code review final (Paso 11):
    - Callers no rotos: OutputManager methods públicos no cambian signature.
    - Cohesión: format/registry/format_for_channel cada uno UNA responsabilidad.
    - Acoplamiento: shared/agent_observability/channels/ NO importa src.modules.* (arch test purity ya activo).

12. Cierre:
    - learnings/S5-*.md (denso, accionable).
    - prompts/S6-start.md refinado con context fresco.
    - README estado fase ✅.
    - Mark FIXED entradas DEFERRED-S5 que se resolvieron.

13. Commit: `feat(sales-agent-redesign-s5): channel format registry shared + OutputManager refactor`

PRINCIPIOS:
- TDD: tests RED primero.
- Anti-parche: copilot output_channels existente — leer antes de redesign. Si shape OK, mover; si no, abstract pattern + flag.
- Best-effort: registry register_channel idempotente; bootstrap not crash si dup.
- Tenant isolation: ChannelFormat es global (no PII) — sin tenant_id filter necesario.
- Stage por nombre en commits.
- Cada tenant tiene su propia voz — pero el formato del canal (max_chars, parse_mode) es universal por canal, NO per-tenant.
- Spanish neutro LATAM en cualquier user-facing copy del format_for_channel (ej. fallback messages "mensaje cortado por longitud").
- §3 protected: `OutputManager.process_response` + webhooks NO se tocan.

Empieza con paso 1.
```
