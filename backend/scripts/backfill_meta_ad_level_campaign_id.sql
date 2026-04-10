-- =============================================================================
-- Backfill: meta ad-level rows missing campaign_id
-- =============================================================================
--
-- Context:
--   Before the fix in meta_provider._extract_meta_ads_by_ad (commit 2a02d721),
--   ad-level rows for Meta were stored with campaign_id=NULL because the
--   extractor's `fields` param did not request campaign_id and the loop
--   never assigned it. Those orphan rows look indistinguishable from
--   account-level rows to naive aggregations.
--
-- Fix scope:
--   This script recovers campaign_id by joining official_metrics against
--   the `ads` catalog table (which was populated by the campaign_sync_pipeline
--   and holds ad_id -> campaign_id mappings). It only touches rows where:
--     - ad_id IS NOT NULL
--     - campaign_id IS NULL
--     - a matching ad exists in `ads` with a non-null campaign_external_id
--
-- Idempotency:
--   Running multiple times is safe — the WHERE clause filters to rows where
--   campaign_id is still NULL, so subsequent runs become no-ops once backfilled.
--
-- Verification (run before/after for comparison):
--   SELECT COUNT(*) FROM official_metrics
--   WHERE ad_id IS NOT NULL AND campaign_id IS NULL;
--
-- Usage:
--   docker exec -i visionarias_postgres psql -U postgres -d visionarias_logs \
--     -f /path/to/this.sql
--   or:
--   docker exec -i visionarias_postgres psql -U postgres -d visionarias_logs \
--     < backend/scripts/backfill_meta_ad_level_campaign_id.sql
-- =============================================================================

BEGIN;

-- Report state before
\echo 'Orphan rows before backfill:'
SELECT COUNT(*) AS orphan_rows
FROM official_metrics
WHERE ad_id IS NOT NULL AND campaign_id IS NULL;

-- Backfill
UPDATE official_metrics om
SET campaign_id = a.campaign_external_id
FROM ads a
WHERE om.ad_id = a.external_id
  AND om.tenant_id = a.tenant_id
  AND om.provider = a.provider
  AND om.ad_id IS NOT NULL
  AND om.campaign_id IS NULL
  AND a.campaign_external_id IS NOT NULL;

-- Report state after
\echo 'Orphan rows after backfill:'
SELECT COUNT(*) AS orphan_rows
FROM official_metrics
WHERE ad_id IS NOT NULL AND campaign_id IS NULL;

\echo 'Rows backfilled per provider:'
SELECT provider, channel_slug, COUNT(*) AS total_ad_rows,
       COUNT(*) FILTER (WHERE campaign_id IS NOT NULL) AS with_campaign,
       COUNT(*) FILTER (WHERE campaign_id IS NULL) AS still_orphan
FROM official_metrics
WHERE ad_id IS NOT NULL
GROUP BY provider, channel_slug
ORDER BY provider, channel_slug;

COMMIT;
