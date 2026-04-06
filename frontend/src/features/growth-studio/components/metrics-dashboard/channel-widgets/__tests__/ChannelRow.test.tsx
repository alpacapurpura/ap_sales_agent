import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChannelRow } from '../ChannelRow';
import type { ChannelMetric } from '@/features/growth-studio/types/metrics';

// ── Mocks ────────────────────────────────────────────────────────────────────

// Mock Sentry to avoid import errors
vi.mock('@sentry/nextjs', () => ({
  captureException: vi.fn(),
}));

// Mock channelIcons — return simple span-based components
vi.mock('../../../../lib/channelIcons', () => ({
  getChannelIcon: (_slug: string) => {
    const MockIcon = (props: React.SVGProps<SVGSVGElement>) => (
      <svg data-testid="channel-icon" {...props} />
    );
    MockIcon.displayName = 'MockIcon';
    return MockIcon;
  },
  getChannelColor: (_slug: string) => '#4285F4',
}));

// Mock useMetricCatalog — return empty catalog
vi.mock('../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    catalog: [],
    catalogByName: {},
    getLabel: (name: string, fallback?: string) => fallback ?? name,
    isAdditive: () => false,
    getTooltipData: () => undefined,
  }),
}));

// Mock ConnectionBadge to simplify rendering
vi.mock('../ConnectionBadge', () => ({
  ConnectionBadge: ({ connected, onConfigure }: { connected: boolean; onConfigure?: () => void }) => {
    if (connected) return <span data-testid="badge-connected">Conectado</span>;
    if (onConfigure) {
      return (
        <button data-testid="badge-configure" onClick={onConfigure}>
          Configurar
        </button>
      );
    }
    return <span data-testid="badge-configure">Configurar</span>;
  },
}));

// Mock CostLink
vi.mock('../CostLink', () => ({
  CostLink: () => <span data-testid="cost-link">Configurar costo</span>,
}));

// Mock CampaignDrillDown — just render children
vi.mock('../CampaignDrillDown', () => ({
  CampaignDrillDown: ({ children }: { children: React.ReactNode }) => <div data-testid="campaign-drilldown">{children}</div>,
}));

// ── Test Data ────────────────────────────────────────────────────────────────

const connectedChannel: ChannelMetric = {
  slug: 'ig-organic',
  name: 'Instagram Organic',
  channelType: 'organic_social',
  metrics: [
    { name: 'reach', value: 15000 },
    { name: 'total_interactions', value: 450 },
    { name: 'ig_followers_count', value: 8200 },
  ],
  sourceLabel: 'Instagram Business',
  connected: true,
  lastUpdated: '2026-03-14T03:15:00Z',
};

const disconnectedChannel: ChannelMetric = {
  slug: 'tiktok-organic',
  name: 'TikTok Organic',
  channelType: 'organic_social',
  metrics: [],
  sourceLabel: 'TikTok',
  connected: false,
};

const noDataChannel: ChannelMetric = {
  slug: 'ga4-search',
  name: 'Google Analytics',
  channelType: 'ga4_search',
  metrics: [],
  sourceLabel: 'GA4',
  connected: true,
};

const zeroLeadsChannel: ChannelMetric = {
  slug: 'manychat-ig',
  name: 'ManyChat IG',
  channelType: 'ai_agent',
  metrics: [
    { name: 'leads', value: 0 },
  ],
  sourceLabel: 'ManyChat',
  connected: true,
};

// ── Tests ────────────────────────────────────────────────────────────────────

