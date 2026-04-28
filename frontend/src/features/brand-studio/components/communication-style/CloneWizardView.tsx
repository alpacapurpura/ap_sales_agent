"use client";

import { Check, Loader2, RefreshCw, Upload, X } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import { useEffect, useReducer, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import {
  useActivateProfile,
  useCloneDryRun,
  useClonePersonality,
  useSimulatePersonality,
} from "@/features/brand-studio/api/personality";

import { CommunicationStyleNav } from "./CommunicationStyleNav";
import { DimensionsPanel } from "./DimensionsPanel";
import { FingerprintPanel } from "./FingerprintPanel";

import type { CloneDryRunResult } from "@/features/brand-studio/api/personality";
import type { PersonalityProfile, SampleExchange } from "@/features/brand-studio/types/personality";

// ── State machine ─────────────────────────────────────────────────────────────

type WizardStep = "material" | "analyzing" | "preview";
type InputMode = "text" | "file";

interface WizardState {
  step: WizardStep;
  inputMode: InputMode;
  text: string;
  file: File | null;
  profile: PersonalityProfile | null;
  previewExchanges: SampleExchange[] | null;
  error: string | null;
}

type WizardAction =
  | { type: "SET_INPUT_MODE"; payload: InputMode }
  | { type: "SET_TEXT"; payload: string }
  | { type: "SET_FILE"; payload: File | null }
  | { type: "START_ANALYZING" }
  | { type: "SET_PREVIEW"; payload: PersonalityProfile }
  | { type: "SET_ERROR"; payload: string }
  | { type: "RESET" }
  | { type: "SET_PREVIEW_EXCHANGES"; payload: SampleExchange[] };

function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case "SET_INPUT_MODE":
      return { ...state, inputMode: action.payload, text: "", file: null, error: null };
    case "SET_TEXT":
      return { ...state, text: action.payload, error: null };
    case "SET_FILE":
      return { ...state, file: action.payload, error: null };
    case "START_ANALYZING":
      return { ...state, step: "analyzing", error: null };
    case "SET_PREVIEW":
      return {
        ...state,
        step: "preview",
        profile: action.payload,
        previewExchanges: action.payload.sample_exchanges.slice(0, 3),
        error: null,
      };
    case "SET_ERROR":
      return { ...state, step: "material", error: action.payload };
    case "RESET":
      return initialState;
    case "SET_PREVIEW_EXCHANGES":
      return { ...state, previewExchanges: action.payload };
    default:
      return state;
  }
}

const initialState: WizardState = {
  step: "material",
  inputMode: "text",
  text: "",
  file: null,
  profile: null,
  previewExchanges: null,
  error: null,
};

// ── Stepper UI ────────────────────────────────────────────────────────────────

const STEPS = [
  { key: "material", label: "Material" },
  { key: "analyzing", label: "Análisis" },
  { key: "preview", label: "Previa" },
] as const;

interface StepperProps {
  current: WizardStep;
}

