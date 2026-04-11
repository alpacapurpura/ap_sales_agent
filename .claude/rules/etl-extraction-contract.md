# ETL Extraction Contract — Always Read, Always Update

This is a **non-negotiable workflow rule** for any task that touches the analytics ETL pipeline. The contract is the single source of truth for what we extract, from where, when, how, and where it lands. If you skip the steps below, future Claude (or the next human) will lose minutes/hours rediscovering what you already knew.

## Two files, two responsibilities

| File | Answers | Used at runtime? |
|---|---|---|
| `backend/src/modules/analytics/domain/metric_catalog.py` | "What does metric `X` **mean**? Is it ADDITIVE / WEIGHTED_AVERAGE / NON_AGGREGABLE / SNAPSHOT / DERIVED? What's its unit, display name, interpretation, benchmarks?" | **Yes** — read by `MetricResolver`, `aggregations.py`, stage services, `/api/v1/analytics/metrics/catalog`. |
| `backend/src/modules/analytics/domain/extraction_contract.py` | "Which provider extracts metric `X`? From which API endpoint? When? Under which credentials? Into which channel slug? With what known issues?" | **No** — pure documentation + test enforcement. |

**Catalog = semantics. Contract = extraction reality.** They are complementary, never duplicates. The architecture test `tests/architecture/test_extraction_contract.py` is the invariant that keeps them aligned: every metric in the catalog whose `providers` tuple lists `X` MUST appear in `X`'s `ChannelOutput` in the contract — or be explicitly allowlisted in `KNOWN_CATALOG_CONTRACT_GAPS` with an audit reference.

## When you READ (questions about ETL)

If the user asks anything like:

- "What does the ETL extract for `<provider>`?"
- "Where does `<metric>` come from?"
- "When does `<provider>` run?"
- "Why is `<channel>` empty?"
- "What's the status of the ETL?"
- "What providers do we support?"

**Step 1 (mandatory):** Read `docs/etl/extraction-contract.md` first. It is human-readable Markdown auto-generated from the contract — do not start by reading the provider source files.

**Step 2 (only if needed):** If the Markdown doesn't fully answer the question, open `backend/src/modules/analytics/domain/extraction_contract.py` (the Python source) for the dataclass details — `known_issues`, `last_verified`, `notes`, `required_credentials` are all in there.

