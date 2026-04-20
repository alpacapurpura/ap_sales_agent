"use client";

import { useAuth } from "@clerk/nextjs";
import { CheckCircle2, Circle } from "lucide-react";

import { reportCopilotEvent } from "../../api/copilot-api";
import { useCopilotStore } from "../../store/copilot-store";

interface ProgressChecklistProps {
  items: { label: string; done: boolean; route?: string }[];
}

/**
 *
 */
export function ProgressChecklist({ items }: ProgressChecklistProps) {
  const enqueuUIAction = useCopilotStore((s) => s.enqueuUIAction);
  const { getToken } = useAuth();

  const handleNavigate = (item: { label: string; route?: string }) => {
    enqueuUIAction({ type: "navigate", route: item.route });
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "checklist_item_clicked",
          {
            label: item.label,
            route: item.route || "",
          },
          token,
        );
      }
    });
  };

  return (
    <div className="my-1 space-y-1.5 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
      {items.map((item, idx) => {
        if (item.done) {
          return (
            <div key={idx} className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
              <span className="text-slate-400 line-through">{item.label}</span>
            </div>
          );
        }

        if (item.route) {
          return (
            <button
              key={idx}
              onClick={() => handleNavigate(item)}
              className="flex w-full items-center gap-2 rounded-lg px-1 py-0.5 text-left text-sm transition-colors hover:bg-purple-50 dark:hover:bg-purple-900/20"
            >
              <Circle className="h-4 w-4 shrink-0 text-purple-400" />
              <span className="text-slate-700 underline decoration-purple-300 dark:text-slate-200">
                {item.label}
              </span>
            </button>
          );
        }

        return (
          <div key={idx} className="flex items-center gap-2 text-sm">
            <Circle className="h-4 w-4 shrink-0 text-slate-300 dark:text-slate-600" />
            <span className="text-slate-500">{item.label}</span>
          </div>
        );
      })}
    </div>
  );
}
