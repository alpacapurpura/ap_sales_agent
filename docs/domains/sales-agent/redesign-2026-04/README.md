# Sales Agent Redesign 2026-04

> **Actualizado 2026-04-28** post-S6 close: agregadas **S6.5 / S11 / S12** para garantizar que **al cerrar S12 el plan deja cero deuda flotante** (`05-tech-debt-log.md` con 0 entries DEFERRED). Decisión CTO 2026-04-28: el plan es ahora autocontenido — cada deuda detectada apunta a fase concreta del plan o WONT-FIX con razón documentada, no a "post-redesign".
>
> Cambios previos: post-revisión de cambios copilot abril 2026 (multi-provider per-role, ChatModelSpec native, observability rebuild cerrado, pricing aliases Kimi K2.6/K2.5, tool_call_dedup, F8 cache_boundary). Plan recortado donde hay code existente que adoptar; ampliado donde se detectó deprecated cleanup + admin migration.

Plan de evolución arquitectónica de `sales_agent` para alcanzar madurez de copilot a nivel de **infraestructura cross-cutting** (observabilidad event-sourced, PII sanitization, cost guardrails, cache-friendly prompts, fitness tests, registries) **sin perder identidad de dominio** (StateGraph lineal qualifier→closer, Closer Studio, smart debounce, multi-channel webhooks).

Adicionalmente:
- **S00 (NUEVO)**: codebase audit + cleanup deprecated `resumen` + Streamlit admin migration prep + sidebar fix.
- Voz de marca real (lee `Estilo Comunicacional` de Brand Studio).
- Scheduler tool (lead-specific booking link, verificación, follow-up).
- Payment lifecycle tool (create link → verify paid → grant access).
- Eval loop (judge + goldens).

Estructura espejo del redesign de copilot. Cada fase = **review código existente + research fresco + diseño + TDD + ejecución + code review final + learnings + prompt para la siguiente**.

---

## Mapa de documentos

| Doc | Para qué |
|---|---|
| [00-vision-and-objectives.md](00-vision-and-objectives.md) | Visión negocio, objetivos, lo que NO se toca |
| [01-master-plan.md](01-master-plan.md) | DAG completo + dependencias |
| [02-architecture-target.md](02-architecture-target.md) | Topología destino (alineada con realidad post-abril 2026) |
| [03-phase-protocol.md](03-phase-protocol.md) | Protocolo obligatorio por fase (10 pasos, incluye code review final) |
| [04-principles.md](04-principles.md) | Principios senior: GoF, DRY, cohesión, acoplamiento, TDD, anti-parche, no-broken-callers |
| [05-tech-debt-log.md](05-tech-debt-log.md) | Registro vivo de deuda técnica cross-fase |
| [06-glossary.md](06-glossary.md) | Términos clave (incluye ChatModelSpec, pricing_aliases, tool_call_dedup) |
| `phases/S{N}-*.md` | Una por fase: research mandate + diseño + plan TDD |
| `learnings/S{N}-*.md` | Aprendizajes generados al cerrar cada fase |
| `prompts/S{N}-start.md` | Prompt exacto para iniciar conversación nueva |

---

## Estado de fases

