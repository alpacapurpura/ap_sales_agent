"use client";

import { Globe, FileText, MessageCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { OnboardingSource } from "../../hooks/useOnboardingWizard";

interface StepSourcePickerProps {
  selectedSources: OnboardingSource[];
  onToggle: (source: OnboardingSource) => void;
  onNext: () => void;
  onManual: () => void;
}

const SOURCE_OPTIONS: {
  id: OnboardingSource;
  icon: typeof Globe;
  title: string;
  description: string;
}[] = [
  {
    id: "website",
    icon: Globe,
    title: "Desde tu Website",
    description: "Extraemos tu identidad, historia, equipo y más escaneando tu sitio web.",
  },
  {
    id: "documents",
    icon: FileText,
    title: "Desde tus Documentos",
    description: "Sube PDFs, presentaciones o documentos con información de tu marca.",
  },
  {
    id: "interview",
    icon: MessageCircle,
    title: "Haciéndolo Juntos",
    description: "Una entrevista guiada por IA donde nos cuentas todo sobre tu marca.",
  },
];

export function StepSourcePicker({
  selectedSources,
  onToggle,
  onNext,
  onManual,
}: StepSourcePickerProps) {
  const hasSelection = selectedSources.length > 0;

  return (
    <div className="mx-auto max-w-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Construyamos tu marca
        </h1>
        <p className="mt-3 text-muted-foreground">
          ¿Qué tienes disponible? Selecciona todo lo que aplique.
        </p>
      </div>

      <div className="grid gap-4">
        {SOURCE_OPTIONS.map(({ id, icon: Icon, title, description }) => {
          const isSelected = selectedSources.includes(id);
          const isDisabled = id === "interview";
          return (
            <button
              key={id}
              type="button"
              onClick={() => !isDisabled && onToggle(id)}
              className={cn(
                "group relative flex items-start gap-4 rounded-xl border-2 p-5 text-left transition-all",
                isSelected && !isDisabled
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-primary/50 hover:bg-muted/40",
                isDisabled && "cursor-not-allowed opacity-50"
              )}
            >
              <div
                className={cn(
                  "flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg transition-colors",
                  isSelected ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
                )}
              >
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground">
                  {title}
                  {isDisabled && (
                    <span className="ml-2 text-xs font-normal text-muted-foreground">
                      Próximamente
                    </span>
                  )}
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">{description}</p>
              </div>
              {isSelected && !isDisabled && (
                <div className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>

      <div className="mt-8 flex items-center justify-between">
        <button
          type="button"
          onClick={onManual}
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Prefiero hacerlo manualmente
        </button>
        <Button onClick={onNext} disabled={!hasSelection} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
