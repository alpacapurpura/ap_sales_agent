/**
 * ETLRateLimitedAction — shows rate limit alert for ETL refresh.
 *
 * Uses role="alert" for screen reader announcement.
 * Shows retry_after_seconds with Spanish neutro copy.
 */
"use client";

import type { ActionComponentProps } from "@/lib/form-runtime/actions/registry";

// ─── Payload types ────────────────────────────────────────────────────────────

interface ETLRateLimitedPayload {
  channel: string;
  retry_after_seconds: number;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders rate limit alert from copilot action payload.
 */
export function ETLRateLimitedAction({ value }: ActionComponentProps<ETLRateLimitedPayload>) {
  const minutes = Math.ceil(value.retry_after_seconds / 60);
  const minutesSuffix = minutes !== 1 ? "s" : "";
  const timeLabel =
    value.retry_after_seconds < 60
      ? `${value.retry_after_seconds} segundos`
      : `${minutes} minuto${minutesSuffix}`;

  return (
    <div
      role="alert"
      className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 space-y-1"
    >
      <p className="text-sm font-medium text-amber-900">
        Límite de tarifa alcanzado — {value.channel}
      </p>
      <p className="text-sm text-amber-700">
        Podrás intentarlo nuevamente en {timeLabel} ({value.retry_after_seconds}s).
      </p>
    </div>
  );
}
