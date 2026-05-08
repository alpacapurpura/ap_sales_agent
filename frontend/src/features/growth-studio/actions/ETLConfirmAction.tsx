/**
 * ETLConfirmAction — shows ETL trigger confirmation prompt with action button.
 *
 * Uses role="alert" for the confirm prompt.
 * On confirm: calls triggerEtlChannel from api/etl-api.ts (API layer owns HTTP calls).
 */
"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useState } from "react";

import { triggerEtlChannel } from "../api/etl-api";
import type { ActionComponentProps } from "@/lib/form-runtime/actions/registry";

// ─── Payload types ────────────────────────────────────────────────────────────

interface ETLConfirmPayload {
  channel: string;
  confirm_message: string;
  etl_endpoint?: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders ETL confirmation prompt from copilot action payload.
 */
export function ETLConfirmAction({ value, onChange }: ActionComponentProps<ETLConfirmPayload>) {
  const { getToken } = useAuth();
  const [isPending, setIsPending] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  const handleConfirm = useCallback(async () => {
    setIsPending(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");

      await triggerEtlChannel(token, value.channel, value.etl_endpoint);

      setConfirmed(true);
      onChange({ ...value });
    } catch {
      // Non-critical: UI remains confirming so user can retry
    } finally {
      setIsPending(false);
    }
  }, [getToken, onChange, value]);

  if (confirmed) {
    return (
      <div role="alert" className="rounded-md border border-green-200 bg-green-50 px-4 py-3">
        <p className="text-sm text-green-800">Actualización iniciada para {value.channel}.</p>
      </div>
    );
  }

  return (
    <div role="alert" className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 space-y-3">
      <p className="text-sm text-blue-900 font-medium">{value.confirm_message}</p>
      <p className="text-xs text-blue-700">Canal: {value.channel}</p>
      <button
        type="button"
        onClick={handleConfirm}
        disabled={isPending}
        className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        aria-label={`Confirmar actualización de ${value.channel}`}
      >
        {isPending ? "Iniciando..." : "Confirmar"}
      </button>
    </div>
  );
}
