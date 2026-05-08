/**
 * ETLRefreshAction — shows ETL refresh status (queued/success) from copilot action payload.
 */
"use client";

import type { ActionComponentProps } from "@/lib/form-runtime/actions/registry";

// ─── Payload types ────────────────────────────────────────────────────────────

interface ETLRefreshPayload {
  status: "queued" | "success" | "error";
  channel: string;
  run_id?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders ETL refresh queued/success state from copilot action payload.
 */
export function ETLRefreshAction({ value }: ActionComponentProps<ETLRefreshPayload>) {
  const statusLabel: Record<string, string> = {
    queued: "Actualización en cola",
    success: "Actualización completada",
    error: "Error en la actualización",
  };

  return (
    <section
      role="region"
      aria-label={`Estado de actualización: ${value.channel}`}
      className="rounded-lg border p-4 space-y-2"
    >
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{value.channel}</span>
        <span className="text-xs text-muted-foreground">
          {statusLabel[value.status] ?? value.status}
        </span>
      </div>

      {value.run_id && <p className="text-xs text-muted-foreground font-mono">{value.run_id}</p>}
    </section>
  );
}
