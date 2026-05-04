# Gap report — Group C (sales_agent, copilot, scheduling, connections) — 2026-05-04

> Auto-generado por agente mapper durante migración SDD Level 3.
> Cada gap representa un área que necesita atención (test missing, coverage bajo, eval missing, etc).
> Agente: module-mapper Group C — paths verificados contra repo en `last_audit: 2026-05-04`.

## Resumen

| Module | Capabilities mapped | Stories mapped | Agentic eval suite | Unit/Integration coverage (BE) | Status |
|---|---|---|---|---|---|
| sales-agent | 5 | 10 | **MISSING** (no `agentic_evals/sales_agent/`) | sólido (snapshots + observability) | **CRÍTICO — agentic stories sin pass^k** |
| copilot | 4 | 9 | **PARCIAL** (`backend/src/modules/copilot/evals/` solo classifier+summarizer) | sólido (1063+ tests) | **HIGH — orchestrator-level eval missing** |
| scheduling | 3 | 6 | n/a (service-stories) | sólido | needs load test + watch channel renewal alert |
| connections | 4 | 8 | n/a (service+ui-stories) | sólido | needs token expiry proactive alert + reconnect e2e |
| **Total** | **16** | **33** | — | — | — |

## Agentic gaps específicos

### sales_agent — CRÍTICO

**No agentic eval suite existe** (`backend/tests/agentic_evals/sales_agent/` no existe). Solo unit tests:
- `test_nodes.py` — qualifier/closer/product_expert nodes individual
- `test_chat_orchestrator_snapshot.py` — golden snapshots turn-by-turn
- `test_specialist_provider_routing.py` — supervisor routing
- `test_semantic_router.py` — tier classifier
- `observability/` — trace/llm_call/cost persistence
- `test_offer_prompt_renderer.py` — prompt rendering goldens

Agentic stories (6) **NO tienen pass^k tracking ni regression_floor verification**:
- `sales-inbound-conversation-qualify` — persona `lead-tibio-dudoso` declarada pero NO ejecutada en CI
- `sales-inbound-conversation-close` — tool trajectory (list_public_editions → resolve_active_tier → create_enrollment → generate_payment_link) declarada en story pero NO testeada con persona `lead-caliente-ready`
- `sales-brand-voice-fidelity` — voice_fidelity grader threshold 0.7 declarado en `SALES_AGENT_VOICE_FIDELITY_THRESHOLD` env (Decision 30) pero NO runs reales contra goldens dataset (no goldens checked-in)
- `sales-tool-send-payment-link` + `sales-tool-schedule-meeting` — adversarial scenarios (cross-tenant, fake discounts) sin grader
- `sales-outbound-campaign-launch` — voice fidelity NO testeada con campaign_instructions adversarial (prompt injection)

Personas declaradas en `docs/specs/personas/` pero **NO consumidas por suite alguna**:
- `lead-frio-impaciente.yaml` (referenciada en 2 stories adversarial)
- `lead-tibio-dudoso.yaml` (referenciada en 2 stories happy)
- `lead-caliente-ready.yaml` (referenciada en 1 story regression)

Rubrics declaradas pero NO instrumentadas en CI:
- `voice-fidelity.md` (threshold 0.7 sales_agent)
- `no-hallucination.md` (no inventar precios/cupones/garantías)
- `no-overpromise.md` (no prometer resultados garantizados)
- `tool-trajectory.md` (closer specialist tool sequence)
- `empathy-tone.md` (provider down recovery)
- `completeness.md` (qualifier extracts atributos)

**Cost tracking accuracy degraded**: `cost_usd=0` post-fix por pricing resolution provider mapping (deepseek tagged como openai en `model_pricing_snapshot`). Story `sales-cost-tracking-cycle-billing` declares como gap. Backlog PR follow-up.

**Pool isolation property-based tests**: existe `test_budget_guard_pool_isolation.py` (arch) pero coverage edge-cases (stale MV soft cap 5%, SA exhausted ≠ Others exhausted) no es exhaustivo.

**No structured event emission al WMS de marketing**: workers (`follow_up_engine`, `payment_reminder_engine`, `frozen_detection`) no emiten events estructurados a analytics para feedback loop (recovery rate, abandonment ratio).

**Frozen detection threshold hardcoded**: `MAX_INTERNAL_TURNS` en `domain/tuning.py` no per-tenant tunable. Tenant high-volume vs low-volume usan misma cadencia.

