"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, Sparkles } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import { forwardRef, useCallback, useState } from "react";

import { Button } from "@/components/ui/button";
import { startInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { cn } from "@/lib/utils";

interface InterviewModeButtonProps extends Omit<
  React.ButtonHTMLAttributes<HTMLButtonElement>,
  "onClick"
> {
  /** The interview domain: "brand", "buyer_persona", "offer" */
  domain: string;
  /** Entity ID for domain-specific interviews (personaId, offerId) */
  entityId?: string;
  /** Custom button label (default: "Modo Entrevista") */
  label?: string;
}

const SECTION_KEY_BY_DOMAIN: Record<string, string> = {
  brand: "brand.root",
  buyer_persona: "brand.buyer-persona",
  offer: "offer.root",
};

function routeFor(domain: string, tenantId: string, entityId?: string): string {
  switch (domain) {
    case "brand":
      return `/${tenantId}/brand-studio`;
    case "buyer_persona":
      return entityId
        ? `/${tenantId}/brand-studio/publico/persona/${entityId}`
        : `/${tenantId}/brand-studio/publico`;
    case "offer":
      return entityId ? `/${tenantId}/offer-studio/offer/${entityId}` : `/${tenantId}/offer-studio`;
    default:
      return `/${tenantId}/${domain.replace("_", "-")}-studio`;
  }
}

/**
 * Starts a copilot interview for the given domain and navigates to the
 * corresponding studio page. The sidebar activates inline from the copilot
 * store — no dedicated /interview route is rendered (those were deleted in
 * Sprint 3 in favour of the sidebar-absorbed flow).
 *
 * For `buyer_persona` + `offer`, entityId is required to bind the interview
 * to a concrete entity; for `brand` the interview is tenant-global.
 */
export const InterviewModeButton = forwardRef<HTMLButtonElement, InterviewModeButtonProps>(
  function InterviewModeButtonImpl(
    { domain, entityId, label = "Modo Entrevista", className, disabled, ...props },
    ref,
  ) {
    const router = useRouter();
    const params = useParams();
    const tenantId = params.tenantId as string;
    const { getToken } = useAuth();

    const [submitting, setSubmitting] = useState(false);

    const handleClick = useCallback(async () => {
      const target = routeFor(domain, tenantId, entityId);

      // buyer_persona + offer require an entity to start an interview.
      // Without entityId just navigate to the listing page.
      const canStartInterview =
        domain === "brand" ||
        ((domain === "buyer_persona" || domain === "offer") && Boolean(entityId));

      if (!canStartInterview) {
        router.push(target);
        return;
      }

      setSubmitting(true);
      try {
        const token = await getToken();
        if (!token) {
          router.push(target);
          return;
        }
        const interview = await startInterview(token, domain, entityId);
        const store = useCopilotStore.getState();
        store.setSession({
          sectionKey: SECTION_KEY_BY_DOMAIN[domain] ?? `${domain}.root`,
          label,
          entityId: entityId ?? "",
          procedure: "interview",
          sessionId: interview.session_id,
          startedAt: new Date(),
          snapshot: {},
        });
        store.setConversationId(interview.conversation_id);
        store.addMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: interview.initial_message,
          timestamp: Date.now(),
        });
        store.setSidebarState("open");
      } catch (err) {
        // Navigate anyway; the copilot can retry from the destination page.
        console.error("Failed to start interview", err);
      } finally {
        setSubmitting(false);
        router.push(target);
      }
    }, [domain, entityId, getToken, label, router, tenantId]);

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
