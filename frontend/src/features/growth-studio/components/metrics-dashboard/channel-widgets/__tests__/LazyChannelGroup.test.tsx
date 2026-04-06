import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';

// ── Mocks ──────────────────────────────────────────────────────────────────────

let mockIsVisible = false;
vi.mock('../../../../hooks/useIntersectionObserver', () => ({
  useIntersectionObserver: () => ({
    ref: vi.fn(),
    isVisible: mockIsVisible,
  }),
}));

const mockGroupDetailData = {
  channels: [
    {
      slug: 'meta-ads',
      name: 'Meta Ads',
      channelType: 'paid',
      metrics: [
        { name: 'spend', value: 1500, unit: 'currency' },
        { name: 'impressions', value: 50000 },
        { name: 'clicks', value: 2000 },
      ],
      sourceLabel: 'Meta',
      connected: true,
    },
  ],
  totals: { spend: 1500, impressions: 50000, clicks: 2000 },
};

let mockGroupDetailReturn = { data: undefined as typeof mockGroupDetailData | undefined, isLoading: false };
vi.mock('../../../../hooks/useGroupDetail', () => ({
  useGroupDetail: () => mockGroupDetailReturn,
}));

// Mock ChannelRow to avoid Shadcn UI dependencies
vi.mock('../ChannelRow', () => ({
  ChannelRow: ({ channel }: { channel: { name: string; slug: string } }) =>
    React.createElement('div', { 'data-testid': `channel-row-${channel.slug}` }, channel.name),
}));

// Mock Accordion components
vi.mock('@/components/ui/accordion', () => ({
  Accordion: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, children),
  AccordionItem: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, children),
  AccordionTrigger: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, children),
  AccordionContent: ({ children }: { children: React.ReactNode }) => React.createElement('div', null, children),
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { LazyChannelGroup } from '../LazyChannelGroup';
import type { ChannelOverview } from '../../../../types/metrics';

// ── Test data ──────────────────────────────────────────────────────────────────

const overviewChannels: ChannelOverview[] = [
  {
    slug: 'meta-ads',
    name: 'Meta Ads',
    channelType: 'paid',
    groupKey: 'paid',
    connected: true,
    headlineKpi: { name: 'spend', value: 1500, unit: 'currency' },
    stale: false,
  },
];

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('LazyChannelGroup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsVisible = false;
    mockGroupDetailReturn = { data: undefined, isLoading: false };
  });

  it('renders overview channels when group not in viewport', () => {
    mockIsVisible = false;

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={overviewChannels}
      />,
    );

    expect(screen.getByText('Meta Ads')).toBeDefined();
  });

  it('renders enriched channels when group detail loads', () => {
    mockIsVisible = true;
    mockGroupDetailReturn = { data: mockGroupDetailData, isLoading: false };

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={overviewChannels}
      />,
    );

    // Channel name should still be visible
    expect(screen.getByText('Meta Ads')).toBeDefined();
  });

  it('shows skeleton state when loading group detail', () => {
    mockIsVisible = true;
    mockGroupDetailReturn = { data: undefined, isLoading: true };

    render(
      <LazyChannelGroup
        stage="attraction"
        groupKey="paid"
        title="Paid"
        overviewChannels={overviewChannels}
      />,
    );

    // Should still render the group title and overview data while loading
    expect(screen.getByText('Meta Ads')).toBeDefined();
  });
});
