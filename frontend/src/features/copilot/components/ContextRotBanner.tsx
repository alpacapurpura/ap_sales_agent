"use client";

import { X } from "lucide-react";
import { forwardRef } from "react";

import { cn } from "@/lib/utils";

import { useCreateConversation } from "../hooks/use-create-conversation";
import { useCopilotStore } from "../store/copilot-store";

// ── Types ────────────────────────────────────────────────────────────

interface ContextRotBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  conversationId: string;
  totalTokens: number;
  messageCount: number;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Banner that warns the user when a conversation context is getting long.
 * Yellow at threshold, red at hard limit.
 * Dismissible per-conversation (in-memory, not persisted).
 */
export const ContextRotBanner = forwardRef<HTMLDivElement, ContextRotBannerProps>(
  ({ conversationId, totalTokens, messageCount, className, ...props }, ref) => {
    const dismissedRotBanners = useCopilotStore((s) => s.dismissedRotBanners);
    const dismissRotBanner = useCopilotStore((s) => s.dismissRotBanner);
    const { mutate: createConversation } = useCreateConversation();

    const isDismissed = dismissedRotBanners.has(conversationId);
    const isRed = totalTokens >= 16000;
    const isVisible = (totalTokens >= 8000 || messageCount >= 12) && !isDismissed;

    if (!isVisible) return null;

    const handleDismiss = () => {
      dismissRotBanner(conversationId);
    };

    const handleNewConversation = () => {
      createConversation();
    };

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          "flex items-start gap-2 px-3 py-2 rounded-md text-sm mx-3 mb-2",
          isRed
            ? "bg-red-50 border border-red-300 text-red-900"
            : "bg-yellow-50 border border-yellow-300 text-yellow-900",
          className,
        )}
        {...props}
      >
        <p className="flex-1 leading-snug">
          Esta conversación ya está larga. Para que el copilot te entienda mejor,{" "}
          <button
            type="button"
            onClick={handleNewConversation}
            className={cn(
              "underline underline-offset-2 hover:no-underline font-medium",
              isRed ? "text-red-800" : "text-yellow-800",
            )}
          >
            empieza una nueva
          </button>
          .
        </p>
        <button
          type="button"
          onClick={handleDismiss}
          aria-label="Cerrar aviso"
          className={cn(
            "flex-shrink-0 rounded hover:opacity-70",
            isRed ? "text-red-700" : "text-yellow-700",
          )}
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  },
);
ContextRotBanner.displayName = "ContextRotBanner";
