"""
Integration test for GA4 Data API — hits real Google Analytics property.

Requires environment variables:
    GOOGLE_CLIENT_ID      - OAuth client ID
    GOOGLE_CLIENT_SECRET  - OAuth client secret
    GOOGLE_REFRESH_TOKEN  - Valid refresh token with analytics.readonly scope
    GA4_PROPERTY_ID       - GA4 property ID (numeric, e.g. "123456789")

Run manually:
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... GOOGLE_REFRESH_TOKEN=... \
    GA4_PROPERTY_ID=... pytest tests/integration/test_ga4_live.py -v

Skipped automatically when credentials are not available.
"""

import os

import pytest

from luana_core_connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)

_REQUIRED_ENVS = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REFRESH_TOKEN",
    "GA4_PROPERTY_ID",
]

_has_ga4_credentials = all(os.environ.get(v) for v in _REQUIRED_ENVS)


@pytest.mark.integration
@pytest.mark.skipif(
    not _has_ga4_credentials,
    reason="GA4 credentials not set (need GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN)",
)
@pytest.mark.asyncio
async def test_run_report_returns_real_session_data():
    """
    Verify that run_report() can execute a real GA4 API call
    and return structured session data for the configured property.
    """
    client_id = os.environ["GOOGLE_CLIENT_ID"]
    client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
    refresh_token = os.environ["GOOGLE_REFRESH_TOKEN"]
    property_id = os.environ["GA4_PROPERTY_ID"]

    client_config = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    credentials_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "token_uri": "https://oauth2.googleapis.com/token",
    }

    adapter = GoogleAnalyticsAdapter(
        client_config=client_config,
        credentials_data=credentials_data,
    )

    result = await adapter.run_report(
        property_id=property_id,
        dimensions=["date"],
        metrics=["sessions"],
        start_date="7daysAgo",
        end_date="today",
    )

    # Structural assertions — the property may have zero traffic
    assert isinstance(result, dict)
    assert "row_count" in result
    assert result["row_count"] >= 0
    assert isinstance(result["rows"], list)
    assert "metadata" in result
    assert result["metadata"]["dimensions"] == ["date"]
    assert result["metadata"]["metrics"] == ["sessions"]

    # If there are rows, verify their structure
    for row in result["rows"]:
        assert "dimensions" in row
        assert "metrics" in row
        assert len(row["dimensions"]) == 1  # date
        assert len(row["metrics"]) == 1  # sessions
