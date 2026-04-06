import { type Page, type Route } from '@playwright/test';
import { MAIL_DASHBOARD_MOCK } from './mail-dashboard-mock-data';

export interface MailDashboardMockOverrides {
  channelDashboard?: (route: Route) => Promise<void>;
  skipPatterns?: ('channel-dashboard')[];
}

/**
 * Intercepts email-nurture channel dashboard API calls for E2E test determinism.
 * Base Growth Studio mocks are handled by the `growthStudioTest` fixture.
 */
export async function setupMailDashboardMocks(page: Page, overrides?: MailDashboardMockOverrides) {
  const skip = overrides?.skipPatterns ?? [];

  // Channel dashboard
  if (overrides?.channelDashboard) {
    await page.route('**/api/v1/analytics/metrics/channel/email-nurture/dashboard**', overrides.channelDashboard);
  } else if (!skip.includes('channel-dashboard')) {
    await page.route('**/api/v1/analytics/metrics/channel/email-nurture/dashboard**', async (route) => {
      const url = route.request().url();
      const period = new URL(url).searchParams.get('period') ?? '30d';
      await route.fulfill({ json: { ...MAIL_DASHBOARD_MOCK, period }, status: 200 });
    });
  }

  // Nurture detail endpoint (so the nurture stage page can load with email channel)
  await page.route('**/api/v1/analytics/metrics/nurture**', async (route) => {
    await route.fulfill({
      json: {
        header_kpis: { total_mqls: 120, cost_per_mql: 8.5 },
        automation: {
          totals: { leads: 120 },
          channels: [{
            slug: 'email-nurture',
            name: 'eMailing Nurturing',
            channel_type: 'automation',
            metrics: [
              { name: 'emails_sent', value: 5000, unit: 'count' },
              { name: 'clicks', value: 150, unit: 'count' },
            ],
            source_label: 'MailerLite',
            connected: true,
            cost_type: null,
            last_updated: '2026-04-06T05:00:00Z',
            stale: false,
            provider_name: 'mailerlite',
          }],
        },
        retargeting: { totals: {}, channels: [] },
        available: { channels: [] },
        period: 'last_30_days',
        last_updated: '2026-04-06T05:00:00Z',
      },
      status: 200,
    });
  });

  // Opportunity detail endpoint
  await page.route('**/api/v1/analytics/metrics/opportunity**', async (route) => {
    await route.fulfill({
      json: {
        header_kpis: { total_sqls: 45 },
        qualification: { totals: { sqls: 30 }, channels: [] },
        checkout: { totals: { sqls: 10 }, channels: [] },
        paymentLinks: { totals: { sqls: 5 }, channels: [] },
        bottlenecks: [],
        available: { channels: [] },
        period: 'last_30_days',
      },
      status: 200,
    });
  });
}
