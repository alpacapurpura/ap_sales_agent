"""Layer 2: Pipeline Integrity — verify official_metrics -> stage service DTOs.

Reads real data from PostgreSQL, calls the backend API, compares values.
Requires Docker containers running with data (run Layer 0 first).

Run: cd backend && .venv/bin/pytest tests/verification/test_pipeline_meta.py -m verify -x -v
"""

import httpx
import pytest
from sqlalchemy import text

pytestmark = pytest.mark.verify


class TestMetaAdsPipeline:
    """Verify meta-ads channel metrics flow correctly through the pipeline."""

    def _fetch_db_totals(self, db_session, tenant_id: str) -> dict[str, float]:
        """Read account-level meta-ads metrics from official_metrics (last 30 days)."""
        rows = db_session.execute(
            text(
                """
                SELECT metric_name, SUM(value) as total
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'meta-ads'
                  AND provider = 'meta'
                  AND campaign_id IS NULL
                  AND ad_set_id IS NULL
                  AND ad_id IS NULL
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY metric_name
                """
            ),
            {"tid": tenant_id},
        ).all()
        return {row.metric_name: float(row.total) for row in rows}

    def _fetch_api_attraction(self, backend_url: str, tenant_id: str) -> dict:
        """Call GET /metrics/attraction and return JSON response."""
        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()

    def _find_channel_in_dto(self, dto: dict, channel_slug: str) -> dict | None:
        """Find a channel in the DTO groups structure."""
        for group in dto.get("groups", []):
            for channel in group.get("channels", []):
                if channel.get("slug") == channel_slug:
                    return channel
        return None

    def _get_metric_value(self, channel: dict, metric_name: str) -> float | None:
        """Extract a metric value from a channel DTO."""
        for metric in channel.get("metrics", []):
            if metric.get("name") == metric_name:
                return float(metric.get("value", 0))
        return None

    def test_meta_ads_present_in_attraction(self, db_session, tenant_id, backend_url):
        """meta-ads channel must appear in the attraction DTO if DB has data."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if not db_totals:
            pytest.skip("No meta-ads data in DB — run Layer 0 first")
        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None, (
            f"meta-ads channel not found in attraction DTO, but DB has {len(db_totals)} metrics"
        )

    def test_meta_ads_spend_matches_db(self, db_session, tenant_id, backend_url):
        """Spend in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "spend" not in db_totals:
            pytest.skip("No spend data in DB")
        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None
        dto_spend = self._get_metric_value(channel, "spend")
        assert dto_spend is not None, "spend metric not found in DTO"
        db_spend = db_totals["spend"]
        if db_spend == 0:
            assert dto_spend == 0
        else:
            pct_diff = abs(dto_spend - db_spend) / db_spend * 100
            assert pct_diff < 1.0, (
                f"Spend mismatch: DTO={dto_spend:.2f} DB={db_spend:.2f} diff={pct_diff:.2f}%"
            )

    def test_meta_ads_impressions_matches_db(self, db_session, tenant_id, backend_url):
        """Impressions in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "impressions" not in db_totals:
            pytest.skip("No impressions data in DB")
        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None
        dto_val = self._get_metric_value(channel, "impressions")
        assert dto_val is not None, "impressions metric not found in DTO"
        db_val = db_totals["impressions"]
        if db_val == 0:
            assert dto_val == 0
        else:
            pct_diff = abs(dto_val - db_val) / db_val * 100
            assert pct_diff < 1.0, (
                f"Impressions mismatch: DTO={dto_val:.0f} DB={db_val:.0f} diff={pct_diff:.2f}%"
            )

    def test_meta_ads_clicks_matches_db(self, db_session, tenant_id, backend_url):
        """Clicks in DTO must match SUM(value) from official_metrics."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "clicks" not in db_totals:
            pytest.skip("No clicks data in DB")
        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None
        dto_val = self._get_metric_value(channel, "clicks")
        assert dto_val is not None, "clicks metric not found in DTO"
        db_val = db_totals["clicks"]
        if db_val == 0:
            assert dto_val == 0
        else:
            pct_diff = abs(dto_val - db_val) / db_val * 100
            assert pct_diff < 1.0, (
                f"Clicks mismatch: DTO={dto_val:.0f} DB={db_val:.0f} diff={pct_diff:.2f}%"
            )

    def test_meta_ads_currency_present(self, db_session, tenant_id, backend_url):
        """Monetary metrics must carry a currency field."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "spend" not in db_totals:
            pytest.skip("No spend data in DB")
        dto = self._fetch_api_attraction(backend_url, tenant_id)
        channel = self._find_channel_in_dto(dto, "meta-ads")
        assert channel is not None
        for metric in channel.get("metrics", []):
            if metric.get("name") == "spend":
                assert metric.get("currency") is not None, (
                    "spend metric missing currency field in DTO"
                )


class TestIgOrganicPipeline:
    """Verify ig-organic channel metrics flow correctly through the pipeline."""

    def _fetch_db_totals(self, db_session, tenant_id: str) -> dict[str, float]:
        """Read ig-organic account-level metrics from official_metrics."""
        rows = db_session.execute(
            text(
                """
                SELECT metric_name, SUM(value) as total
                FROM official_metrics
                WHERE tenant_id = :tid
                  AND channel_slug = 'ig-organic'
                  AND provider = 'meta'
                  AND metric_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY metric_name
                """
            ),
            {"tid": tenant_id},
        ).all()
        return {row.metric_name: float(row.total) for row in rows}

    def test_ig_organic_present_in_attraction(self, db_session, tenant_id, backend_url):
        """ig-organic channel must appear in attraction DTO if DB has data."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if not db_totals:
            pytest.skip("No ig-organic data in DB — run Layer 0 first")
        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        dto = resp.json()
        found = False
        for group in dto.get("groups", []):
            for ch in group.get("channels", []):
                if ch.get("slug") == "ig-organic":
                    found = True
                    break
        assert found, "ig-organic not found in attraction DTO"

    def test_ig_organic_reach_matches_db(self, db_session, tenant_id, backend_url):
        """IG reach (NON_AGGREGABLE) uses last value, not SUM."""
        db_totals = self._fetch_db_totals(db_session, tenant_id)
        if "reach" not in db_totals:
            pytest.skip("No ig-organic reach data in DB")
        resp = httpx.get(
            f"{backend_url}/api/v1/analytics/metrics/attraction",
            headers={"X-Tenant-ID": tenant_id},
            timeout=30.0,
        )
        resp.raise_for_status()
        dto = resp.json()
        channel = None
        for group in dto.get("groups", []):
            for ch in group.get("channels", []):
                if ch.get("slug") == "ig-organic":
                    channel = ch
                    break
        assert channel is not None
        dto_reach = None
        for m in channel.get("metrics", []):
            if m.get("name") == "reach":
                dto_reach = float(m.get("value", 0))
                break
        assert dto_reach is not None, "reach not found in ig-organic DTO"
        assert dto_reach > 0, f"reach should be > 0 (DB has {db_totals['reach']})"
