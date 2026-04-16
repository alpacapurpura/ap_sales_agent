"use client";

import { Sparkles } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import { forwardRef, useCallback } from "react";

import { Button } from "@/components/ui/button";
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

/**
 * Navigates to the correct interview route for a given domain.
 *
 * Routes:
 *   brand          -> /brand-studio/interview
 *   buyer_persona  -> /brand-studio/interview/buyer-persona?personaId={entityId}
 *   offer          -> /offer-studio/interview?offerId={entityId}
 */
export const InterviewModeButton = forwardRef<HTMLButtonElement, InterviewModeButtonProps>(
  ({ domain, entityId, label = "Modo Entrevista", className, ...props }, ref) => {
    const router = useRouter();
    const params = useParams();
    const tenantId = params.tenantId as string;

    const handleClick = useCallback(() => {
      let path: string;

      switch (domain) {
        case "brand":
          path = `/${tenantId}/brand-studio/interview`;
          break;
        case "buyer_persona": {
          const personaQuery = entityId ? `?personaId=${entityId}` : "";
          path = `/${tenantId}/brand-studio/interview/buyer-persona${personaQuery}`;
          break;
        }
        case "offer": {
          const offerQuery = entityId ? `?offerId=${entityId}` : "";
          path = `/${tenantId}/offer-studio/interview${offerQuery}`;
          break;
        }
        default:
          path = `/${tenantId}/${domain.replace("_", "-")}-studio/interview`;
      }

      router.push(path);
    }, [domain, entityId, tenantId, router]);

    return (
      <Button
        ref={ref}
        variant="outline"
        onClick={handleClick}
        className={cn(
          "gap-2 border-purple-500/30 text-purple-300 hover:bg-purple-500/10 hover:text-purple-200",
          className,
        )}
        {...props}
      >
        <Sparkles className="h-4 w-4" />
        {label}
      </Button>
    );
  },
);
InterviewModeButton.displayName = "InterviewModeButton";
