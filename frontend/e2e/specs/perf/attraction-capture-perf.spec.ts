import { test, expect } from '../../fixtures/auth.fixture';
import * as fs from 'fs';
import * as path from 'path';

/**
 * @perf Performance measurement for Attraction & Capture progressive loading.
 *
 * Captures API call count, payload size, and timing metrics.
 * Saves results to perf-baselines/attraction-capture.json for before/after comparison.
 */
test.describe('Attraction & Capture Performance @perf', () => {
  test('measures initial load metrics', async ({ page, tenantId }) => {
    const apiCalls: { url: string; status: number; size: number }[] = [];

    // Intercept all analytics API calls
    page.on('response', async (response) => {
      const url = response.url();
      if (url.includes('/api/v1/analytics/')) {
        const body = await response.body().catch(() => Buffer.alloc(0));
        apiCalls.push({
          url: url.replace(/.*\/api/, '/api'),
          status: response.status(),
          size: body.length,
        });
      }
    });

    // Navigate to Attraction & Capture page
    await page.goto(`/${tenantId}/growth-studio/atraccion-captura`);

    // Wait for overview data to load (should be fast with progressive loading)
    await page.waitForResponse(
      (res) => res.url().includes('/overview') && res.status() === 200,
      { timeout: 15000 },
    ).catch(() => {
      // Overview might already be loaded — continue
    });

    // Wait a bit for any additional lazy-loaded requests
    await page.waitForTimeout(2000);

    // Collect Navigation Timing
    const navTiming = await page.evaluate(() => {
      const entry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      return {
        domContentLoaded: entry?.domContentLoadedEventEnd ?? 0,
        loadEventEnd: entry?.loadEventEnd ?? 0,
        responseStart: entry?.responseStart ?? 0,
      };
    });

    // Collect LCP
    const lcp = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let lcpValue = 0;
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length > 0) {
            lcpValue = entries[entries.length - 1].startTime;
          }
        });
        observer.observe({ type: 'largest-contentful-paint', buffered: true });
        setTimeout(() => {
          observer.disconnect();
          resolve(lcpValue);
        }, 1000);
      });
    });

    // Build metrics report
    const totalPayloadBytes = apiCalls.reduce((sum, c) => sum + c.size, 0);
    const metrics = {
      timestamp: new Date().toISOString(),
      apiCalls: {
        total: apiCalls.length,
        details: apiCalls.map((c) => ({
          url: c.url,
          status: c.status,
          sizeKB: +(c.size / 1024).toFixed(2),
        })),
      },
      payload: {
        totalKB: +(totalPayloadBytes / 1024).toFixed(2),
      },
      timing: {
        domContentLoadedMs: Math.round(navTiming.domContentLoaded),
        loadEventEndMs: Math.round(navTiming.loadEventEnd),
        lcpMs: Math.round(lcp),
      },
    };

    // Save baseline JSON
    const baselinePath = path.join(__dirname, '../../perf-baselines/attraction-capture.json');
    fs.mkdirSync(path.dirname(baselinePath), { recursive: true });
    fs.writeFileSync(baselinePath, JSON.stringify(metrics, null, 2));

    // Generous assertions (baseline capture — not meant to fail)
    expect(apiCalls.length).toBeLessThanOrEqual(10);
    expect(totalPayloadBytes).toBeLessThan(500 * 1024); // < 500 KB

    // Log for visibility in CI output
    console.log('\n📊 Performance Metrics:');
    console.log(`  API calls: ${apiCalls.length}`);
    console.log(`  Total payload: ${metrics.payload.totalKB} KB`);
    console.log(`  DOM Content Loaded: ${metrics.timing.domContentLoadedMs}ms`);
    console.log(`  LCP: ${metrics.timing.lcpMs}ms`);
    console.log(`  Baseline saved to: ${baselinePath}`);
  });

  test('no group detail calls before scroll', async ({ page, tenantId }) => {
    const groupDetailCalls: string[] = [];

    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('/groups/')) {
        groupDetailCalls.push(url);
      }
    });

    await page.goto(`/${tenantId}/growth-studio/atraccion-captura`);

    // Wait for initial load to settle (overviews only)
    await page.waitForTimeout(3000);

    // Before scrolling, there should be NO group detail calls
    // (groups load on viewport intersection, not on mount)
    expect(groupDetailCalls).toHaveLength(0);
  });
});
