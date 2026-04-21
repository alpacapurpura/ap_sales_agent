"use client";

import { Info, Plus } from "lucide-react";
import { useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { OfferValueLevel } from "@/features/offer-studio/types";
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
  /** Sprint 15.2 — invoked when the user clicks "Otra / A medida" inside a
   *  rung group. Captures the rung from the visual context so the wizard
   *  can keep the value_level even when there is no preset. */
  onPickCustom: (rung: OfferValueLevel) => void;
  /** When true, the UI shows the empty-state hint inviting the user to
   *  declare business_types in Brand Studio. The wizard itself does
   *  not navigate — it only prompts. */
  businessTypesDeclared: boolean;
  /** Echoes the tenant's declared types in the help caption so the user
   *  sees *why* they're being shown these specific presets. */
  businessTypesDeclaredList?: readonly ExpertBusinessType[];
}

/**
 * Step 1 of the preset-first wizard. Sprint 15.2 layout: presets grouped
 * by ladder rung with a colored header per group + an "Otra / A medida"
 * escape card at the end of each group.
 *
 * Each preset card shows the icon, label_es (user vocabulary),
 * description_es, examples, and an (i) tooltip with the catalog's
 * suitability_note_es. Each rung header carries an (i) tooltip explaining
 * the role of that ladder rung in plain language.
 */
export function PresetPickerStep({
  presets,
  onPick,
  onPickCustom,
  businessTypesDeclared,
  businessTypesDeclaredList = [],
}: PresetPickerStepProps) {
  if (!businessTypesDeclared) {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">¿Qué tipo de oferta vas a crear?</h3>
          <p className="text-sm text-muted-foreground">
            Primero declara a qué te dedicas desde Brand Studio → Identidad. Esto nos permite
            filtrarte los tipos de oferta que realmente usan negocios como el tuyo.
          </p>
        </div>
        <div className="flex items-start gap-3 rounded-md border border-dashed bg-muted/30 p-4 text-sm text-muted-foreground">
          <Info className="h-4 w-4 shrink-0 mt-0.5" aria-hidden />
          <p>
            Mientras tanto, puedes ver todos los tipos de oferta disponibles — pero la experiencia
            se potencia muchísimo cuando declaras tu negocio primero.
          </p>
        </div>
        <PresetGroupedGrid presets={presets} onPick={onPick} onPickCustom={onPickCustom} />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-lg font-semibold">¿Qué tipo de oferta vas a crear?</h3>
        <p className="text-sm text-muted-foreground">
          Las ofertas están agrupadas por el papel que cumplen en tu negocio.
          {businessTypesDeclaredList.length > 0 && (
            <>
              {" "}
              Mostrando <strong>{presets.length}</strong> opciones ajustadas a tu perfil.
            </>
          )}
        </p>
      </div>
      <PresetGroupedGrid presets={presets} onPick={onPick} onPickCustom={onPickCustom} />
    </div>
  );
}

// ── Rung metadata (visual / copy) ──────────────────────────────────────────

interface RungVisual {
  rung: OfferValueLevel;
  label: string;
  subtitle: string;
  priceHint: string | null;
  tooltipBody: string;
  bg: string;
  border: string;
  iconBg: string;
  iconColor: string;
  cardHover: string;
  badge: string;
  iconBox: string;
}

