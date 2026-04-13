"use client";

import { useState } from "react";
import { OfferArchetype, OfferDeliveryModel, OfferValueLevel, OfferStatus } from "@/features/offer-studio/types";
import { ARCHETYPE_METADATA } from "@/features/offer-studio/config/archetype-metadata";
import {
  FORMAT_PRESETS,
  DELIVERY_MODEL_LABELS,
  VALUE_LEVEL_LABELS,
  type FormatPreset,
} from "@/features/offer-studio/config/format-presets";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { ArrowLeft, ArrowRight, Loader2, SkipForward, Rocket, Sparkles } from "lucide-react";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import {
  archetypeSupportsEditions,
  getEditionsCopy,
} from "@/features/offer-studio/utils/editions-copy";

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
  /**
   * Wizard answer to "will this offer run in editions/cohorts/batches?".
   * `undefined` = let the backend apply the archetype-aware default.
   */
  has_editions?: boolean;
  headline_promise?: string;
  status: OfferStatus;
  delivery_model?: OfferDeliveryModel;
  value_level?: OfferValueLevel;
  specific_details?: Record<string, unknown>;
}

const ARCHETYPE_ORDER: OfferArchetype[] = [
  OfferArchetype.PRODUCTO,
  OfferArchetype.PROGRAMA,
  OfferArchetype.SERVICIO,
  OfferArchetype.MEMBRESIA,
  OfferArchetype.EXPERIENCIA,
];

