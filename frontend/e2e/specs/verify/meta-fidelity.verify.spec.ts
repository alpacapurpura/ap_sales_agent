/**
 * Layer 3: UI Fidelity — Meta channels.
 *
 * Strategy: Call the backend API directly to capture expected DTO values,
 * then navigate the UI and assert displayed values match.
 *
 * NOT mocked — hits the real backend with real data.
 *
 * Requires:
 *   - Docker containers running with real data (post Layer 0)
 *   - Clerk auth configured (same as smoke tests)
 *
 * Run: cd frontend && npx playwright test --project=verify
 */
import { test, expect } from '@playwright/test';

const TENANT_ID = process.env.E2E_TENANT_ID!;
const BACKEND_URL = process.env.E2E_BACKEND_URL || 'http://localhost:8000';

interface MetricValue {
  name: string;
  value: number;
  unit: string;
  currency?: string | null;
}

interface ChannelDto {
  slug: string;
  name: string;
  metrics: MetricValue[];
}

interface GroupDto {
  key: string;
  channels: ChannelDto[];
}

interface AttractionDto {
  groups: GroupDto[];
}

function findChannel(dto: AttractionDto, slug: string): ChannelDto | undefined {
  for (const group of dto.groups ?? []) {
    for (const ch of group.channels ?? []) {
      if (ch.slug === slug) return ch;
    }
  }
  return undefined;
}

function getMetric(channel: ChannelDto, name: string): MetricValue | undefined {
  return channel.metrics?.find((m) => m.name === name);
}

/**
 * Format a number the way our UI does, for text matching.
 * Simplified — matches the most common patterns.
 */
function formatForMatch(value: number, unit: string): string {
  if (unit === 'currency') {
    return value.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  if (unit === 'percentage') {
    return value.toFixed(2);
  }
  if (unit === 'ratio') {
    return value.toFixed(2);
  }
  if (value >= 1000) {
    return value.toLocaleString('en-US', { maximumFractionDigits: 0 });
  }
  return value.toString();
}

test.describe('Meta Ads - Data Fidelity @verify', () => {
  let attractionDto: AttractionDto;

  test.beforeAll(async ({ request }) => {
    const response = await request.get(
      `${BACKEND_URL}/api/v1/analytics/metrics/attraction`,
      { headers: { 'X-Tenant-ID': TENANT_ID } },
    );
    expect(response.ok()).toBeTruthy();
    attractionDto = await response.json();
  });

  test('meta-ads channel exists in attraction API response', () => {
    const channel = findChannel(attractionDto, 'meta-ads');
    expect(channel).toBeDefined();
    expect(channel!.metrics.length).toBeGreaterThan(0);
  });

  test('meta-ads spend is visible and matches API', async ({ page }) => {
    const channel = findChannel(attractionDto, 'meta-ads');
    test.skip(!channel, 'No meta-ads channel in DTO');

    const spendMetric = getMetric(channel!, 'spend');
    test.skip(!spendMetric, 'No spend metric in DTO');

    await page.goto(`/${TENANT_ID}/growth-studio/atraccion-captura`, {
      waitUntil: 'networkidle',
    });

    const metaAdsRow = page
      .getByRole('button', { name: /Meta Ads/i })
      .first();
    await expect(metaAdsRow).toBeVisible({ timeout: 15_000 });
    await metaAdsRow.click();

    const spendFormatted = formatForMatch(spendMetric!.value, 'currency');
    const sidebar = page
      .locator('[data-testid="channel-sidebar"], [role="complementary"]')
      .first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });
    await expect(sidebar).toContainText(spendFormatted, { timeout: 5_000 });
  });

  test('meta-ads impressions visible and matches API', async ({ page }) => {
    const channel = findChannel(attractionDto, 'meta-ads');
    test.skip(!channel, 'No meta-ads channel in DTO');

    const metric = getMetric(channel!, 'impressions');
    test.skip(!metric, 'No impressions metric in DTO');

    await page.goto(`/${TENANT_ID}/growth-studio/atraccion-captura`, {
      waitUntil: 'networkidle',
    });

    const metaAdsRow = page
      .getByRole('button', { name: /Meta Ads/i })
      .first();
    await expect(metaAdsRow).toBeVisible({ timeout: 15_000 });
    await metaAdsRow.click();

    const sidebar = page
      .locator('[data-testid="channel-sidebar"], [role="complementary"]')
      .first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    const formatted = formatForMatch(metric!.value, 'count');
    await expect(sidebar).toContainText(formatted, { timeout: 5_000 });
  });
});

test.describe('IG Organic - Data Fidelity @verify', () => {
  let attractionDto: AttractionDto;

  test.beforeAll(async ({ request }) => {
    const response = await request.get(
      `${BACKEND_URL}/api/v1/analytics/metrics/attraction`,
      { headers: { 'X-Tenant-ID': TENANT_ID } },
    );
    expect(response.ok()).toBeTruthy();
    attractionDto = await response.json();
  });

  test('ig-organic channel exists in attraction API response', () => {
    const channel = findChannel(attractionDto, 'ig-organic');
    expect(channel).toBeDefined();
    expect(channel!.metrics.length).toBeGreaterThan(0);
  });

  test('ig-organic reach visible and non-zero', async ({ page }) => {
    const channel = findChannel(attractionDto, 'ig-organic');
    test.skip(!channel, 'No ig-organic channel in DTO');

    const metric = getMetric(channel!, 'reach');
    test.skip(!metric || metric.value === 0, 'No reach data');

    await page.goto(`/${TENANT_ID}/growth-studio/atraccion-captura`, {
      waitUntil: 'networkidle',
    });

    const igRow = page
      .getByRole('button', { name: /Instagram Organic|IG Organic/i })
      .first();
    await expect(igRow).toBeVisible({ timeout: 15_000 });
    await igRow.click();

    const sidebar = page
      .locator('[data-testid="channel-sidebar"], [role="complementary"]')
      .first();
    await expect(sidebar).toBeVisible({ timeout: 10_000 });

    const formatted = formatForMatch(metric!.value, 'count');
    await expect(sidebar).toContainText(formatted, { timeout: 5_000 });
  });
});