const RUNG_VISUALS: readonly RungVisual[] = [
  {
    rung: OfferValueLevel.LEAD_MAGNET,
    label: "Algo gratis para captar gente",
    subtitle: "Para que te conozcan y dejen su contacto. Sin pagos ni compromiso.",
    priceHint: "Gratis",
    tooltipBody:
      "Para cuando todavía no tienes relación con tu cliente y quieres que dejen su contacto a cambio de algo de valor. La conversión a oferta paga depende de qué tan bien hagas el seguimiento por WhatsApp/email.",
    bg: "bg-gradient-to-br from-emerald-50 to-emerald-100 dark:from-emerald-950/40 dark:to-emerald-900/30",
    border: "border-emerald-200 dark:border-emerald-800/60",
    iconBg: "bg-white dark:bg-emerald-950",
    iconColor: "text-emerald-700 dark:text-emerald-300",
    cardHover: "hover:border-emerald-400 dark:hover:border-emerald-600",
    badge: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-200",
    iconBox: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/70 dark:text-emerald-300",
  },
  {
    rung: OfferValueLevel.ACTIVACION,
    label: "Primera compra: bajo precio, sin riesgo",
    subtitle: "El primer paso pago. Para que prueben qué haces sin gastar mucho.",
    priceHint: "USD 10–200",
    tooltipBody:
      "El primer cobro real. Bajo ticket para que el cliente pruebe sin pensarlo dos veces. Función: convertir lead en cliente reduciendo fricción psicológica.",
    bg: "bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950/40 dark:to-blue-900/30",
    border: "border-blue-200 dark:border-blue-800/60",
    iconBg: "bg-white dark:bg-blue-950",
    iconColor: "text-blue-700 dark:text-blue-300",
    cardHover: "hover:border-blue-400 dark:hover:border-blue-600",
    badge: "bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-200",
    iconBox: "bg-blue-50 text-blue-700 dark:bg-blue-950/70 dark:text-blue-300",
  },
  {
    rung: OfferValueLevel.TRANSFORMACION,
    label: "Mi oferta principal",
    subtitle: "Tu producto estrella. El grueso de tu facturación.",
    priceHint: "USD 200–2.000",
    tooltipBody:
      "Tu producto core. Donde está el grueso de tu facturación y la transformación real del cliente. Justifica todo el funnel previo. En Latam: ofrece 3-6 cuotas sin interés con Mercado Pago.",
    bg: "bg-gradient-to-br from-amber-50 to-amber-100 dark:from-amber-950/40 dark:to-amber-900/30",
    border: "border-amber-200 dark:border-amber-800/60",
    iconBg: "bg-white dark:bg-amber-950",
    iconColor: "text-amber-700 dark:text-amber-300",
    cardHover: "hover:border-amber-400 dark:hover:border-amber-600",
    badge: "bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200",
    iconBox: "bg-amber-50 text-amber-700 dark:bg-amber-950/70 dark:text-amber-300",
  },
  {
    rung: OfferValueLevel.MAXIMIZACION,
    label: "Premium / alto ticket",
    subtitle: "Para clientes que ya te conocen y quieren más profundidad o exclusividad.",
    priceHint: "USD 2.000–10.000+",
    tooltipBody:
      "Para clientes que ya compraron tu oferta principal y quieren más profundidad o exclusividad. La conversión es alta porque vienen calientes. Aplicación con entrevista filtra y eleva exclusividad.",
    bg: "bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950/40 dark:to-purple-900/30",
    border: "border-purple-200 dark:border-purple-800/60",
    iconBg: "bg-white dark:bg-purple-950",
    iconColor: "text-purple-700 dark:text-purple-300",
    cardHover: "hover:border-purple-400 dark:hover:border-purple-600",
    badge: "bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-200",
    iconBox: "bg-purple-50 text-purple-700 dark:bg-purple-950/70 dark:text-purple-300",
  },
  {
    rung: OfferValueLevel.CORPORATIVO,
    label: "Para empresas (B2B)",
    subtitle: "Cuando vendes a empresas, no a personas individuales.",
    priceHint: "USD 10.000+",
    tooltipBody:
      "Cuando vendes a empresas formalmente: convenios, capacitación in-company, integraciones custom, MSA. Decisor suele ser RR.HH., Procurement o C-level. Sales cycle más largo.",
    bg: "bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/60 dark:to-slate-800/60",
    border: "border-slate-200 dark:border-slate-700",
    iconBg: "bg-white dark:bg-slate-900",
    iconColor: "text-slate-700 dark:text-slate-300",
    cardHover: "hover:border-slate-400 dark:hover:border-slate-600",
    badge: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200",
    iconBox: "bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-300",
  },
];

// ── Grouped grid ──────────────────────────────────────────────────────────

