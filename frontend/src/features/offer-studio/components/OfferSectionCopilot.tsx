"use client";

import { CheckCircle2, Loader2, Sparkles, TriangleAlert } from "lucide-react";
import { useContext, useEffect } from "react";
import { toast } from "sonner";

import { FormRuntimeContext } from "@/components/form-runtime/FormRuntimeContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { useOfferCopilot } from "../hooks/use-offer-copilot";

// ---------------------------------------------------------------------------
// Section → tools mapping (mirrors backend Sección: annotations)
// ---------------------------------------------------------------------------

interface ToolEntry {
  key: string;
  label: string;
  description: string;
}

const SECTION_TOOLS: Record<string, ToolEntry[]> = {
  identity: [
    {
      key: "adapt_from_brand_identity",
      label: "Adaptar desde Brand Studio",
      description: "Trae el nombre y SKU sugerido desde la identidad de tu marca.",
    },
  ],
  promise: [
    {
      key: "adapt_from_brand_narrative",
      label: "Generar desde narrativa",
      description: "Crea variantes de promesa a partir del StoryBrand de tu marca.",
    },
    {
      key: "rewrite_tones",
      label: "Reescribir en 3 tonos",
      description: "Reescribe tu promesa actual en registros formal, cercano y entusiasta.",
    },
    {
      key: "validate_preset_coherence",
      label: "Validar coherencia con preset",
      description: "Verifica que la promesa sea consistente con el tipo de oferta elegido.",
    },
  ],
  strategy: [
    {
      key: "reuse_brand_buyer_personas",
      label: "Reutilizar buyer personas",
      description: "Importa las buyer personas de la marca para definir la audiencia.",
    },
  ],
  pricing: [
    {
      key: "high_ticket_tiering_template",
      label: "Plantilla de 3 niveles",
      description: "Sugiere una estructura de tiers para ofertas de alto valor.",
    },
    {
      key: "recurring_billing_setup",
      label: "Configurar recurrencia",
      description: "Sugiere opciones de facturación recurrente para suscripciones.",
    },
    {
      key: "detect_currency_mismatch",
      label: "Detectar discrepancia de moneda",
      description: "Revisa si la moneda configurada coincide con la del tenant.",
    },
  ],
  location: [
    {
      key: "detect_hybrid_split",
      label: "Detectar modalidad híbrida",
      description:
        "Analiza la sección y sugiere cómo dividir componentes presenciales y virtuales.",
    },
  ],
  testimonials: [
    {
      key: "import_from_brand_vault",
      label: "Importar desde vault de marca",
      description: "Trae testimonios guardados en el Brand Studio.",
    },
    {
      key: "suggest_missing_objections",
      label: "Sugerir objeciones faltantes",
      description: "Identifica objeciones comunes que aún no están cubiertas.",
    },
  ],
  faq: [
    {
      key: "generate_from_preset_flags",
      label: "Generar desde flags del preset",
      description: "Crea FAQs alineadas con el tipo de oferta que configuraste.",
    },
    {
      key: "pull_sales_agent_common_questions",
      label: "Traer preguntas del agente",
      description: "Extrae las preguntas más frecuentes de tus leads.",
    },
  ],
  value_stack: [
    {
      key: "assemble_from_brand_authority",
      label: "Ensamblar desde autoridad de marca",
      description: "Construye el value stack con los activos de autoridad del Brand Studio.",
    },
  ],
  instructors: [
    {
      key: "reuse_brand_team",
      label: "Reutilizar equipo de marca",
      description: "Importa los miembros del equipo definidos en Brand Studio como instructores.",
    },
  ],
};

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface OfferSectionCopilotProps {
  offerId: string;
  sectionSlug: string;
  editionCode?: string;
  /**
   * Called with the draft fields when the user clicks "Aplicar al formulario".
   * When the component is rendered inside a ``FormRuntimeProvider``, fields
   * are also patched via ``setFieldValue`` from context — no manual wiring
   * needed. The callback is still called so callers can react (e.g. scroll,
   * show a toast, trigger a save).
   */
  onApplyDraft: (draftFields: Record<string, unknown>) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ToolCardProps {
  tool: ToolEntry;
  isInvoking: boolean;
  onApply: (toolKey: string) => void;
}

function ToolCard({ tool, isInvoking, onApply }: ToolCardProps) {
  return (
    <div className="rounded-lg border bg-card p-3 shadow-sm">
      <div className="mb-1 flex items-start gap-2">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
        <span className="text-sm font-medium leading-tight">{tool.label}</span>
      </div>
      <p className="mb-3 text-xs leading-relaxed text-muted-foreground">{tool.description}</p>
      <Button
        size="sm"
        variant="outline"
        className="w-full text-xs"
        disabled={isInvoking}
        onClick={() => onApply(tool.key)}
        aria-label="Aplicar sugerencia"
      >
        {isInvoking ? (
          <span className="flex items-center gap-1.5" aria-label="Procesando sugerencia">
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
            Procesando…
          </span>
        ) : (
          "Aplicar sugerencia"
        )}
      </Button>
    </div>
  );
}

interface DraftPreviewProps {
  suggestions: string[];
  confidence: number;
  onApplyToForm: () => void;
}

function DraftPreview({ suggestions, confidence, onApplyToForm }: DraftPreviewProps) {
  const confidencePct = Math.round(confidence * 100);

  return (
    <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-4 w-4 text-primary" aria-hidden />
          <span className="text-sm font-medium">Borrador listo</span>
        </div>
        <Badge variant="secondary" className="text-xs">
          {confidencePct}%
        </Badge>
      </div>

      {suggestions.length > 0 && (
        <ul className="mb-3 space-y-1">
          {suggestions.map((s, i) => (
            <li key={i} className="text-xs leading-relaxed text-muted-foreground">
              • {s}
            </li>
          ))}
        </ul>
      )}

      <Button
        size="sm"
        className="w-full text-xs"
        onClick={onApplyToForm}
        aria-label="Aplicar al formulario"
      >
        Aplicar al formulario
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 * Copilot sidebar panel for a single offer section.
 *
 * Renders tool cards mapped to ``sectionSlug``. Each card invokes the
 * backend via ``useOfferCopilot``. When a result arrives, it shows a draft
 * preview. The user applies the draft via the "Aplicar al formulario" button.
 *
 * When rendered inside a ``FormRuntimeProvider``, draft fields are patched
 * into the form via ``setFieldValue`` from context. The ``onApplyDraft``
 * callback is always invoked afterward for caller-side coordination.
 *
 * This component never writes to the backend (Decision R3 — no write-through).
 */
export function OfferSectionCopilot({
  offerId,
  sectionSlug,
  editionCode,
  onApplyDraft,
  className,
}: OfferSectionCopilotProps) {
  const { invokeTool, isInvoking, lastResult, lastError } = useOfferCopilot({
    offerId,
    sectionSlug,
    editionCode,
  });

  // Optional: patch form fields directly when inside a FormRuntimeProvider.
  const formRuntime = useContext(FormRuntimeContext);

  const tools = SECTION_TOOLS[sectionSlug] ?? [];

  // Show toast on error
  useEffect(() => {
    if (lastError) {
      toast.error(`Error del copiloto: ${lastError.message}`);
    }
  }, [lastError]);

  const handleInvoke = async (toolKey: string) => {
    await invokeTool(toolKey);
  };

  const handleApplyToForm = () => {
    if (!lastResult?.draftFields) return;

    const draft = lastResult.draftFields;

    // Patch into form runtime when available (integrated mode)
    if (formRuntime) {
      Object.entries(draft).forEach(([path, value]) => {
        formRuntime.setFieldValue(path, value);
      });
    }

    // Always call the external callback so callers can react
    onApplyDraft(draft);
  };

  return (
    <div className={cn("flex h-full flex-col", className)}>
      {/* Header */}
      <div className="flex items-center gap-2 border-b px-4 py-3">
        <Sparkles className="h-4 w-4 text-primary" aria-hidden />
        <span className="text-sm font-semibold">Copiloto</span>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-3 p-4">
          {/* Empty state */}
          {tools.length === 0 && (
            <div className="flex flex-col items-center gap-2 py-8 text-center">
              <TriangleAlert className="h-6 w-6 text-muted-foreground" aria-hidden />
              <p className="text-sm text-muted-foreground">
                No hay sugerencias disponibles para esta sección.
              </p>
            </div>
          )}

          {/* Tool cards + draft preview */}
          {tools.length > 0 && (
            <>
              {isInvoking ? (
                <div className="space-y-3" aria-label="Procesando sugerencia">
                  {tools.map((t) => (
                    <Skeleton key={t.key} className="h-24 w-full rounded-lg" />
                  ))}
                </div>
              ) : (
                tools.map((t) => (
                  <ToolCard key={t.key} tool={t} isInvoking={isInvoking} onApply={handleInvoke} />
                ))
              )}

              {lastResult && !isInvoking && (
                <>
                  <Separator />
                  <DraftPreview
                    suggestions={lastResult.suggestions}
                    confidence={lastResult.confidence}
                    onApplyToForm={handleApplyToForm}
                  />
                </>
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
