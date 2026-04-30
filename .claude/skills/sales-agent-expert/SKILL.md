---
name: sales-agent-expert
description: "Senior + arquitecto + CTO del módulo sales_agent post redesign 2026-04. Carga §3 protected surfaces, anti-patterns, decisiones cross-fase, checklist pre-commit. NO carga code vivo (paths/LOC/tests cambian). Use cuando user pida cambio/feature/bug en sales_agent: voz de marca, scheduler/payment tools, observabilidad, callback handler, prompt cache, channel registry, semantic router, closer studio, follow_up engine, eval loop, costo agentes. Triggers: 'modifica sales_agent', 'bug en sales_agent', 'agregar tool al agente', 'agente no cierra', 'suena robótico', 'voz de marca', 'agregar canal sales', 'modificar prompt del specialist', 'closer studio', 'follow-up no dispara', 'el agente repite preguntas', 'PII en trazas', 'costo Kimi', 'DeepSeek alias', 'tier pricing 200k', 'eval goldens'."
---

# Sales Agent Expert (post redesign 2026-04)

Antes de codear: skill + plan + tech-debt-log. Plan: `docs/domains/sales-agent/redesign-2026-04/README.md` (S00–S12 cerrado).

## §3 — NO se toca

| Surface | Razón |
|---|---|
| `closer_studio.py` API + WS | Live ops + Streamlit + FE dependen. |
| `BufferService.smart_debounce` | CPM/canales LATAM tuned producción. |
| `OutputManager.process_response` chunking | CPM_SPEED + cap calibrados. `typing_simulation_cpm` per-canal lo extiende vía registry (S12), fallback global preservado. |
| `enrollment_*` end-to-end | Producción. S9 EXTIENDE. |
| `agent_state_checkpoint` schema | Migración riesgosa. |
| Webhook adapters (Telegram/WhatsApp/IG) | Auth + signature frágiles. |
| `follow_up_engine` cadence math | Timing horario + tz tenant. |
| `PromptVersionModel` | Sales necesita override DB-backed per tenant. |
| `model_pricing_snapshot` schema + LiteLLM sync | Cross-agent. Solo extender via raw_payload. |
| `tool_call_dedup.py` | Anti-loop post fbc79125. |

Tocar §3 → **PARAR, preguntar al usuario**.

## Antes de codear (orden estricto)

1. **Trazas primero**. Bug → query `sales_agent_trace_event` + `sales_agent_llm_call`. Sin traza del síntoma → bug del recorder, fix antes que el síntoma.
2. **Plan + tech-debt-log + learnings**. Decisiones cross-fase viven en `learnings/S{0..12}-*.md`.
3. **grep AST de surface**, no asumir. Paths cambian; SSoT no.
4. Ambiguo → **preguntar antes de tocar**.

## Anti-patterns (cerrados)

- ❌ Migrar StateGraph a deepagents.
- ❌ Eliminar Closer Studio + WS + buffer + OutputManager + follow_up_engine + frozen_detection.
- ❌ Subagents deepagents.
- ❌ Hardcodear model wire-name strings en specialists. Usar `LLM_ROLE_BY_SITE` SSoT.
- ❌ Hardcodear canales literales en `OutputManager`. Usar `get_channel_format(channel_type)`.
- ❌ Importar `copilot/` desde `sales_agent/` (o viceversa). Ambos consumen `shared/`.
- ❌ Tocar `PromptVersionModel`.
- ❌ `from __future__ import annotations` en `*/orchestrator/graph.py` (rompe LangGraph runtime introspection).
- ❌ Bypass `sanitize_payload` en writes a `*_trace_event` o `*_llm_call`.
- ❌ Duplicar plumbing del `BaseAgentCallbackHandler` shared. Solo overrides agent-specific.
- ❌ Bypass channel registry shared. Nuevo canal → `register_channel` en startup.
- ❌ Crear feature branches/worktrees salvo instrucción explícita. Todo en `development`.
- ❌ Aliases DeepSeek retired Jul 24 2026 (`deepseek-chat`, `deepseek-reasoner`). Usar `deepseek-v4-flash` / `deepseek-v4-pro`. Arch ratchet bloquea.
- ❌ Tier pricing >200k tokens sin resolver. Si LiteLLM declara `input_cost_per_token_above_200k_tokens`, calculator debe split (`TIER_THRESHOLD = 200_000`). Arch ratchet.

