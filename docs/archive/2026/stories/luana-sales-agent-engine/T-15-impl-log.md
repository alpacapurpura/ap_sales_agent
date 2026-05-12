# T-15 Implementation Log

**Ticket:** Lift sales_agent copilot_provider/provider.py (subclasses luana-core-copilot BaseCopilotProvider)
**Owner:** builder-agentic Opus 4.7 (R23 mandatory)
**Date:** 2026-05-12
**Status:** GREEN
**Commit (luana-platform):** `c82a3f2`

## Skills Consulted

- **copilot-expert** — "Provider pattern (F1) + discovery (convention + entry points)" cardinal. New modules register via `[project.entry-points."nicolify.copilot_providers"]` (Story 6 pattern). Discovery scans entry-points + convention path. ModuleRegistry built from providers via `BaseCopilotProvider.module_data()`.
- **sales-agent-expert** — copilot_provider lift is mechanical (1 file SalesAgentCopilotProvider + entry-point registration). No §3 protected surfaces here.
- **.claude/rules/anti-duplication.md** — copilot_provider/ is sales-agent module-specific; no shared base mirror concern (the abstraction lives at `luana_core_copilot.domain.ports.BaseCopilotProvider`, and sales-agent CONSUMES it correctly).

## Workflow

1. **Inspected source** — copilot_provider has only 2 files (provider.py + __init__.py). Provider subclasses `src.modules.copilot.domain.ports.BaseCopilotProvider`.
2. **cp -r** the directory.
3. **Applied sed** — `from src.modules.copilot.` → `from luana_core_copilot.`, plus the standard self-reference + shared substitutions.
4. **Verified zero leaks** — grep clean.
5. **Smoke import** — initial test failed because `provider` is exposed in __init__.py, not provider.py. Adjusted import path: `from luana_core_sales_agent.copilot_provider import provider`. Verified subclass + isinstance assertions PASS.
6. **Tested ModuleRegistry discovery** — discovery did NOT pick up sales_agent initially because no entry-point registered in pyproject.toml. Discovery scans `nicolify.copilot_providers` entry-points + convention paths. Convention root `src.modules` doesn't exist in workspace, so entry-points is the only path.
7. **Added entry-point** to luana-core-sales-agent/pyproject.toml:
   ```toml
   [project.entry-points."nicolify.copilot_providers"]
   sales_agent = "luana_core_sales_agent.copilot_provider:provider"
   ```
8. **Ran `uv sync`** to reinstall package and register entry-point metadata.
9. **Re-verified discovery** with cache reset — sales_agent now in registry keys.
10. **Ruff check passed** + AISALESHT untouched + committed.

## Verification matrix

| Check | Status | Evidence |
|---|---|---|
| AISALESHT untouched | OK | `git diff HEAD --name-only \| grep sales_agent` empty |
| Zero `src.*` leaks | OK | grep clean over copilot_provider/ |
| Provider subclass | OK | `issubclass(SalesAgentCopilotProvider, BaseCopilotProvider)` PASS |
| Provider instance | OK | `isinstance(provider, BaseCopilotProvider)` PASS |
| ModuleData populated | OK | module_id='sales_agent', label='Sales Agent', route_prefix='sales' |
| Discovery + ModuleRegistry pick up sales_agent | OK | `'sales_agent' in get_module_registry()` PASS |
| Ruff clean | OK | All checks passed |

## Test execution

Discovery smoke output:
```
2026-05-12 01:09:32 [info] copilot.discovery.complete
  convention=[]
  entry_points=['analytics', 'brand', 'commercial_calendar', 'connections', 'crm', 'landing', 'offer', 'sales_agent', 'social_proof']
  merged=['analytics', 'brand', 'commercial_calendar', 'connections', 'crm', 'landing', 'offer', 'sales_agent', 'social_proof']

Module registry keys: ['analytics', 'brand', 'commercial_calendar', 'connections', 'crm', 'landing', 'offer', 'sales_agent', 'social_proof']

PASS: sales_agent discovered + in module_registry
```

9 modules now discovered (8 from Story 6 + Story 7 sales_agent). Adding sales_agent does NOT regress any existing discovery.

## Cardinal invariants honored

- ★ AISALESHT UNTOUCHED (V-NF-4 cardinal)
- ★ Provider subclasses BaseCopilotProvider (F1 pattern preserved from Story 6 cement)
- ★ Entry-point registration follows Stories 5+6 pattern (brand-studio, offer-studio, etc.)
- ★ ModuleRegistry discovery picks up sales_agent (T-15 ticket cardinal)
- ★ D-T3 hexagonal cement preserved (zero PersonalityCompiler imports)
- ★ D-T6 anti-mirror preserved (no observability bases touched)

## Notes for T-16+

- ModuleRegistry now has 9 modules. Story 4 `luana-core-connections/api/dependencies/__init__.py` NotImplementedError stub (Stories 4+6 deferral) can now be resolved in T-16 with real ChatOrchestrator wiring (both luana_core_copilot + luana_core_sales_agent available).
- Future Story 8 (campaigns/scheduling lift) will further expand discovery (scheduling module → entry-point similar pattern).
