'use client';

import { useGrowthStudioContext } from '../context/GrowthStudioContext';
import type { PeriodType } from '../../../api/stage-detail-api';

const PERIOD_OPTIONS: { value: PeriodType; label: string }[] = [
  { value: 'last_30_days', label: '30 días' },
  { value: 'weekly', label: 'Semanal' },
  { value: 'monthly', label: 'Mensual' },
  { value: 'quarterly', label: 'Trimestral' },
];

export function PeriodSelector() {
  const { selectedPeriod, setSelectedPeriod } = useGrowthStudioContext();

  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/50 p-0.5">
      {PERIOD_OPTIONS.map(({ value, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => setSelectedPeriod(value)}
          className={`
            rounded-md px-3 py-1.5 text-xs font-medium transition-colors
            ${selectedPeriod === value
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'}
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
