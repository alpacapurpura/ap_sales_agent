import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NoDataSidebarPanel } from '../NoDataSidebarPanel';
import type { ChannelMetric } from '@/features/growth-studio/types/metrics';

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock('../../../../lib/channelIcons', () => ({
  getChannelIcon: (_slug: string) => {
    const MockIcon = (props: React.SVGProps<SVGSVGElement>) => (
      <svg data-testid="sidebar-channel-icon" {...props} />
    );
    MockIcon.displayName = 'MockIcon';
    return MockIcon;
  },
  getChannelColor: (_slug: string) => '#4285F4',
}));

// Mock DetailPanel to render inline
vi.mock('@/components/ui/detail-panel', () => ({
  DetailPanel: ({ open, children }: { open: boolean; children: React.ReactNode }) =>
    open ? <div data-testid="detail-panel">{children}</div> : null,
  DetailPanelHeader: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="detail-panel-header">{children}</div>
  ),
  DetailPanelTitle: ({ children }: { children: React.ReactNode }) => (
    <h2 data-testid="detail-panel-title">{children}</h2>
  ),
  DetailPanelClose: () => <button data-testid="detail-panel-close">Close</button>,
}));

// ── Test data ────────────────────────────────────────────────────────────────

const channel: ChannelMetric = {
  slug: 'ga4-search',
  name: 'Google Analytics',
  channelType: 'ga4_search',
  metrics: [],
  sourceLabel: 'GA4',
  connected: true,
  providerName: 'google_analytics',
};

// ── Tests ────────────────────────────────────────────────────────────────────

describe('NoDataSidebarPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when not open', () => {
    render(<NoDataSidebarPanel isOpen={false} onClose={vi.fn()} channel={null} />);
    expect(screen.queryByTestId('detail-panel')).not.toBeInTheDocument();
  });

  it('renders when open with a channel', () => {
    render(<NoDataSidebarPanel isOpen={true} onClose={vi.fn()} channel={channel} />);
    expect(screen.getByTestId('detail-panel')).toBeInTheDocument();
  });

  it('shows channel name in header', () => {
    render(<NoDataSidebarPanel isOpen={true} onClose={vi.fn()} channel={channel} />);
    expect(screen.getByText('Google Analytics')).toBeInTheDocument();
  });

  it('shows channel icon', () => {
    render(<NoDataSidebarPanel isOpen={true} onClose={vi.fn()} channel={channel} />);
    expect(screen.getByTestId('sidebar-channel-icon')).toBeInTheDocument();
  });

  it('shows "Próximamente" placeholder text', () => {
    render(<NoDataSidebarPanel isOpen={true} onClose={vi.fn()} channel={channel} />);
    expect(screen.getByText(/próximamente/i)).toBeInTheDocument();
    expect(screen.getByText(/triggers & actions/i)).toBeInTheDocument();
  });

  it('shows descriptive text about future features', () => {
    render(<NoDataSidebarPanel isOpen={true} onClose={vi.fn()} channel={channel} />);
    expect(screen.getByText(/acciones automáticas/i)).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();

    render(<NoDataSidebarPanel isOpen={true} onClose={handleClose} channel={channel} />);

    await user.click(screen.getByText('Cerrar'));
    expect(handleClose).toHaveBeenCalled();
  });
});