| # | Fase | Estado | Entregable principal |
|---|---|---|---|
| **S00** | [Codebase audit + cleanup deprecated](phases/S00-codebase-audit-and-cleanup.md) | 📋 PLANNED | Borrar `/sales/resumen` deprecated, fix redirect+sidebar, plan migración admin `sales_audit.py`, snapshot estado limpio |
| S0 | [shared/agent_observability extract](phases/S0-shared-observability-extract.md) | ✅ DONE | Módulo `src/shared/agent_observability/` (13 archivos movidos + 3 abstract bases). Zero behavior change copilot. |
| S1 | [sales_agent observability parity](phases/S1-sales-agent-observability-parity.md) | 📋 PLANNED | Callback handler + tablas event-sourced + PII LATAM + tool_call_dedup |
| S2 | [cost guardrails cross-agent](phases/S2-cost-guardrails.md) | ✅ DONE | Registry pasivo + CrossAgentCostAggregator + cost_alert breakdown + workers shared (retention/aggregate_refresh/cost_alert) + MV v2 cross-agent + Streamlit `/costo-agentes`. |
| S3 | [prompt cache_boundary refactor](phases/S3-prompt-cache-boundary.md) | ✅ DONE | `compose_system_prompt(fragments)` mirror F8 copilot. Single string + CACHE_BOUNDARY_MARKER. Prefix ~2700 tokens >2× threshold. Specialists qualifier/product_expert/closer migrados; supervisor fuera de scope. |
| S4 | [adopt ChatModelSpec + per-role routing](phases/S4-chatmodelspec-tier.md) | ✅ DONE | `SPECIALIST_TO_ROLE` SSoT en `domain/model_tier.py`. Closer→AGENT (Kimi K2.6), supervisor→NANO; qualifier/product_expert REASONING (DeepSeek V4 auto-cache). Arch test ratchet bloquea hardcoded model strings. 1639 tests verde. |
| S5 | [channel format registry](phases/S5-channel-registry.md) | ✅ DONE | `shared/agent_observability/channels/{format,format_for_channel,intent_detector}.py` (move desde copilot + extend `chunk_size`/`typing_simulation_cpm`/`parse_mode`). Slot 6 `CHANNEL_FORMAT_HINT` populated via registry. `OutputManager._enforce_chunk_size` consume registry. Arch ratchet `test_no_hardcoded_channel_in_output_manager.py` sin allowlist. 3134 tests verde. |
| S6 | [fitness tests ratchet](phases/S6-fitness-tests-ratchet.md) | ✅ DONE | 6 arch fitness tests nuevos (ratchet imports + anchors + handler invariants + PII coverage + tenant isolation + subagent isolation preventive). Sweeps oportunista S4/S5: 11 call sites copilot migrados a SSoT shared, 3 shims borrados; `LLM_ROLE_BY_SITE` SSoT extendido (specialists + summary/nudge NANO + safety FAST). Drop legacy + cutover admin movido a S6.5 (ventana dual-write 4 sem cumple 2026-05-26). 622 arch tests + 2535 sales/copilot/admin/shared verde. |
| **S6.5** | [legacy drop + admin cutover](phases/S6-5-legacy-drop-admin-cutover.md) | 📋 PLANNED (reloj-gated 2026-05-26, **paralelo / post-S10 — NO bloquea S7..S10**) | Drop tablas legacy `agent_trace_model` + `LLMLogModel` (post 2026-05-26). Cutover `sales_audit.py`. Arch tests `test_no_legacy_agent_trace_reads.py` + `test_admin_no_legacy_table_reads.py` + `test_no_future_annotations_in_langgraph_files.py`. Cleanup docs `agent_log_model` ghost name. |
| S7 | [brand voice integration](phases/S7-brand-voice-integration.md) | 📋 PLANNED | Lighthouse Brand Studio "Estilo Comunicacional" → identity rendering |
| S8 | [tools: scheduler integration](phases/S8-tools-scheduler.md) | ✅ DONE | Strategy `SchedulerProvider` + `InternalSchedulerProvider` + 3 tools (create/verify/get_slots) + webhook endpoint registry-driven + 2 ARQ crons (verify + reminders T-24h/T-1h/T+1h) + voz de marca via slot 5 SSoT + stage scoping + 5 arch tests. Migration 080 + 1151 tests verde. |
| S9 | [tools: payment lifecycle](phases/S9-tools-payment-access.md) | ✅ DONE | Strategy `PaymentGatewayProvider` + `MercadoPagoPaymentProvider` / `StripePaymentProvider` + 3 tools (create/verify/grant_access saga) + webhook endpoint registry-driven fail-closed + `PaymentStateService` JSONB SSoT + `PaymentGrantAuditModel` append-only + 2 ARQ crons (verify_pending 15min + reminder_engine 30min) + `auto_grant_on_paid` subscriber + `AccessProvider` Protocol + port `payment_connection.py`. Migration 081 + 1166 tests verde. |
| S10 | [quality eval loop](phases/S10-quality-eval-loop.md) | ✅ DONE | `SalesAgentJudge` (5-dim rubric: brand_voice / channel_format / commercial_effectiveness / pii_safety / tone_locale) + 20 goldens cubriendo 6 categorías + cron `weekly_sales_agent_quality_eval` Mondays 07:00 UTC + drift detection (>5% week-over-week) + Streamlit `/sales-agent-quality` dashboard + migration 082 + arch test PII sanitization en judge prompt + anchor `SALES-AGENT-QUALITY-S10`. Stub default + opt-in `RUN_LLM_JUDGE=1`. Threshold 3.5/5 mirror copilot F9. 92 tests S10 + 636 arch + 534 sales_agent + 165 admin/quality verde. |
| **S11A** | [shared base lift](phases/S11-shared-lift-orchestrator-decomp.md) (sub-fase A) | ✅ DONE | `BaseAgentCallbackHandler` shared (102→634 LOC) absorbe 8 callbacks LangChain + Template Method skeleton + helpers. Sales subclass 85 LOC (-87%). Copilot subclass 83 LOC (-86%). Snapshot framework determinístico activo. 3270 tests verde (637 arch + 2633 modules). |
| **S11B** | [orchestrator decomposition](phases/S11-shared-lift-orchestrator-decomp.md) (sub-fase B) | ✅ DONE | Strangler Fig 7 commits: `chat.py` 1140→337 LOC (-70%, ceiling arch ratchet 400) + `AuditEmitter` + `IdentityResolver` + `ConversationPipeline` + `smart_debounce_runner` + `closer_studio_service.py` split Query/Command/Kpi + facade back-compat + `semantic_router.py` registry-based (domain SYSTEM_ROUTES + application overlay). Snapshot byte-equal preserved post-cada commit. §3 intacto. 3313 tests verde (638 arch + 2675 modules). S11 entera ✅. |
| **S12** | [final hardening — zero debt](phases/S12-final-hardening-zero-debt.md) | 📋 PLANNED | Tier pricing >200k arch ratchet + Presidio WONT-FIX classification + `typing_simulation_cpm` wiring (validar §3) + scan voseo final + audit `05-tech-debt-log.md` cero DEFERRED. |

