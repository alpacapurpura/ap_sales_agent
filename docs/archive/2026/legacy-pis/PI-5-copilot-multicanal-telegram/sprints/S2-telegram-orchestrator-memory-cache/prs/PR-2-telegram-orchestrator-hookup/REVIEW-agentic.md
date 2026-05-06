# Agentic Review — PR-2-telegram-orchestrator-hookup

> Auditor: `nicolify-agentic-auditor` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-01
> Iter: 2
> Verdict: **PASS**
> Generated: 2026-05-01T13:30:00Z

## Inputs
- CONTEXT-BRIEF.md: used (Haiku 4.5 pre-cocked, faithfulness=clean) + raw verification of architect §16 questions
- gate-output.json: used (iter-2, schema 1.0); cross-checked with native pytest run
- Skills invoked: copilot-expert=Y, sales-agent-expert=N (sales_agent untouched per D-PI5-005), tessl__langgraph=Y, tessl__graceful-degradation=Y

## Gate status (from gate-output.json + native re-run)
| Gate | Status | Errors |
|---|---|---|
| pytest (PR-2 scope) | PASS | 0 (100/100 GREEN — domain/memory/orchestrator/tools/repo/integration/arch) |
| pytest (ajenos) | n/a (out of PR-2 scope) | 12 pre-existing failures (sales_agent CAMPAIGN_CONTEXT/TOOL_REQUEST_FORMAT enums other session, voice_api 410 Gone deprecación intencional, deep_agent kimi clamp pre-existing, outbox PR-1 cascade, DDD campaigns→sales_agent, folder_naming, voice_fidelity timeout) |
| ruff lint | PASS | 0 (PR-2 modified files clean) |
| ruff format | PASS | 0 (11 files already formatted) |
| arch-fitness | PASS | 0 (test_copilot_anchors + test_system_prompt_order + test_copilot_telegram_separation::test_telegram_cache_prefix_meets_anthropic_threshold + test_no_new_copilot_module_imports + test_copilot_provider_compliance + test_channel_formatter_compliance + test_workflow_compliance — all GREEN) |
| mypy | WARN | 1 pre-existing (`rolling_summarizer.py:84` Any-return on `_resolve_llm` — present pre-PR-2, NOT introduced by builder; verified via `git show d09799b9~1`) |

