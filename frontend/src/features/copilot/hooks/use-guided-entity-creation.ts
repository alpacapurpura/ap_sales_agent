"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { reportCopilotEvent } from "@/features/copilot/api/copilot-api";
import { useCopilotChat } from "@/features/copilot/hooks/use-copilot-chat";
import { type GuidedDomain, promptFor, routeFor } from "@/features/copilot/lib/guided-prompts";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

export interface UseGuidedEntityCreationConfig<T extends { id: string }, TArgs = void> {
  /** Guided-setup domain ("brand" | "buyer_persona" | "offer"). */
  domain: GuidedDomain | (string & {});
  /** Tenant in URL — used to compute the default navigation URL. */
  tenantId: string;
  /**
   * Create the entity in the backend. The hook calls this exactly once per
   * `create()` invocation, forwarding whatever args the caller passed.
   * Must return an entity with at least an `id`.
   */
  createEntity: (args: TArgs) => Promise<T>;
  /**
   * Optional URL builder for navigation after the guided trigger.
   * Defaults to `routeFor(domain, tenantId, entity.id)` so the same routing
   * contract that GuidedSetupButton uses is reused across studios.
   */
  getNavigateUrl?: (entity: T) => string;
  /**
   * Optional override for the final navigation step. Defaults to
   * `next/navigation` `router.push`. Pass the studio-specific navigator
   * (e.g. `useNavigation().navigate`) when you need its loading/tracking
   * semantics on top of plain `push`.
   */
  onNavigate?: (url: string) => void;
}

export interface UseGuidedEntityCreationResult<TArgs = void> {
  /** Triggers create → openPanel → guided prompt → navigate. Idempotent while in flight. */
  create: (args: TArgs) => Promise<void>;
  creating: boolean;
  error: string | null;
}

/**
 * Encapsulates the "Crear nueva X con IA" flow that brand-studio,
 * offer-studio and buyer-persona share:
 *
 *  1. Create the entity in the backend (caller-supplied).
 *  2. Open the copilot panel so the user sees the guided rail.
 *  3. Send the chat message that makes the LLM call ``start_guided_setup``.
 *     Best-effort: if the chat is unavailable we still navigate so the user
 *     can retry from the detail page.
 *  4. Navigate to the entity detail URL (or a caller-provided override).
 *  5. Fire-and-forget telemetry so we can measure adoption.
 *
 * Centralising this pipeline avoids the four-line copy-paste that lived in
 * each dashboard and keeps the guided prompt + route contract aligned with
 * GuidedSetupButton via the shared `guided-prompts` module.
 */
export function useGuidedEntityCreation<T extends { id: string }, TArgs = void>({
  domain,
  tenantId,
  createEntity,
  getNavigateUrl,
  onNavigate,
}: UseGuidedEntityCreationConfig<T, TArgs>): UseGuidedEntityCreationResult<TArgs> {
  const router = useRouter();
  const { getToken } = useAuth();
  const { sendMessage } = useCopilotChat();

  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const create = useCallback(
    async (args: TArgs) => {
      if (creating) return;
      setCreating(true);
      setError(null);

      let entity: T;
      try {
        entity = await createEntity(args);
      } catch (err) {
        const message = err instanceof Error ? err.message : "No se pudo crear la entidad.";
        console.error("useGuidedEntityCreation.createEntity failed", err);
        setError(message);
        setCreating(false);
        return;
      }

      useCopilotStore.getState().openPanel();

      try {
        await sendMessage(promptFor(domain, entity.id));
      } catch (sendErr) {
        // Best-effort: the entity exists, navigation must still happen so the
        // user can retry guided from the detail page.
        console.error("useGuidedEntityCreation.sendMessage failed", sendErr);
      }

      const token = await getToken();
      if (token) {
        reportCopilotEvent("guided_setup_requested", { domain, entity_id: entity.id }, token);
      }

      const url = getNavigateUrl ? getNavigateUrl(entity) : routeFor(domain, tenantId, entity.id);
      if (onNavigate) {
        onNavigate(url);
      } else {
        router.push(url);
      }

      setCreating(false);
    },
    [
      creating,
      createEntity,
      domain,
      getNavigateUrl,
      getToken,
      onNavigate,
      router,
      sendMessage,
      tenantId,
    ],
  );

  return { create, creating, error };
}
