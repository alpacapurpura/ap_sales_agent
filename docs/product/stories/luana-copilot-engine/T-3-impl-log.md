# T-3 impl log

## Status: GREEN (within T-3 DAG scope — self-contained domain tests pass)
## Commit: 63b069c (luana-platform main) — AISALESHT untouched
## Validators satisfied: V-NF-2 (package builds + tests collect), V-F-registry-2 (ModuleDescriptor + Workflow + RoutingPolicy preserved verbatim)
## Files touched: 41 (33 src + 7 test + several __init__.py inherited from cp -r)

## Source files lifted (33 .py)

```
domain/__init__.py
domain/card_payloads.py            # 20 CardPayload schemas (PlanCard, ProposalCard, Clarify, etc.)
domain/context_window.py
domain/events.py                   # 6 domain events (TurnStarted/Ended, RoutingDecided, CardEmitted, SuggestionShown/Accepted)
domain/extraction_domain_registry.py  # ExtractionDomainConfig
domain/field_paths_hint.py
domain/hooks/__init__.py
domain/hooks/copilot_events.py     # 10 hook events (ConversationCreated, MessageReceived/Sent, MutationApplied/Reverted, PlanProposed/Resolved, ProcedureAdvanced/Completed, TierDecided)
domain/hooks/hook_registry.py      # HookRegistry Protocol
domain/message.py
domain/message_blocks.py
domain/module_registry.py          # ModuleDescriptor + get_module_registry (D-T1 frozen)
domain/mutation_journal.py
domain/navigation_map.py
domain/offer_fields.py
domain/plan_state.py
domain/ports.py                    # Workflow re-export + ProcedureState provider port
domain/procedure_state.py
domain/routing_policy.py           # RoutingPolicy + ClassifierType
domain/rules/__init__.py
domain/rules/rule_definition.py
domain/rules/rule_metadata.py
domain/rules/rule_registry.py
domain/schema_introspection.py
domain/skills/__init__.py
domain/skills/skill_definition.py
domain/skills/skill_metadata.py
domain/skills/skill_registry.py
domain/suggestion.py               # Suggestion + SuggestionCategory + SuggestionContext (D-T1 frozen)
domain/telegram.py
domain/tenant_limits.py
domain/voice.py
domain/workflow.py                 # Workflow dataclass (D-T1 frozen — preserved verbatim)
```

## Tests lifted (7 .py — only those existing in AISALESHT path for domain scope)

```
tests/test_module_registry.py             # cross-layer dep (needs application.discovery — T-12)
tests/test_extraction_domain_registry.py  # self-contained ✓
tests/test_field_paths_hint.py            # cross-layer dep (needs brand/offer copilot_provider — T-16)
tests/test_message_blocks.py              # self-contained ✓
tests/domain/__init__.py
tests/domain/test_events.py               # self-contained ✓
tests/domain/test_provider_ports.py       # self-contained ✓
tests/domain/test_routing_policy.py       # self-contained ✓
```

Architect's T-3 step 3 listed 18 test names; only 7 actually exist in AISALESHT for domain scope (architect spec was approximate; ALL extant domain tests were lifted).

## Validation runs

### Self-contained domain tests (T-3 scope):
```
pytest core/luana-core-copilot/tests/test_message_blocks.py \
       core/luana-core-copilot/tests/test_extraction_domain_registry.py \
       core/luana-core-copilot/tests/domain/ -x -q
→ 75 passed in 0.13s ✓
```

### Cross-layer tests (T-3 stage — EXPECTED to need later layers):
- `test_module_registry.py` → fails at `from luana_core_copilot.application.discovery import discover_providers` (application/ not lifted; T-12 lifts).
- `test_field_paths_hint.py` → fails at empty hint (needs brand-studio + offer-studio copilot_provider/ subfolders registered via discover_providers; T-16 unlifts).

Per architect's DAG: these become GREEN at T-12 (application/discovery lift) + T-16 (unlift Stories 2-5 copilot_provider/ subfolders + ModuleRegistry discovery). NOT a T-3 failure — by design.

## Verification recipes (05-guidelines.md §8 partial — full applies post-T-15)

```bash
# Zero src.modules.* / src.shared.* / src.core.* leaks ✓
grep -rEn "from src\.(modules|shared|core)\." src/ → empty
grep -rEn "from luana_core_(sales_agent|campaigns|advertising|social_media|scheduling)\." src/ → empty (no forward-Story)
```

## Class preservation (D-T1 partial cement)

| Class | File | Status |
|---|---|---|
| `ModuleDescriptor` | domain/module_registry.py | preserved ✓ |
| `Workflow` | domain/workflow.py | preserved ✓ |
| `RoutingPolicy` | domain/routing_policy.py | preserved ✓ |
| `ClassifierType` | domain/routing_policy.py | preserved ✓ |
| `Suggestion` + `SuggestionContext` + `SuggestionCategory` | domain/suggestion.py | preserved ✓ |
| `ExtractionDomainConfig` | domain/extraction_domain_registry.py | preserved ✓ |
| 20 CardPayload classes | domain/card_payloads.py | preserved ✓ |
| 6 events + 10 hook events | events.py + hooks/copilot_events.py | preserved ✓ |
| HookRegistry Protocol | hooks/hook_registry.py | preserved ✓ |

`ToolRegistry` / `WorkflowRegistry` / `ExtractorRegistry` / `SuggestionRegistry` proper live in `application/` layer — lifted in T-10/T-11 (not T-3 scope).

## [COPILOT-*] anchors in domain layer

8 anchors detected in domain/ (subset of 36 total project-wide). Full count enforced at T-20 V-AG-8 (test_copilot_anchors_count_stable.py).

## Skills consulted (R23 enforcement)

- `copilot-expert` — domain layer = SSoT for `ModuleDescriptor` + provider port contract. D-T1 cardinal: registry public APIs FROZEN at lift moment. 36-anchor cap enforced T-20.
- `sales-agent-expert` §0 — confirmed shared/agent_observability/ paths rewrite via sed to `luana_core_observability.*` per anti-duplication.md inventory.
- `tessl__langgraph` — T-3 does not touch LangGraph (orchestrator/ = T-9 scope). Domain ports are LangGraph-agnostic Protocols.
- `backend-expert` (architectural-fitness.md) — domain pure (no framework imports beyond Pydantic + stdlib). Verified — no FastAPI / SQLA imports in domain/.
- Rules: `anti-duplication` (no observability mirrors at this layer — domain doesn't touch observability), `backend-ddd` (Inside-Out preserved), `tenant-isolation` (domain ports take tenant_id), `parallel-safety` (staged by name, 41 files explicit).

## Steps executed

1. `cp -r backend/src/modules/copilot/domain/ luana-platform/.../luana_core_copilot/`
2. Clean __pycache__ → 33 .py files
3. Apply 23 sed substitutions per 05-guidelines.md §1.3 (mechanical import path rewrites)
4. Verify zero `src.modules.*` / `src.shared.*` / `src.core.*` leaks → OK
5. Verify zero forward-Story imports (sales_agent/campaigns/etc.) → OK
6. Copy 4 top-level + 3 domain-subdir tests (only those existing in AISALESHT for scope)
7. Apply same sed on tests
8. Run self-contained domain tests → 75 passed
9. Stage 41 files by exact name (no `git add .` per parallel-safety.md)
10. Conventional commit + push origin main
