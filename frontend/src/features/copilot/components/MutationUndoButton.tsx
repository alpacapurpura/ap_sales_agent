"use client";

import { Loader2, RotateCcw } from "lucide-react";
import { forwardRef, useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { useRevertMutations } from "../hooks/use-revert-mutations";

// ── Types ────────────────────────────────────────────────────────────

interface MutationUndoButtonProps extends React.HTMLAttributes<HTMLDivElement> {
  conversationId: string;
  mutationCount: number;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Button that opens an AlertDialog to confirm reverting all applied mutations
 * in the current conversation. Hidden when mutationCount === 0.
 */
export const MutationUndoButton = forwardRef<HTMLDivElement, MutationUndoButtonProps>(
  ({ conversationId, mutationCount, className, ...props }, ref) => {
    const [open, setOpen] = useState(false);
    const { mutate: revert, isPending } = useRevertMutations(conversationId);

    if (mutationCount === 0) return null;

    const handleConfirm = () => {
      revert({}, { onSettled: () => setOpen(false) });
    };

    return (
      <div ref={ref} className={cn(className)} {...props}>
        <AlertDialog open={open} onOpenChange={setOpen}>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 gap-1 text-xs text-muted-foreground hover:text-foreground"
              aria-label={`Deshacer cambios (${mutationCount})`}
            >
              {isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <RotateCcw className="h-3.5 w-3.5" />
              )}
              <span>{mutationCount}</span>
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>¿Seguro que quieres deshacer los cambios?</AlertDialogTitle>
              <AlertDialogDescription>
                Se revertirán {mutationCount} cambios aplicados en esta conversación. Esta acción no
                se puede deshacer.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={isPending}>Cancelar</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirm}
                disabled={isPending}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Deshacer todo
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    );
  },
);
MutationUndoButton.displayName = "MutationUndoButton";
