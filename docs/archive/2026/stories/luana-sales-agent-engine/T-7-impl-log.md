# T-7 — Lift sales_agent infrastructure/external/ + ws_manager (§3 protected hash-stable)

## Status: in_progress (builder-agentic Opus 4.7 batch 2)
## Validators targeted: V-NF-2, V-F-channels (channel format consumption)

## Skills Consulted

| Skill | Why | Decision |
|---|---|---|
| sales-agent-expert | §3 PROTECTED: output_manager.process_response chunking + SmartBufferService.smart_debounce_runner CPM. typing_simulation_cpm S12 registry override. Channel format SSoT lives in luana_core_channels. | Sed-only rewrites. NO logic refactor. Capture POST-sed sha256. |
| tessl__graceful-degradation | output_manager makes external HTTP calls (channel APIs) — timeout + fallback present. | Verify post-sed (preserve existing pattern). |
| backend-expert | OutputManager imports `from luana_core_channels.format import get_channel_format` (sed-converted). | Verify import path. |
| anti-duplication | Channel format dispatch lives in shared/luana_core_channels — never mirror. | Verify imports use luana_core_channels.* not local. |
| parallel-safety | Stage by exact filename. | luana-platform commit only. |

## Lift workflow

1. cp -r external + cp ws_manager.py
2. Apply sed (import-only — NO logic refactor)
3. Verify §3 protected files (3 in external + 1 ws_manager = 4 hash-stable post-sed)
4. Verify channel_format consumption via luana_core_channels
5. Verify typing_simulation_cpm registry override pattern preserved (S12)
6. Verify zero leaks
7. Commit
