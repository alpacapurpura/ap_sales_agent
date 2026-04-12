"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface SessionRestoreModalProps {
  open: boolean;
  blocksCompleted: number;
  totalBlocks: number;
  onContinue: () => void;
  onStartOver: () => void;
  isLoading?: boolean;
}

/**
 * Modal shown when the user navigates to /brand-studio/interview without
 * a ?session= param and an active session already exists.
 *
 * Gives the user the choice to resume the paused session or start fresh.
 */
export function SessionRestoreModal({
  open,
  blocksCompleted,
  totalBlocks,
  onContinue,
  onStartOver,
  isLoading = false,
}: SessionRestoreModalProps) {
  return (
    <Dialog open={open}>
      <DialogContent className="sm:max-w-md bg-[#1a1a2e] border-white/10 text-white">
        <DialogHeader>
          <DialogTitle className="text-white">
            Tienes una entrevista pausada
          </DialogTitle>
          <DialogDescription className="text-white/60">
            {blocksCompleted} de {totalBlocks} bloques completados. ¿Quieres
            continuar donde quedaste o empezar de nuevo?
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3 py-4">
          {/* Progress bar */}
          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-purple-500 rounded-full transition-all"
              style={{
                width: `${totalBlocks > 0 ? Math.round((blocksCompleted / totalBlocks) * 100) : 0}%`,
              }}
            />
          </div>
          <p className="text-xs text-white/40 text-right">
            {totalBlocks > 0
              ? `${Math.round((blocksCompleted / totalBlocks) * 100)}% completado`
              : "0% completado"}
          </p>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            variant="ghost"
            onClick={onStartOver}
            disabled={isLoading}
            className="text-white/60 hover:text-white hover:bg-white/10 border border-white/10"
          >
            Empezar de nuevo
          </Button>
          <Button
            onClick={onContinue}
            disabled={isLoading}
            className="bg-purple-600 hover:bg-purple-700 text-white"
          >
            {isLoading ? "Cargando..." : "Continuar donde quedé"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