function Stepper({ current }: StepperProps) {
  const currentIdx = STEPS.findIndex((s) => s.key === current);

  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, idx) => {
        const isDone = idx < currentIdx;
        const isCurrent = step.key === current;
        return (
          <div key={step.key} className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <div
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${
                  isCurrent
                    ? "bg-primary text-primary-foreground"
                    : isDone
                      ? "bg-primary/30 text-primary"
                      : "bg-muted text-muted-foreground"
                }`}
                aria-current={isCurrent ? "step" : undefined}
              >
                {isDone ? <Check className="h-3 w-3" aria-hidden /> : idx + 1}
              </div>
              <span
                className={`text-xs ${isCurrent ? "font-medium text-foreground" : "text-muted-foreground"}`}
              >
                {step.label}
              </span>
            </div>
            {idx < STEPS.length - 1 && <div className="h-px w-8 bg-border" aria-hidden />}
          </div>
        );
      })}
    </div>
  );
}

// ── Analysis progress items ───────────────────────────────────────────────────

const PIPELINE_STEPS = [
  "Parseo de mensajes",
  "Limpieza de ruido",
  "Perfil psicológico",
  "Arquitectura del estilo",
  "Embeddings Qdrant",
  "Simulación de ejemplos",
] as const;

function AnalyzingStep() {
  return (
    <div className="flex flex-col gap-6">
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground">Analizando tu estilo…</p>
        <Progress value={undefined} className="h-1.5 animate-pulse" />
      </div>

      <div className="space-y-3">
        {PIPELINE_STEPS.map((step) => (
          <div key={step} className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            <span>{step}</span>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        Esto suele tardar 2-4 minutos. Puedes cerrar esta ventana; te avisamos cuando termine. El
        estilo anterior sigue activo hasta que actives el nuevo.
      </p>
    </div>
  );
}

// ── Quality Gauge (B4+B5) ─────────────────────────────────────────────────────

const TIER_STYLES: Record<
  CloneDryRunResult["quality_tier"],
  { label: string; barClass: string; textClass: string }
> = {
  insufficient: {
    label: "Insuficiente",
    barClass: "bg-destructive",
    textClass: "text-destructive",
  },
  basic: {
    label: "Básico",
    barClass: "bg-amber-500",
    textClass: "text-amber-700 dark:text-amber-400",
  },
  decent: {
    label: "Decente",
    barClass: "bg-emerald-500",
    textClass: "text-emerald-700 dark:text-emerald-400",
  },
  strong: {
    label: "Alta fidelidad",
    barClass: "bg-primary",
    textClass: "text-primary",
  },
};

const CONTEXT_LABELS: Record<string, string> = {
  greeting: "Saludo",
  price: "Precio",
  objection: "Objeción",
  closing: "Cierre",
  follow_up: "Follow-up",
};

function QualityGauge({ gauge }: { gauge: CloneDryRunResult }) {
  const tier = TIER_STYLES[gauge.quality_tier];
  const pct = Math.round(gauge.quality_score * 100);
  return (
    <div className="space-y-3 rounded-lg border border-border bg-card/50 p-4 text-sm">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Calidad del clon
          </p>
          <p className={`text-base font-semibold ${tier.textClass}`}>
            {tier.label} · {gauge.message_count} mensaje{gauge.message_count === 1 ? "" : "s"}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Formato</p>
          <p className="font-medium">{gauge.detected_format}</p>
        </div>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full transition-all ${tier.barClass}`}
          style={{ width: `${pct}%` }}
          aria-label={`Puntaje ${pct}%`}
        />
      </div>
      <div className="flex flex-wrap gap-2 text-xs">
        {Object.entries(gauge.contexts_detected).map(([ctx, count]) => {
          const covered = count > 0;
          return (
            <span
              key={ctx}
              className={`rounded-full px-2 py-0.5 ${
                covered
                  ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {covered ? "✓" : "·"} {CONTEXT_LABELS[ctx] ?? ctx} ({count})
            </span>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground">{gauge.recommendation}</p>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

/**
 * Three-step clone wizard accessed via `?view=clone` query param. Uses
 * `useReducer` for the state machine: material → analyzing (shown during the
 * pending mutation) → preview (profile is_active=false). The user reviews and
 * optionally activates the cloned profile.
 */
export function CloneWizardView() {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;

  const [state, dispatch] = useReducer(wizardReducer, initialState);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const clone = useClonePersonality();
  const activate = useActivateProfile();
  const simulate = useSimulatePersonality();
  const dryRun = useCloneDryRun();
  const [gauge, setGauge] = useState<CloneDryRunResult | null>(null);

  // Quality gauge: debounced parser-only inspection (<1s, no LLM) so the user
  // sees the tier (basic/decent/strong) BEFORE committing to the 2-4 minute
  // LangGraph pipeline. Skips when material is empty.
  useEffect(() => {
    if (state.step !== "material") return;
    const trimmed = state.text.trim();
    if (state.inputMode === "text" && !trimmed) {
      setGauge(null);
      return;
    }
    if (state.inputMode === "file" && !state.file) {
      setGauge(null);
      return;
    }
    const handle = setTimeout(() => {
      dryRun
        .mutateAsync({
          textInput: state.inputMode === "text" ? trimmed : undefined,
          file: state.inputMode === "file" ? (state.file ?? undefined) : undefined,
        })
        .then((r) => setGauge(r))
        .catch(() => setGauge(null));
    }, 600);
    return () => clearTimeout(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.text, state.file, state.inputMode, state.step]);

  // ── Paso 1 handlers ─────────────────────────────────────────────────────────

  const handleSubmitMaterial = async () => {
    if (!state.text.trim() && !state.file) return;
    dispatch({ type: "START_ANALYZING" });

    try {
      const profile = await clone.mutateAsync({
        textInput: state.inputMode === "text" ? state.text : undefined,
        file: state.inputMode === "file" ? (state.file ?? undefined) : undefined,
      });
      dispatch({ type: "SET_PREVIEW", payload: profile });
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "No pudimos analizar tu material. Intenta nuevamente en unos minutos.";
      dispatch({ type: "SET_ERROR", payload: message });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    dispatch({ type: "SET_FILE", payload: file });
  };

  // ── Paso 3 handlers ─────────────────────────────────────────────────────────

  const handleRegenerate = async () => {
    if (!state.profile) return;
    try {
      const result = await simulate.mutateAsync(state.profile.id);
      const exchanges: SampleExchange[] = result.responses.slice(0, 3).map((r) => ({
        context: r.context,
        other_message: r.prospect_message,
        author_response: r.agent_response,
      }));
      dispatch({ type: "SET_PREVIEW_EXCHANGES", payload: exchanges });
      toast.success("Ejemplos regenerados.");
    } catch {
      toast.error("(no pudimos generar una respuesta — revisa tu configuración)");
    }
  };

  const handleActivate = async () => {
    if (!state.profile) return;
    try {
      await activate.mutateAsync(state.profile.id);
      toast.success("Estilo activado.");
      router.push(`/${tenantId}/brand-studio/estilo`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error al activar.";
      toast.error(message);
    }
  };

  const handleDiscard = () => {
    dispatch({ type: "RESET" });
    router.push(`/${tenantId}/brand-studio/estilo`);
  };

  // ── Render ────────────────────────────────────────────────────────────────

  const hasMaterial =
    (state.inputMode === "text" && state.text.trim().length > 0) ||
    (state.inputMode === "file" && state.file !== null);
  // Block submit when the gauge says insufficient. Users with material that
  // hasn't been gauged yet still can submit (BE rejects on its own) — we
  // don't gate UX on the network round-trip.
  const canSubmit = hasMaterial && gauge?.quality_tier !== "insufficient";

  return (
    <div className="flex flex-col gap-6">
      <CommunicationStyleNav />

      <div className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight text-foreground">Clonar tu estilo</h2>
        <Stepper current={state.step} />
      </div>

      {/* ── Paso 1: Material ─────────────────────────────────────── */}
      {state.step === "material" && (
        <div className="flex flex-col gap-5">
          <p className="text-sm text-muted-foreground">¿Cómo quieres aportar tu material?</p>

          {/* Mode radio */}
          <div className="flex gap-4 text-sm">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="inputMode"
                value="text"
                checked={state.inputMode === "text"}
                onChange={() => dispatch({ type: "SET_INPUT_MODE", payload: "text" })}
                className="accent-primary"
              />
              Pegar texto
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="inputMode"
                value="file"
                checked={state.inputMode === "file"}
                onChange={() => dispatch({ type: "SET_INPUT_MODE", payload: "file" })}
                className="accent-primary"
              />
              Subir archivo
            </label>
          </div>

          {/* Text input */}
          {state.inputMode === "text" && (
            <div className="space-y-2">
              <Textarea
                value={state.text}
                onChange={(e) => dispatch({ type: "SET_TEXT", payload: e.target.value })}
                placeholder={
                  "Pega TUS conversaciones con leads — incluye tus mensajes y los del prospecto. " +
                  "Mejor: WhatsApp/IG/Telegram export sin editar.\n\n" +
                  "Mínimo 10 (clon básico) · 30+ (decente) · 100+ (alta fidelidad)\n" +
                  "Variedad importa: saludos, precios, objeciones, cierres, follow-ups."
                }
                rows={10}
                className="resize-y text-sm"
                aria-label="Material de texto para clonar estilo"
              />
              {state.text.trim().length > 0 && (
                <p className="text-xs text-muted-foreground">
                  {state.text.split("\n").filter((l) => l.trim().length > 0).length} líneas
                  detectadas
                </p>
              )}
            </div>
          )}

          {/* File input */}
          {state.inputMode === "file" && (
            <div className="space-y-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.json,.csv"
                onChange={handleFileChange}
                className="hidden"
                aria-label="Subir archivo de conversaciones"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex w-full flex-col items-center gap-3 rounded-xl border-2 border-dashed border-border bg-muted/20 px-6 py-10 text-sm text-muted-foreground transition-colors hover:border-primary/50 hover:bg-primary/5"
                aria-label="Seleccionar archivo de conversaciones"
              >
                <Upload className="h-6 w-6" aria-hidden />
                {state.file ? (
                  <span className="font-medium text-foreground">{state.file.name}</span>
                ) : (
                  <span>
                    Haz clic para seleccionar un archivo
                    <br />
                    <span className="text-xs">
                      WhatsApp .txt · Instagram DM .json · Telegram .json · .csv
                    </span>
                  </span>
                )}
              </button>
              {state.file && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => dispatch({ type: "SET_FILE", payload: null })}
                  className="gap-1 text-xs text-muted-foreground"
                >
                  <X className="h-3 w-3" aria-hidden />
                  Quitar archivo
                </Button>
              )}
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            Cantidad y diversidad importan. Pega <strong>tus mensajes Y los del lead</strong> —
            necesitamos ver la conversación completa. Cobertura ideal: saludo, precio, objeción,
            cierre y follow-up.
          </p>

          {gauge && <QualityGauge gauge={gauge} />}

          {state.error && (
            <p
              role="alert"
              className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2 text-sm text-destructive"
            >
              {state.error}
            </p>
          )}

          <div className="flex justify-between gap-3">
            <Button variant="ghost" size="sm" onClick={handleDiscard}>
              Cancelar
            </Button>
            <Button size="sm" disabled={!canSubmit} onClick={handleSubmitMaterial}>
              Analizar mi estilo →
            </Button>
          </div>
        </div>
      )}

      {/* ── Paso 2: Análisis ──────────────────────────────────────── */}
      {state.step === "analyzing" && <AnalyzingStep />}

      {/* ── Paso 3: Previa ────────────────────────────────────────── */}
      {state.step === "preview" && state.profile && (
        <div className="flex flex-col gap-6">
          <p className="text-sm font-medium text-foreground">Así habla tu estilo clonado</p>

          <DimensionsPanel profileId={state.profile.id} dimensions={state.profile.dimensions} />

          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Huella lingüística detectada
            </p>
            <FingerprintPanel patterns={state.profile.linguistic_patterns} />
          </div>

          {/* Sample exchanges preview */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Ejemplos generados con tu estilo
              </p>
              <Button
                size="sm"
                variant="ghost"
                onClick={handleRegenerate}
                disabled={simulate.isPending}
                className="h-7 gap-1 px-2 text-xs"
                aria-label="Regenerar ejemplos de conversación"
              >
                {simulate.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                ) : (
                  <RefreshCw className="h-3 w-3" aria-hidden />
                )}
                Regenerar ejemplos
              </Button>
            </div>
            <div className="space-y-3">
              {(state.previewExchanges ?? []).map((ex, idx) => (
                <div
                  key={`${ex.context}-${idx}`}
                  className="rounded-lg border border-border bg-card/50 p-4 space-y-2 text-[13px]"
                >
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Contexto: {ex.context}
                  </p>
                  <div className="space-y-1.5">
                    <div className="flex gap-2">
                      <span className="w-8 flex-shrink-0 text-xs font-medium text-muted-foreground">
                        Lead
                      </span>
                      <p className="text-foreground/80">{ex.other_message}</p>
                    </div>
                    <div className="flex gap-2">
                      <span className="w-8 flex-shrink-0 text-xs font-medium text-primary">Tú</span>
                      <p className="text-foreground">{ex.author_response}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-3 border-t border-border pt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDiscard}
              className="gap-1"
              aria-label="Descartar este estilo clonado"
            >
              ← Descartar
            </Button>
            <Button
              size="sm"
              onClick={handleActivate}
              disabled={activate.isPending}
              className="ml-auto"
              aria-label="Activar este estilo clonado"
            >
              {activate.isPending && (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" aria-hidden />
              )}
              Activar este estilo →
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
