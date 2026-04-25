"use client";

import { ArrowLeft, ArrowRight, Loader2, Plus, Sparkles } from "lucide-react";
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
import { useOfferTypePresetCatalog } from "@/features/offer-studio/hooks/use-offer-type-preset-catalog";
import { useValueLevelMetadata } from "@/features/offer-studio/hooks/use-value-level-catalog";
import { OfferStatus, OfferValueLevel } from "@/features/offer-studio/types";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { useTenantProfile } from "@/features/tenant-profile/hooks/use-tenant-profile";

import { ArchetypePickerStep } from "./ArchetypePickerStep";
import { ConditionalQuestionsStep } from "./ConditionalQuestionsStep";
import { PresetPickerStep } from "./PresetPickerStep";

import type {
  ConditionalQuestion,
  ExpertBusinessType,
  OfferTypePreset,
} from "@/features/offer-studio/api/offer-type-preset-catalog-api";
import type {
  OfferDeliveryModel,
  PricingStructure,
  OfferArchetype,
} from "@/features/offer-studio/types";

interface CreateOfferWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateOffer: (data: WizardResult) => Promise<void>;
  creating?: boolean;
  /**
   * Pre-selected ladder rung — set when the wizard is opened from a
   * context-specific launcher (e.g. the "+" on the Activación column or
   * the Lead Magnet stream header). When present, it overrides the
   * preset's ``typical_value_level`` so the user's explicit click wins.
   * Sprint 15: the value-level step was removed — the rung is always
   * derived from (presetValueLevel ?? customRung ?? preset.typical_value_level).
   */
  presetValueLevel?: OfferValueLevel;
}

export interface WizardResult {
  /** Primary axis (Sprint 13+). Set when a preset was picked. Undefined
   *  in the "Otra / A medida" flow — backend's legacy archetype-only path
   *  handles the no-preset case. */
  preset_id?: string;
  /** Set in both flows: from preset.archetype OR from the custom archetype
   *  picker sub-step. */
  archetype: OfferArchetype;
  /** Wizard-captured yes/no refinements. Backend promotes these into
   *  runtime flags via ``resolve_preset_flags``. Empty in the custom flow. */
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
 *  dynamic step plan below picks the active subset per preset / custom flow.
 *  Sprint 15.2: ``archetype`` step appears only in the custom ("Otra / A
 *  medida") flow, between preset picker and name. */
type StepKey = "preset" | "archetype" | "questions" | "name" | "pricing";

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
  creating = false,
  presetValueLevel,
}: CreateOfferWizardProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const { data: tenantProfile } = useTenantProfile();
  const brandBusinessTypes = (tenantProfile?.business_types ?? []) as ExpertBusinessType[];

  const { data: presetCatalog } = useOfferTypePresetCatalog(brandBusinessTypes);
  const presetsForTenant = presetCatalog?.presets ?? [];
  const questionRegistry = useMemo(() => {
    const map = new Map<string, ConditionalQuestion>();
    for (const q of presetCatalog?.questions ?? []) map.set(q.question_id, q);
    return map;
  }, [presetCatalog?.questions]);

  // ── State ────────────────────────────────────────────────────────────────
  const [selectedPreset, setSelectedPreset] = useState<OfferTypePreset | null>(null);
  // Custom flow state — populated only when the user picks "Otra / A medida"
  // inside a rung group.
  const [customRung, setCustomRung] = useState<OfferValueLevel | null>(null);
  const [customArchetype, setCustomArchetype] = useState<OfferArchetype | null>(null);

  const [conditionalAnswers, setConditionalAnswers] = useState<Record<string, boolean>>({});
  const [offerName, setOfferName] = useState("");
  const [price, setPrice] = useState<string>("");
  const [currencyCode, setCurrencyCode] = useState<string>(tenantCurrency);
  const [headlinePromise, setHeadlinePromise] = useState("");

  // ── Derived values ───────────────────────────────────────────────────────
  const isCustomFlow = customRung !== null;

  // Value level resolution chain. Explicit launcher wins over custom rung
  // wins over preset typical, with ACTIVACION as last fallback.
  const valueLevel: OfferValueLevel =
    presetValueLevel ??
    customRung ??
    selectedPreset?.typical_value_level ??
    OfferValueLevel.ACTIVACION;

  const archetype: OfferArchetype | null = customArchetype ?? selectedPreset?.archetype ?? null;

  const valueLevelMeta = useValueLevelMetadata(valueLevel);
  const isLeadMagnet = valueLevel === OfferValueLevel.LEAD_MAGNET;

  // No reopen-sync needed — derived from props + state each render. Kept
  // the ``open`` dependency hook as a no-op seam for analytics / focus.
  useEffect(() => {
    // Intentionally empty.
  }, [open]);

  // ── Step plan ────────────────────────────────────────────────────────────
  const plan: StepPlan = useMemo(() => {
    const steps: StepKey[] = ["preset"];
    if (isCustomFlow) {
      // Custom flow: ask for archetype before going to name+price. Skip
      // conditional questions entirely (presets carry those, not custom).
      steps.push("archetype");
    } else if (selectedPreset && selectedPreset.conditional_question_ids.length > 0) {
      steps.push("questions");
    }
    steps.push("name");
    if (!isLeadMagnet) steps.push("pricing");
    return { steps, totalVisible: steps.length };
  }, [isCustomFlow, isLeadMagnet, selectedPreset]);

