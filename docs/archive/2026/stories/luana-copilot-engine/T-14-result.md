---
story_id: luana-copilot-engine
ticket: T-14
status: GREEN
completed_at: 2026-05-11
verdict: done
---

# T-14 result — Lift copilot api/ layer

## Status: GREEN (lift integrity preserved — 40 PASS isolated)

## Commit
luana-platform main: (pending push)

## Validators satisfied
- V-NF-2 (verbatim lift fidelity — 21 src + 14 tests)

## Tests run
- 40 PASS isolated (voice + plan + media + knowledge_search + conversational_channel_port)
- Remaining tests deferred to T-15 (need full conftest with db_session fixture)

## Files lifted (21 src + 14 tests)
- 11 routers (chat, conversations, voice, telegram, plan, suggestions, actions, events, media, knowledge, nudge) + _dependencies
- 8 DTOs (conversation, document, media, suggestions, tenant_limits, voice, telegram, dto)
- 14 API tests across voice + plan + media + knowledge + conversation_security + e2e + channel_port

## Invariants preserved
- `FastAPI(redirect_slashes=False)` mandatory app-level — preserved
- `response_model=` mandatory per Tessl pii-sanitisation — preserved
- X-Tenant-ID header — preserved

## Next
T-15 — evals + utils + conftest + aggregate GREEN check.
