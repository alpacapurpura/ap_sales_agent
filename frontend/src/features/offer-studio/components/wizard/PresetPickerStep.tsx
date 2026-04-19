"use client";

import { Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { cn } from "@/lib/utils";

import type {
  ExpertBusinessType,
  OfferTypePreset,
} from "@/features/offer-studio/api/offer-type-preset-catalog-api";

interface PresetPickerStepProps {
  /** Presets filtered by the tenant's business_types. Empty list = still
   *  loading or tenant hasn't declared any business_types. */
  presets: readonly OfferTypePreset[];
  onPick: (preset: OfferTypePreset) => void;
  /** When true, the UI shows the empty-state hint inviting the user to
   *  declare business_types in Brand Studio. The wizard itself does
   *  not navigate — it only prompts. */
  businessTypesDeclared: boolean;
  /** Echoes the tenant's declared types in the help caption so the user
   *  sees *why* they're being shown these specific presets. */
  businessTypesDeclaredList?: readonly ExpertBusinessType[];
}

/**
 * Step 1 of the preset-first wizard. Grid of cards, one per preset
 * filtered by the tenant's declared business_types. Each card shows the
 * icon, label_es (user vocabulary), description_es, and 2-3 examples.
 *
 * Why this replaces the legacy ArchetypeStep + FormatStep: the preset
 * is a composite (business_type × archetype × sections + flags + example
 * formats) — picking it commits all three axes at once, so the wizard
 * drops from 2 picker steps to 1. Archetype is never shown.
 */
export function PresetPickerStep({
  presets,
  onPick,
  businessTypesDeclared,
  businessTypesDeclaredList = [],
}: PresetPickerStepProps) {
  if (!businessTypesDeclared) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">¿Qué tipo de oferta vas a crear?</h3>
          <p className="text-sm text-muted-foreground">
            Primero declará a qué te dedicás desde Brand Studio → Identidad. Esto nos permite
            filtrarte los tipos de oferta que realmente usan negocios como el tuyo.
          </p>
        </div>
        <div className="flex items-start gap-3 rounded-md border border-dashed bg-muted/30 p-4 text-sm text-muted-foreground">
          <Info className="h-4 w-4 shrink-0 mt-0.5" aria-hidden />
          <p>
            Mientras tanto, podés ver todos los tipos de oferta disponibles — pero la experiencia se
            potencia muchísimo cuando declarás tu negocio primero.
          </p>
        </div>
        <PresetGrid presets={presets} onPick={onPick} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Qué tipo de oferta vas a crear?</h3>
        <p className="text-sm text-muted-foreground">
          Elegí la que más se parece a lo que tenés en mente. Los próximos pasos se adaptan según tu
          elección.
          {businessTypesDeclaredList.length > 0 && (
            <>
              {" "}
              Mostrando <strong>{presets.length}</strong> opciones ajustadas a tu perfil.
            </>
          )}
        </p>
      </div>
      <PresetGrid presets={presets} onPick={onPick} />
    </div>
  );
}

interface PresetGridProps {
  presets: readonly OfferTypePreset[];
  onPick: (preset: OfferTypePreset) => void;
}

function PresetGrid({ presets, onPick }: PresetGridProps) {
  if (presets.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
        Cargando opciones de oferta…
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {presets.map((preset) => {
        const Icon = resolveIconByName(preset.icon_name);
        return <PresetCard key={preset.preset_id} preset={preset} Icon={Icon} onPick={onPick} />;
      })}
    </div>
  );
}

interface PresetCardProps {
  preset: OfferTypePreset;
  Icon: ReturnType<typeof resolveIconByName>;
  onPick: (preset: OfferTypePreset) => void;
}

function PresetCard({ preset, Icon, onPick }: PresetCardProps) {
  const examples = preset.examples_es.slice(0, 3);
  const isLeadMagnet = preset.default_flags.includes("is_lead_magnet");
  const isHighTicket = preset.default_flags.includes("high_ticket");
  const isRecurring = preset.default_flags.includes("recurring_billing");

  return (
    <button
      type="button"
      onClick={() => onPick(preset)}
      className={cn(
        "text-left rounded-lg border bg-card p-4 transition",
        "hover:border-primary hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        "flex flex-col gap-3",
      )}
    >
      <div className="flex items-start gap-3">
        <div className="shrink-0 h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center">
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold">{preset.label_es}</span>
            {isLeadMagnet && (
              <Badge
                variant="outline"
                className="text-[10px] h-4 px-1.5 border-transparent bg-sky-100 text-sky-800"
              >
                Gratuito
              </Badge>
            )}
            {isHighTicket && (
              <Badge
                variant="outline"
                className="text-[10px] h-4 px-1.5 border-transparent bg-amber-100 text-amber-900"
              >
                Alto ticket
              </Badge>
            )}
            {isRecurring && (
              <Badge
                variant="outline"
                className="text-[10px] h-4 px-1.5 border-transparent bg-violet-100 text-violet-800"
              >
                Recurrente
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground line-clamp-3">{preset.description_es}</p>
        </div>
      </div>
      {examples.length > 0 && (
        <div className="flex flex-wrap gap-1 pl-13 sm:pl-[52px]">
          {examples.map((ex) => (
            <span
              key={ex}
              className="text-[11px] rounded bg-muted px-1.5 py-0.5 text-muted-foreground"
            >
              {ex}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}
