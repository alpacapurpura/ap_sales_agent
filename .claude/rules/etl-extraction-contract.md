---
globs: "backend/src/modules/analytics/**/*.py"
description: ETL extraction contract workflow — read/update/verify cycle
---

# ETL Extraction Contract — Always Read, Always Update

**Non-negotiable workflow rule** for any task touching analytics ETL pipeline. Contract = single source of truth for what we extract, from where, when, how, where it lands. Skip steps below → future Claude or human loses time rediscovering known info.

## Two files, two responsibilities

| File | Answers | Used at runtime? |
|---|---|---|
| `backend/src/modules/analytics/domain/metric_catalog.py` | "What does metric `X` **mean**? Is it ADDITIVE / WEIGHTED_AVERAGE / NON_AGGREGABLE / SNAPSHOT / DERIVED? Unit, display name, interpretation, benchmarks?" | **Yes** — read by `MetricResolver`, `aggregations.py`, stage services, `/api/v1/analytics/metrics/catalog`. |
| `backend/src/modules/analytics/domain/extraction_contract.py` | "Which provider extracts metric `X`? From which API endpoint? When? Under which credentials? Into which channel slug? Known issues?" | **No** — pure documentation + test enforcement. |

**Catalog = semantics. Contract = extraction reality.** Complementary, never duplicates. Architecture test `tests/architecture/test_extraction_contract.py` keeps them aligned: every metric in catalog whose `providers` tuple lists `X` MUST appear in `X`'s `ChannelOutput` in contract — or be explicitly allowlisted in `KNOWN_CATALOG_CONTRACT_GAPS` with audit reference.

## When you READ (questions about ETL)

If user asks anything like:

- "What does the ETL extract for `<provider>`?"
- "Where does `<metric>` come from?"
- "When does `<provider>` run?"
- "Why is `<channel>` empty?"
- "What's the status of the ETL?"
- "What providers do we support?"

**Step 1 (mandatory):** Read `docs/etl/extraction-contract.md` first. Human-readable Markdown auto-generated from contract — don't start by reading provider source files.

**Step 2 (only if needed):** If Markdown doesn't fully answer, open `backend/src/modules/analytics/domain/extraction_contract.py` for dataclass details — `known_issues`, `last_verified`, `notes`, `required_credentials` all there.

**Step 3 (only if step 2 insufficient):** Read actual provider source. If contract was wrong or incomplete, **MUST update contract before finishing task** (see "When you UPDATE"). Contract only valuable if it stays true.

## When you UPDATE (anything touching extraction)

Trigger: **any change** to:

- `backend/src/modules/analytics/infrastructure/providers/*.py`
- `backend/src/modules/analytics/infrastructure/etl/pipeline.py`
- `backend/src/modules/analytics/infrastructure/etl/period_pipeline.py`
- `backend/src/modules/analytics/infrastructure/etl/aggregations.py`
- `backend/src/modules/analytics/application/services/etl_service.py`
- `backend/src/modules/analytics/workers/scheduler.py`
- `backend/src/modules/analytics/workers/tasks.py`
- `backend/src/modules/analytics/domain/metric_catalog.py`
- `backend/src/workers/settings.py` (worker function registration)

### The 5-step ETL update workflow

1. **Implement change** in provider / pipeline / catalog file.
2. **Update contract entry** in `backend/src/modules/analytics/domain/extraction_contract.py`:
   - Added metric → add `MetricMapping` to right `ChannelOutput`.
   - Added channel → add `ChannelOutput` to right contract entry.
   - Added provider → create new `_<name>_contract()` factory, register in `EXTRACTION_CONTRACTS`.
   - Added API endpoint → add `APIEndpoint` to `api_endpoints`.
   - Discovered bug → append to `known_issues`.
   - Bump `last_verified` to today.
3. **If catalog (`metric_catalog.py`) changed**, re-check every catalog metric whose `providers` tuple lists provider `X` is also listed in `X`'s contract — test will catch it, but faster to fix proactively.
4. **Regenerate Markdown doc** (mandatory, FINAL STEP of every ETL change):
   ```bash
   cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py
   ```
   Or via Make:
   ```bash
   make extraction-contract
   ```
5. **Run architecture test** (runs in `make arch-test` and `/test-all`, but run explicitly when iterating):
   ```bash
   cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q
   ```

### What gets committed

Single ETL change commits **all four files** in same commit (provider, contract entry, regenerated Markdown, any test updates). Reviewers — including future Claude — read diff and immediately understand:

- What changed in provider
- How contract reflects it
- What user-facing docs now say
- That architectural test still passes

Commit only provider change without contract update → architecture test fails on next CI run for someone else.

## The 5-step rule applies even when

- "Just" added new metric to existing channel.
- "Just" renamed channel slug.
- "Just" fixed bug in parsing logic that changes which API field maps to which metric.
- "Just" added `# noqa` comment proving metric isn't actually emitted anymore.
- "Just" changed cron schedule of worker.

Every change invalidates a piece of contract. Test will fail. Update it.

## Best practices for extraction code

Patterns existing providers follow. Apply when adding/modifying providers — update contract entry to reflect any deviation.

### Reliability

