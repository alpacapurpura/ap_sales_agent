# Klipfolio / MetricHQ — Industry Benchmark Data

Reference data for Growth Studio metric contextualization.
Used by `backend/src/modules/analytics/domain/industry_benchmarks.py`.

## Files

| File | Source | Metrics |
|---|---|---|
| `google-ads-benchmarks.md` | WordStream/Klipfolio | CTR, CPC, CVR, CPA (Search & Display, 16 industries) |
| `facebook-ads-benchmarks.md` | WordStream/Klipfolio | CTR, CPC, CVR, CPA (Meta Ads, 17 industries) |
| `email-marketing-benchmarks.md` | Campaign Monitor 2022 | Open Rate, Click Rate, CTOR, Unsubscribe (17 industries) |
| `instagram-benchmarks.md` | Social Insider 2025 | Engagement, Views, Saves, Comments (by format & size) |

## Usage

These files are the **source of truth** for benchmark values hardcoded in
`industry_benchmarks.py`. When updating benchmarks, update both the reference
file and the Python module.

## Scraping History

- **Original scrape:** Unknown date (pre-2026-03, lost during merge)
- **Re-scraped:** 2026-04-06 via WebFetch from Klipfolio, MetricHQ, WordStream, Campaign Monitor, Social Insider