## 12 categories
| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | `state["client_context"]` mutation only on freshly-built dict from `_build_client_context()` (chat.py:653-673 returns dict literal; chat.py:740-745 mutates the local fresh dict, not shared state). Reducer for `messages` already `add_messages` (state.py preserved). No subgraph topology change — same `build_deep_agent_graph` (deep_agent.py:215). |
| 2 | Tool registration | PASS | No new tools registered. `get_tools_for_context(ctx, channel=channel or "web")` (deep_agent.py:281) routes channel from state to existing registry. `ToolGroupMeta.available_channels` SSoT preserved (registry.py:353-372). All telegram-disallowed groups (`navigation`/`guided`/`landing`/`offer_section`) marked `frozenset({"web"})` correctly. |
| 3 | Prompt cache architecture | PASS | `_TELEGRAM_CHANNEL_CONTEXT_ES` is plain `str` (graph.py:679 — no `f"""` prefix), no Python interpolation. The `{tenant_slug}` and `{ruta}` are LITERAL braces emitted to LLM (verified grep — only 4 brace occurrences, all in user-facing template the LLM substitutes at output time, not Python f-string). Slot order: STATIC_IDENTITY → TOOLS_HINT → MARKETING_KB_HINT → TELEGRAM_CHANNEL_CONTEXT → LIGHTHOUSE → EDITABLE_CATALOG → MODULES_LIST (system_prompt_layout.py:65-73) — preserves [COPILOT-MARKETING-KB-F10] anchor + LIGHTHOUSE position. Returns `""` when channel != "telegram" → web bytes byte-identical (graph.py:894-896). Cache prefix size ≥2048 tokens enforced via `test_telegram_cache_prefix_meets_anthropic_threshold` (test_copilot_telegram_separation.py:197-223). |
| 4 | deepagents subagent isolation | PASS | No new subagents added. Existing `AUDIT_INSPECTOR_SUBAGENT`, `URL_ANALYZER_SUBAGENT`, `DATA_QUERY_SUBAGENT` preserved verbatim (deep_agent.py:289-293). Sub-agent `tools=[]` invariant preserved (no parent state leak). |
| 5 | Observability (`copilot_trace_event` + cost recording) | PASS (with WARN) | `invoke_text` uses identical `obs.observe_turn(...)` context manager as `stream_chat` (chat.py:1219-1280); `_run_graph_stream` callback handler writes to `copilot_llm_call` table including `cached_read_tokens`/`cached_write_tokens` per LLM call (verified `shared/agent_observability/recording/base_callback_handler.py:582-583`). PII sanitization preserved at recorder layer. `tenant_id` propagated through `obs._build_observability_context(tenant_id=...)` (chat.py:1219-1223). **WARN**: `CopilotInvokeResult.cache_read_tokens` / `cache_creation_tokens` / `total_tokens` hardcoded `0` at chat.py:1303-1305 (with comment `# populated when obs aggregator surfaces it`) — DTO-level surfaces not wired to obs aggregator yet, so the worker `_LOGGER.info("copilot_telegram_turn_completed", cache_read_tokens=0, ...)` always logs zero. The DB SOURCE OF TRUTH is honest (callback handler writes per-call), but the structured-log telemetry from worker is lossy. Documented as deferred wiring (S5 follow-up per CONTRACT §16 Q1). |
| 6 | Eval goldens (sales_agent) | PASS | n/a — sales_agent surface untouched (D-PI5-005). Copilot quality goldens (`tests/quality/golden/`) byte-identical when channel="web" (telegram fragment returns `""`), so existing goldens pass byte-for-byte. |
| 7 | RAG / Qdrant hygiene | PASS | No Qdrant/RAG changes in PR-2. `KnowledgeService` calls via `knowledge_search` tool unchanged. Telegram tool subset includes `knowledge_search` (graph.py:719-720 telegram tools list) — tenant filter inherited from existing infra. |
| 8 | LLM provider routing | PASS | No new model routing. `LLMFactory.get_service().get_client(ModelRole.AGENT, temperature=0.6)` preserved (deep_agent.py:254-257). No hardcoded model strings introduced. `RollingSummarizer._resolve_llm()` routes via `LLMFactory.get_service().get_client(ModelRole.NANO, temperature=0.0)` (rolling_summarizer.py:82) — pre-existing. |
| 9 | Cost optimization | PASS | Cache hit rate target documented in CONTRACT §8.5/§8.8 (≥60% by turn 3). 5min TTL choice (`cache_control: {"type": "ephemeral"}`) justified per Anthropic docs accessed 2026-05-01 in CONTRACT §8.5 (5m write = 1.25× base; 1h write = 2× base). Per-turn fragment ≥2048 tokens (Sonnet floor + Kimi K2.6 baseline ≥1024) enforced via arch test. WARN-level: structured-log cache_read_tokens=0 always (see Cat 5) means runtime dashboards won't reflect actual cache hit rate without DB queries. |
| 10 | Channel format & brand voice | PASS | `format_for_channel_impl(content=result.response_text, channel_id="telegram")` invoked in worker (telegram_worker.py:235-238). MarkdownV2 escaping inside `CopilotTelegramBot.send_message(parse_mode="MarkdownV2")` (telegram_worker.py:248-253). `_TELEGRAM_CHANNEL_CONTEXT_ES` line 752 explicitly says "Respeta la voz del tenant (lighthouse). El tenant define tuteo / voseo / formal..." — does NOT hardcode voice. Default fallback line 754: "español neutro LATAM con tuteo, sin voseo" (correct copilot UI rule per `.claude/rules/spanish-text.md`). User-facing fallback messages (telegram_worker.py:189, 217, 229, 244) all tuteo neutro. Spanish neutro check: no voseo (`mirá`/`tenés`/`podés`) detected. |
| 11 | DDD compliance (agentic) | PASS | Layers preserved: domain → `domain/context_window.py` (frozen dataclass + dispatcher); application → `application/orchestrator/{chat,graph,deep_agent,system_prompt_layout,invoke_result}.py` + `application/memory/{context_window_builder,rolling_summarizer}.py` + `application/tools/registry.py`; infrastructure → `infrastructure/repositories/conversation_repository.py` + `infrastructure/workers/telegram_worker.py`; api → `api/dto.py`. No cross-module imports introduced (verified test_no_new_copilot_module_imports.py PASS — ratchet 22 frozen). Worker imports only from `copilot.*` + `shared.agent_observability.channels` (consumed READ-ONLY per anti-duplication rule). |
| 12 | Tests / TDD | PASS | 8 new test files for PR-2 scope (3 created iter-1 + 5 created iter-2): `test_context_window_telegram_config.py`, `test_memory_builders_for_channel.py`, `test_telegram_channel_context_fragment.py`, `test_invoke_text.py` (212 LOC), `test_registry_telegram_runtime_filter.py` (170 LOC), `test_conversation_repository_telegram_lookup.py` (172 LOC), `test_telegram_end_to_end.py` (213 LOC, 3 cases linked-happy/unlinked-CTA/`/start TOKEN`), arch test `test_telegram_cache_prefix_meets_anthropic_threshold`. 100/100 PASS. Anchor cap bumped 37→39 (test_copilot_anchors.py registers `COPILOT-INVOKE-RESULT-PR2-PI5` + `COPILOT-TELEGRAM-CHANNEL-CONTEXT`). Slot ratchet extended in test_system_prompt_order.py. |