1. **Wrap sub-extractors in `_safe_extract`** so partial failures land in `extraction_runs.sub_extractor_failures` and don't sink whole run.
2. **Convert credential errors to `ConnectionRevokedException`** (`RefreshError`, `TransportError`, `invalid_grant`) so worker stops retrying with Fibonacci backoff and user can be notified.
3. **Never silently swallow exceptions.** If must catch, log with `logger.exception`, tag Sentry event with `provider` + `sub_extractor`.
4. **Commit `ExtractionRun` row before try block.** `pipeline.py` and `period_pipeline.py` already do this — never revert. Without commit, later `db.rollback()` wipes run row and `update_status` raises misleading "ExtractionRun not found" hiding real failure.
5. **Filter every query by `tenant_id`.** Even internal providers like `crm_internal` must scope by tenant.
6. **Make every upsert idempotent.** Use `ON CONFLICT (tenant_id, provider, channel_slug, metric_name, metric_date) DO UPDATE` for `official_metrics`, equivalent natural key for `period_metrics` and `metric_aggregations`.

### Correctness

7. **Period-aggregated rows MUST NOT land in `official_metrics`.** Meta `/insights` calls at `account`/`campaign`/`ad` level MUST pass `time_increment=1`. Architecture test `test_meta_provider_invariants.py` enforces this — if genuinely need period aggregate, route through `extract_period_metrics` and `period_metrics` table, add function to `ALLOWED_PERIOD_FUNCTIONS`.
8. **Currency must come from data source, never hardcoded.** See `.claude/rules/currency-handling.md` and `.claude/rules/master-data.md`. Every provider emitting monetary metrics MUST resolve source currency (from ad account, shop, etc.) and emit on `ExtractedMetric.currency`.
9. **All datetimes UTC in DB.** Use `utc_now()` from `shared/domain/datetime_utils.py`. Per-tenant timezones in `TenantLocale`.
10. **Channel slugs follow stage convention.** Email channels: `email-{stage}` (`email-capture`, `email-nurture`, …). Meta channels: `ig-organic`, `fb-organic`, `meta-ads`, `meta-pixel`. Stick to existing patterns when adding new provider.

### Observability

11. **Log every sub-extractor start + complete + failure** with `extractor_name` and `provider` tags.
12. **Populate `cost_type`** via `get_cost_type(channel_slug, stage)` so dashboard can group by paid / owned / earned.
13. **Use `extra` JSONB for breakdowns and metadata** that don't fit in single `value` column (top queries, demographic dimensions, video retention curves). Document schema in contract entry's `notes`.

### Multi-stage providers

14. **Multi-stage provider (Shopify, MailerLite) iterates `PROVIDER_STAGES[provider_name]` inside `etl_service.run_extraction`.** Each stage produces own channel slugs. Known issue: if stage A succeeds and stage B fails, A is committed but run row reports B's status. Document in `known_issues` until fixed.

### Pass-through providers

15. **Some providers (Manychat) are pass-through by design.** Their `extract_metrics` returns empty `ExtractionResult` because data arrives via webhooks. Mark as `ProviderStatus.PASS_THROUGH` in contract. NOT bugs — documentation that scheduler should still see them so cache invalidation works.

## Anti-patterns to refuse

If user (or you) about to do any of these, stop and fix properly or document in `known_issues`:

- ❌ Adding provider to `PROVIDER_REGISTRY` without contract entry → `test_every_registered_provider_has_contract` will fail.
- ❌ Editing provider's `provider_name()` without updating contract key → `test_contract_provider_name_matches_class` will fail.
- ❌ Adding metric to `metric_catalog.py` with `providers=("foo",)` when `foo`'s contract doesn't emit that metric → `test_catalog_metrics_appear_in_contract` will fail.
- ❌ Editing provider but skipping `make extraction-contract` → `test_generated_markdown_is_up_to_date` will fail.
- ❌ Adding `# type: ignore` or `# noqa` to silence architecture test instead of fixing drift → architectural test for reason; don't disable it.
- ❌ Bypassing contract because "it's just a small change" → no such thing as small change to ETL; data integrity depends on this.

## Quick reference commands

```bash
# Read the contract (humans + LLMs)
cat docs/etl/extraction-contract.md | less

# Edit the contract (Python — single source of truth)
$EDITOR backend/src/modules/analytics/domain/extraction_contract.py

# Regenerate the Markdown after editing the Python contract
cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py
# or:
make extraction-contract

# Verify the contract still matches reality
cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q

# Sample what each provider has actually populated in production (Visionarias)
ssh -i ~/.ssh/id_rsa -p 22022 root@161.132.41.191 \
  'docker exec visionarias_postgres psql -U postgres -d visionarias_logs --pset=pager=off \
   -c "SELECT provider, channel_slug, metric_name, COUNT(*) c, MIN(metric_date) min_d, MAX(metric_date) max_d \
       FROM official_metrics \
       WHERE tenant_id='\''9831cfbe-3912-429e-a944-40f3e7bf1372'\'' \
       GROUP BY provider, channel_slug, metric_name ORDER BY provider, channel_slug;"'
```

## Memory anchor

Future Claude reading this rule: user asks ANY question about ETL, analytics pipeline, providers, metrics, channels, or data source — **first action** is read `docs/etl/extraction-contract.md`. Before writing any code in `backend/src/modules/analytics/`, **first action** is read this rule and contract. Done modifying anything in `analytics/` — **last action** is `make extraction-contract && pytest tests/architecture/test_extraction_contract.py`. No exceptions.