"use client";

import { BarChart3, CheckCircle2, Target } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import { BestPracticesBlock } from "./BestPracticesBlock";

const DISMISSED_KEY = "meta-ads-onboarding-dismissed";

export interface OnboardingCampaign {
  externalId: string;
  name: string;
  objective: string | null;
}

interface MetaAdsOnboardingModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  campaigns: OnboardingCampaign[];
  /** Called when user chooses "Asociar ahora" in step 2 — parent opens the assignment drawer. */
  onAssignNow: () => void;
}

type Step = 1 | 2 | 3;

function objectiveLabelEs(objective: string | null): string {
  if (!objective) return "";
  const map: Record<string, string> = {
    OUTCOME_SALES: "Ventas",
    OUTCOME_LEADS: "Leads",
    OUTCOME_ENGAGEMENT: "Interacción",
    OUTCOME_AWARENESS: "Alcance",
    OUTCOME_TRAFFIC: "Tráfico",
    OUTCOME_MESSAGES: "Mensajes",
    CONVERSIONS: "Conversiones",
    LINK_CLICKS: "Clics",
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, "").replace(/_/g, " ");
}

function persistDismiss() {
  try {
    localStorage.setItem(DISMISSED_KEY, "1");
  } catch {
    /* noop */
  }
}

export function MetaAdsOnboardingModal(props: MetaAdsOnboardingModalProps) {
  // Inner body is keyed on `open` so the step state resets automatically
  // whenever the modal re-opens — no useEffect needed.
  return (
    <Dialog
      open={props.open}
      onOpenChange={(o) => {
        if (!o) {
          persistDismiss();
        }
        props.onOpenChange(o);
      }}
    >
      {props.open && <ModalBody key={`open-${props.open}`} {...props} />}
    </Dialog>
  );
}

type ModalBodyProps = MetaAdsOnboardingModalProps;

function ModalBody({ onOpenChange, campaigns, onAssignNow }: ModalBodyProps) {
  const [step, setStep] = useState<Step>(1);

  function handleClose() {
    persistDismiss();
    onOpenChange(false);
  }

  function handleAssignNow() {
    persistDismiss();
    onOpenChange(false);
    onAssignNow();
  }

  function renderStep1() {
    return (
      <>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" aria-hidden="true" />
            Bienvenido al dashboard de Meta Ads
          </DialogTitle>
          <DialogDescription>
            Antes de empezar, una breve guía sobre cómo estructurar tus campañas para obtener
            métricas claras por producto.
          </DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <BestPracticesBlock />
          <div className="mt-4 rounded-md border bg-card p-3">
            <p className="text-xs font-medium mb-2 text-muted-foreground">Jerarquía de Meta:</p>
            <div className="flex flex-wrap items-center gap-1 text-[11px]">
              <span className="rounded bg-zinc-500/10 px-2 py-0.5">Cuenta</span>
              <span className="text-muted-foreground">›</span>
              <span className="rounded bg-blue-500/10 px-2 py-0.5 text-blue-400">Campaña</span>
              <span className="text-muted-foreground">›</span>
              <span className="rounded bg-purple-500/10 px-2 py-0.5 text-purple-400">Ad Set</span>
              <span className="text-muted-foreground">›</span>
              <span className="rounded bg-amber-500/10 px-2 py-0.5 text-amber-400">Anuncio</span>
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground">
              Asociamos offers al nivel de <strong>Campaña</strong> (o Ad Set si usás CBO).
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" type="button" onClick={handleClose}>
            Saltar
          </Button>
          <Button type="button" onClick={() => setStep(2)}>
            Siguiente
          </Button>
        </DialogFooter>
      </>
    );
  }

  function renderStep2() {
    return (
      <>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-blue-500" aria-hidden="true" />
            Detectamos {campaigns.length} campaña{campaigns.length === 1 ? "" : "s"} activa
            {campaigns.length === 1 ? "" : "s"}
          </DialogTitle>
          <DialogDescription>¿Vamos a asociarlas ahora con tus offers?</DialogDescription>
        </DialogHeader>
        <div className="py-2 max-h-[240px] overflow-y-auto">
          <div className="space-y-1.5">
            {campaigns.map((c) => (
              <div
                key={c.externalId}
                className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
              >
                <p className="text-sm font-medium truncate">{c.name}</p>
                {c.objective && (
                  <span className="shrink-0 inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                    {objectiveLabelEs(c.objective)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => setStep(3)}>
            Más tarde
          </Button>
          <Button type="button" onClick={handleAssignNow}>
            Asociar ahora
          </Button>
        </DialogFooter>
      </>
    );
  }

  function renderStep3() {
    return (
      <>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />
            Entendido
          </DialogTitle>
          <DialogDescription>
            Cuando quieras, podés asociarlas desde la pestaña <strong>Campañas</strong>. Mientras
            tanto, verás una alerta en el Resumen indicándote las campañas sin asignar.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" onClick={handleClose}>
            Cerrar
          </Button>
        </DialogFooter>
      </>
    );
  }

  return (
    <DialogContent className="max-w-[560px]">
      {step === 1 && renderStep1()}
      {step === 2 && renderStep2()}
      {step === 3 && renderStep3()}
    </DialogContent>
  );
}