interface PresetGroupedGridProps {
  presets: readonly OfferTypePreset[];
  onPick: (preset: OfferTypePreset) => void;
  onPickCustom: (rung: OfferValueLevel) => void;
}

function PresetGroupedGrid({ presets, onPick, onPickCustom }: PresetGroupedGridProps) {
  const grouped = useMemo(() => {
    const map = new Map<OfferValueLevel, OfferTypePreset[]>();
    for (const preset of presets) {
      const list = map.get(preset.typical_value_level) ?? [];
      list.push(preset);
      map.set(preset.typical_value_level, list);
    }
    return map;
  }, [presets]);

  if (presets.length === 0) {
    return (
      <div className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
        Cargando opciones de oferta…
      </div>
    );
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-7">
        {RUNG_VISUALS.map((visual) => {
          const groupPresets = grouped.get(visual.rung) ?? [];
          // Render every rung — even empty ones get the "Otra / A medida"
          // card so the user always has an escape hatch on every ladder rung,
          // including those without business-type-specific presets.
          return (
            <RungGroup
              key={visual.rung}
              visual={visual}
              presets={groupPresets}
              onPick={onPick}
              onPickCustom={onPickCustom}
            />
          );
        })}
      </div>
    </TooltipProvider>
  );
}

// ── Rung group ────────────────────────────────────────────────────────────

interface RungGroupProps {
  visual: RungVisual;
  presets: readonly OfferTypePreset[];
  onPick: (preset: OfferTypePreset) => void;
  onPickCustom: (rung: OfferValueLevel) => void;
}

function RungGroup({ visual, presets, onPick, onPickCustom }: RungGroupProps) {
  return (
    <div>
      {/* Rung header */}
      <div className={cn("rounded-xl border p-4 mb-3", visual.bg, visual.border)}>
        <div className="flex items-start gap-3">
          <RungIcon visual={visual} Icon={resolveIconByName(RUNG_HEADER_ICON_NAME[visual.rung])} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-0.5">
              <h4 className="font-bold text-base">{visual.label}</h4>
              {visual.priceHint && (
                <span className={cn("text-[11px] px-1.5 py-0.5 rounded font-medium", visual.badge)}>
                  {visual.priceHint}
                </span>
              )}
              <span className="text-[11px] px-1.5 py-0.5 rounded bg-background/70 text-muted-foreground font-medium border border-background/40">
                {presets.length} {presets.length === 1 ? "opción" : "opciones"}
              </span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="ml-auto p-0.5 rounded hover:bg-background/50 text-muted-foreground hover:text-foreground transition"
                    aria-label="Más información sobre este nivel"
                  >
                    <Info className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
                  {visual.tooltipBody}
                </TooltipContent>
              </Tooltip>
            </div>
            <p className="text-xs text-muted-foreground">{visual.subtitle}</p>
          </div>
        </div>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 ml-2">
        {presets.map((preset) => (
          <PresetCard
            key={preset.preset_id}
            preset={preset}
            onPick={onPick}
            iconBoxClass={visual.iconBox}
            hoverClass={visual.cardHover}
            Icon={resolveIconByName(preset.icon_name)}
          />
        ))}
        <CustomCard rung={visual.rung} onPickCustom={onPickCustom} hoverClass={visual.cardHover} />
      </div>
    </div>
  );
}

// Per-rung header icon name. Module scope so the lint rule
// react-hooks/static-components is satisfied (no component creation
// inside render).
const RUNG_HEADER_ICON_NAME: Readonly<Record<OfferValueLevel, string>> = {
  [OfferValueLevel.LEAD_MAGNET]: "Gift",
  [OfferValueLevel.ACTIVACION]: "Rocket",
  [OfferValueLevel.TRANSFORMACION]: "Star",
  [OfferValueLevel.MAXIMIZACION]: "Gem",
  [OfferValueLevel.CORPORATIVO]: "Building2",
};

interface RungIconProps {
  visual: RungVisual;
  Icon: ReturnType<typeof resolveIconByName>;
}

