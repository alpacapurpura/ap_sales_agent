"use client";

import { useState } from "react";
import { OfferArchetype, OfferStatus } from "@/features/offer-studio/types";
import { ARCHETYPE_METADATA } from "@/features/offer-studio/config/archetype-metadata";
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
import { ArrowLeft, ArrowRight, Loader2, Sparkles, SkipForward } from "lucide-react";

interface CreateOfferWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateOffer: (data: WizardResult) => Promise<void>;
  creating?: boolean;
}

export interface WizardResult {
  archetype: OfferArchetype;
  format_hint?: string;
  name: string;
  is_lead_magnet: boolean;
  headline_promise?: string;
  status: OfferStatus;
}

const ARCHETYPE_ORDER: OfferArchetype[] = [
  OfferArchetype.PRODUCTO,
  OfferArchetype.PROGRAMA,
  OfferArchetype.SERVICIO,
  OfferArchetype.MEMBRESIA,
  OfferArchetype.EXPERIENCIA,
];

export function CreateOfferWizard({ open, onOpenChange, onCreateOffer, creating = false }: CreateOfferWizardProps) {
  const [step, setStep] = useState(1);
  const [selectedArchetype, setSelectedArchetype] = useState<OfferArchetype | null>(null);
  const [formatHint, setFormatHint] = useState<string>("");
  const [customFormat, setCustomFormat] = useState("");
  const [offerName, setOfferName] = useState("");
  const [price, setPrice] = useState<string>("");
  const [isLeadMagnet, setIsLeadMagnet] = useState(false);
  const [headlinePromise, setHeadlinePromise] = useState("");

  const resetWizard = () => {
    setStep(1);
    setSelectedArchetype(null);
    setFormatHint("");
    setCustomFormat("");
    setOfferName("");
    setPrice("");
    setIsLeadMagnet(false);
    setHeadlinePromise("");
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) resetWizard();
    onOpenChange(open);
  };

  const priceNum = parseFloat(price) || 0;
  const effectiveLeadMagnet = isLeadMagnet || priceNum === 0;

  const handleSelectArchetype = (archetype: OfferArchetype) => {
    setSelectedArchetype(archetype);
    setStep(2);
  };

  const handleSelectFormat = (format: string) => {
    setFormatHint(format);
    setOfferName(`Mi ${format}`);
    setStep(3);
  };

  const handleSkipFormat = () => {
    setFormatHint("");
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
      headline_promise: headlinePromise || undefined,
      status: OfferStatus.DRAFT,
    });
  };

  const meta = selectedArchetype ? ARCHETYPE_METADATA[selectedArchetype] : null;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {step === 1 && "Que tipo de oferta quieres crear?"}
            {step === 2 && `${meta?.label}: Elige un formato`}
            {step === 3 && "Datos basicos"}
            {step === 4 && "Promesa de resultado"}
          </DialogTitle>
          <DialogDescription>
            {step === 1 && "Elige el arquetipo que mejor describe tu oferta."}
            {step === 2 && "Opcional: esto ayuda a organizar tus ofertas."}
            {step === 3 && "Dale un nombre y precio inicial."}
            {step === 4 && "Opcional: define que resultado logra tu cliente."}
          </DialogDescription>
        </DialogHeader>

        {/* Step indicators */}
        <div className="flex items-center gap-1 px-1">
          {[1, 2, 3, 4].map((s) => (
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

          {/* STEP 2: Format Selection */}
          {step === 2 && meta && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {meta.defaultFormats.map((format) => (
                  <Button
                    key={format}
                    variant={formatHint === format ? "default" : "outline"}
                    size="sm"
                    className="rounded-full"
                    onClick={() => handleSelectFormat(format)}
                  >
                    {format}
                  </Button>
                ))}
              </div>

              <div className="flex items-center gap-2">
                <Input
                  placeholder="O escribe un formato personalizado..."
                  value={customFormat}
                  onChange={(e) => setCustomFormat(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCustomFormat()}
                  className="flex-1"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCustomFormat}
                  disabled={!customFormat.trim()}
                >
                  Usar
                </Button>
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
              <div className="space-y-2">
                <Label htmlFor="wizard-name">Nombre de la oferta</Label>
                <Input
                  id="wizard-name"
                  value={offerName}
                  onChange={(e) => setOfferName(e.target.value)}
                  placeholder="Ej. Mi Curso de Marketing"
                  className="h-11"
                  autoFocus
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="wizard-price">Precio (USD)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-medium">$</span>
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
                    className="h-11 pl-8"
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
            {step === 4 && (
              <>
                <Button
                  variant="outline"
                  onClick={handleCreate}
                  disabled={creating || !offerName.trim()}
                >
                  Completar despues
                </Button>
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