  const [stepIndex, setStepIndex] = useState(0);
  const currentStep: StepKey = plan.steps[stepIndex] ?? "preset";
  const progressPercent = ((stepIndex + 1) / plan.totalVisible) * 100;

  // ── Handlers ─────────────────────────────────────────────────────────────
  const resetWizard = () => {
    setSelectedPreset(null);
    setCustomRung(null);
    setCustomArchetype(null);
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
    setCustomRung(null);
    setCustomArchetype(null);
    if (!offerName) setOfferName(`Mi ${preset.label_es.toLowerCase()}`);
    setStepIndex(1);
  };

  const handlePickCustom = (rung: OfferValueLevel) => {
    setSelectedPreset(null);
    setCustomRung(rung);
    setCustomArchetype(null);
    if (!offerName) setOfferName("Mi oferta a medida");
    setStepIndex(1);
  };

  const handlePickArchetype = (picked: OfferArchetype) => {
    setCustomArchetype(picked);
    setStepIndex((i) => i + 1);
  };

  const handleNext = () => {
    setStepIndex((i) => Math.min(i + 1, plan.totalVisible - 1));
  };

  const handleBack = () => {
    setStepIndex((i) => Math.max(i - 1, 0));
  };

  const buildResult = (): WizardResult | null => {
    if (!archetype || !offerName.trim()) return null;
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
    const requiresStartDate =
      selectedPreset?.default_flags.includes("requires_start_date") ?? false;
    return {
      preset_id: selectedPreset?.preset_id,
      archetype,
      conditional_answers:
        Object.keys(conditionalAnswers).length > 0 ? conditionalAnswers : undefined,
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

  const canSubmit = Boolean(archetype && offerName.trim() && !creating);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto p-0 sm:max-w-[1100px]">
        <div className="px-10 pt-7 pb-5 border-b">
          <DialogHeader className="space-y-2">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <DialogTitle className="text-2xl tracking-tight">Crear oferta nueva</DialogTitle>
                <DialogDescription className="mt-1">
                  Elige el tipo de oferta que más se parezca a lo que vendes.
                </DialogDescription>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {selectedPreset && (
                  <Badge variant="secondary" className="text-xs gap-1">
                    <Sparkles className="h-3 w-3" aria-hidden />
                    {selectedPreset.label_es}
                  </Badge>
                )}
                {isCustomFlow && (
                  <Badge variant="secondary" className="text-xs gap-1 border-dashed">
                    <Plus className="h-3 w-3" aria-hidden />A medida
                  </Badge>
                )}
                {archetype && valueLevelMeta && (
                  <Badge variant="secondary" className="text-xs">
                    Nivel:&nbsp;<strong className="font-semibold">{valueLevelMeta.label_es}</strong>
                  </Badge>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3 pt-2">
              <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                Paso {stepIndex + 1} de {plan.totalVisible}
              </span>
              <div className="h-1.5 flex-1 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          </DialogHeader>
        </div>

        <div className="px-10 py-6">
          {currentStep === "preset" && (
            <PresetPickerStep
              presets={presetsForTenant}
              onPick={handlePickPreset}
              onPickCustom={handlePickCustom}
              businessTypesDeclared={brandBusinessTypes.length > 0}
              businessTypesDeclaredList={brandBusinessTypes}
            />
          )}
          {currentStep === "archetype" && (
            <ArchetypePickerStep
              onPick={handlePickArchetype}
              rungLabel={valueLevelMeta?.label_es}
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
              presetLabel={selectedPreset?.label_es ?? "oferta a medida"}
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

        <DialogFooter className="px-10 py-5 border-t bg-zinc-50/50 flex-col-reverse sm:flex-row gap-2">
          {stepIndex > 0 && (
            <Button variant="ghost" onClick={handleBack} disabled={creating}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Atrás
            </Button>
          )}

          {currentStep !== "preset" &&
            currentStep !== "archetype" &&
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
            currentStep !== "archetype" && (
              <Button onClick={handleCreate} disabled={!canSubmit} className="sm:ml-auto">
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                Crear oferta
              </Button>
            )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
        <h3 className="text-lg font-semibold">Define su identidad</h3>
        <p className="text-sm text-muted-foreground">
          {presetLabel
            ? `Este "${presetLabel.toLowerCase()}" necesita un nombre público y, opcionalmente, una frase titular.`
            : "Ponle un nombre público y, opcionalmente, una frase titular."}
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
            Es lo que tu cliente ve en anuncios, landings y checkout. Puedes cambiarlo después.
          </p>
        </div>
        <div>
          <Label htmlFor="wizard-offer-headline">Frase titular (opcional)</Label>
          <Textarea
            id="wizard-offer-headline"
            placeholder="Aprende a invertir tus primeros USD 500 sin miedo en 8 semanas"
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
        <h3 className="text-lg font-semibold">¿Cuánto cobras?</h3>
        <p className="text-sm text-muted-foreground">
          Empieza con un precio base en la moneda que más cobras. Puedes agregar cuotas, descuentos
          y planes después en el editor.
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
