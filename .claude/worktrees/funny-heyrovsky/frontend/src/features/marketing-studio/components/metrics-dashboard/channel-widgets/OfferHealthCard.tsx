'use client';

import type { OfferHealthData } from '../../../types/metrics';

interface OfferHealthCardProps {
  offer: OfferHealthData;
}

export function OfferHealthCard({ offer }: OfferHealthCardProps) {
  const isHealthy = offer.healthPct >= 60;

  return (
    <div className="rounded-lg border p-3 space-y-1">
      {/* First line: name + badge */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-semibold">{offer.publicName}</span>
          <span className="text-xs text-muted-foreground ml-2">
            {offer.totalCustomers} clientes
          </span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded-full ${
            isHealthy
              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400'
              : 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/30 dark:text-yellow-400'
          }`}
        >
          {isHealthy ? 'Saludable' : 'Atencion'}
        </span>
      </div>

      {/* Second line: counts + health % */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-emerald-600 dark:text-emerald-400">
          {offer.activeCount} activos
        </span>
        <span className="text-yellow-600 dark:text-yellow-400">
          {offer.inactiveCount} inactivos
        </span>
        <span className="text-muted-foreground font-semibold">
          {offer.healthPct.toFixed(0)}%
        </span>
      </div>

      {/* Third line: TTV (if available) */}
      {offer.ttvDays != null && (
        <div className="text-xs text-muted-foreground">
          Tiempo de activacion: {Math.round(offer.ttvDays)} dias
        </div>
      )}
    </div>
  );
}
