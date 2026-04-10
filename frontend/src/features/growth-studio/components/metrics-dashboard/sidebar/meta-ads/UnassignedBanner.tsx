'use client';

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

import { Button } from '@/components/ui/button';

interface UnassignedBannerProps {
  count: number;
  onAssignClick: () => void;
}

function todayKey(): string {
  const today = new Date().toISOString().slice(0, 10);
  return `meta-ads-unassigned-banner-dismissed-${today}`;
}

function isDismissed(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    return localStorage.getItem(todayKey()) === '1';
  } catch {
    return false;
  }
}

export function UnassignedBanner({ count, onAssignClick }: UnassignedBannerProps) {
  const [dismissed, setDismissed] = useState(() => isDismissed());

  if (count <= 0) return null;
  if (dismissed) return null;

  const handleDismiss = () => {
    try {
      localStorage.setItem(todayKey(), '1');
    } catch {
      /* noop */
    }
    setDismissed(true);
  };

  const label = count === 1 ? 'campaña' : 'campañas';

  return (
    <div
      className="flex items-start justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3"
      role="status"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" aria-hidden="true" />
        <div>
          <p className="text-sm font-medium text-amber-400">
            Tenés {count} {label} sin asignar a un offer
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Asigná cada campaña a un producto para ver métricas claras por offer.
          </p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={onAssignClick}
          className="h-7 border-amber-500/50 text-amber-400 hover:bg-amber-500/20"
        >
          Asignar ahora
        </Button>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Cerrar banner"
          className="rounded-md p-1 text-amber-500/70 hover:bg-amber-500/10 hover:text-amber-400"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