describe('ChannelRow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the channel name for a connected channel', () => {
    render(<ChannelRow channel={connectedChannel} />);

    expect(screen.getByText('Instagram Organic')).toBeInTheDocument();
  });

  it('renders the source label for a connected channel', () => {
    render(<ChannelRow channel={connectedChannel} />);

    expect(screen.getByText('Instagram Business')).toBeInTheDocument();
  });

  it('renders sourceDisplayName when provided', () => {
    const channelWithDisplayName: ChannelMetric = {
      ...connectedChannel,
      sourceDisplayName: '@myaccount',
    };
    render(<ChannelRow channel={channelWithDisplayName} />);

    // Format: "sourceLabel . sourceDisplayName"
    expect(screen.getByText(/Instagram Business.*@myaccount/)).toBeInTheDocument();
  });

  it('shows metric values for connected channels', () => {
    render(<ChannelRow channel={connectedChannel} />);

    // ig-organic summary metrics: reach, total_interactions, ig_followers_count
    // formatNumber: 15000 >= 10000 -> (15000/1000).toFixed(0) = "15k"
    expect(screen.getByText('15k')).toBeInTheDocument();
    // 450 < 1000 -> toLocaleString
    expect(screen.getByText('450')).toBeInTheDocument();
    // 8200: (8200/1000).toFixed(1) = "8.2k"
    expect(screen.getByText('8.2k')).toBeInTheDocument();
  });

  it('shows metric labels from METRIC_LABELS fallback', () => {
    render(<ChannelRow channel={connectedChannel} />);

    // Labels from METRIC_LABELS map: reach -> Alcance, total_interactions -> Interacciones
    expect(screen.getByText('Alcance')).toBeInTheDocument();
    expect(screen.getByText('Interacciones')).toBeInTheDocument();
  });

  it('shows "Configurar" badge for unconnected channels', () => {
    render(<ChannelRow channel={disconnectedChannel} />);

    expect(screen.getByText('TikTok Organic')).toBeInTheDocument();
    expect(screen.getByText('Configurar')).toBeInTheDocument();
  });

  it('calls onConfigure when "Configurar" is clicked on unconnected channel', async () => {
    const handleConfigure = vi.fn();
    const user = userEvent.setup();

    render(<ChannelRow channel={disconnectedChannel} onConfigure={handleConfigure} />);

    const configureBtn = screen.getByTestId('badge-configure');
    await user.click(configureBtn);

    expect(handleConfigure).toHaveBeenCalledWith('tiktok-organic', 'TikTok Organic');
  });

  it('shows placeholder "---" and "Sin datos" for connected channels with no metrics', () => {
    render(<ChannelRow channel={noDataChannel} />);

    expect(screen.getByText('---')).toBeInTheDocument();
    expect(screen.getByText('Sin datos')).toBeInTheDocument();
  });

  it('shows "0 leads" for channels with zero leads metric', () => {
    render(<ChannelRow channel={zeroLeadsChannel} />);

    expect(screen.getByText('0 leads')).toBeInTheDocument();
  });

  it('shows "Desactualizado" badge when channel is stale', () => {
    const staleChannel: ChannelMetric = {
      ...connectedChannel,
      stale: true,
      lastUpdated: '2026-03-10T00:00:00Z',
    };
    render(<ChannelRow channel={staleChannel} />);

    expect(screen.getByText('Desactualizado')).toBeInTheDocument();
  });

  it('shows "Próximamente" badge for ai-sdr channel with no metrics', () => {
    const aiSdrChannel: ChannelMetric = {
      slug: 'ai-sdr',
      name: 'AI SDR',
      channelType: 'ai_agent',
      metrics: [],
      sourceLabel: 'Nicolify AI',
      connected: true,
    };
    render(<ChannelRow channel={aiSdrChannel} />);

    expect(screen.getByText('Próximamente')).toBeInTheDocument();
  });

  it('shows "Próximamente" badge for checkout-lp channel', () => {
    const checkoutChannel: ChannelMetric = {
      slug: 'checkout-lp',
      name: 'Checkout Landing',
      channelType: 'checkout',
      metrics: [{ name: 'views', value: 100 }],
      sourceLabel: 'Shopify',
      connected: true,
    };
    render(<ChannelRow channel={checkoutChannel} />);

    expect(screen.getByText('Próximamente')).toBeInTheDocument();
  });

  it('renders channel icon via getChannelIcon', () => {
    render(<ChannelRow channel={connectedChannel} />);

    const icon = screen.getByTestId('channel-icon');
    expect(icon).toBeInTheDocument();
  });

  it('calls onChannelClick when connected row is clicked', async () => {
    const handleChannelClick = vi.fn();
    const user = userEvent.setup();

    render(<ChannelRow channel={connectedChannel} onChannelClick={handleChannelClick} />);

    const row = screen.getByText('Instagram Organic').closest('div[class*="cursor-pointer"]');
    expect(row).toBeTruthy();
    await user.click(row!);

    expect(handleChannelClick).toHaveBeenCalledWith(connectedChannel);
  });

  it('is wrapped with React.memo', () => {
    // The ChannelRow export is a React.memo component
    // React.memo wraps the component, so its $$typeof should be react.memo
    expect(ChannelRow).toBeDefined();
    // React.memo components have a special type property
    expect((ChannelRow as { $$typeof?: symbol }).$$typeof).toBeDefined();
  });
});