function RungIcon({ visual, Icon }: RungIconProps) {
  return (
    <div
      className={cn(
        "shrink-0 h-12 w-12 rounded-xl flex items-center justify-center shadow-sm",
        visual.iconBg,
        visual.iconColor,
      )}
    >
      <Icon className="h-6 w-6" />
    </div>
  );
}

// ── Preset card ───────────────────────────────────────────────────────────

interface PresetCardProps {
  preset: OfferTypePreset;
  onPick: (preset: OfferTypePreset) => void;
  iconBoxClass: string;
  hoverClass: string;
  Icon: ReturnType<typeof resolveIconByName>;
}

function PresetCard({ preset, onPick, iconBoxClass, hoverClass, Icon }: PresetCardProps) {
  const examples = preset.examples_es.slice(0, 3);
  const isHighTicket = preset.default_flags.includes("high_ticket");
  const isRecurring = preset.default_flags.includes("recurring_billing");

  const handleClick = () => onPick(preset);

  return (
    <div
      className={cn(
        "relative rounded-xl border bg-card p-4 transition group",
        "hover:shadow-md hover:-translate-y-0.5",
        hoverClass,
      )}
    >
      <button
        type="button"
        onClick={handleClick}
        className="text-left w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg"
      >
        <div
          className={cn(
            "h-10 w-10 rounded-lg flex items-center justify-center mb-2.5",
            iconBoxClass,
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap mb-1">
          <h5 className="font-semibold text-sm leading-snug">{preset.label_es}</h5>
          {isHighTicket && (
            <Badge
              variant="outline"
              className="text-[10px] h-4 px-1.5 border-transparent bg-amber-100 text-amber-900 dark:bg-amber-900/60 dark:text-amber-200"
            >
              Alto ticket
            </Badge>
          )}
          {isRecurring && (
            <Badge
              variant="outline"
              className="text-[10px] h-4 px-1.5 border-transparent bg-violet-100 text-violet-800 dark:bg-violet-900/60 dark:text-violet-200"
            >
              Recurrente
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 mb-2.5">
          {preset.description_es}
        </p>
        {examples.length > 0 && (
          <div className="border-t border-border pt-2">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground/70 font-semibold mb-0.5">
              Ejemplos
            </p>
            <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
              {examples.join(" · ")}
            </p>
          </div>
        )}
      </button>

      {/* Tooltip (i) anchored top-right — Latam-specific suitability hint */}
      {preset.suitability_note_es && (
        <div className="absolute top-2.5 right-2.5">
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className="p-0.5 rounded text-muted-foreground/50 hover:text-foreground hover:bg-zinc-100 transition"
                aria-label="Tip Latam para este tipo de oferta"
                onClick={(e) => e.stopPropagation()}
              >
                <Info className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-xs text-xs leading-relaxed">
              {preset.suitability_note_es}
            </TooltipContent>
          </Tooltip>
        </div>
      )}
    </div>
  );
}

// ── Custom ("Otra / A medida") card ───────────────────────────────────────

interface CustomCardProps {
  rung: OfferValueLevel;
  onPickCustom: (rung: OfferValueLevel) => void;
  hoverClass: string;
}

function CustomCard({ rung, onPickCustom, hoverClass }: CustomCardProps) {
  const handleClick = () => onPickCustom(rung);

  return (
    <button
      type="button"
      onClick={handleClick}
      className={cn(
        "text-left rounded-xl border-2 border-dashed bg-card/50 p-4 transition",
        "hover:bg-card hover:shadow-md hover:-translate-y-0.5",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
        "flex flex-col items-start justify-center min-h-[140px]",
        hoverClass,
      )}
      aria-label="Crear oferta a medida en este nivel"
    >
      <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center mb-2.5">
        <Plus className="h-5 w-5 text-muted-foreground" />
      </div>
      <h5 className="font-semibold text-sm mb-1">Otra / A medida</h5>
      <p className="text-xs text-muted-foreground leading-relaxed">
        No encontré el tipo exacto. Quiero configurarla yo.
      </p>
    </button>
  );
}
