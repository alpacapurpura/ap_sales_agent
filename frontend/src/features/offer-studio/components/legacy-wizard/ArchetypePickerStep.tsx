"use client";

import { CalendarDays, Layers, Package, RefreshCw, Wrench } from "lucide-react";

import { OfferArchetype } from "@/features/offer-studio/types";
import { cn } from "@/lib/utils";

import type { LucideIcon } from "lucide-react";

interface ArchetypePickerStepProps {
  /** Echoed back when the user picks. The wizard then advances to name+price. */
  onPick: (archetype: OfferArchetype) => void;
  /** Optional rung label shown in the step subtitle so the user knows the
   *  archetype pick still respects the ladder rung they came from. */
  rungLabel?: string;
}

interface ArchetypeOption {
  archetype: OfferArchetype;
  icon: LucideIcon;
  iconClass: string;
  label: string;
  description: string;
  examples: string;
}

/**
 * Sprint 15.2 — sub-step shown when the user picks "Otra / A medida"
 * inside any rung group. Asks the underlying archetype in plain language
 * (no "PROGRAMA" / "EXPERIENCIA" jargon) so the editor + downstream
 * (sales-agent grounding, landing generator) still get a valid archetype
 * tag without a preset_id.
 *
 * Architecture note: the offer is created with ``preset_id=None`` and the
 * picked archetype. The backend's ``OfferService.create_offer`` already
 * supports this legacy path; ``ARCHETYPE_CATALOG[archetype].sections``
 * provides the section fallback when no preset is present.
 */
export function ArchetypePickerStep({ onPick, rungLabel }: ArchetypePickerStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Cómo funciona tu oferta?</h3>
        <p className="text-sm text-muted-foreground">
          Como vamos a configurarla a medida, necesitamos saber su forma básica para armarte el
          editor correcto.
          {rungLabel && (
            <>
              {" "}
              Sigue siendo del nivel <strong>{rungLabel}</strong>.
            </>
          )}
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {ARCHETYPE_OPTIONS.map((option) => (
          <ArchetypeCard key={option.archetype} option={option} onPick={onPick} />
        ))}
      </div>
    </div>
  );
}

const ARCHETYPE_OPTIONS: readonly ArchetypeOption[] = [
  {
    archetype: OfferArchetype.PRODUCTO,
    icon: Package,
    iconClass: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
    label: "Algo que entrego una vez",
    description: "Un producto o material que se entrega y la transacción queda cerrada.",
    examples: "Ebook, plantilla, producto físico, kit, gift card",
  },
  {
    archetype: OfferArchetype.SERVICIO,
    icon: Wrench,
    iconClass: "bg-blue-50 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300",
    label: "Trabajo 1:1 con o para alguien",
    description:
      "Servicio puntual o por proyecto. Tú ejecutas o acompañas directamente al cliente.",
    examples: "Consulta, sesión, asesoría, servicio profesional, dictamen",
  },
  {
    archetype: OfferArchetype.PROGRAMA,
    icon: Layers,
    iconClass: "bg-amber-50 text-amber-700 dark:bg-amber-950/70 dark:text-amber-300",
    label: "Un proceso largo con varios pasos",
    description:
      "Recorrido estructurado con materiales, sesiones y seguimiento. Tiene inicio y fin.",
    examples: "Bootcamp, programa de transformación, paquete de sesiones, cohorte",
  },
  {
    archetype: OfferArchetype.MEMBRESIA,
    icon: RefreshCw,
    iconClass: "bg-violet-50 text-violet-700 dark:bg-violet-950/70 dark:text-violet-300",
    label: "Acceso continuo con suscripción",
    description: "Cobro recurrente mensual o anual mientras el cliente sigue activo.",
    examples: "Membresía, plan mensual, mastermind, retainer, club, comunidad paga",
  },
  {
    archetype: OfferArchetype.EXPERIENCIA,
    icon: CalendarDays,
    iconClass: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300",
    label: "Un evento con fecha fija",
    description: "Encuentro presencial o virtual programado para una o varias fechas concretas.",
    examples: "Workshop, retiro, taller, summit, masterclass, conferencia",
  },
];

interface ArchetypeCardProps {
  option: ArchetypeOption;
  onPick: (archetype: OfferArchetype) => void;
}

function ArchetypeCard({ option, onPick }: ArchetypeCardProps) {
  const Icon = option.icon;
  const handleClick = () => onPick(option.archetype);

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "text-left rounded-xl border bg-card p-4 transition",
        "hover:border-primary hover:shadow-md hover:-translate-y-0.5",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        "flex items-start gap-3",
      )}
    >
      <div
        className={cn(
          "shrink-0 h-11 w-11 rounded-lg flex items-center justify-center",
          option.iconClass,
        )}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0 space-y-1">
        <h5 className="font-semibold text-sm">{option.label}</h5>
        <p className="text-xs text-muted-foreground leading-relaxed">{option.description}</p>
        <p className="text-[11px] text-muted-foreground/80 italic mt-1.5">Ej: {option.examples}</p>
      </div>
    </button>
  );
}
