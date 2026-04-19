"use client";

import { ArrowLeft, ArrowRight, Loader2, Rocket, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CurrencySelect } from "@/components/shared/CurrencySelect";
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
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useOfferTypePresetCatalog } from "@/features/offer-studio/hooks/use-offer-type-preset-catalog";
import {
  useValueLevelCatalog,
  useValueLevelMetadata,
} from "@/features/offer-studio/hooks/use-value-level-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { OfferStatus, OfferValueLevel } from "@/features/offer-studio/types";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { cn } from "@/lib/utils";

import { ConditionalQuestionsStep } from "./ConditionalQuestionsStep";
import { PresetPickerStep } from "./PresetPickerStep";

import type {
  ConditionalQuestion,
  ExpertBusinessType,
  OfferTypePreset,
} from "@/features/offer-studio/api/offer-type-preset-catalog-api";
import type {
  OfferArchetype,
  OfferDeliveryModel,
  PricingStructure,
} from "@/features/offer-studio/types";

interface CreateOfferWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateOffer: (data: WizardResult) => Promise<void>;
  onCreateWithIA?: (data: WizardResult) => Promise<void>;
  creating?: boolean;
  /**
   * Pre-selected ladder rung — set when the wizard is opened from a
   * context-specific launcher (e.g. the "+" on the Activación column or
   * the Lead Magnet stream header). When present, the value-level step
   * is hidden because the user has already answered that question by
   * where they clicked.
   */
  presetValueLevel?: OfferValueLevel;
}

export interface WizardResult {
  /** Primary axis (Sprint 13+). Always emitted when a preset was picked. */
  preset_id?: string;
  /** Derived from the preset. Kept on the payload for backwards compat
   *  with the OfferCreate DTO and for legacy downstream consumers. */
  archetype: OfferArchetype;
  /** Wizard-captured yes/no refinements. Backend promotes these into
   *  runtime flags via ``resolve_preset_flags``. */
  conditional_answers?: Record<string, boolean>;
  format_hint?: string;
  name: string;
  is_lead_magnet: boolean;
  has_editions?: boolean;
  headline_promise?: string;
  status: OfferStatus;
  delivery_model?: OfferDeliveryModel;
  value_level: OfferValueLevel;
  specific_details?: Record<string, unknown>;
  currency?: string;
  pricing_options?: PricingStructure[];
}

/** Internal step identifiers. Not all run on every session — the
 *  dynamic step plan below picks the active subset per preset. */
type StepKey = "preset" | "value_level" | "questions" | "name" | "pricing";

interface StepPlan {
  steps: readonly StepKey[];
  totalVisible: number;
}

/**
 *
 */
export function CreateOfferWizard({
  open,
  onOpenChange,
  onCreateOffer,
  onCreateWithIA,
  creating = false,
  presetValueLevel,
}: CreateOfferWizardProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const { data: valueLevelCatalog } = useValueLevelCatalog();
  const { settings } = useBrandSettings();
  const brandBusinessTypes = (settings?.identity?.business_types ?? []) as ExpertBusinessType[];

  const { data: presetCatalog } = useOfferTypePresetCatalog(brandBusinessTypes);
  const presetsForTenant = presetCatalog?.presets ?? [];
  const questionRegistry = useMemo(() => {
    const map = new Map<string, ConditionalQuestion>();
    for (const q of presetCatalog?.questions ?? []) map.set(q.question_id, q);
    return map;
  }, [presetCatalog?.questions]);

  const [selectedPreset, setSelectedPreset] = useState<OfferTypePreset | null>(null);
  const [valueLevel, setValueLevel] = useState<OfferValueLevel | null>(presetValueLevel ?? null);
  const [conditionalAnswers, setConditionalAnswers] = useState<Record<string, boolean>>({});
  const [offerName, setOfferName] = useState("");
  const [price, setPrice] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState<string>(tenantCurrency);
  const [headlinePromise, setHeadlinePromise] = useState("");

  const valueLevelMeta = useValueLevelMetadata(valueLevel ?? undefined);

  // Keep state in sync with a reopen from a different launcher. Same
  // rationale as the legacy wizard — preserve user work; only sync the
  // preselected rung if it changed.
  useEffect(() => {
    if (!open) return;
    if (presetValueLevel && presetValueLevel !== valueLevel) {
      setValueLevel(presetValueLevel);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, presetValueLevel]);

  const hasPresetValueLevel = Boolean(presetValueLevel);
  const isLeadMagnetFromPreset = Boolean(selectedPreset?.default_flags.includes("is_lead_magnet"));
  const isLeadMagnetFromRung = valueLevel === OfferValueLevel.LEAD_MAGNET;
  const isLeadMagnet = isLeadMagnetFromPreset || isLeadMagnetFromRung;

  /** Compute which steps apply given the current preset + preselections.
   *  Recomputed per render so state changes (preset pick) collapse the
   *  plan immediately (e.g. a lead-magnet preset skips pricing). */
  const plan: StepPlan = useMemo(() => {
    const steps: StepKey[] = ["preset"];
    if (!hasPresetValueLevel && !isLeadMagnetFromPreset) steps.push("value_level");
    if (selectedPreset && selectedPreset.conditional_question_ids.length > 0) {
      steps.push("questions");
    }
    steps.push("name");
    if (!isLeadMagnet) steps.push("pricing");
    return { steps, totalVisible: steps.length };
  }, [hasPresetValueLevel, isLeadMagnetFromPreset, isLeadMagnet, selectedPreset]);

  const [stepIndex, setStepIndex] = useState(0);
  const currentStep: StepKey = plan.steps[stepIndex] ?? "preset";
  const progressPercent = ((stepIndex + 1) / plan.totalVisible) * 100;

  const resetWizard = () => {
    setSelectedPreset(null);
    setValueLevel(presetValueLevel ?? null);
    setConditionalAnswers({});
    setOfferName("");
    setPrice("");
    setCurrencyCode(tenantCurrency);
    setHeadlinePromise("");
    setStepIndex(0);
  };

  const handleOpenChange = (next: boolean) => {
    if (!next) resetWizard();
    onOpenChange(next);
  };

  const activePresetQuestions = useMemo<readonly ConditionalQuestion[]>(() => {
    if (!selectedPreset) return [];
    return selectedPreset.conditional_question_ids
      .map((qid) => questionRegistry.get(qid))
      .filter((q): q is ConditionalQuestion => Boolean(q));
  }, [questionRegistry, selectedPreset]);

  const handlePickPreset = (preset: OfferTypePreset) => {
    setSelectedPreset(preset);
    if (!offerName) setOfferName(`Mi ${preset.label_es.toLowerCase()}`);
    // Advance one step; the `plan` will redefine how many remain.
    setStepIndex(1);
  };

  const handlePickValueLevel = (pick: OfferValueLevel) => {
    setValueLevel(pick);
    setStepIndex((i) => i + 1);
  };

  const handleNext = () => {
    setStepIndex((i) => Math.min(i + 1, plan.totalVisible - 1));
  };

  const handleBack = () => {
    setStepIndex((i) => Math.max(i - 1, 0));
  };

  const buildResult = (): WizardResult | null => {
    if (!selectedPreset || !valueLevel || !offerName.trim()) return null;
    const priceNum = parseFloat(price);
    const pricingOptions: PricingStructure[] = isLeadMagnet
      ? []
      : [
          {
            label: "Standard",
            plan_type: "one_time",
            total_amount: Number.isFinite(priceNum) && priceNum >= 0 ? priceNum : 0,
            currency: currencyCode,
            deposit_required: 0,
            number_of_installments: 1,
            installment_amount: 0,
          },
        ];
    const requiresStartDate = selectedPreset.default_flags.includes("requires_start_date");
    return {
      preset_id: selectedPreset.preset_id,
      archetype: selectedPreset.archetype,
      conditional_answers: Object.keys(conditionalAnswers).length ? conditionalAnswers : undefined,
      format_hint: undefined,
      name: offerName.trim(),
      is_lead_magnet: isLeadMagnet,
      has_editions: requiresStartDate ? true : undefined,
      headline_promise: headlinePromise.trim() || undefined,
      status: OfferStatus.DRAFT,
      delivery_model: undefined,
      value_level: valueLevel,
      specific_details: undefined,
      currency: currencyCode,
      pricing_options: pricingOptions,
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

  const canSubmit = Boolean(selectedPreset && valueLevel && offerName.trim() && !creating);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <DialogTitle>Crear oferta nueva</DialogTitle>
            <div className="flex items-center gap-2 flex-wrap">
              {selectedPreset && (
                <Badge variant="secondary" className="text-xs gap-1">
                  <Sparkles className="h-3 w-3" aria-hidden />
                  {selectedPreset.label_es}
                </Badge>
              )}
              {hasPresetValueLevel && valueLevelMeta && (
                <Badge variant="secondary" className="text-xs">
                  Nivel:&nbsp;<strong className="font-semibold">{valueLevelMeta.label_es}</strong>
                </Badge>
              )}
            </div>
          </div>
          <DialogDescription>
            Paso {stepIndex + 1} de {plan.totalVisible}
          </DialogDescription>
          <div className="h-1 w-full bg-muted rounded-full mt-2">
            <div
              className="h-full bg-primary rounded-full transition-all"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </DialogHeader>

        <div className="py-4">
          {currentStep === "preset" && (
            <PresetPickerStep
              presets={presetsForTenant}
              onPick={handlePickPreset}
              businessTypesDeclared={brandBusinessTypes.length > 0}
              businessTypesDeclaredList={brandBusinessTypes}
            />
          )}
          {currentStep === "value_level" && (
            <ValueLevelStep
              onPick={handlePickValueLevel}
              valueLevels={valueLevelCatalog?.value_levels ?? EMPTY_LIST}
            />
          )}
          {currentStep === "questions" && selectedPreset && (
            <ConditionalQuestionsStep
              questions={activePresetQuestions}
              answers={conditionalAnswers}
              onChange={setConditionalAnswers}
              presetLabel={selectedPreset.label_es}
            />
          )}
          {currentStep === "name" && (
            <NamePromiseStep
              name={offerName}
              onNameChange={setOfferName}
              headline={headlinePromise}
              onHeadlineChange={setHeadlinePromise}
              presetLabel={selectedPreset?.label_es ?? ""}
            />
          )}
          {currentStep === "pricing" && (
            <PricingStep
              price={price}
              onPriceChange={setPrice}
              currencyCode={currencyCode}
              onCurrencyChange={setCurrencyCode}
              valueLevelLabel={valueLevelMeta?.label_es ?? ""}
              priceMinUsd={valueLevelMeta?.typical_price_min_usd ?? null}
              priceMaxUsd={valueLevelMeta?.typical_price_max_usd ?? null}
            />
          )}
        </div>

        <DialogFooter className="flex-col-reverse sm:flex-row gap-2">
          {stepIndex > 0 && (
            <Button variant="ghost" onClick={handleBack} disabled={creating}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Atrás
            </Button>
          )}

          {currentStep !== "preset" &&
            currentStep !== "value_level" &&
            stepIndex < plan.totalVisible - 1 && (
              <Button
                className="sm:ml-auto"
                onClick={handleNext}
                disabled={creating || (currentStep === "name" && !offerName.trim())}
              >
                Siguiente <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            )}

          {stepIndex === plan.totalVisible - 1 &&
            currentStep !== "preset" &&
            currentStep !== "value_level" && (
              <div className="flex gap-2 sm:ml-auto">
                {onCreateWithIA && (
                  <Button variant="outline" onClick={handleCreateWithIA} disabled={!canSubmit}>
                    {creating ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="mr-2 h-4 w-4" />
                    )}
                    Crear con IA
                  </Button>
                )}
                <Button onClick={handleCreate} disabled={!canSubmit}>
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

// Stable reference so React Query loading state doesn't create a new array
// each render and thrash the memoized children.
const EMPTY_LIST: readonly never[] = [];

// ── STEP: VALUE LEVEL (legacy, unchanged semantics) ──────────────────────────

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
            ? "Gratis"
            : v.typical_price_min_usd != null && v.typical_price_max_usd != null
              ? `USD ${v.typical_price_min_usd}–${v.typical_price_max_usd}`
              : null;
          return (
            <button
              key={v.value_level}
              type="button"
              onClick={() => onPick(v.value_level as OfferValueLevel)}
              className={cn(
                "text-left rounded-lg border bg-card p-4 hover:border-primary hover:shadow-sm transition",
                "flex items-start gap-3",
              )}
            >
              <div className="shrink-0 h-10 w-10 rounded-md bg-primary/10 text-primary flex items-center justify-center">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-semibold">{v.label_es}</span>
                  {priceHint && (
                    <span className="text-[11px] text-muted-foreground">{priceHint}</span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{v.role_in_funnel_es}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── STEP: NAME + PROMISE ─────────────────────────────────────────────────────

interface NamePromiseStepProps {
  name: string;
  onNameChange: (value: string) => void;
  headline: string;
  onHeadlineChange: (value: string) => void;
  presetLabel: string;
}

function NamePromiseStep({
  name,
  onNameChange,
  headline,
  onHeadlineChange,
  presetLabel,
}: NamePromiseStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Dale una identidad</h3>
        <p className="text-sm text-muted-foreground">
          {presetLabel
            ? `Este "${presetLabel.toLowerCase()}" necesita un nombre público y, opcionalmente, una frase titular.`
            : "Dale un nombre público y, opcionalmente, una frase titular."}
        </p>
      </div>
      <div className="space-y-4">
        <div>
          <Label htmlFor="wizard-offer-name">Nombre público</Label>
          <Input
            id="wizard-offer-name"
            placeholder="Ej: Programa Libertad Financiera"
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Es lo que tu cliente ve en anuncios, landings y checkout. Podés cambiarlo después.
          </p>
        </div>
        <div>
          <Label htmlFor="wizard-offer-headline">Frase titular (opcional)</Label>
          <Textarea
            id="wizard-offer-headline"
            placeholder="Aprendé a invertir tus primeros USD 500 sin miedo en 8 semanas"
            value={headline}
            onChange={(e) => onHeadlineChange(e.target.value)}
            rows={3}
          />
          <p className="text-xs text-muted-foreground mt-1">
            Promesa concreta y medible. Mejor cuanto más específica.
          </p>
        </div>
      </div>
    </div>
  );
}

// ── STEP: PRICING ────────────────────────────────────────────────────────────

interface PricingStepProps {
  price: string;
  onPriceChange: (value: string) => void;
  currencyCode: string;
  onCurrencyChange: (value: string) => void;
  valueLevelLabel: string;
  priceMinUsd: number | null;
  priceMaxUsd: number | null;
}

function PricingStep({
  price,
  onPriceChange,
  currencyCode,
  onCurrencyChange,
  valueLevelLabel,
  priceMinUsd,
  priceMaxUsd,
}: PricingStepProps) {
  const priceHint =
    priceMinUsd != null && priceMaxUsd != null
      ? `Rango típico para ${valueLevelLabel}: USD ${priceMinUsd}–${priceMaxUsd}`
      : null;
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">¿Cuánto cobrás?</h3>
        <p className="text-sm text-muted-foreground">
          Arrancá con un precio base en la moneda que más cobrás. Podés agregar cuotas, descuentos y
          planes después en el editor.
        </p>
      </div>
      <div className="grid grid-cols-[1fr_140px] gap-3">
        <div>
          <Label htmlFor="wizard-offer-price">Precio</Label>
          <Input
            id="wizard-offer-price"
            placeholder="Ej: 1497"
            inputMode="decimal"
            value={price}
            onChange={(e) => onPriceChange(e.target.value)}
          />
          {priceHint && <p className="text-xs text-muted-foreground mt-1">{priceHint}</p>}
        </div>
        <div>
          <Label htmlFor="wizard-offer-currency">Moneda</Label>
          <CurrencySelect value={currencyCode} onChange={onCurrencyChange} />
        </div>
      </div>
    </div>
  );
}
