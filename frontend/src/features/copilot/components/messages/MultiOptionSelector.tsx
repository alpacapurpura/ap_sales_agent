"use client";

import { useState } from "react";
import { Check } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { reportCopilotEvent } from "../../api/copilot-api";

interface MultiOptionSelectorProps {
  options: Array<{ id: string; title: string; content: string }>;
  fieldId: string;
}

type SelectorStatus = "pending" | "applied";

export function MultiOptionSelector({ options, fieldId }: MultiOptionSelectorProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState<SelectorStatus>("pending");
  const { getToken } = useAuth();

  const handleApply = () => {
    const selected = options.find((o) => o.id === selectedId);
    if (!selected) return;

    window.dispatchEvent(
      new CustomEvent("copilot:field-update", {
        detail: { fieldId, newValue: selected.content },
      }),
    );
    setStatus("applied");
    getToken().then((token) => {
      if (token) {
        reportCopilotEvent(
          "option_selected",
          {
            field_id: fieldId,
            selected_option_id: selected.id,
            selected_title: selected.title,
          },
          token,
        );
      }
    });
  };

  return (
    <div className="my-1 space-y-2">
      {options.map((opt) => {
        const isSelected = selectedId === opt.id;
        return (
          <Card
            key={opt.id}
            onClick={() => status === "pending" && setSelectedId(opt.id)}
            className={[
              "cursor-pointer px-3 py-2.5 text-sm transition-all",
              isSelected
                ? "border-purple-400 bg-purple-50/50 ring-1 ring-purple-400 dark:border-purple-500 dark:bg-purple-900/20"
                : "hover:border-slate-300 dark:hover:border-slate-600",
              status === "applied" && !isSelected ? "opacity-40" : "",
              status === "applied" && isSelected
                ? "border-green-300 bg-green-50/50 dark:border-green-700 dark:bg-green-900/20"
                : "",
            ].join(" ")}
          >
            <div className="font-medium text-slate-700 dark:text-slate-200">{opt.title}</div>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{opt.content}</p>
          </Card>
        );
      })}

      {status === "pending" && selectedId && (
        <Button
          size="sm"
          onClick={handleApply}
          className="h-7 bg-purple-600 px-3 text-xs text-white hover:bg-purple-700"
        >
          <Check className="mr-1 h-3 w-3" />
          Aplicar
        </Button>
      )}

      {status === "applied" && <span className="text-xs text-green-600">Aplicado</span>}
    </div>
  );
}
