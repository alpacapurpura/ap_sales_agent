"use client";

import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import type { FocusEntity } from "../store/copilot-store";

interface FocusModeButtonProps {
  domain: FocusEntity["domain"];
  entityId?: string;
  label: string;
  entityData: Record<string, unknown>;
  className?: string;
}

export function FocusModeButton({
  domain,
  entityId,
  label,
  entityData,
  className,
}: FocusModeButtonProps) {
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setFocusSnapshot = useCopilotStore((s) => s.setFocusSnapshot);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);

  const handleActivateFocus = () => {
    setFocusEntity({ domain, entityId, label });
    setFocusSnapshot(entityData);
    clearSelectedFields();
    setSidebarState("expanded");
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleActivateFocus}
      className={className}
    >
      <Sparkles className="mr-1.5 h-3.5 w-3.5 text-purple-500" />
      Focus
    </Button>
  );
}
