'use client';

import { Mail } from 'lucide-react';
import type { ChannelMetric } from '../../../../types/metrics';
import { ChannelOverviewPanel } from '../shared/ChannelOverviewPanel';
import { MailDeliverabilityHealth } from './MailDeliverabilityHealth';
import { MailListGrowthIndicator } from './MailListGrowthIndicator';

const HERO_METRICS = ['open_rate', 'click_rate', 'emails_sent', 'active_subscribers'];

interface MailOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  initialTab?: string | null;
}

export function MailOverviewPanel({
  channel,
  onClose,
  onExpand,
}: MailOverviewPanelProps) {
  return (
    <ChannelOverviewPanel
      channel={channel}
      onClose={onClose}
      onExpand={onExpand}
      icon={Mail}
      iconColor="text-amber-500"
      heroMetrics={HERO_METRICS}
      gradientPrefix="mail"
      dashboardSlug="email-nurture"
    >
      {(data) => (
        <>
          <MailDeliverabilityHealth kpis={data.kpis} />
          <MailListGrowthIndicator kpis={data.kpis} />
        </>
      )}
    </ChannelOverviewPanel>
  );
}
