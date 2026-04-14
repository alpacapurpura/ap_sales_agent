"use client";

import { useState } from "react";
import { BookOpen, Package, Undo2, User, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useCopilotStore } from "../store/copilot-store";
import { cn } from "@/lib/utils";

const DOMAIN_ICONS: Record<string, typeof Package> = {
  offer: Package,
  brand: BookOpen,
  buyer_persona: User,
};

export function FocusBar() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);
  const interviewProgress = useCopilotStore((s) => s.interviewProgress);
  const previewData = useCopilotStore((s) => s.previewData);
  const clearFocus = useCopilotStore((s) => s.clearFocus);
  const clearInterview = useCopilotStore((s) => s.clearInterview);
  const setSidebarState = useCopilotStore((s) => s.setSidebarState);

  const [showExitDialog, setShowExitDialog] = useState(false);

  if (!focusEntity) return null;

  const Icon = DOMAIN_ICONS[focusEntity.domain] ?? Package;
  const hasSnapshot = focusSnapshot && Object.keys(focusSnapshot).length > 0;

  /** Hay cambios sin guardar si previewData tiene alguna clave pendiente. */
  const hasUnsavedChanges = previewData !== null && Object.keys(previewData).length > 0;

  const doExitFocus = () => {
    clearInterview();
    clearFocus();
    setSidebarState("open");
  };

  const handleExitFocus = () => {
    if (hasUnsavedChanges) {
      setShowExitDialog(true);
    } else {
      doExitFocus();
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div
        className="flex items-center gap-2 border-b border-slate-200 bg-purple-50 px-3 py-2 dark:border-slate-700 dark:bg-purple-900/20"
        data-testid="focus-bar"
      >
        <Icon className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400" />
        <span className="min-w-0 truncate text-xs font-medium text-purple-800 dark:text-purple-300">
          {focusEntity.label}
        </span>

        {interviewProgress && (
          <div className="ml-auto mr-2 flex items-center gap-1">
            {Array.from({ length: interviewProgress.totalBlocks }).map((_, i) => {
              const completedId = interviewProgress.blocksCompleted[i];
              const isCompleted = i < interviewProgress.blocksCompleted.length;
              const isCurrent = i === interviewProgress.blocksCompleted.length;
              const tooltipLabel =
                completedId ??
                (isCurrent
                  ? interviewProgress.currentBlock || `Bloque ${i + 1}`
                  : `Bloque ${i + 1}`);

              return (
                <Tooltip key={i}>
                  <TooltipTrigger asChild>
                    <div
                      data-testid="progress-dot"
                      className={cn(
                        "h-1.5 w-1.5 cursor-default rounded-full transition-colors duration-300",
                        isCompleted && "bg-green-500",
                        isCurrent && "animate-pulse bg-purple-500",
                        !isCompleted && !isCurrent && "bg-slate-300 dark:bg-slate-600",
                      )}
                    />
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="text-xs">
                    {tooltipLabel}
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </div>
        )}

        {!interviewProgress && <div className="flex-1" />}

        {hasSnapshot && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              window.dispatchEvent(
                new CustomEvent("copilot:undo-all", {
                  detail: { snapshot: focusSnapshot },
                }),
              );
            }}
            className="h-6 gap-1 px-2 text-xs text-purple-600 hover:text-purple-800 dark:text-purple-400"
          >
            <Undo2 className="h-3 w-3" />
            Deshacer todo
          </Button>
        )}

        <Button
          size="sm"
          variant="ghost"
          onClick={handleExitFocus}
          className="h-6 gap-1 px-2 text-xs text-slate-500 hover:text-slate-700"
        >
          <X className="h-3 w-3" />
          Salir de Focus
        </Button>
      </div>

      <AlertDialog open={showExitDialog} onOpenChange={setShowExitDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Salir del modo Focus?</AlertDialogTitle>
            <AlertDialogDescription>
              Tienes cambios sin guardar en esta sesión de entrevista. Si sales ahora, se perderán
              los cambios pendientes que aún no han sido aplicados al formulario.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setShowExitDialog(false)}>
              Continuar entrevista
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setShowExitDialog(false);
                doExitFocus();
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Salir sin guardar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </TooltipProvider>
  );
}
