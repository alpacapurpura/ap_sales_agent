"use client";

import { OfferValueLevel } from "@/lib/api/offer";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Plus, Rocket, Lightbulb, TrendingUp, Gem, Building } from "lucide-react";

interface EmptyLevelSlotProps {
  level: OfferValueLevel;
  onCreate: (level: OfferValueLevel) => void;
}

const LEVEL_CONFIG = {
  [OfferValueLevel.N0]: {
    label: "Adquisición (N0)",
    description: "Crea un Lead Magnet para atraer tráfico.",
    icon: Lightbulb
  },
  [OfferValueLevel.N1]: {
    label: "Activación (N1)",
    description: "Convierte leads en clientes con bajo riesgo.",
    icon: Rocket
  },
  [OfferValueLevel.N2]: {
    label: "Escalabilidad (N2)",
    description: "Tu oferta principal (Core Offer) escalable.",
    icon: TrendingUp
  },
  [OfferValueLevel.N3]: {
    label: "Profit Maximizer (N3)",
    description: "Aumenta el LTV con servicios premium.",
    icon: Gem
  },
  [OfferValueLevel.N4]: {
    label: "Delegación (N4)",
    description: "Servicios DFY o Retainers de alto valor.",
    icon: Building
  },
  [OfferValueLevel.N5]: {
    label: "Legado (N5)",
    description: "Masterminds y experiencias exclusivas.",
    icon: Building
  },
  [OfferValueLevel.N6]: {
    label: "Corporativo (N6)",
    description: "Ventas B2B y grandes contratos.",
    icon: Building
  }
};

export function EmptyLevelSlot({ level, onCreate }: EmptyLevelSlotProps) {
  const config = LEVEL_CONFIG[level] || LEVEL_CONFIG[OfferValueLevel.N0];
  const Icon = config.icon;

  return (
    <div 
      className={cn(
        "group h-[120px] w-full border-2 border-dashed border-muted-foreground/25 rounded-lg",
        "bg-muted/5 hover:bg-muted/10 transition-colors cursor-pointer",
        "flex flex-col items-center justify-center text-center p-4 gap-2"
      )}
      onClick={() => onCreate(level)}
    >
      <div className="flex flex-col items-center gap-1">
        <div className="flex items-center gap-2 text-muted-foreground group-hover:text-foreground transition-colors">
          <Icon className="h-5 w-5 opacity-50 group-hover:opacity-100" />
          <span className="font-semibold text-sm">{config.label} Vacío</span>
        </div>
        <p className="text-xs text-muted-foreground max-w-[250px]">
          {config.description}
        </p>
      </div>
      
      <Button variant="ghost" size="sm" className="h-7 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
        <Plus className="mr-1 h-3 w-3" />
        Crear Oferta {level}
      </Button>
    </div>
  );
}
