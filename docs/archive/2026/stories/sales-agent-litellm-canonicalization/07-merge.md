# 07-merge — Story A: sales-agent-litellm-canonicalization

**PM ratification:** PROCEED to /pase-produccion
**Story:** sales-agent-litellm-canonicalization
**Sprint:** S1-eval-runner / PI-12
**Ratified by:** /pm orchestrator (Opus 4.7) per Chris pre-authorization
**Date:** 2026-05-06

## Merge approval

All 11 tickets resolved (10 audit-APPROVED + 1 PM-ratified operational gate per R7). REVIEW-final.md verdict: APPROVED. Ready for /pase-produccion deploy.

## Final commits on `development` (Story A scope)

- `5856be4d` feat(pi-12-T-1): cost recorder canonicalization
- `3cb98fd4` feat(pi-12-T-1.bis): test bridge migration
- `8b6d798f` feat(pi-12-T-2): make sync-pricing extension
- `71f39529` + `4193cbb3` feat(pi-12-T-3): Alembic migration repair
- `38f7e1b7` feat(pi-12-T-7): tests audit ~20 files migration
- `429913a3` feat(pi-12-T-4): DELETE 6 legacy adapters + Gemini audit 6/6
- `28617716` + `560f14b5` feat(pi-12-T-5): kill flag LITELLM_PROXY_ENABLED
- `f6e7ad0a` + `29b97eba` feat(pi-12-T-6a): Phase 1 deprecate tenant API keys
- `253e6024` test(pi-12-T-8): arch fitness ratchet + meta-test
- `aabd3acc` + `c93ba549` docs(pi-12-T-9): purge stale references + learnings.md
- `a10e146c` + `dc1714d0` feat(pi-12-T-6c): Phase 3 DROP COLUMN final

Plus closure docs commits (Wave 2/3/4/5/6/7 closures): `ec777a08`, `3ff20d6b`, `57b3eadc`, `42f4a0f8`, `467e04f3`, plus this Wave 8 closure commit (TBD).

## Decisions ratified (binding cross-PI)

All A1/A2/A3/A4/A5/A6/X1/X2/B1-B7 decisions per architect 03-arch-be.md + 03-arch-agentic.md. See REVIEW-final.md § "Decisions ratified".

## pm-nico/current-state updates (Chris ratification needed at /pase-produccion)

### `docs/product/modules/sales-agent.md` § "LLM routing"
**Status:** Updated by T-9 builder. PM ratification pending /pase-produccion verification.

Changes:
- LiteLLM Proxy = canonical único path (post-T-5 flag deletion)
- 6 legacy per-provider adapters deleted (post-T-4)
- 4 tenant API key columns deprecated + dropped (post T-6a + T-6c)
- `gemini_api_key` retained throughout
- Cost recorder via `CostRecorderCustomLogger` bridge (T-1)

### `docs/domains/llm-routing.md`
**Status:** Updated by T-9 builder.

Changes:
- "Capa 5 — LiteLLM Proxy (rollback)" section DELETED
- "LiteLLM Proxy = canonical único" section rewritten
- NEW `## CustomLogger pattern (cost recorder)` section documenting T-1 bridge LangChain↔LiteLLM + 60s TTL cache

### `docs/domains/tech_module_shared.md`
**Status:** Updated by T-9 builder.

Changes:
- Removed LITELLM_PROXY_ENABLED references
- Removed legacy adapter list
- Reflects post-canonicalization state

### `.claude/rules/anti-default-flip-audit.md` inventory
**Status:** Updated by T-5 builder.

Changes:
- LITELLM_PROXY_ENABLED row REMOVED from inventario table
- Footnote ADDED: "removed PI-12 S1 sales-agent-litellm-canonicalization T-5 — legacy adapters deleted T-4. The LiteLLM Proxy is now the only runtime LLM dispatch path — there is no fallback toggle to audit."

### `learnings.md` (NEW story-level)
**Status:** Created by T-9 builder.

Captures:
- CostRecorderCustomLogger NEW class justification (T-1)
- T-6b operational gate rationale (R7 pre-clientes 1d)
- A3 gemini audit results (T-4) — 6/6 PASS + LOC correction (99 not 320)

## /pase-produccion handoff

**Pre-deploy verification:**
- HEAD `development`: latest closure commit (Wave 8 closure pending)
- All audit-passed tickets present
- Pre-commit hooks pass (voseo + ruff + R3 SSoT freshness)
- Ratchet gates 827/827 PASS

**Deploy steps (per /pase-produccion SKILL):**
1. Merge `development` → `main`
2. Run `/test-all` natively (BE 9070+ PASS + FE if applicable + arch 827 PASS)
3. `git push origin main` (triggers GitHub Actions auto-deploy)
4. Monitor workflow until deployment completes
5. Post-deploy verification:
   - `docker exec visionarias_brain_dev alembic current` → reads as `124_drop_tenant_provider_api_keys`
   - `docker exec visionarias_postgres_dev psql -c '\d tenants'` → 4 deprecated cols ABSENT, gemini_api_key PRESENT
   - Streamlit `/admin/llm_virtual_keys` panel: SELECT COUNT(*) WHERE 4 deprecated cols IS NOT NULL = 0 → confirms T-6b operational gate auto-promotion
   - LiteLLM proxy reachability check (main.py boot)
   - First sales_agent invocation: `sales_agent_llm_call` row provider canonical (deepseek/kimi/openai/qwen/gemini), cost_usd > 0

**Post-deploy ratification:**
- /pm marks T-6b state `pushed` → `verified` post-Streamlit query
- /pm updates docs/product/modules/sales-agent.md § "LLM routing" canonical state per /pase-produccion log evidence
- Sprint.md status → done

## Cross-references

- REVIEW-final.md: this story's full audit summary
- 04-tickets.yaml: 11 tickets with all transitions to audit-passed
- checkpoint.md: bitácora chronological closure
- Architect spec: 03-arch-be.md
- Spec: 01-spec.md (Gherkin AI-resistant 4 scenarios)
- Story YAML: docs/product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml
