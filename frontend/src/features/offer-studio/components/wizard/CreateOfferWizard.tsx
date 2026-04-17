"use client";

import { ArrowLeft, ArrowRight, Loader2, Rocket, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";
import { useArchetypeCatalog } from "@/features/offer-studio/hooks/use-archetype-catalog";
import {
  useValueLevelCatalog,
  useValueLevelMetadata,
} from "@/features/offer-studio/hooks/use-value-level-catalog";
import { useFormatCatalog } from "@/features/offer-studio/hooks/use-format-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { OfferArchetype, OfferStatus, OfferValueLevel } from "@/features/offer-studio/types";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { cn } from "@/lib/utils";

import type { FormatMetadata } from "@/features/offer-studio/api/format-catalog-api";
import type { OfferDeliveryModel } from "@/features/offer-studio/types";

interface CreateOfferWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateOffer: (data: WizardResult) => Promise<void>;
  onCreateWithIA?: (data: WizardResult) => Promise<void>;
  creating?: boolean;
}

export interface WizardResult {
  archetype: OfferArchetype;
  format_hint?: string;
  name: string;
  is_lead_magnet: boolean;
  has_editions?: boolean;
  headline_promise?: string;
  status: OfferStatus;
  delivery_model?: OfferDeliveryModel;
  value_level: OfferValueLevel;
  specific_details?: Record<string, unknown>;
}

type Step = 1 | 2 | 3 | 4 | 5 | 6;

// Stable reference so React Query loading state doesn't create a new array
// each render and thrash the memoized children.
const EMPTY_LIST: readonly never[] = [];

