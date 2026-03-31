"use client";

import { OfferValueLevel } from "@/features/offer-studio/types";
import { LadderGap } from "@/features/offer-studio/utils/ladder-completeness";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Plus, Lightbulb, Rocket, TrendingUp, Gem, Building } from "lucide-react";

interface EmptyLevelSlotProps {
  level: OfferValueLevel;
  onCreate: (level: OfferValueLevel) => void;
  gap?: LadderGap;
  onCreateWithPreset?: (presetId: string) => void;
}

const LEVEL_CONFIG = {
  [OfferValueLevel.LEAD_MAGNET]: {
    label: "Lead Magnet",
    description: "Crea un recurso gratuito para atraer prospectos.",
    icon: Lightbulb
  },
  [OfferValueLevel.ACTIVACION]: {
    label: "Activacion",
    description: "Convierte leads en clientes con bajo riesgo.",
    icon: Rocket
  },
  [OfferValueLevel.TRANSFORMACION]: {
    label: "Transformacion",
    description: "Tu oferta principal (Core Offer) escalable.",
    icon: TrendingUp
  },
  [OfferValueLevel.MAXIMIZACION]: {
    label: "Maximizacion",
    description: "Aumenta el LTV con servicios premium.",
    icon: Gem
  },
  [OfferValueLevel.CORPORATIVO]: {
    label: "Corporativo",
    description: "Ventas B2B y grandes contratos.",
    icon: Building
  }
};

const PRIORITY_STYLES = {
  critico: "border-red-500/40 bg-red-500/5",
  recomendado: "border-amber-500/40 bg-amber-500/5",
  opcional: "border-muted-foreground/25 bg-muted/5",
};

const PRIORITY_BADGE = {
  critico: { label: "Critico", className: "bg-red-500/10 text-red-600 border-red-500/20" },
  recomendado: { label: "Recomendado", className: "bg-amber-500/10 text-amber-600 border-amber-500/20" },
  opcional: { label: "Opcional", className: "bg-muted text-muted-foreground border-transparent" },
};

// Simple preset ID to label map for suggested chips
const PRESET_LABELS: Record<string, string> = {
  producto_ebook: "Ebook / Guia",
  producto_curso: "Curso Grabado",
  producto_kit: "Kit / Toolkit",
  programa_masterclass: "Masterclass",
  programa_bootcamp: "Bootcamp",
  programa_certificacion: "Certificacion",
  programa_evergreen: "Curso Evergreen",
  servicio_mentoria: "Mentoria 1:1",
  servicio_dfy: "Servicio DFY",
  servicio_vip_day: "VIP Day",
  servicio_retainer: "Retainer",
  membresia_comunidad: "Comunidad",
  membresia_biblioteca: "Biblioteca",
  membresia_mastermind: "Mastermind",
  membresia_inner_circle: "Inner Circle",
  experiencia_retiro: "Retiro",
  experiencia_evento: "Evento",
  experiencia_taller: "Taller",
  experiencia_summit: "Summit Virtual",
};

export function EmptyLevelSlot({ level, onCreate, gap, onCreateWithPreset }: EmptyLevelSlotProps) {
  const config = LEVEL_CONFIG[level] || LEVEL_CONFIG[OfferValueLevel.LEAD_MAGNET];
  const Icon = config.icon;
  const priority = gap?.priority || "opcional";
  const priorityStyle = PRIORITY_STYLES[priority];
  const badge = PRIORITY_BADGE[priority];

  return (
    <div
      className={cn(
        "group w-full border-2 border-dashed rounded-lg",
        "hover:bg-muted/10 transition-colors cursor-pointer",
        "flex flex-col items-center justify-center text-center p-4 gap-2",
        gap ? "min-h-[140px]" : "h-[120px]",
        priorityStyle
      )}
      onClick={() => onCreate(level)}
    >
      <div className="flex flex-col items-center gap-1">
        <div className="flex items-center gap-2 text-muted-foreground group-hover:text-foreground transition-colors">
          <Icon className="h-5 w-5 opacity-50 group-hover:opacity-100" />
          <span className="font-semibold text-sm">{config.label}</span>
          {gap && (
            <Badge variant="outline" className={cn("text-[10px] h-4 px-1.5", badge.className)}>
              {badge.label}
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground max-w-[280px]">
          {gap ? gap.description : config.description}
        </p>
      </div>

      {/* Suggested preset chips */}
      {gap && gap.suggestedPresetIds.length > 0 && onCreateWithPreset && (
        <div className="flex flex-wrap justify-center gap-1 mt-1">
          {gap.suggestedPresetIds.slice(0, 3).map(presetId => (
            <button
              key={presetId}
              onClick={(e) => {
                e.stopPropagation();
                onCreateWithPreset(presetId);
              }}
              className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            >
              {PRESET_LABELS[presetId] || presetId}
            </button>
          ))}
        </div>
      )}

      <Button variant="ghost" size="sm" className="h-7 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
        <Plus className="mr-1 h-3 w-3" />
        Crear Oferta
      </Button>
    </div>
  );
}
