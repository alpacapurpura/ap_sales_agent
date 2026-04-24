"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, Sparkles } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { forwardRef, useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { reportCopilotEvent } from "@/features/copilot/api/copilot-api";
import { useCopilotChat } from "@/features/copilot/hooks/use-copilot-chat";
import { canStartGuided, promptFor, routeFor } from "@/features/copilot/lib/guided-prompts";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

interface GuidedSetupButtonProps extends Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  "onClick"
> {
  /** Guided setup domain: "brand", "buyer_persona", "offer". */
  domain: string;
  /** Entity ID for domain-specific flows (personaId, offerId). */
  entityId?: string;
  /** Custom label (default "Guíame paso a paso"). */
  label?: string;
}

/**
 * Triggers guided-setup mode by sending a message that the LLM answers with
 * the ``start_guided_setup`` tool call. The sidebar opens automatically and
 * the header/progress chip update from the ``guided_started`` UIAction.
 *
 * Replaces the old ``InterviewModeButton`` which hit a dedicated
 * ``/api/v1/copilot/interview/start`` endpoint. That endpoint has been
 * retired; guided flows now live entirely inside the main chat orchestrator.
 *
 * Para flujos donde el guided se dispara *después* de crear una entidad
 * nueva (Crear oferta con IA, Crear buyer persona con IA), usar
 * `useGuidedEntityCreation` — encapsula create + openPanel + sendMessage +
 * navigate sobre el mismo contrato compartido.
 */
export const GuidedSetupButton = forwardRef<HTMLButtonElement, GuidedSetupButtonProps>(
  function GuidedSetupButtonImpl(
    { domain, entityId, label = "Guíame paso a paso", className, disabled, ...props },
    ref,
  ) {
    const router = useRouter();
    const params = useParams();
    const tenantId = params.tenantId as string;
    const { getToken } = useAuth();
    const { sendMessage } = useCopilotChat();

    const [submitting, setSubmitting] = useState(false);

    const handleClick = useCallback(async () => {
      const target = routeFor(domain, tenantId, entityId);

      // buyer_persona + offer require an entity. If missing, just navigate
      // to the listing page (user will pick one there).
      if (!canStartGuided(domain, entityId)) {
        router.push(target);
        return;
      }

      setSubmitting(true);
      try {
        useCopilotStore.getState().openPanel();
        await sendMessage(promptFor(domain, entityId));
        // Fire-and-forget telemetry; never await.
        const token = await getToken();
        if (token) {
          reportCopilotEvent(
            "guided_setup_requested",
            { domain, entity_id: entityId ?? null },
            token,
          );
        }
      } finally {
        setSubmitting(false);
        router.push(target);
      }
    }, [domain, entityId, getToken, router, sendMessage, tenantId]);

    return (
      <Button
        ref={ref}
        variant="outline"
        onClick={handleClick}
        disabled={Boolean(disabled) || submitting}
        className={cn(
          "gap-2 border-purple-500/30 text-purple-300 hover:bg-purple-500/10 hover:text-purple-200",
          className,
        )}
        {...props}
      >
        {submitting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        {label}
      </Button>
    );
  },
);