export function CreateOfferWizard({
  open,
  onOpenChange,
  onCreateOffer,
  onCreateWithIA,
  creating = false,
}: CreateOfferWizardProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const { data: archetypeCatalog } = useArchetypeCatalog();
  const { data: valueLevelCatalog } = useValueLevelCatalog();
  const { settings } = useBrandSettings();
  const brandBusinessTypes = settings?.identity?.business_types ?? [];

  const [step, setStep] = useState<Step>(1);
  const [archetype, setArchetype] = useState<OfferArchetype | null>(null);
  const [valueLevel, setValueLevel] = useState<OfferValueLevel | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<FormatMetadata | null>(null);
  const [customFormatHint, setCustomFormatHint] = useState("");
  const [offerName, setOfferName] = useState("");
  const [price, setPrice] = useState<string>("");
  const [hasEditions, setHasEditions] = useState<boolean>(true);
  const [headlinePromise, setHeadlinePromise] = useState("");

  const valueLevelMeta = useValueLevelMetadata(valueLevel ?? undefined);
  const archetypeCaps = archetypeCatalog?.archetypes?.find((a) => a.archetype === archetype);
  const showsEditionsStep = archetypeCaps?.supports_editions === true;
  const isLeadMagnet = valueLevel === OfferValueLevel.LEAD_MAGNET;

  const totalSteps: Step = showsEditionsStep ? 6 : 5;
  const progressPercent = (step / totalSteps) * 100;

  // Format catalog filtered by archetype + tenant's business types. When
  // the brand hasn't declared business types yet we fall back to the full
  // archetype list.
  const { data: formatCatalog } = useFormatCatalog({
    archetype: archetype ?? undefined,
    businessTypes: brandBusinessTypes.length > 0 ? brandBusinessTypes : undefined,
  });
  const formatOptions: readonly FormatMetadata[] = formatCatalog?.formats ?? [];

  const resetWizard = () => {
    setStep(1);
    setArchetype(null);
    setValueLevel(null);
    setSelectedFormat(null);
    setCustomFormatHint("");
    setOfferName("");
    setPrice("");
    setHasEditions(true);
    setHeadlinePromise("");
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) resetWizard();
    onOpenChange(next);
  };

  const handlePickArchetype = (pick: OfferArchetype) => {
    setArchetype(pick);
    setStep(2);
  };

  const handlePickValueLevel = (pick: OfferValueLevel) => {
    setValueLevel(pick);
    // Paid offers pre-fill the price placeholder from the catalog; lead magnets
    // force the price to "0" in the name+price step render below.
    setStep(3);
  };

  const handlePickFormat = (format: FormatMetadata) => {
    setSelectedFormat(format);
    setCustomFormatHint("");
    // Pre-fill the offer name with the format label so the user sees a
    // sensible default; they can still edit it freely in step 4.
    if (!offerName) setOfferName(`Mi ${format.label_es}`);
    setStep(4);
  };

  const handleSkipFormat = () => {
    setSelectedFormat(null);
    setStep(4);
  };

  const handleSubmitCustomFormat = () => {
    if (!customFormatHint.trim()) return;
    if (!offerName) setOfferName(`Mi ${customFormatHint.trim()}`);
    setStep(4);
  };

  const buildResult = (): WizardResult | null => {
    if (!archetype || !valueLevel || !offerName.trim()) return null;
    return {
      archetype,
      format_hint: selectedFormat?.format_hint || customFormatHint.trim() || undefined,
      name: offerName.trim(),
      is_lead_magnet: isLeadMagnet,
      has_editions: showsEditionsStep ? hasEditions : undefined,
      headline_promise: headlinePromise.trim() || undefined,
      status: OfferStatus.DRAFT,
      delivery_model: selectedFormat?.delivery_model as OfferDeliveryModel | undefined,
      value_level: valueLevel,
      specific_details: selectedFormat?.specific_details_defaults,
    };
  };

  const handleCreate = async () => {
    const result = buildResult();
    if (!result) return;
    await onCreateOffer(result);
  };

  const handleCreateWithIA = async () => {
    if (!onCreateWithIA) return;
    const result = buildResult();
    if (!result) return;
    await onCreateWithIA(result);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Crear oferta nueva</DialogTitle>
          <DialogDescription>
            Paso {step} de {totalSteps}
          </DialogDescription>
          <div className="h-1 w-full bg-muted rounded-full mt-2">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </DialogHeader>

        <div className="py-4">
          {step === 1 && (
            <ArchetypeStep
              onPick={handlePickArchetype}
              archetypes={archetypeCatalog?.archetypes ?? EMPTY_LIST}
            />
          )}
          {step === 2 && archetype && (
            <ValueLevelStep
              onPick={handlePickValueLevel}
              valueLevels={valueLevelCatalog?.value_levels ?? EMPTY_LIST}
            />
          )}
          {step === 3 && (
            <FormatStep
              formats={formatOptions}
              onPick={handlePickFormat}
              onSkip={handleSkipFormat}
              onCustom={handleSubmitCustomFormat}
              customValue={customFormatHint}
              onCustomChange={setCustomFormatHint}
              usingBrandFilter={brandBusinessTypes.length > 0}
            />
          )}
          {step === 4 && (
            <NamePriceStep
              isLeadMagnet={isLeadMagnet}
              name={offerName}
              onNameChange={setOfferName}
              price={price}
              onPriceChange={setPrice}
              tenantCurrency={tenantCurrency}
              valueLevelLabel={valueLevelMeta?.label_es ?? ""}
              priceMinUsd={valueLevelMeta?.typical_price_min_usd ?? null}
              priceMaxUsd={valueLevelMeta?.typical_price_max_usd ?? null}
            />
          )}
          {step === 5 && showsEditionsStep && (
            <EditionsStep
              title={archetypeCaps?.editions_wizard_copy?.title ?? ""}
              description={archetypeCaps?.editions_wizard_copy?.description ?? ""}
              yesLabel={archetypeCaps?.editions_wizard_copy?.yes_label ?? "Sí"}
              noLabel={archetypeCaps?.editions_wizard_copy?.no_label ?? "No"}
              value={hasEditions}
              onChange={setHasEditions}
            />
          )}
          {step === (showsEditionsStep ? 6 : 5) && (
            <PromiseStep value={headlinePromise} onChange={setHeadlinePromise} />
          )}
        </div>

        <DialogFooter className="flex-col-reverse sm:flex-row gap-2">
          {step > 1 && (
            <Button
              variant="ghost"
              onClick={() => setStep((s) => (s > 1 ? ((s - 1) as Step) : s))}
              disabled={creating}
            >
              <ArrowLeft className="mr-2 h-4 w-4" /> Atrás
            </Button>
          )}

          {/* Middle steps have their own CTAs (pick-card, skip, submit custom) */}
          {step === 3 && (
            <div className="flex gap-2 sm:ml-auto">
              <Button variant="ghost" onClick={handleSkipFormat} disabled={creating}>
                Saltar este paso
              </Button>
            </div>
          )}

          {(step === 4 || step === 5) && (
            <Button
              className="sm:ml-auto"
              onClick={() => setStep((s) => ((s + 1) as Step))}
              disabled={creating || (step === 4 && !offerName.trim())}
            >
              Siguiente <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}

          {step === totalSteps && (
            <div className="flex gap-2 sm:ml-auto">
              {onCreateWithIA && (
                <Button
                  variant="outline"
                  onClick={handleCreateWithIA}
                  disabled={creating || !offerName.trim() || !archetype || !valueLevel}
                >
                  {creating ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Crear con IA
                </Button>
              )}
              <Button
                onClick={handleCreate}
                disabled={creating || !offerName.trim() || !archetype || !valueLevel}
              >
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Rocket className="mr-2 h-4 w-4" />
                )}
                Crear oferta
              </Button>
            </div>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── STEP 1: ARCHETYPE ────────────────────────────────────────────────────────

interface ArchetypeStepProps {
  onPick: (archetype: OfferArchetype) => void;
  archetypes: readonly {
    archetype: string;
    label_es: string;
    subtitle_es: string;
    icon_name: string;
    examples_es: readonly string[];
  }[];
}

function ArchetypeStep({ onPick, archetypes }: ArchetypeStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Qué tipo de oferta vas a crear?</h3>
        <p className="text-sm text-muted-foreground">
          Esto define la estructura — cómo se entrega y qué detalles pediremos después.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {archetypes.map((a) => {
          const Icon = resolveIconByName(a.icon_name);
          return (
            <button
              key={a.archetype}
              type="button"
              onClick={() => onPick(a.archetype as OfferArchetype)}
              className={cn(
                "text-left rounded-lg border bg-card p-4 hover:border-primary hover:shadow-sm transition",
                "flex items-start gap-3",
              )}
            >
              <div className="shrink-0 h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="font-semibold">{a.label_es}</div>
                <p className="text-xs text-muted-foreground">{a.subtitle_es}</p>
                {a.examples_es.length > 0 && (
                  <p className="text-[11px] text-muted-foreground/80">
                    Ej: {a.examples_es.slice(0, 3).join(", ")}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── STEP 2: VALUE LEVEL ──────────────────────────────────────────────────────

interface ValueLevelStepProps {
  onPick: (valueLevel: OfferValueLevel) => void;
  valueLevels: readonly {
    value_level: string;
    label_es: string;
    description_es: string;
    role_in_funnel_es: string;
    icon_name: string;
    is_free: boolean;
    typical_price_min_usd: number | null;
    typical_price_max_usd: number | null;
  }[];
}

function ValueLevelStep({ onPick, valueLevels }: ValueLevelStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Qué rol cumple esta oferta en tu escalera?</h3>
        <p className="text-sm text-muted-foreground">
          Decide cuánto cobrar, para qué parte del funnel sirve, y cómo se presenta.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {valueLevels.map((v) => {
          const Icon = resolveIconByName(v.icon_name);
          const priceHint = v.is_free
            ? "Gratuito"
            : v.typical_price_min_usd !== null && v.typical_price_max_usd !== null
              ? `USD ${v.typical_price_min_usd}-${v.typical_price_max_usd}`
              : "Precio a definir";
          return (
            <button
              key={v.value_level}
              type="button"
              onClick={() => onPick(v.value_level as OfferValueLevel)}
              className="text-left rounded-lg border bg-card p-4 hover:border-primary hover:shadow-sm transition flex items-start gap-3"
            >
              <div className="shrink-0 h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">{v.label_es}</span>
                  <Badge variant="secondary" className="text-[10px]">
                    {priceHint}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">{v.description_es}</p>
                <p className="text-[11px] text-muted-foreground/80 italic">
                  {v.role_in_funnel_es}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── STEP 3: FORMAT ───────────────────────────────────────────────────────────

interface FormatStepProps {
  formats: readonly FormatMetadata[];
  onPick: (format: FormatMetadata) => void;
  onSkip: () => void;
  onCustom: () => void;
  customValue: string;
  onCustomChange: (value: string) => void;
  usingBrandFilter: boolean;
}

function FormatStep({
  formats,
  onPick,
  onCustom,
  customValue,
  onCustomChange,
  usingBrandFilter,
}: FormatStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Qué formato tiene?</h3>
        <p className="text-sm text-muted-foreground">
          {usingBrandFilter
            ? "Filtrados según el perfil de tu negocio. Podés saltar este paso si ninguno encaja."
            : "Seleccioná el formato que más se acerca. Podés saltar si no encaja."}
        </p>
      </div>

      {formats.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[340px] overflow-y-auto pr-2">
          {formats.map((f) => {
            const Icon = resolveIconByName(f.icon_name);
            return (
              <button
                key={f.format_id}
                type="button"
                onClick={() => onPick(f)}
                className="text-left rounded-lg border bg-card p-3 hover:border-primary hover:shadow-sm transition flex items-start gap-3"
              >
                <div className="shrink-0 h-9 w-9 rounded-md bg-muted text-foreground/80 flex items-center justify-center">
                  <Icon className="h-4 w-4" />
                </div>
                <div className="flex-1 space-y-1">
                  <div className="font-medium text-sm">{f.label_es}</div>
                  <p className="text-xs text-muted-foreground line-clamp-2">{f.description_es}</p>
                </div>
              </button>
            );
          })}
        </div>
      )}

      <div className="rounded-lg border border-dashed p-3 space-y-2 bg-muted/30">
        <Label htmlFor="wizard-custom-format" className="text-xs">
          O describí tu propio formato
        </Label>
        <div className="flex gap-2">
          <Input
            id="wizard-custom-format"
            value={customValue}
            onChange={(e) => onCustomChange(e.target.value)}
            placeholder="Ej: Sesión de estrategia de 2 horas"
          />
          <Button
            variant="outline"
            onClick={onCustom}
            disabled={!customValue.trim()}
            size="sm"
          >
            Usar
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── STEP 4: NAME + PRICE ─────────────────────────────────────────────────────

interface NamePriceStepProps {
  isLeadMagnet: boolean;
  name: string;
  onNameChange: (value: string) => void;
  price: string;
  onPriceChange: (value: string) => void;
  tenantCurrency: string;
  valueLevelLabel: string;
  priceMinUsd: number | null;
  priceMaxUsd: number | null;
}

function NamePriceStep({
  isLeadMagnet,
  name,
  onNameChange,
  price,
  onPriceChange,
  tenantCurrency,
  valueLevelLabel,
  priceMinUsd,
  priceMaxUsd,
}: NamePriceStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Nombre y precio</h3>
        <p className="text-sm text-muted-foreground">
          Nivel seleccionado: <span className="font-medium">{valueLevelLabel}</span>
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="wizard-name">Nombre de la oferta</Label>
        <Input
          id="wizard-name"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          placeholder="Programa Elite de Ventas"
          autoFocus
        />
      </div>
      {isLeadMagnet ? (
        <div className="rounded-lg border border-dashed p-3 bg-muted/30 text-sm text-muted-foreground">
          Los lead magnets son gratuitos — no se pide precio en este paso.
        </div>
      ) : (
        <div className="space-y-2">
          <Label htmlFor="wizard-price">Precio ({tenantCurrency})</Label>
          <Input
            id="wizard-price"
            type="number"
            min="0"
            value={price}
            onChange={(e) => onPriceChange(e.target.value)}
            placeholder="0"
          />
          {priceMinUsd !== null && priceMaxUsd !== null && (
            <p className="text-xs text-muted-foreground">
              Rango típico para {valueLevelLabel}: USD {priceMinUsd}–{priceMaxUsd}
              . El precio final se ajusta al valor que vas a entregar.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── STEP 5: EDITIONS (conditional) ───────────────────────────────────────────

interface EditionsStepProps {
  title: string;
  description: string;
  yesLabel: string;
  noLabel: string;
  value: boolean;
  onChange: (value: boolean) => void;
}

function EditionsStep({
  title,
  description,
  yesLabel,
  noLabel,
  value,
  onChange,
}: EditionsStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => onChange(true)}
          className={cn(
            "rounded-lg border p-4 text-left transition",
            value ? "border-primary bg-primary/5" : "hover:border-primary/40",
          )}
        >
          <span className="font-medium">{yesLabel}</span>
        </button>
        <button
          type="button"
          onClick={() => onChange(false)}
          className={cn(
            "rounded-lg border p-4 text-left transition",
            !value ? "border-primary bg-primary/5" : "hover:border-primary/40",
          )}
        >
          <span className="font-medium">{noLabel}</span>
        </button>
      </div>
    </div>
  );
}

// ── STEP 6: PROMISE ──────────────────────────────────────────────────────────

interface PromiseStepProps {
  value: string;
  onChange: (value: string) => void;
}

function PromiseStep({ value, onChange }: PromiseStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Qué resultado logra tu cliente?</h3>
        <p className="text-sm text-muted-foreground">
          Podés completar esto después desde el editor. Sirve como punto de partida.
        </p>
      </div>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ej: Lanza tu primer funnel de ventas en 30 días sin saber de tecnología"
        rows={3}
        autoFocus
      />
    </div>
  );
}
