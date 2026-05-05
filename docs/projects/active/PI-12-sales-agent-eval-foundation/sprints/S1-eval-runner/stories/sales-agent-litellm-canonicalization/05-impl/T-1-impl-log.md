# T-1-impl-log.md — Cost recorder canonicalization

---
ticket_id: T-1
story_id: sales-agent-litellm-canonicalization
state: building
assigned_to: claude-opus-4-7
started_at: 2026-05-05T05:00Z
last_update: 2026-05-05T05:00Z
current_step: "Step 0 — anti-duplication grep + dependency provisioning"
blocker: null
---

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `backend-expert` | All BE work — DDD, structlog, Pydantic v2, arch fitness | `references/runtime-quality-checklist.md` will be re-read pre-commit. SQLA 2.0 + soft deletes N/A (no DB writes from new file; only thread-safe in-process cache). |
| `tessl__fastapi` | App startup hook registration (`litellm.callbacks = [...]`) at FastAPI lifespan | `@app.on_event("startup")` is legacy — file already uses it pervasively, so we follow the existing pattern (refactor to lifespan is out of scope). Annotated DI not applicable. |
| `tessl__pytest-api-testing` | RED tests in `tests/shared/agent_observability/cost/test_litellm_canonicalization.py` | function-scoped fixtures, factory pattern for cache cleanup, parametrize for failure modes, no DB needed (pure unit + bridge mock). |
| `tessl__graceful-degradation` | Callback runs in critical LLM path — must never block turn | Best-effort try/except around every cache mutation + warning logs. TTL purge prevents unbounded growth. p95 < 50ms NFR enforced via micro-benchmark. |

## Step 0 — anti-duplication grep gate

Per `.claude/rules/anti-duplication.md` cardinal rule, before creating
`backend/src/shared/agent_observability/recording/cost_recorder.py` (NEW):

```bash
$ find /home/chris/AISALESHT/backend/src -name "cost_recorder.py"
(no output)

$ grep -rn "CustomLogger\|cost_recorder\|CostRecorder" /home/chris/AISALESHT/backend/src/
(no output)

$ grep -rn 'kwargs\["response_cost"\]\|response_cost' /home/chris/AISALESHT/backend/src/
(no output)
```

Result: no existing pattern. The architect (§10 of `03-arch-be.md`) ratified
`CostRecorderCustomLogger` as a NEW class at a NEW surface (LiteLLM
`CustomLogger` is conceptually distinct from LangChain `BaseCallbackHandler`;
the two coexist, bridged by `litellm_call_id` + thread-safe TTL cache 60s).
Justification: anti-duplication rule honoured because the new abstraction sits
on a new boundary (LiteLLM proxy callback), not a duplicate of an existing
shared surface. The `BaseAgentCallbackHandler` IS the shared LangChain plumbing
already lifted in S11A; T-1 EXTENDS it to consume `pop_cost(call_id)` instead
of mirroring.

## Cross-module reads (out-of-scope but read-only)

None for T-1.

## Plan inicial

1. Step 0 anti-duplication grep — DONE.
2. Provision litellm Python SDK in `requirements-runtime.txt` (pin <1.83 for
   openai compat with langchain-openai==1.1.11). Install in `.venv`.
3. RED tests — write 6 tests in
   `backend/tests/shared/agent_observability/cost/test_litellm_canonicalization.py`
   covering: A1 happy (canonical provider+cost), A2 unknown model → null cost,
   A3 p95 < 50ms (micro-benchmark), A4 calculate_cost not invoked, A5 bridge
   end-to-end, plus orphan TTL purge warning.
4. GREEN — create `cost_recorder.py` (NEW), modify `base_callback_handler.py`
   to derive provider via `litellm.get_llm_provider(model)[1]` + drop "/" strip
   (A1 keeps slashed) + consume `pop_cost(litellm_call_id)`.
5. Modify `cost/calculator.py` docstring → "reconciliation utility only".
6. Register `litellm.callbacks = [CostRecorderCustomLogger()]` in `main.py` +
   `workers/settings.py` (Worker + Scheduler `on_startup`).
7. Update existing test `test_callback_handler_litellm_strip.py` — A1 changes
   model to slashed, so test assertions need to flip from "stripped" to
   "preserved". Document in commit body.
8. Native lint + tests + arch fitness.
9. Commit with conventional message.

## Bitácora paso-a-paso

### 05:00 — Setup
- Read 01-spec.md, 03-arch-be.md, 04-tickets.yaml T-1 entry, 00-story.md.
- Confirmed scope is BE-only (no agentic/copilot file edits beyond `BaseAgentCallbackHandler` shared which is consumed by both — that file lives in `shared/`, not in `modules/copilot/` or `modules/sales_agent/`).
- Loaded skills: backend-expert + tessl__fastapi + tessl__pytest-api-testing + tessl__graceful-degradation.
- Step 0 grep gate PASSED — no existing patterns conflict.

### 05:05 — Dependency provisioning
- `litellm` not in `requirements-runtime.txt`. Architect spec assumes `import litellm` works.
- Pin chosen: `litellm>=1.50.0,<1.83` (1.83+ pins `openai==2.24.0` which conflicts with `langchain-openai==1.1.11` requiring `openai>=2.26.0`).
- Installed `litellm-1.82.6` in `.venv` (used `--no-deps` for the package install to avoid the openai downgrade, then re-pinned `openai>=2.26.0,<3.0.0`).
- Verified: `litellm.get_llm_provider("deepseek/deepseek-v4-flash")` → `('deepseek-v4-flash', 'deepseek', '<api_key>', 'https://api.deepseek.com/beta')`. Position 1 = canonical provider as architect noted.
- Verified: `litellm.callbacks` attribute exists, default `[]`.
- `BadRequestError` raised on truly unknown model (`'foo-unknown-model'` without provider prefix).

### Pending steps
- See plan above. Continuing.
