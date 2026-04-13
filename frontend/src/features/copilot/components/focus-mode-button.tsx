"use client";

import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCopilotStore } from "../store/copilot-store";
import type { FocusEntity } from "../store/copilot-store";

interface FocusModeButtonProps {
  domain: FocusEntity["domain"];
  entityId?: string;
  label: string;
  /**
   * Snapshot of entity data captured at render time.
   * Used as the snapshot when `getEntityData` is not provided.
   */
  entityData: Record<string, unknown>;
  /**
   * [R3] Optional callback to fetch the latest entity data at activation
   * time. When provided, the result is used as the focus snapshot instead
   * of the potentially-stale `entityData` prop.
   */
  getEntityData?: () => Record<string, unknown>;
  /**
   * [UX3] Optional callback fired on `mouseEnter` to prefetch entity data
   * into the React Query cache so activation is instant.
   */
  prefetchFn?: () => void;
  className?: string;
}

export function FocusModeButton({
  domain,
  entityId,
  label,
  entityData,
  getEntityData,
  prefetchFn,
  className,
}: FocusModeButtonProps) {
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setFocusSnapshot = useCopilotStore((s) => s.setFocusSnapshot);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);

  const handleMouseEnter = () => {
    prefetchFn?.();
  };

  const handleActivateFocus = () => {
    // R3: resolve fresh data at click time rather than using the stale render-time prop
    const snapshot = getEntityData ? getEntityData() : entityData;
    setFocusEntity({ domain, entityId, label });
    setFocusSnapshot(snapshot);
    clearSelectedFields();
    setSidebarState("expanded");
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onMouseEnter={handleMouseEnter}
      onClick={handleActivateFocus}
      className={className}
    >
      <Sparkles className="mr-1.5 h-3.5 w-3.5 text-purple-500" />
      Focus
    </Button>
  );
}