## Findings (file:line)

### FAIL
(none)

### WARN
- [Cat 5] `backend/src/modules/copilot/application/orchestrator/chat.py:1303-1305` — `CopilotInvokeResult.cache_read_tokens=0`, `cache_creation_tokens=0`, `total_tokens=0` are hardcoded with `# populated when obs aggregator surfaces it`. The structured log emitted by `telegram_worker.py:264-274` `_LOGGER.info("copilot_telegram_turn_completed", cache_read_tokens=0, ...)` always shows 0 even on cache-hit turns. Source of truth (`copilot_llm_call.cached_read_tokens`/`cached_write_tokens` columns) IS honest — handler writes per-call. **Recommendation**: surface `acc.obs.usage_aggregator()` (or equivalent) so the DTO populates from the observability layer; otherwise downstream dashboards / alerts based on worker structured logs will undercount cache savings. PR-2 docstring acknowledges this is deferred wiring; not a blocker for PR-2 close because DB observability is honest, but should be tracked as S5 follow-up alongside `copilot_conversations.rolling_summary` persistence.
- [Cat 5] `backend/src/modules/copilot/application/orchestrator/chat.py:1245-1253` — `invoke_text` exception handler does NOT call `acc.obs.set_turn_error(error_kind, ...)` after catching `Exception`. Inner `_run_graph_stream` does call `set_turn_error` from its own try/excepts (chat.py:1397, 1425, 1460), so traces remain honest for ~99% of failure modes (timeout / tool-loop / generic stream errors). Only generator-machinery errors that escape `_run_graph_stream`'s frame would leave the trace marked `status='ok'`. **Recommendation**: defensive `acc.obs.set_turn_error(error_kind, str(exc))` in `invoke_text` line 1247 (next iter or S5 follow-up). Not auto-fix — minor.
- [Cat 9] mypy 1 error pre-existing (`rolling_summarizer.py:84` `_resolve_llm` returning `Any` → `BaseChatModel`). Verified via `git show d09799b9~1` that this error pre-existed PR-2; builder did not introduce. Recommendation: add explicit cast or refactor — should NOT block PR-2 verdict. Out of scope per PM ruling.

### info
- [Cat 3] graph.py:670-678 — comment correctly identifies `{tenant_slug}` and `{ruta}` as LITERAL placeholders the LLM substitutes at output time (not Python f-strings). Architecture rationale block also documents the ≥2048 token target (Sonnet floor + Kimi K2.6 baseline). Excellent invariance documentation.
- [Cat 5] worker `_mask_chat_id(chat_id)` (telegram_worker.py:300-304) properly redacts chat_id to first 5 chars + `***` in all log lines. PII pattern enforced.
- [Cat 11] `invoke_result.py` correctly uses `model_config = ConfigDict(from_attributes=True, frozen=True)` (Pydantic v2 idiom, not legacy `class Config`). Frozen=True prevents accidental mutation post-construction.
- [Cat 12] `test_conversation_repository_telegram_lookup.py:172` covers cross-tenant isolation explicitly — same `(user, channel_type, channel_chat_id)` for tenant A returns row A, never tenant B's row.

## Cross-scope flags (if any)
(none — PR-2 surface is single-module agentic only, modules/copilot/. No backend negocio, no frontend, no migration.)