## Decisiones cross-fase no obvias

- **`BaseAgentCallbackHandler` Template Method (S0/S11A)** — subclase implementa solo `_persist_llm_call_row` + `_persist_trace_event_row`. DRY threshold = 2 consumers (sales + copilot).
- **`compose_system_prompt(fragments)` + `CACHE_BOUNDARY_MARKER` (S3)** — slots cacheable cross-tenant → cacheable per-tenant → volatile. Hit rate ≥60% si prefix ≥1024 tokens.
- **`model_pricing_snapshot` cross-agent en `shared/`** — reference data global. Tier pricing >200k via raw_payload JSONB.
- **Dual-write 4 sem pre-cutover legacy** — reconciliation worker mide drift; cutover prematuro rompe `sales_audit.py` dual-read.
- **`LLM_ROLE_BY_SITE` superset + `SPECIALIST_TO_ROLE` sub-view** — specialists back-compat; summary + nudge + safety centralizados.
- **Tenant isolation en CADA query** (incluido `get_by_id`).
- **`FastAPI(redirect_slashes=False)`** — Next.js proxy strips body en 307. App-level only.
- **PII regex sync (no Presidio) — WONT-FIX (S12)** — Presidio overhead 50-200ms incompatible con hot path <10ms p99. Reabrir solo con enterprise contract.
- **typing_simulation_cpm (S12)** — registry override per-canal, fallback `CPM_SPEED` cuando None / 0 / negativo.
- **Voz del agente — voseo del tenant respetado** — `.claude/rules/spanish-text.md` NO aplica al output del agente. Voseo del tenant es feature.

## SSoT vivos

| Concepto | Dónde mirar |
|---|---|
| Voz del agente | `personality_profiles.system_instruction` → slot 5 cache prefix |
| Specialist→role | `domain/model_tier.py::SPECIALIST_TO_ROLE` + `LLM_ROLE_BY_SITE` |
| Channel format | `shared/agent_observability/channels/format.py::CHANNEL_FORMATS` + `get_channel_format` |
| Pricing | `model_pricing_snapshot` + `pricing/aliases.py` + `pricing/resolver.py` |
| Tools | `application/tools/registry.py` + `STAGE_TOOL_SCOPE` |
| Routing log | `sales_agent_routing_log` → Streamlit `/sales-routing` (S12) |
| Quality eval | `SalesAgentJudge` + 20 goldens + cron weekly → `/sales-agent-quality` |
| Costo cross-agent | `mv_daily_llm_cost_per_tenant_v2` → `/costo-agentes` |

## Checklist pre-commit "senior dev pass"

1. ¿Toca §3? → escalé al usuario.
2. ¿Test reproductor antes del fix? RED → GREEN.
3. ¿Pasa por SSoT (channels / models / pricing / LLM_ROLE / personality)?
4. ¿`sanitize_payload` en cada write a observability tables?
5. ¿`tenant_id` filter en CADA query?
6. ¿`response_model=` en endpoint nuevo? PII removido / mascarado / justificado.
7. ¿Spanish neutro LATAM en user-facing? Voz del tenant respetada en output del agente.
8. ¿Stage por nombre en commit (no `-A` ni `.`)?
9. ¿Arch tests verde native?
10. ¿Tech-debt-log actualizado? Cada entry → fase concreta o WONT-FIX con razón.

## Glossary

- **turn**: 1 webhook/POST. 1 `turn_start` + 1 `turn_end` + N `llm_call`/`tool_call`.
- **callback handler**: `BaseAgentCallbackHandler` + subclase. Best-effort (try/except + structlog warning + rollback).
- **LLM_ROLE_BY_SITE**: SSoT site → `ModelRole`. Arch ratchet sin allowlist.
- **channel registry**: `register_channel` + `get_channel_format` cross-agent. 7 baseline.
- **specialist**: Nodo StateGraph (qualifier / product_expert / closer / supervisor / tool_executor / safety / escalate).
- **dual-write**: Escribir legacy + nueva durante 4 sem. Cutover post-window.
- **ratchet**: Test que solo permite shrink.
- **Stranger Fig**: Refactor incremental, snapshot diff = 0 byte-equal per commit.
- **§3**: Surfaces protegidas. Tocar = preguntar.
- **Tier pricing**: LiteLLM `input_cost_per_token_above_200k_tokens`. Calculator split en 200_000 (S12).

