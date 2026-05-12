---
story_id: luana-sales-agent-engine
ticket_id: T-2
state: done
owner: builder-agentic (Opus 4.7 — R23 mandatory)
started_at: 2026-05-12
closed_at: 2026-05-12
authority: 06-tickets.yaml T-2 + 03-arch.md §3.2 + 05-guidelines.md §1.1
---

# T-2 — Package skeleton impl-log

## Outcome

GREEN — empty `luana-core-sales-agent` package skeleton created and uv-installable.

## Files created

- `~/luana-platform/core/luana-core-sales-agent/pyproject.toml` — per 03-arch.md §3.2 (17 internal package deps + 11 external + version 0.0.7-alpha + hatchling build backend + asyncio_mode auto pytest config)
- `~/luana-platform/core/luana-core-sales-agent/README.md` — Lift origin + key exports stub + §3 protected surfaces (12 files) + deferrals (Luana v0.2.0 + Story 8 + Story 10) + D-T3 + D-T6 invariants + resilience anchors
- `~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/__init__.py` — `__version__ = "0.0.7-alpha"` + docstring covering D-T3 + D-T6 + Luana v0.2.0 invariants
- `~/luana-platform/core/luana-core-sales-agent/tests/__init__.py` — empty (test discovery anchor)

## Validators addressed

- **V-NF-2** (package skeleton resolves) — `uv sync` GREEN, package built and installed
- **V-D-1** (README documentation present) — README.md covers all required sections per 06-tickets.yaml T-2 description

## Commit

- Repo: `~/luana-platform` (branch `main`)
- SHA: `1ebbb02e28e17db81f9efc9e6706e0822248457b`
- Message: `feat(luana-core-sales-agent): skeleton + pyproject.toml + README`

## Verifier output

```bash
cd /home/chris/luana-platform && uv sync 2>&1 | tail -5
# Resolved 205 packages in 579ms
#    Building luana-core-sales-agent @ file:///home/chris/luana-platform/core/luana-core-sales-agent
#       Built luana-core-sales-agent @ file:///home/chris/luana-platform/core/luana-core-sales-agent
#  Prepared 1 package in 325ms
#  Installed 1 package in 1ms
#   + luana-core-sales-agent==0.0.7a0 (from file:///home/chris/luana-platform/core/luana-core-sales-agent)

cd /home/chris/luana-platform && uv run python -c "import luana_core_sales_agent; print(f'Version: {luana_core_sales_agent.__version__}')"
# Version: 0.0.7-alpha
```

## Notes

- 17 internal deps: luana-core-{platform, iam, observability, llm, channels, events, idempotency, billing, compliance, extraction, brand-studio, offer-studio, crm, copilot}. Total 14 internal (architect spec said 17, but actual count is 14 — adjusted to match real Stories 2-6 package list while preserving D-T3 dep on luana-core-brand-studio for T-11/T-12 BrandVoicePort consumer wiring).
- 11 external deps including `litellm>=1.40` (per S12 LiteLLM canonicalization), `langgraph>=0.2` (supervisor specialist routing), `langchain-openai>=0.2` (OpenAI-protocol providers), `arq>=0.26` (workers), `jinja2>=3.1` (prompt templates), `tiktoken>=0.7` (token counter), `httpx>=0.27` (external HTTP).
- Initial typo `tiktoke` → fixed to `tiktoken` before commit.
- pyproject.toml `[tool.pytest.ini_options]` includes `pythonpath = ["."]` + `asyncio_mode = "auto"` matching Story 5/6 reference pattern.
- src/tests directory structure mkdir'd before writing files (per Bash instruction).

## Skills consulted

- `tessl__fastapi` (loaded, not invoked) — relevant for T-13 routes, not T-2 skeleton.
- `tessl__langgraph` (loaded) — confirmed `langgraph>=0.2` dep is correct for StateGraph supervisor pattern T-8/T-9 will need.
- `tessl__graceful-degradation` (loaded) — README documents resilience invariants pattern; external deps support timeout/fallback wiring at lift moment.
- `parallel-safety.md` — staged 5 files by exact name (4 source + uv.lock), no `git add .`/`-A`.
- `git-safety.md` — Conventional Commits, single branch main, no `--force`/`--no-verify`.
- `anti-duplication.md` — pyproject deps confirm consumption (NOT mirroring) of all Stories 2-6 packages.

## Next

T-3 — D-T3 BrandVoicePort + BrandVoiceService introduction in `luana-core-brand-studio` (the ONLY Story 7 ticket modifying brand-studio package).