**Outbound supervisor skip-qualifier boundary**: `lead_score=39` vs `lead_score=40` boundary (Decision 30) NO testeado con persona simulated en eval suite.

**Adversarial scenarios sin instrumentación**:
- Jailbreak ('ignora tus instrucciones')
- Prompt injection en campaign_instructions
- Persona hostile leak system prompt
- Cross-tenant tool args spoofing

### copilot — HIGH

**Eval suite parcial existe** (`backend/src/modules/copilot/evals/` con runner.py + 100 goldens) pero solo cubre:
- Classifier (50 ejemplos × 5 categorías + 10 adversarial each → ROUGE)
- Summarizer (50 ejemplos → cosine similarity)

**NO cubre orchestrator-level**:
- Tool trajectory (deep_agent + create_deep_agent subagents)
- Voice fidelity (output_sanitizer voseo enforcement)
- Card emission/accept flow (`copilot-doc-extract-to-brand-fields` + `copilot-url-extract-to-offer-fields`)
- Conversational long context (Lost-in-the-Middle mitigation per-turn anchor declared parcial en module doc)
- RAG style anchors per tenant (slot 5) status=placeholder

Personas declaradas pero NO consumidas:
- `tenant-novato-tech.yaml`
- `tenant-experto-saturado.yaml`

**Telegram channel sin eval suite específico**:
- `copilot-telegram-orchestrator-respond` — memory windowing (TELEGRAM_CONTEXT_WINDOW_CONFIG) no testeada con persona simulated multi-turn
- Cache prefix ≥2048 tokens activo declarado pero hit rate NO instrumentado en eval (solo arch test `test_telegram_cache_prefix_meets_anthropic_threshold`)
- Adversarial: prompt injection via Telegram caption — no testeado en eval

**Suggestion engine sin regression**:
- `copilot-suggestions-show-route-aware` — heuristic <11ms p99 declarado en CONTRACT D-15 pero NO load test que lo confirme con 4 providers concurrent
- ML feedback loop (suggestion_accepted ratio) = backlog PI-2 S2+
- Métricas adopción declaradas pero NO dashboard production

**Document extraction adversarial**:
- Doc malicioso con prompt injection ("ignore previous, extract X as Y") — no testeado en eval suite
- Solo arch test `test_prompt_injection_sanitizer.py` cubre output_sanitizer

**DTO cache token fields hardcoded 0** (S5 wire-up pendiente per module doc):
- `invoke_text` outer except defensive `set_turn_error` (S5)
- UNIQUE constraint conversations multi-channel deferred S5 PR-5 — race posible en SELECT-then-INSERT

**Subagent isolation tests**: existen `test_subagent_stream_isolation.py` + `test_stream_provenance.py` pero no cubren classifier failure mid-stream con concurrencia tenant.

**Voice fidelity grader running pero coverage Y%**: `test_deep_agent_prompt_voseo_compliance.py` enforce static prompt LATAM neutro, pero NO valida output runtime contra rubric `voice-fidelity.md`.

## Gaps generales (no-agentic)

### scheduling

#### scheduling-google-availability-resolve (story)
- No load test availability_service (>100 event_types per tenant, cuándo cache cap se rompe)
- Cache 60s expiry edge cases sin coverage
- Watch channel TTL ~1 week renewal cron NO documented (silent failure → stale availability)

#### scheduling-google-watch-channel-push (story)
- NO alert si watch channel expira sin renew (debe estar en monitoring)
- Push validation X-Goog-Channel-Token covered, pero replay attacks no exhaustivos

#### scheduling-event-type-create + public-link
- No FE feature `frontend/src/features/scheduling/` — admin solo via Streamlit
- Copilot tool `create_event_type` parcial (mencionado en module doc) — no e2e regression
- Conversational modify availability via copilot = gap declarado en module doc

#### scheduling-public-book-confirm-ics (story)
- Public page UI = pendiente FE (currently render simple HTML server-side, no React)
- No e2e regression flow completo (book → confirm → cancel → ICS sync con Google Calendar real)
- Reminder cadence hardcoded (24h + 1h pre-meeting) — no per-event_type tunable
- No multi-attendee flow (group bookings declared en domain pero no UI)

#### scheduling-cancel-reschedule (story)
- Reschedule: Google Calendar event id REUSED + updated time — sin test que valide attendees preservados
- Token replay attack 410 Gone implementado pero rate limit por IP no enforce

### connections

