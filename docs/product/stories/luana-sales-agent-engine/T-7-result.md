# T-7 result — Lift sales_agent infrastructure/external/ + ws_manager (§3 protected hash-stable)

## Status: GREEN
## Commit: 153b262 (luana-platform main) — AISALESHT untouched
## Validators satisfied: V-NF-2, V-F-channels (channel format consumption verified)
## Files lifted: 5 src

## Files (4 §3 protected hash-stable)

### infrastructure/external/ (4 files)
- output_manager.py (§3 PROTECTED — chunking + CPM_SPEED + S12 typing_simulation_cpm registry override)
- buffer_service.py (§3 PROTECTED — SmartBufferService.smart_debounce_runner CPM LATAM)
- safety_service.py (§3 PROTECTED)
- __init__.py

### infrastructure/ws_manager.py (§3 PROTECTED — WebSocket manager)

## §3 sha256 POST-sed POST-ruff canonical (V-AG-8 T-18 baseline)

| File | sha256 |
|---|---|
| external/output_manager.py | `9660a1dbef857164f5ea951a82e63cb115d202a01098430e2dba41b0d5ea7fc5` |
| external/buffer_service.py | `2a098923aecce2d6ae2ed9f908fb60d1da7d5e2312a3d44dd07b951819c006b3` |
| external/safety_service.py | `bc62b0990f5767a7b5f0930fe36d0692bec42557621b327d41cd5e6a25983edc` |
| ws_manager.py | `2348f92d1709c5846da3be197ded1e2f1ce00b46ca1e468218f561a862b429b3` |

Note: ws_manager.py sha256 unchanged pre/post-sed (no `src.*` imports needed rewrites).

## Verifications passed

### Channel format consumption (V-F-channels)
```
$ grep "from luana_core_channels" ~/luana-platform/.../external/output_manager.py
from luana_core_channels.format import get_channel_format ✓
```

### S12 typing_simulation_cpm registry override pattern preserved
```python
# output_manager.py:225-233
# typing_simulation_cpm for the channel, the per-channel CPM overrides the global CPM_SPEED.
# Falsy values (None / 0 / negative) fall back to CPM_SPEED so the §3 (S12 cement).
cpm = cls.CPM_SPEED
if channel_type:
    override = get_channel_format(channel_type).typing_simulation_cpm
    ...
```

## Tests GREEN: 17 (unchanged — output_manager + buffer_service tests need fixtures from T-12+)

```
$ cd ~/luana-platform && uv run pytest core/luana-core-sales-agent/tests/ -x -q
17 passed in 0.13s
```

## Verification recipes

```bash
# Zero src.* leaks ✓
grep -rEn "from src\." ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/external/  → empty
grep "from src\." ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/ws_manager.py  → empty

# AISALESHT untouched ✓
git diff HEAD --name-only | grep backend/src/modules/sales_agent  → empty
```

Last line: done -> docs/product/stories/luana-sales-agent-engine/T-7-result.md