Estados: 📋 PLANNED / 🚧 IN_PROGRESS / ✅ DONE / ⛔ BLOCKED

---

## Cómo arrancar

1. Lee [03-phase-protocol.md](03-phase-protocol.md) — protocolo 10 pasos obligatorio.
2. Lee [04-principles.md](04-principles.md) — principios senior no negociables.
3. Abre `prompts/S00-start.md` — copia el contenido y pégalo en una conversación nueva.
4. Esa conversación ejecuta S00 completo (audit + cleanup deprecated), deja `learnings/S00-*.md` y `prompts/S0-start.md` listos.
5. Siguiente conversación: pega `prompts/S0-start.md`. Y así.

---

## Reglas anti-deriva

- **No saltarse research fresco.** Cada fase: research mandate (web + context7/Tessl + lectura code).
- **Code review final pre-cierre** (Paso 11 de 03-phase-protocol.md): verificar callers no rotos, alta cohesión, bajo acoplamiento, no introducir tech debt.
- **No ampliar scope.** Oportunidad descubierta → `learnings/` o `05-tech-debt-log.md`. No al código en curso.
- **No agregar parches.** Bug ajeno → validar (¿real? ¿impacto?) → fix limpio + log. Sin band-aids.
- **No romper §3 de [00-vision-and-objectives.md](00-vision-and-objectives.md).**
- **TDD obligatorio.** Test reproductor antes de cualquier fix.
- **Spanish neutro LATAM** en user-facing (sin voseo). Excepción: voz de marca tenant si así lo configuró en Brand Studio.
- **No confundir** `sales/resumen` deprecated con growth-studio Meta Ads `ResumenTab/Card/Hook` (activos).
