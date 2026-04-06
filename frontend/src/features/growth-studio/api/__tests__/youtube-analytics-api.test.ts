import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock config before importing the module under test
vi.mock('@/lib/config', () => ({
  config: { api: { baseUrl: 'https://api.test.com' } },
}));

// Mock fetchClient to capture the URL it receives
const mockFetchClient = vi.fn().mockResolvedValue({
  ok: true,
  json: () => Promise.resolve({ data: [] }),
});
vi.mock('@/lib/http-client', () => ({
  fetchClient: (...args: unknown[]) => mockFetchClient(...args),
}));

import {
  getYoutubeTopVideosEnriched,
  getYoutubeTrafficSources,
  getYoutubeDemographics,
  getYoutubeCountries,
} from '../youtube-analytics-api';

describe('youtube-analytics-api URL paths', () => {
  const TOKEN = 'test-token';

  beforeEach(() => {
    mockFetchClient.mockClear();
  });

  it('getYoutubeTopVideosEnriched calls /connections/youtube-analytics/top-videos-enriched', async () => {
    await getYoutubeTopVideosEnriched(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain('/api/v1/connections/youtube-analytics/top-videos-enriched');
  });

  it('getYoutubeTrafficSources calls /connections/youtube-analytics/traffic-sources', async () => {
    await getYoutubeTrafficSources(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain('/api/v1/connections/youtube-analytics/traffic-sources');
  });

  it('getYoutubeDemographics calls /connections/youtube-analytics/demographics', async () => {
    await getYoutubeDemographics(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain('/api/v1/connections/youtube-analytics/demographics');
  });

  it('getYoutubeCountries calls /connections/youtube-analytics/countries', async () => {
    await getYoutubeCountries(TOKEN);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain('/api/v1/connections/youtube-analytics/countries');
  });

  it('includes query params when provided', async () => {
    await getYoutubeTopVideosEnriched(TOKEN, '2026-01-01', '2026-01-31', 5);
    const url = mockFetchClient.mock.calls[0][0] as string;
    expect(url).toContain('start_date=2026-01-01');
    expect(url).toContain('end_date=2026-01-31');
    expect(url).toContain('max_results=5');
  });
});
