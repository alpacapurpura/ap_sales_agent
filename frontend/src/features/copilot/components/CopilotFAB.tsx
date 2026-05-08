"use client";

import { MessageCircle } from "lucide-react";

import { useShellMutexContext } from "@/components/shared/layout/ShellMutexContext";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { useViewport } from "@/hooks/use-viewport";
import { Z_INDEX_CLASSES } from "@/lib/tokens/z-index";
import { cn } from "@/lib/utils";

/**
 * Floating Action Button to reopen the Copilot sidebar on mobile.
 *
 * Renders NULL when:
 * - Viewport >= md (tablet or desktop) — FAB is mobile-only.
 * - Copilot sidebarState !== 'collapsed' — the sidebar is already visible.
 *
 * Click dispatches `shellMutex.openPanel('copilot')` to open copilot
 * while respecting the mutex policy (closes app-sidebar if needed).
 *
 * AD7: fixed bottom-right, aria-label="Abrir asistente".
 * AD5: z-class via Z_INDEX_CLASSES.FAB (z-[70]) — no hardcoded z-NN.
 *
 * T-5 Phase 5 deliverable.
 */
export function CopilotFAB() {
  const viewport = useViewport();
  const sidebarState = useCopilotStore((s) => s.sidebarState);
  const shellMutex = useShellMutexContext();

  // Only show on mobile (<768px) — on tablet/desktop the copilot rail is always accessible.
  if (!viewport.isMobile) {
    return null;
  }

  // Only show when copilot is fully collapsed — if rail/full it's already visible.
  if (sidebarState !== "collapsed") {
    return null;
  }

  function handleClick() {
    shellMutex?.openPanel("copilot");
  }

  return (
    <Button
      onClick={handleClick}
      size="icon"
      aria-label="Abrir asistente"
      className={cn("fixed bottom-4 right-4 h-12 w-12 rounded-full shadow-lg", Z_INDEX_CLASSES.FAB)}
    >
      <MessageCircle className="h-5 w-5" aria-hidden="true" />
    </Button>
  );
}

CopilotFAB.displayName = "CopilotFAB";