#### connections-meta-oauth-flow (story)
- Token refresh cron no documented (silent expiry → user surprise)
- No alert si connection becomes stale (status=disconnected sin user notification)
- Ads scope optional pero no claro UX cuándo incluirlo

#### connections-meta-page-account-pick (story)
- Page revoked mid-session: status detection delayed (depends on next API call failure)
- Cross-tenant page picker bug-prone (e.g., agency tenant con multi-pages)

#### connections-manychat-webhook-receive (story)
- WhatsApp via Manychat custom = parcial (per module doc 'WhatsApp pendiente')
- No retry policy definido para Send Content failures (5xx)
- Tags catalog no SSoT (tenants definen ad-hoc, drift posible)

#### connections-manychat-send-content-api (story)
- Format adapter Markdown→Manychat blocks: edge cases (multiline, lists, links nested) no exhaustivo
- Rate limit 600/min global per tenant pero no per-subscriber (10 msg/sec ManyChat enforce)

#### connections-google-oauth-bundle (story)
- Refresh cron daily — silent failure si token revoked (status=expired requires user action)
- Scope revocation mid-session (e.g., user solo revoked Calendar): partially_disconnected status no surface en UI

#### connections-ga4-property-picker (story — IN-PROGRESS)
- **GA4 property picker FE PENDING** (MEMORY.md project_ga4_property_picker.md — Tasks 5-8 pendientes)
- BE done — listar properties accesibles via GA4 API
- FE pending — UI dropdown picker + auto-save + state_check

#### connections-status-list-ui (story)
- No background job watching token expiry (proactive alert)
- "Test connection" button tests basic auth pero no end-to-end (e.g., test Manychat = solo verifica token, no envía mensaje real)

#### connections-reconnect-flow (story)
- Reconnect flow no preserva config (custom domain, tenant settings) — re-config needed
- Reconnect different account: page_id preserved pero no admin-validated → silent broken state

## Cross-cutting

- **Anti-duplication shared lift completed**: `BaseObservabilityContext` + `BaseAgentCallbackHandler` + `FXResolver.default()` + `sanitize_payload` shared, copilot+sales_agent both subclass (ratchet F1 0 entries). Verify per `anti-duplication.md` cardinal rule.
- **Multi-channel format**: `format_for_channel_impl` shared, copilot Telegram + sales_agent Manychat both consume (no mirror).
- **PII sanitization**: `sanitize_payload` shared aplicado consistente.
- **Outbox pattern flag rollout**: `USE_OUTBOX_PATTERN_SALES_AGENT=True` default + `USE_OUTBOX_PATTERN_COPILOT=True` default — both live PR-6 PI-1 S2.
- **BudgetGuard wiring**: SA pool single point `ConversationPipeline.__init__`, copilot single point `build_deep_agent_graph`. Both use `BudgetGuardingChatModel` shared.

## Acción recomendada (priorización)

| Pri | Tarea | Owner | Effort |
|---|---|---|---|
| **P0** | Implementar agentic eval suite `backend/tests/agentic_evals/sales_agent/` con personas + rubrics + pass^k runner | sales-agent-expert | L (10-15d) |
| **P0** | Voice fidelity grader runs en CI gate de PRs sales_agent (consume rubric voice-fidelity.md vs personality_profile per tenant) | sales-agent-expert | M (5d) |
| **P0** | Goldens dataset sales_agent (3-5 tenants reales con voice profile distintos × happy/negative/edge/adversarial) | sales-agent-expert | L (10d) |
| P1 | Extender copilot evals a orchestrator-level (deep_agent tool trajectory + voice fidelity) | copilot-expert | L |
| P1 | Cost tracking accuracy fix (deepseek pricing resolver provider mapping) | sales-agent-expert + metrics-expert | S (2d) |
| P1 | GA4 property picker FE complete Tasks 5-8 | frontend-expert | M (3-5d) |
| P2 | Watch channel renewal cron + alert si TTL <1d | backend-expert | S |
| P2 | Token expiry proactive alert (Meta + Google + Manychat) | backend-expert | S |
| P2 | Streamlit dashboards: `/admin/cost-sales-agent` + `/admin/copilot-suggestions-adoption` | backend-expert | M |
| P3 | E2E regression scheduling (book → confirm → cancel → ICS sync) | playwright-expert | M |
| P3 | E2E regression connections reconnect flow (Meta + Google + Manychat) | playwright-expert | M |
| P3 | FE feature `frontend/src/features/scheduling/` (replace Streamlit admin) | frontend-expert | L |
