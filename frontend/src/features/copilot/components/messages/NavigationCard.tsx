"use client";

import { useAuth } from "@clerk/nextjs";
import { ArrowRight, MapPin } from "lucide-react";

import { Button } from "@/components/ui/button";

import { reportCopilotEvent } from "../../api/copilot-api";
import { useCopilotNavigator } from "../../hooks/use-copilot-navigator";

import type { UIAction } from "../../store/copilot-store";

interface NavigationCardProps {
  action: UIAction;
}

/**
 *
 */
export function NavigationCard({ action }: NavigationCardProps) {
  const { executeAction } = useCopilotNavigator();
  const { getToken } = useAuth();

  const label = action.page_label ?? action.route?.split("/").pop() ?? "Destino";

  const sublabel = action.section_id ? `> ${action.section_id}` : undefined;

  const handleClick = () => {
    executeAction(action);
    void getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "navigation_clicked",
          {
            route: action.route || "",
            page_label: label,
            section_id: action.section_id || "",
          },
          token,
        );
      }
    });
  };

  return (
    <Button
      variant="outline"
      onClick={handleClick}
      className="my-1 flex w-full items-center justify-between gap-2 rounded-xl border-purple-200 bg-purple-50/50 px-3 py-2.5 text-left text-sm hover:bg-purple-100 dark:border-purple-800 dark:bg-purple-900/20 dark:hover:bg-purple-900/40"
    >
      <div className="flex items-center gap-2">
        <MapPin className="h-4 w-4 shrink-0 text-purple-500" />
        <div>
          <span className="font-medium text-slate-700 dark:text-slate-200">{label}</span>
          {sublabel && <span className="ml-1 text-xs text-slate-400">{sublabel}</span>}
        </div>
      </div>
      <ArrowRight className="h-3.5 w-3.5 text-purple-400" />
    </Button>
  );
}
