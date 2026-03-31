'use client';

interface HealthBarProps {
  activeCount: number;
  inactiveCount: number;
}

export function HealthBar({ activeCount, inactiveCount }: HealthBarProps) {
  const total = activeCount + inactiveCount;
  const activePct = total > 0 ? (activeCount / total) * 100 : 0;
  const inactivePct = total > 0 ? (inactiveCount / total) * 100 : 0;

  return (
    <div className="w-full h-4 rounded-full bg-muted overflow-hidden flex shadow-inner">
      <div
        className="h-full bg-emerald-500 transition-all duration-500"
        style={{ width: `${activePct}%` }}
      />
      <div
        className="h-full bg-amber-400 transition-all duration-500"
        style={{ width: `${inactivePct}%` }}
      />
    </div>
  );
}
