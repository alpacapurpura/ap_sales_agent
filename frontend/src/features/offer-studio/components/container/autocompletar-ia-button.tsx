"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { OfferSmartFillDialog } from "../editor/components/smart-fill/offer-smart-fill-dialog";

export interface AutocompletarIAButtonProps {
  offerId: string;
}

/**
 * Header button that opens the existing `OfferSmartFillDialog` to fill empty
 * sections of the offer with AI based on the Brand Studio data.
 *
 * This is a thin wrapper — the real flow lives in `OfferSmartFillDialog`.
 */
export function AutocompletarIAButton({ offerId }: AutocompletarIAButtonProps) {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  return (
    <>
      <TooltipProvider delayDuration={200}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOpen(true)}
              className="h-8 gap-1.5 text-primary"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Autocompletar IA
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Rellená las secciones vacías usando los datos del Brand Studio.
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <OfferSmartFillDialog
        open={open}
        onOpenChange={setOpen}
        offerId={offerId}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["offer", offerId] });
        }}
      />
    </>
  );
}