## Pointers

- `CLAUDE.md` raíz.
- `docs/domains/sales-agent/redesign-2026-04/{README,00-vision-and-objectives,02-architecture-target,04-principles,05-tech-debt-log}.md`.
- `.claude/rules/{copilot-resilience,copilot-observability,sales-agent-brand-voice,parallel-safety,spanish-text}.md`.
- `references/` (pre-redesign conversation craft — útil para evolución de copy, no arquitectura post-S12).

## Budget + Outbound Gating (PI-1 S0 PR-2)

sales_agent está **subject a 2 gates** del módulo `shared/billing/` + `shared/compliance/` (PI-1 S0 PR-2 — wiring specialists diferido a S2; primitivas expuestas hoy).

### Gate 1 — `BudgetGuard.check` (LLM cost, SA pool reservado)

```python
decision = await budget_guard.check(
    tenant_id=tenant_id,
    agent_kind="sales_agent",       # ← bucket SA (reserved pool)
    estimated_cost_usd=Decimal("..."),  # tier-aware si LiteLLM declara input_cost_per_token_above_200k_tokens (Kimi K2.6, S12)
)
```

- `agent_kind="sales_agent"` → consume del **SA pool reservado** (`plan_config.llm_budget_total_usd * sales_agent_reserved_pct`, default 50%).
- SA exhausto **NO** consume Others pool (copilot reserve). Hard separation por bucket. Arch test property-based enforce.
- Tier pricing >200k (Kimi K2.6, S12 cementado): caller (specialist) pre-computes `estimated_cost_usd` con `TIER_THRESHOLD = 200_000` split. BudgetGuard NO recomputa tiers (no invade calculator §3-protected).

### Gate 2 — `OutboundRateLimiter.check` (volumen mensajes outbound)

```python
allowed = await outbound_rate_limiter.check(tenant_id=tenant_id)
if not allowed:
    # short-circuit pre-send: log + skip OutputManager.process_response chunking
    ...
```

- Sliding window Redis (24h) con cap `plan_config.max_outbound_msg_per_day`.
- `None` cap → unlimited (subject a budget).
- Soft-fail: Redis unavailable → fail-open (per `tessl__graceful-degradation`).

### Plan defaults (editable Streamlit `/planes-billing` — 1 UPDATE row, 0 migration)

| plan_id | llm_budget_total_usd | SA pool (50%) | max_outbound_msg_per_day |
|---|---|---|---|
| free | $5.00 | $2.50 | 100 |
| basic | $15.00 | $7.50 | 500 |
| intermediate | $30.00 | $15.00 | 2000 |
| advanced | $45.00 | $22.50 | 5000 |
| ultra | $95.00 | $47.50 | 20000 |

### Custom override per-tenant

`tenant_subscription.custom_overrides JSONB` permite per-tenant override (ej. tenant enterprise con `{"max_outbound_msg_per_day": 50000, "llm_budget_total_usd": 200}`). `PlanService.get_effective(tenant_id)` mergea overrides sobre plan base. Cache 5min con cross-instance pub/sub invalidation (PR-2 Q5).

### MV stale soft cap

Si `mv_refresh_log.get_last_refresh('mv_daily_llm_cost_per_tenant_v2')` > 1h → `BudgetGuard` aplica soft cap 105% (admite 5% overrun para no bloquear ventas). Cementado PR-2 Q4.

### Cuándo wirear (S2)

PR-2 expone primitivas, **NO modifica specialists**. S2 wirea:
- `qualifier` / `product_expert` / `closer` / `supervisor` antes de cada LLM call → `BudgetGuard.check`.
- `OutputManager.send_outbound_message` → `OutboundRateLimiter.check` antes de `process_response`.

§3 protected surfaces (Closer Studio, BufferService, OutputManager.process_response chunking) NO se tocan — el gate vive antes del entry point.

**Detalle vivo en PR-2 CONTRACT.md.** Skill solo agrega anchor — ver:
`docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/CONTRACT.md`

## Project invariants (read on demand)

- `references/sales-agent-brand-voice.md` — SSoT voz, compiler v2, slot architecture, micro-anchor per-turn, cache invalidation, tests obligatorios
