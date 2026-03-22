'use client';

interface HealthBarProps {
  activeCount: number;
  inactiveCount: number;
}

export function HealthBar({ activeCount, inactiveCount }: HealthBarProps) {
  const total = activeCount + inactiveCount;
  const activePct = total > 0 ? (activeCount / total) * 100 : 100;
  const inactivePct = total > 0 ? (inactiveCount / total) * 100 : 0;

  // Ensure minimum 1% visual width for non-zero segments
  const minWidth = total > 0 ? 1 : 0;

  return (
    <div className="px-3 py-2">
      <div className="flex h-3 w-full rounded-full overflow-hidden bg-muted">
        <div
          className="bg-emerald-500 transition-all"
          style={{ width: `${Math.max(activePct, activeCount > 0 ? minWidth : 0)}%` }}
        />
        <div
          className="bg-yellow-400 transition-all"
          style={{ width: `${Math.max(inactivePct, inactiveCount > 0 ? minWidth : 0)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-muted-foreground mt-1">
        <span className="text-emerald-600 dark:text-emerald-400">{activeCount} activos</span>
        <span className="text-yellow-600 dark:text-yellow-400">{inactiveCount} inactivos</span>
      </div>
    </div>
  );
}