export function CreateOfferWizard({ open, onOpenChange, onCreateOffer, onCreateWithIA, creating = false }: CreateOfferWizardProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const [step, setStep] = useState(1);
  const [selectedArchetype, setSelectedArchetype] = useState<OfferArchetype | null>(null);
  const [formatHint, setFormatHint] = useState<string>("");
  const [customFormat, setCustomFormat] = useState("");
  const [offerName, setOfferName] = useState("");
  const [price, setPrice] = useState<string>("");
  const [isLeadMagnet, setIsLeadMagnet] = useState(false);
  const [headlinePromise, setHeadlinePromise] = useState("");
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [selectedDeliveryModel, setSelectedDeliveryModel] = useState<OfferDeliveryModel | undefined>(undefined);
  const [selectedValueLevel, setSelectedValueLevel] = useState<OfferValueLevel | undefined>(undefined);
  const [selectedSpecificDetails, setSelectedSpecificDetails] = useState<Record<string, unknown> | undefined>(undefined);
  // Wizard answer for "will this offer run in editions?". Defaults to true for
  // archetypes that support editions; ignored otherwise.
  const [hasEditions, setHasEditions] = useState<boolean>(true);

  const resetWizard = () => {
    setStep(1);
    setSelectedArchetype(null);
    setFormatHint("");
    setCustomFormat("");
    setOfferName("");
    setPrice("");
    setIsLeadMagnet(false);
    setHeadlinePromise("");
    setSelectedPresetId(null);
    setSelectedDeliveryModel(undefined);
    setSelectedValueLevel(undefined);
    setSelectedSpecificDetails(undefined);
    setHasEditions(true);
  };

  const showsEditionsStep =
    selectedArchetype !== null && archetypeSupportsEditions(selectedArchetype);
  const editionsCopy = selectedArchetype
    ? getEditionsCopy(selectedArchetype)
    : null;
  const totalSteps = showsEditionsStep ? 5 : 4;
  const finalStep = totalSteps;

  const handleOpenChange = (open: boolean) => {
    if (!open) resetWizard();
    onOpenChange(open);
  };

  const priceNum = parseFloat(price) || 0;
  const effectiveLeadMagnet = isLeadMagnet;

  const handleSelectArchetype = (archetype: OfferArchetype) => {
    setSelectedArchetype(archetype);
    setStep(2);
  };

  const handleSelectPreset = (preset: FormatPreset) => {
    const isCustom = preset.id.endsWith("_custom");
    setSelectedPresetId(preset.id);
    setSelectedDeliveryModel(preset.delivery_model);
    setSelectedValueLevel(preset.suggested_value_level);
    setSelectedSpecificDetails(preset.specific_details_defaults);

    if (isCustom) {
      // For custom preset, clear format hint and let user type
      setFormatHint("");
      setOfferName("");
    } else {
      setFormatHint(preset.format_hint);
      setOfferName(`Mi ${preset.label}`);
    }
    setStep(3);
  };

  const handleSkipFormat = () => {
    setFormatHint("");
    setSelectedPresetId(null);
    setSelectedDeliveryModel(undefined);
    setSelectedValueLevel(undefined);
    setSelectedSpecificDetails(undefined);
    setStep(3);
  };

  const handleCustomFormat = () => {
    if (customFormat.trim()) {
      setFormatHint(customFormat.trim());
      setOfferName(`Mi ${customFormat.trim()}`);
      setStep(3);
    }
  };

  const handleCreate = async () => {
    if (!selectedArchetype || !offerName.trim()) return;
    await onCreateOffer({
      archetype: selectedArchetype,
      format_hint: formatHint || undefined,
      name: offerName.trim(),
      is_lead_magnet: effectiveLeadMagnet,
      // Only send the wizard answer when the user actually got to the question.
      // Otherwise let the backend apply the archetype-aware default.
      has_editions: showsEditionsStep ? hasEditions : undefined,
      headline_promise: headlinePromise || undefined,
      status: OfferStatus.DRAFT,
      delivery_model: selectedDeliveryModel,
      value_level: selectedValueLevel,
      specific_details: selectedSpecificDetails,
    });
  };

  const handleCreateWithIA = async () => {
    if (!selectedArchetype || !offerName.trim() || !onCreateWithIA) return;
    await onCreateWithIA({
      archetype: selectedArchetype,
      format_hint: formatHint || undefined,
      name: offerName.trim(),
      is_lead_magnet: effectiveLeadMagnet,
      has_editions: showsEditionsStep ? hasEditions : undefined,
      headline_promise: headlinePromise || undefined,
      status: OfferStatus.DRAFT,
      delivery_model: selectedDeliveryModel,
      value_level: selectedValueLevel,
      specific_details: selectedSpecificDetails,
    });
  };

  const meta = selectedArchetype ? ARCHETYPE_METADATA[selectedArchetype] : null;
  const presets = selectedArchetype ? FORMAT_PRESETS[selectedArchetype] : [];

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {step === 1 && "Que tipo de oferta quieres crear?"}
            {step === 2 && `${meta?.label}: Elige un formato`}
            {step === 3 && "Datos basicos"}
            {step === 4 && "Promesa de resultado"}
            {step === 5 && editionsCopy?.title}
          </DialogTitle>
          <DialogDescription>
            {step === 1 && "Elige el arquetipo que mejor describe tu oferta."}
            {step === 2 && "Selecciona un formato predefinido o crea uno personalizado."}
            {step === 3 && "Dale un nombre y precio inicial."}
            {step === 4 && "Opcional: define que resultado logra tu cliente."}
            {step === 5 && editionsCopy?.description}
          </DialogDescription>
        </DialogHeader>

        {/* Step indicators */}
        <div className="flex items-center gap-1 px-1">
          {Array.from({ length: totalSteps }, (_, i) => i + 1).map((s) => (
            <div
              key={s}
              className={cn(
                "h-1.5 flex-1 rounded-full transition-colors",
                s <= step ? "bg-primary" : "bg-muted"
              )}
            />
          ))}
        </div>

        <div className="py-2">
          {/* STEP 1: Archetype Selection */}
          {step === 1 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {ARCHETYPE_ORDER.map((archetype) => {
                const m = ARCHETYPE_METADATA[archetype];
                const Icon = m.icon;
                return (
                  <button
                    key={archetype}
                    onClick={() => handleSelectArchetype(archetype)}
                    className={cn(
                      "flex flex-col items-start gap-2 p-4 rounded-xl border text-left transition-all hover:shadow-md hover:border-primary/50",
                      "bg-background cursor-pointer"
                    )}
                  >
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-semibold text-sm">{m.label}</p>
                      <p className="text-xs text-muted-foreground leading-snug">{m.subtitle}</p>
                    </div>
                    <p className="text-[10px] text-muted-foreground/70 line-clamp-2">{m.examples}</p>
                  </button>
                );
              })}
            </div>
          )}

          {/* STEP 2: Format Preset Selection */}
          {step === 2 && meta && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {presets.map((preset) => {
                  const isCustom = preset.id.endsWith("_custom");
                  return (
                    <button
                      key={preset.id}
                      onClick={() => handleSelectPreset(preset)}
                      className={cn(
                        "flex flex-col items-start gap-2 p-4 rounded-xl text-left transition-all hover:shadow-md cursor-pointer",
                        isCustom
                          ? "border-2 border-dashed border-muted-foreground/30 hover:border-primary/50 bg-background"
                          : "border border-border hover:border-primary/50 bg-background",
                        selectedPresetId === preset.id && "border-primary ring-1 ring-primary/20"
                      )}
                    >
                      <div className="flex items-center justify-between w-full">
                        <p className="font-semibold text-sm">{preset.label}</p>
                      </div>
                      <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                        {preset.description}
                      </p>
                      {!isCustom && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                            {VALUE_LEVEL_LABELS[preset.suggested_value_level]}
                          </Badge>
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                            {DELIVERY_MODEL_LABELS[preset.delivery_model]}
                          </Badge>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>

              <Button variant="ghost" size="sm" className="text-muted-foreground" onClick={handleSkipFormat}>
                <SkipForward className="mr-1 h-3 w-3" />
                Saltar este paso
              </Button>
            </div>
          )}

          {/* STEP 3: Basics */}
          {step === 3 && (
            <div className="space-y-4">
              {/* Show custom format input when "Personalizado" was selected */}
              {selectedPresetId?.endsWith("_custom") && (
                <div className="space-y-2">
                  <Label htmlFor="wizard-custom-format">Formato personalizado</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="wizard-custom-format"
                      placeholder="Escribe tu formato (ej: Workshop Online)"
                      value={customFormat}
                      onChange={(e) => setCustomFormat(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleCustomFormat();
                        }
                      }}
                      className="flex-1"
                      autoFocus
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (customFormat.trim()) {
                          setFormatHint(customFormat.trim());
                          setOfferName(`Mi ${customFormat.trim()}`);
                        }
                      }}
                      disabled={!customFormat.trim()}
                    >
                      Aplicar
                    </Button>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="wizard-name">Nombre de la oferta</Label>
                <Input
                  id="wizard-name"
                  value={offerName}
                  onChange={(e) => setOfferName(e.target.value)}
                  placeholder="Ej. Mi Curso de Marketing"
                  className="h-11"
                  autoFocus={!selectedPresetId?.endsWith("_custom")}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="wizard-price">Precio ({tenantCurrency})</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted-foreground font-medium">{tenantCurrency}</span>
                  <Input
                    id="wizard-price"
                    type="number"
                    min="0"
                    value={price}
                    onChange={(e) => {
                      setPrice(e.target.value);
                      if (parseFloat(e.target.value) === 0) setIsLeadMagnet(true);
                    }}
                    placeholder="0"
                    className="h-11 pl-12"
                  />
                </div>
                {priceNum === 0 && (
                  <p className="text-xs text-muted-foreground">Se marcara como Lead Magnet automaticamente.</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Checkbox
                  id="wizard-lead-magnet"
                  checked={isLeadMagnet}
                  onCheckedChange={(checked) => setIsLeadMagnet(!!checked)}
                />
                <Label htmlFor="wizard-lead-magnet" className="text-sm cursor-pointer">
                  Es un lead magnet (gratuito para captar prospectos)
                </Label>
              </div>

              {meta && (
                <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg">
                  <Badge variant="secondary" className="text-xs">
                    {meta.label}
                  </Badge>
                  {formatHint && (
                    <Badge variant="outline" className="text-xs">
                      {formatHint}
                    </Badge>
                  )}
                  {selectedDeliveryModel && (
                    <Badge variant="outline" className="text-xs">
                      {DELIVERY_MODEL_LABELS[selectedDeliveryModel]}
                    </Badge>
                  )}
                </div>
              )}
            </div>
          )}

          {/* STEP 4: Promise */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="wizard-promise">En una frase, que resultado logra tu cliente?</Label>
                <Textarea
                  id="wizard-promise"
                  value={headlinePromise}
                  onChange={(e) => setHeadlinePromise(e.target.value)}
                  placeholder="Ej. Lanza tu primer funnel de ventas en 30 dias sin saber de tecnologia"
                  rows={3}
                  autoFocus
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Puedes completar esto despues desde el editor. No te preocupes si no lo tienes claro aun.
              </p>
            </div>
          )}

          {/* STEP 5: Has editions? (only for PROGRAMA/SERVICIO/EXPERIENCIA) */}
          {step === 5 && editionsCopy && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-primary/5 border border-primary/20">
                <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <Rocket className="h-4 w-4 text-primary" />
                </div>
                <p className="text-sm text-muted-foreground leading-snug">
                  {editionsCopy.description}
                </p>
              </div>

              <div className="grid gap-2">
                <button
                  type="button"
                  onClick={() => setHasEditions(true)}
                  className={cn(
                    "flex items-center gap-3 p-4 rounded-xl border text-left transition-all hover:border-primary/50 cursor-pointer",
                    hasEditions
                      ? "border-primary ring-1 ring-primary/20 bg-primary/5"
                      : "border-border bg-background"
                  )}
                >
                  <div
                    className={cn(
                      "h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0",
                      hasEditions ? "border-primary" : "border-muted-foreground/40"
                    )}
                  >
                    {hasEditions && <div className="h-2 w-2 rounded-full bg-primary" />}
                  </div>
                  <p className="text-sm font-medium">{editionsCopy.yesLabel}</p>
                </button>

                <button
                  type="button"
                  onClick={() => setHasEditions(false)}
                  className={cn(
                    "flex items-center gap-3 p-4 rounded-xl border text-left transition-all hover:border-primary/50 cursor-pointer",
                    !hasEditions
                      ? "border-primary ring-1 ring-primary/20 bg-primary/5"
                      : "border-border bg-background"
                  )}
                >
                  <div
                    className={cn(
                      "h-4 w-4 rounded-full border-2 flex items-center justify-center shrink-0",
                      !hasEditions ? "border-primary" : "border-muted-foreground/40"
                    )}
                  >
                    {!hasEditions && <div className="h-2 w-2 rounded-full bg-primary" />}
                  </div>
                  <p className="text-sm font-medium">{editionsCopy.noLabel}</p>
                </button>
              </div>

              <p className="text-xs text-muted-foreground">
                {editionsCopy.helper}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="flex items-center justify-between sm:justify-between gap-2">
          <div>
            {step > 1 && (
              <Button variant="ghost" size="sm" onClick={() => setStep(step - 1)}>
                <ArrowLeft className="mr-1 h-3 w-3" />
                Atras
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2">
            {step === 3 && (
              <Button
                onClick={() => setStep(4)}
                disabled={!offerName.trim()}
              >
                Siguiente
                <ArrowRight className="ml-1 h-3 w-3" />
              </Button>
            )}
            {step === 4 && showsEditionsStep && (
              <>
                <Button
                  variant="outline"
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  Completar despues
                </Button>
                <Button
                  onClick={() => setStep(5)}
                  disabled={!offerName.trim()}
                >
                  Siguiente
                  <ArrowRight className="ml-1 h-3 w-3" />
                </Button>
              </>
            )}
            {step === 4 && !showsEditionsStep && (
              <>
                <Button
                  variant="outline"
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  Completar despues
                </Button>
                {onCreateWithIA && (
                  <Button
                    variant="secondary"
                    onClick={handleCreateWithIA}
                    disabled={creating || !offerName.trim()}
                  >
                    <Sparkles className="mr-1 h-3 w-3" />
                    Crear con asistente IA
                  </Button>
                )}
                <Button
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Crear Oferta
                </Button>
              </>
            )}
            {step === finalStep && finalStep === 5 && (
              <>
                <Button
                  variant="outline"
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  Completar despues
                </Button>
                {onCreateWithIA && (
                  <Button
                    variant="secondary"
                    onClick={handleCreateWithIA}
                    disabled={creating || !offerName.trim()}
                  >
                    <Sparkles className="mr-1 h-3 w-3" />
                    Crear con asistente IA
                  </Button>
                )}
                <Button
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Crear Oferta
                </Button>
              </>
            )}
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