**Step 3 (only if step 2 doesn't suffice):** Read the actual provider source. If you find that the contract was wrong or incomplete, **you MUST update the contract before you finish the task** (see "When you UPDATE" below). The contract is only valuable if it stays true.

## When you UPDATE (anything that touches extraction)

The trigger for this workflow is **any change** to:

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

1. **Implement the change** in the provider / pipeline / catalog file.
2. **Update the contract entry** in `backend/src/modules/analytics/domain/extraction_contract.py`:
   - If you added a metric, add a `MetricMapping` to the right `ChannelOutput`.
   - If you added a channel, add a `ChannelOutput` to the right contract entry.
   - If you added a provider, create a new `_<name>_contract()` factory and register it in `EXTRACTION_CONTRACTS`.
   - If you added an API endpoint, add an `APIEndpoint` to `api_endpoints`.
   - If you discovered a bug, append to `known_issues`.
   - Bump `last_verified` to today's date.
3. **If the catalog (`metric_catalog.py`) changed**, re-check that every catalog metric whose `providers` tuple lists provider `X` is also listed in `X`'s contract — the test will catch you if you don't, but it's faster to fix proactively.
4. **Regenerate the Markdown doc** (this is mandatory and is the FINAL STEP of every ETL change):
   ```bash
   cd backend && .venv/bin/python scripts/generate_extraction_contract_doc.py
   ```
   Or via Make:
   ```bash
   make extraction-contract
   ```
5. **Run the architecture test** (it runs in `make arch-test` and `/test-all`, but you should run it explicitly when iterating):
   ```bash
   cd backend && .venv/bin/pytest tests/architecture/test_extraction_contract.py -x -q
   ```

### What gets committed

A single ETL change should commit **all four files** in the same commit (provider, contract entry, regenerated Markdown, and any test updates). Reviewers — including future Claude — should be able to read the diff and immediately understand:

- What changed in the provider
- How the contract reflects it
- What the user-facing docs now say
- That the architectural test still passes

If you commit only the provider change without the contract update, the architecture test will fail on the next CI run for someone else. Don't be that commit.

## The 5-step rule applies even when

- You "just" added a new metric to an existing channel.
- You "just" renamed a channel slug.
- You "just" fixed a bug in the parsing logic that changes which API field maps to which metric.
- You "just" added a `# noqa` comment that proves a metric isn't actually emitted any more.
- You "just" changed the cron schedule of a worker.

Every one of those changes invalidates a piece of the contract. The test will fail. Update it.

## Best practices for extraction code

These are the patterns the existing providers follow. Apply them when adding/modifying providers — and update the contract entry to reflect any deviation.

### Reliability

1. **Wrap sub-extractors in `_safe_extract`** so partial failures land in `extraction_runs.sub_extractor_failures` and don't sink the whole run.
2. **Convert credential errors to `ConnectionRevokedException`** (`RefreshError`, `TransportError`, `invalid_grant`) so the worker stops retrying with Fibonacci backoff and the user can be notified.
3. **Never silently swallow exceptions.** If you must catch, log with `logger.exception` and tag the Sentry event with `provider` + `sub_extractor`.
4. **Commit the `ExtractionRun` row before the try block.** The `pipeline.py` and `period_pipeline.py` already do this — never revert it. Without the commit, a later `db.rollback()` wipes the run row and `update_status` raises a misleading "ExtractionRun not found" that hides the real failure.
5. **Filter every query by `tenant_id`.** Even internal providers like `crm_internal` must scope by tenant.
6. **Make every upsert idempotent.** Use `ON CONFLICT (tenant_id, provider, channel_slug, metric_name, metric_date) DO UPDATE` for `official_metrics`, and the equivalent natural key for `period_metrics` and `metric_aggregations`.

### Correctness

7. **Period-aggregated rows MUST NOT land in `official_metrics`.** Meta `/insights` calls at the `account`/`campaign`/`ad` level MUST pass `time_increment=1`. The architectural test `test_meta_provider_invariants.py` enforces this — if you genuinely need a period aggregate, route it through `extract_period_metrics` and the `period_metrics` table, and add the function to `ALLOWED_PERIOD_FUNCTIONS`.
8. **Currency must come from the data source, never hardcoded.** See `.claude/rules/currency-handling.md` and `.claude/rules/master-data.md`. Every provider that emits monetary metrics MUST resolve the source currency (from the ad account, the shop, etc.) and emit it on the `ExtractedMetric.currency` field.
9. **All datetimes are UTC in the DB.** Use `utc_now()` from `shared/domain/datetime_utils.py`. Per-tenant timezones live in `TenantLocale`.
10. **Channel slugs follow the stage convention.** Email channels are `email-{stage}` (`email-capture`, `email-nurture`, …). Meta channels are `ig-organic`, `fb-organic`, `meta-ads`, `meta-pixel`. Stick to existing patterns when adding a new provider.

### Observability

11. **Log every sub-extractor start + complete + failure** with `extractor_name` and `provider` tags.
12. **Populate `cost_type`** via `get_cost_type(channel_slug, stage)` so the dashboard can group by paid / owned / earned.
13. **Use `extra` JSONB for breakdowns and metadata** that don't fit in a single `value` column (top queries, demographic dimensions, video retention curves). Document the schema in the contract entry's `notes`.

### Multi-stage providers

14. **A multi-stage provider (Shopify, MailerLite) iterates `PROVIDER_STAGES[provider_name]` inside `etl_service.run_extraction`.** Each stage produces its own channel slugs. Known issue: if stage A succeeds and stage B fails, A is committed but the run row reports B's status. Document this in `known_issues` until it is fixed.

### Pass-through providers

15. **Some providers (Manychat) are pass-through by design.** Their `extract_metrics` returns an empty `ExtractionResult` because data arrives via webhooks. Mark them as `ProviderStatus.PASS_THROUGH` in the contract. They are NOT bugs — they are documentation that the scheduler should still see them so cache invalidation works.

## Anti-patterns to refuse

If a user (or you) is about to do any of these, stop and either fix it properly or document it explicitly in `known_issues`:

- ❌ Adding a provider to `PROVIDER_REGISTRY` without a contract entry → `test_every_registered_provider_has_contract` will fail.
- ❌ Editing a provider's `provider_name()` without updating the contract key → `test_contract_provider_name_matches_class` will fail.
- ❌ Adding a metric to `metric_catalog.py` with `providers=("foo",)` when `foo`'s contract doesn't emit that metric → `test_catalog_metrics_appear_in_contract` will fail.
- ❌ Editing a provider but skipping `make extraction-contract` → `test_generated_markdown_is_up_to_date` will fail.
- ❌ Adding a `# type: ignore` or `# noqa` to silence the architecture test instead of fixing the drift → it's an architectural test for a reason; don't disable it.
- ❌ Bypassing the contract because "it's just a small change" → there is no such thing as a small change to the ETL; data integrity depends on this.

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

Future Claude reading this rule: when the user asks ANY question about the ETL, the analytics pipeline, providers, metrics, channels, or where data comes from — your **first action** is to read `docs/etl/extraction-contract.md`. Before you write any code in `backend/src/modules/analytics/`, your **first action** is to read this rule and the contract. When you're done modifying anything in `analytics/`, your **last action** is `make extraction-contract && pytest tests/architecture/test_extraction_contract.py`. There are no exceptions.
