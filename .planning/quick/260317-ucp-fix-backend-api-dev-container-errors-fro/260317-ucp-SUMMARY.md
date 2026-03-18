# Quick Task 260317-ucp: Fix backend api_dev container crash

**Date:** 2026-03-18
**Status:** Complete (no code changes)

## Root Cause

The `api_dev` container was crashing in a loop with:
```
ImportError: cannot import name 'START' from 'langgraph.graph'
```

**Import chain:** `main.py` → `brand/api/style.py` → `copilot/agents/style_analyzer/graph.py` → `from langgraph.graph import START, END`

The container had `langgraph==0.0.24` installed, but `requirements-runtime.txt` was updated to `langgraph==1.1.2` in quick task 260317-naa (langchain/langgraph migration). The container was never rebuilt after that change.

## Fix Applied

1. `docker compose build api_dev` — rebuilt container image with updated requirements
2. `docker compose up -d api_dev` — recreated container from new image
3. Verified: `langgraph==1.1.2` now installed, uvicorn starts cleanly

## No Code Changes

The code was already correct (updated in 260317-naa). Only the container image was stale.