## Research notes (DATE-AWARE)
- Source: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (accessed 2026-05-01 by architect, re-verified by auditor on same date).
  - Takeaway: Anthropic Opus 4.7 floor 4096 tokens, Sonnet 4.6 floor 2048 tokens, 5min TTL default, validate via `cache_creation_input_tokens` + `cache_read_input_tokens`. PR-2 targets ≥2048 (PM-resolved Q3, Sonnet floor + Kimi K2.6 baseline ≥1024 covered with margin).
  - Delta vs reference anchors: none — agent definition anchors match live docs.
- Source: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (accessed 2026-05-01).
  - Takeaway: per-invocation context flows via initial state dict; sync call should use `compiled_graph.ainvoke()` but for SSE-yielding streams, `_run_graph_stream` consumed internally is the right pattern. PR-2 follows this idiomatic pattern (no graph subclass).
- Source: `tessl__graceful-degradation` skill rules.
  - Takeaway: every external call needs timeout + fallback. PR-2 worker has 30s `asyncio.wait_for` on `invoke_text`, per-dependency try/except (lookup / orchestrator / format / bot send), structured logging on each failure path, never raises to ARQ. Conforms.
- Knowledge cutoff disclosure: Opus 4.7 cutoff is January 2026. Anthropic prompt-caching thresholds + LangGraph patterns + deepagents `task` semantics validated on live docs as of 2026-05-01 — auditor did NOT rely on remembered values.

## Recommendations for builder fix-loop
(none required — verdict PASS. Two WARN items recommended for S5 follow-up, NOT blocking PR-2 close):
1. (S5 candidate) Wire `CopilotInvokeResult.cache_read_tokens` + `cache_creation_tokens` + `total_tokens` to `acc.obs` aggregator so worker structured logs reflect real cache hits.
2. (S5 candidate) Add defensive `acc.obs.set_turn_error(...)` in `invoke_text` outer except to cover edge generator-machinery errors that escape `_run_graph_stream`.
3. (Pre-existing, NOT PR-2) Address `rolling_summarizer.py:84` mypy error in a separate cleanup PR.

## Drift detection (CONTRACT vs code)
**NO drift detected.** All CONTRACT §1-§14 decisions honored verbatim:
- §1: `TELEGRAM_CONTEXT_WINDOW_CONFIG` instance + `get_context_window_config(channel)` dispatcher present (context_window.py:37-65). Web default unchanged.
- §3: `CopilotInvokeResult` Pydantic frozen DTO (`from_attributes=True`, `frozen=True`) — invoke_result.py:19-32.
- §6: `get_or_create_by_channel` optimistic SELECT-then-INSERT, tenant-scoped, excludes `deleted_at` rows — conversation_repository.py:103-168.
- §7.1: `invoke_text` shares `_prepare_conversation` + `_run_graph_stream` with `stream_chat` (chat.py:1170-1307). NEVER raises (graceful-degradation iron rule).
- §7.2: `for_channel` classmethods on builder + summarizer (context_window_builder.py:30-48; rolling_summarizer.py:56-75).
- §7.3: Worker hookup with 30s timeout, per-dependency error isolation, sync-session block after async-session close — telegram_worker.py:142-276.
- §7.4: `get_tools_for_context(ctx, channel=channel or "web")` from `state["client_context"]["channel"]` — deep_agent.py:280-281.
- §8.5: `TELEGRAM_CHANNEL_CONTEXT` slot at idx 3 between MARKETING_KB_HINT and LIGHTHOUSE; ≥2048 token target enforced. Anchor `[COPILOT-TELEGRAM-CHANNEL-CONTEXT]` registered.
- §11: All cross-cutting concerns honored (tenant isolation, PII mask, Spanish neutro defaults, idempotency at update_id).
- §12: Anchor cap 37→39 (matches IMPL-LOG iter-2 — registered both `COPILOT-INVOKE-RESULT-PR2-PI5` + `COPILOT-TELEGRAM-CHANNEL-CONTEXT`); ratchet shrink-only invariant preserved.
- §14: Test surfaces — all 8 declared test files exist + GREEN.

PM Q1-Q6 resolutions all absorbed: Q1 (PR-2 owns first-time wiring) ✓, Q2 (no new function) ✓, Q3 (≥2048 floor) ✓, Q4 (kwarg + DTO both paths) ✓, Q5 (UNIQUE deferred S5) ✓ documented in repo method docstring, Q6 (classmethod canonical) ✓.
