"use client";

import { MoreVertical, RefreshCw, Pencil, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface LandingKebabMenuProps {
  tenantId: string;
  offerId: string;
  isOutdated?: boolean;
  onRegenerate: () => void;
  onUnpublish: () => void;
}

/**
 * Secondary actions for a generated landing: Regenerar, Editar en Puck,
 * Despublicar. When the landing is outdated, "Regenerar (recomendado)" is
 * promoted to the top of the list.
 */
export function LandingKebabMenu({
  tenantId,
  offerId,
  isOutdated = false,
  onRegenerate,
  onUnpublish,
}: LandingKebabMenuProps) {
  const openPuck = () => {
    window.open(`/${tenantId}/editor/${offerId}`, "_blank", "noopener,noreferrer");
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          aria-label="Más acciones de landing"
        >
          <MoreVertical className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem onClick={onRegenerate}>
          <RefreshCw className="mr-2 h-4 w-4" />
          {isOutdated ? "Regenerar (recomendado)" : "Regenerar"}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={openPuck}>
          <Pencil className="mr-2 h-4 w-4" />
          Editar en Puck
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onUnpublish} className="text-destructive">
          <EyeOff className="mr-2 h-4 w-4" />
          Despublicar
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
