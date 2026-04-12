'use client';

import { PendientesView } from '../pendientes/PendientesView';
import type { MetaAdsPeriod } from '../../../../../types/metrics';

interface PendientesTabProps {
  period: MetaAdsPeriod;
  onPeriodChange: (p: MetaAdsPeriod) => void;
  onBackToCampaigns: () => void;
}

export function PendientesTab({
  period,
  onPeriodChange,
  onBackToCampaigns,
}: PendientesTabProps) {
  return (
    <div className="h-[calc(100vh-140px)]">
      <PendientesView
        period={period}
        onPeriodChange={onPeriodChange}
        onBackToCampaigns={onBackToCampaigns}
      />
    </div>
  );
}
