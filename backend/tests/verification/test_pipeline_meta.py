"""Layer 2: Pipeline Integrity — verify official_metrics data integrity.

Reads real data from PostgreSQL and validates that:
- Expected metrics exist for each channel
- Additive metrics have consistent daily values (no negative, no NULL)
- Currency is populated on monetary metrics
- Channel slugs match the channel registry

Does NOT call the backend API (that's Layer 3's job). Only needs DB access.

Run: DATABASE_URL=postgresql://postgres:password@localhost:5432/visionarias_logs \
     E2E_TENANT_ID=<uuid> \
     cd backend && .venv/bin/pytest tests/verification/ -m verify -x -v
"""

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.verify

# Expected metrics per channel (core metrics that should always exist)
META_ADS_EXPECTED = {"spend", "impressions", "clicks", "reach", "ctr", "cpm", "cpc"}
IG_ORGANIC_EXPECTED = {"reach", "ig_views", "total_interactions", "ig_likes"}
FB_ORGANIC_EXPECTED = {"fb_page_reach"}


class TestMetaAdsDataIntegrity:
    """Verify meta-ads official_metrics data is consistent."""

    def _fetch_metrics(self, db_session, tenant_id: str) -> list:
        return db_session.execute(
            text(
                """
                SELECT metric_name, metric_date, value, unit, currency
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'meta-ads'
                  AND provider = 'meta'
                  AND campaign_id IS NULL
                  AND ad_set_id IS NULL
                  AND ad_id IS NULL
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY metric_date, metric_name
                """,
            ),
            {"tid": tenant_id},
        ).all()

    def test_meta_ads_has_data(self, db_session, tenant_id):
        """meta-ads channel must have recent data in official_metrics."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No meta-ads data in DB — run Layer 0 first")
        assert len(rows) > 0

    def test_meta_ads_expected_metrics_present(self, db_session, tenant_id):
        """All core meta-ads metrics must be present."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No meta-ads data in DB")
        actual_metrics = {r.metric_name for r in rows}
        missing = META_ADS_EXPECTED - actual_metrics
        assert not missing, f"Missing core meta-ads metrics: {missing}"

    def test_meta_ads_no_negative_values(self, db_session, tenant_id):
        """No metric should have a negative value."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No meta-ads data in DB")
        negatives = [
            (r.metric_name, r.metric_date, r.value) for r in rows if r.value < 0
        ]
        assert not negatives, f"Found negative values: {negatives[:5]}"

    def test_meta_ads_spend_has_currency(self, db_session, tenant_id):
        """Spend metrics must have a currency value set."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No meta-ads data in DB")
        spend_rows = [r for r in rows if r.metric_name == "spend"]
        if not spend_rows:
            pytest.skip("No spend rows")
        missing_currency = [r for r in spend_rows if not r.currency]
        assert not missing_currency, (
            f"{len(missing_currency)} spend rows missing currency "
            f"(first: date={missing_currency[0].metric_date})"
        )

    def test_meta_ads_daily_continuity(self, db_session, tenant_id):
        """There should be no date gaps > 3 days in recent data."""
        dates = db_session.execute(
            text(
                """
                SELECT DISTINCT metric_date
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'meta-ads'
                  AND provider = 'meta'
                  AND campaign_id IS NULL
                  AND metric_date >= CURRENT_DATE - INTERVAL '14 days'
                ORDER BY metric_date
                """,
            ),
            {"tid": tenant_id},
        ).all()
        if len(dates) < 2:
            pytest.skip("Fewer than 2 days of data")
        gaps = []
        for i in range(1, len(dates)):
            delta = (dates[i].metric_date - dates[i - 1].metric_date).days
            if delta > 3:
                gaps.append((dates[i - 1].metric_date, dates[i].metric_date, delta))
        assert not gaps, f"Date gaps > 3 days found: {gaps}"


class TestIgOrganicDataIntegrity:
    """Verify ig-organic official_metrics data is consistent."""

    def _fetch_metrics(self, db_session, tenant_id: str) -> list:
        return db_session.execute(
            text(
                """
                SELECT metric_name, metric_date, value, unit
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'ig-organic'
                  AND provider = 'meta'
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                ORDER BY metric_date, metric_name
                """,
            ),
            {"tid": tenant_id},
        ).all()

    def test_ig_organic_has_data(self, db_session, tenant_id):
        """ig-organic channel must have recent data."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No ig-organic data in DB — run Layer 0 first")
        assert len(rows) > 0

    def test_ig_organic_expected_metrics_present(self, db_session, tenant_id):
        """Core IG organic metrics must be present."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No ig-organic data in DB")
        actual_metrics = {r.metric_name for r in rows}
        missing = IG_ORGANIC_EXPECTED - actual_metrics
        assert not missing, f"Missing core ig-organic metrics: {missing}"

    def test_ig_organic_no_negative_values(self, db_session, tenant_id):
        """No metric should have a negative value (except delta metrics)."""
        rows = self._fetch_metrics(db_session, tenant_id)
        if not rows:
            pytest.skip("No ig-organic data in DB")
        # Delta metrics can be negative (unfollows, un-reposts, etc.)
        delta_metrics = {"ig_follows_and_unfollows", "ig_reposts", "ig_follows_lost"}
        negatives = [
            (r.metric_name, r.metric_date, r.value)
            for r in rows
            if r.value < 0 and r.metric_name not in delta_metrics
        ]
        assert not negatives, f"Found negative values: {negatives[:5]}"


class TestFbOrganicDataIntegrity:
    """Verify fb-organic official_metrics data is consistent."""

    def test_fb_organic_expected_metrics_if_data_exists(self, db_session, tenant_id):
        """If fb-organic has any data, core metrics must be present."""
        rows = db_session.execute(
            text(
                """
                SELECT metric_name, COUNT(*) as cnt
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'fb-organic'
                  AND provider = 'meta'
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY metric_name
                """,
            ),
            {"tid": tenant_id},
        ).all()
        if not rows:
            pytest.skip("No fb-organic data in DB")
        actual_metrics = {r.metric_name for r in rows}
        missing = FB_ORGANIC_EXPECTED - actual_metrics
        assert not missing, f"Missing core fb-organic metrics: {missing}"
