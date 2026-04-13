"use client";

import { forwardRef, useCallback } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

interface SectionChatTriggerProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "onClick"> {
  /** Unique identifier for the section (e.g. "identity", "tone") */
  sectionId: string;
  /** Human-readable section label (e.g. "Identidad", "Tono y Voz") */
  sectionLabel: string;
}

/**
 * Small icon button that opens the copilot panel with section context.
 * Used inline next to section headers so users can ask the AI about
 * a specific part of a form or page.
 */
export const SectionChatTrigger = forwardRef<
  HTMLButtonElement,
  SectionChatTriggerProps
>(({ sectionId, sectionLabel, className, ...props }, ref) => {
  const { openPanel, addSelectedField } = useCopilotStore();

  const handleClick = useCallback(() => {
    addSelectedField({
      fieldId: sectionId,
      fieldLabel: sectionLabel,
      fieldValue: "",
    });
    openPanel();
  }, [sectionId, sectionLabel, addSelectedField, openPanel]);

  return (
    <Button
      ref={ref}
      type="button"
      variant="ghost"
      size="icon"
      onClick={handleClick}
      aria-label={`Consultar sobre ${sectionLabel}`}
      className={cn(
        "h-7 w-7 text-muted-foreground hover:text-purple-400",
        className,
      )}
      {...props}
    >
      <MessageCircle className="h-3.5 w-3.5" />
    </Button>
  );
});
SectionChatTrigger.displayName = "SectionChatTrigger";
