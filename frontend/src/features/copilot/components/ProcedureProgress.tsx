"use client";

import { useCopilotStore } from "../store/copilot-store";
import { cn } from "@/lib/utils";

export function ProcedureProgress() {
  const { activeProcedure, clearActiveProcedure } = useCopilotStore();

  if (!activeProcedure) return null;

  const { name, steps, currentStepIndex } = activeProcedure;
  const allComplete = currentStepIndex >= steps.length;

  return (
    <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-purple-600 dark:text-purple-400">
          {name}
        </span>
        <button
          onClick={clearActiveProcedure}
          className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
        >
          Cerrar
        </button>
      </div>

      {/* Stepper dots */}
      <div className="flex items-center gap-1">
        {steps.map((step, idx) => (
          <div key={step.id} className="flex items-center">
            {idx > 0 && (
              <div
                className={cn(
                  "mx-0.5 h-0.5 w-3",
                  step.status === "completed" || (idx <= currentStepIndex && allComplete)
                    ? "bg-green-400"
                    : "bg-slate-200 dark:bg-slate-700"
                )}
              />
            )}
            <div className="group relative flex flex-col items-center">
              <div
                className={cn(
                  "h-3 w-3 rounded-full border-2 transition-all",
                  step.status === "completed" &&
                    "border-green-500 bg-green-500",
                  step.status === "current" &&
                    "animate-pulse border-purple-500 bg-purple-500",
                  step.status === "pending" &&
                    "border-slate-300 bg-slate-100 dark:border-slate-600 dark:bg-slate-800"
                )}
              />
              {/* Tooltip on hover */}
              <div className="pointer-events-none absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-white opacity-0 transition-opacity group-hover:opacity-100 dark:bg-slate-600">
                {step.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Current step label */}
      {!allComplete && steps[currentStepIndex] && (
        <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
          Paso {currentStepIndex + 1}/{steps.length}: {steps[currentStepIndex].label}
        </p>
      )}
      {allComplete && (
        <p className="mt-2 text-[11px] text-green-600 dark:text-green-400">
          Completado
        </p>
      )}
    </div>
  );
}
