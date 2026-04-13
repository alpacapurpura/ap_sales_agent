"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { PreviewSectionsProps } from "@/features/copilot/config/interview-preview-registry";

// ── Types ────────────────────────────────────────────────────────────────────

interface SectionConfig {
  key: string;
  label: string;
  fields: string[];
}

interface ObjectionData {
  type: string;
  trigger_phrases?: string[];
  strategy?: string;
  rebuttal?: string;
}

interface DeliverableData {
  name: string;
  format?: string;
  quantity?: string;
  value_stack_price?: number;
}

interface PricingData {
  label?: string;
  total_amount?: number;
  currency?: string;
  number_of_installments?: number;
  installment_amount?: number;
}

// ── Section definitions ──────────────────────────────────────────────────────

const SECTIONS: SectionConfig[] = [
  {
    key: "identity",
    label: "Identidad",
    fields: ["public_name", "archetype", "value_level", "delivery_model"],
  },
  {
    key: "strategy",
    label: "Estrategia",
    fields: ["primary_outcome", "time_to_value", "target_avatar_match"],
  },
  {
    key: "promise",
    label: "Promesa",
    fields: ["headline_promise", "primary_outcome", "time_to_value"],
  },
  {
    key: "psychology",
    label: "Psicolog\u00eda",
    fields: ["marketing_pain_points", "marketing_desires", "objections"],
  },
  {
    key: "pricing",
    label: "Pricing",
    fields: ["pricing_options", "guarantee_type", "guarantee_terms"],
  },
  {
    key: "value_stack",
    label: "Value Stack",
    fields: ["deliverables"],
  },
  {
    key: "closing",
    label: "Cierre",
    fields: [
      "guarantee_type",
      "guarantee_terms",
      "onboarding_action",
      "checkout_page_url",
    ],
  },
];

// ── Block to section mapping ─────────────────────────────────────────────────

const BLOCK_TO_SECTION: Record<string, string> = {
  identity: "identity",
  strategy: "strategy",
  promise: "promise",
  psychology: "psychology",
  pricing: "pricing",
  value_stack: "value_stack",
  closing: "closing",
  // Also map possible alternative block names
  identidad: "identity",
  estrategia: "strategy",
  promesa: "promise",
  psicologia: "psychology",
  cierre: "closing",
};

// ── Guarantee display names ──────────────────────────────────────────────────

const GUARANTEE_LABELS: Record<string, string> = {
  none: "Sin garant\u00eda",
  conditional_action_based: "Condicional (basada en acci\u00f3n)",
  unconditional_30_day: "Incondicional 30 d\u00edas",
  double_money_back: "Doble devoluci\u00f3n",
  satisfaction_or_free_work: "Satisfacci\u00f3n o trabajo gratis",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function computeSectionProgress(
  data: Record<string, unknown>,
  fields: string[]
): number {
  if (fields.length === 0) return 0;
  let filled = 0;
  for (const field of fields) {
    const val = data[field];
    if (val === undefined || val === null || val === "") continue;
    if (Array.isArray(val) && val.length === 0) continue;
    filled++;
  }
  return Math.round((filled / fields.length) * 100);
}

function PendingText() {
  return (
    <span className="text-xs italic text-muted-foreground">Pendiente...</span>
  );
}

// ── Section content renderers ────────────────────────────────────────────────

function IdentityContent({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="space-y-2">
      <FieldRow label="Nombre" value={data.public_name as string} />
      <FieldRow label="Arquetipo" value={data.archetype as string} />
      <FieldRow label="Nivel de valor" value={data.value_level as string} />
      <FieldRow
        label="Modelo de entrega"
        value={data.delivery_model as string}
      />
    </div>
  );
}

function StrategyContent({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="space-y-2">
      <FieldRow
        label="Resultado principal"
        value={data.primary_outcome as string}
      />
      <FieldRow
        label="Tiempo al resultado"
        value={data.time_to_value as string}
      />
    </div>
  );
}

function PromiseContent({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="space-y-2">
      <FieldRow
        label="Promesa principal"
        value={data.headline_promise as string}
      />
      <FieldRow
        label="Resultado principal"
        value={data.primary_outcome as string}
      />
      <FieldRow
        label="Tiempo al resultado"
        value={data.time_to_value as string}
      />
    </div>
  );
}

function PsychologyContent({ data }: { data: Record<string, unknown> }) {
  const pains = (data.marketing_pain_points as string[]) ?? [];
  const desires = (data.marketing_desires as string[]) ?? [];
  const objections = (data.objections as ObjectionData[]) ?? [];

  return (
    <div className="space-y-3">
      {/* Pains */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">
          Dolores
        </p>
        {pains.length > 0 ? (
          <div className="space-y-1">
            {pains.map((pain, i) => (
              <div
                key={i}
                className="rounded-md border border-red-500/30 bg-red-500/5 px-2.5 py-1.5 text-xs text-foreground"
              >
                {pain}
              </div>
            ))}
          </div>
        ) : (
          <PendingText />
        )}
      </div>

      {/* Desires */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">
          Deseos
        </p>
        {desires.length > 0 ? (
          <div className="space-y-1">
            {desires.map((desire, i) => (
              <div
                key={i}
                className="rounded-md border border-green-500/30 bg-green-500/5 px-2.5 py-1.5 text-xs text-foreground"
              >
                {desire}
              </div>
            ))}
          </div>
        ) : (
          <PendingText />
        )}
      </div>

      {/* Objections */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">
          Objeciones
        </p>
        {objections.length > 0 ? (
          <div className="space-y-1">
            {objections.map((obj, i) => (
              <div
                key={i}
                className="rounded-md border border-amber-500/30 bg-amber-500/5 px-2.5 py-1.5 text-xs text-foreground"
              >
                <span className="font-medium">
                  {obj.trigger_phrases?.[0] ?? obj.type}
                </span>
                {obj.rebuttal && (
                  <p className="mt-0.5 text-muted-foreground">{obj.rebuttal}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <PendingText />
        )}
      </div>
    </div>
  );
}

function PricingContent({ data }: { data: Record<string, unknown> }) {
  const pricing = (data.pricing_options as PricingData[]) ?? [];
  const guaranteeType = data.guarantee_type as string | undefined;
  const guaranteeTerms = data.guarantee_terms as string | undefined;

  return (
    <div className="space-y-3">
      {/* Pricing options */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1.5">
          Opciones de precio
        </p>
        {pricing.length > 0 ? (
          <div className="space-y-1.5">
            {pricing.map((opt, i) => (
              <div
                key={i}
                className="rounded-md border border-white/10 bg-white/5 px-2.5 py-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">
                    {opt.label ?? "Plan"}
                  </span>
                  <span className="font-bold text-foreground">
                    {opt.currency ?? "USD"}{" "}
                    {opt.total_amount?.toLocaleString() ?? "0"}
                  </span>
                </div>
                {(opt.number_of_installments ?? 0) > 1 && (
                  <p className="mt-0.5 text-muted-foreground">
                    {opt.number_of_installments} cuotas de{" "}
                    {opt.currency ?? "USD"} {opt.installment_amount}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <PendingText />
        )}
      </div>

      {/* Guarantee */}
      <div>
        <p className="text-xs font-medium text-muted-foreground mb-1">
          Garant\u00eda
        </p>
        {guaranteeType ? (
          <p className="text-xs text-foreground">
            {GUARANTEE_LABELS[guaranteeType] ?? guaranteeType}
            {guaranteeTerms && (
              <span className="text-muted-foreground">
                {" "}
                - {guaranteeTerms}
              </span>
            )}
          </p>
        ) : (
          <PendingText />
        )}
      </div>
    </div>
  );
}

function ValueStackContent({ data }: { data: Record<string, unknown> }) {
  const deliverables = (data.deliverables as DeliverableData[]) ?? [];

  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground mb-1.5">
        Entregables
      </p>
      {deliverables.length > 0 ? (
        <div className="space-y-1">
          {deliverables.map((del, i) => (
            <div
              key={i}
              className="flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs"
            >
              <span className="text-green-400">&#10003;</span>
              <span className="flex-1 text-foreground">{del.name}</span>
              {del.value_stack_price !== undefined &&
                del.value_stack_price > 0 && (
                  <span className="text-muted-foreground">
                    ${del.value_stack_price}
                  </span>
                )}
            </div>
          ))}
        </div>
      ) : (
        <PendingText />
      )}
    </div>
  );
}

function ClosingContent({ data }: { data: Record<string, unknown> }) {
  const guaranteeType = data.guarantee_type as string | undefined;
  const onboardingAction = data.onboarding_action as string | undefined;
  const checkoutUrl = data.checkout_page_url as string | undefined;

  return (
    <div className="space-y-2">
      <FieldRow
        label="Garant\u00eda"
        value={
          guaranteeType
            ? GUARANTEE_LABELS[guaranteeType] ?? guaranteeType
            : undefined
        }
      />
      <FieldRow label="Onboarding" value={onboardingAction} />
      <FieldRow label="Checkout URL" value={checkoutUrl} />
    </div>
  );
}

// ── Shared field row ─────────────────────────────────────────────────────────

function FieldRow({
  label,
  value,
}: {
  label: string;
  value: string | undefined | null;
}) {
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {value ? (
        <p className="text-xs text-foreground">{value}</p>
      ) : (
        <PendingText />
      )}
    </div>
  );
}

// ── Section renderer ─────────────────────────────────────────────────────────

function SectionContent({
  sectionKey,
  data,
}: {
  sectionKey: string;
  data: Record<string, unknown>;
}) {
  switch (sectionKey) {
    case "identity":
      return <IdentityContent data={data} />;
    case "strategy":
      return <StrategyContent data={data} />;
    case "promise":
      return <PromiseContent data={data} />;
    case "psychology":
      return <PsychologyContent data={data} />;
    case "pricing":
      return <PricingContent data={data} />;
    case "value_stack":
      return <ValueStackContent data={data} />;
    case "closing":
      return <ClosingContent data={data} />;
    default:
      return null;
  }
}

// ── Main component ───────────────────────────────────────────────────────────

export function OfferPreviewSections({
  data,
  currentBlock,
  blocksCompleted,
}: PreviewSectionsProps) {
  const activeSection = BLOCK_TO_SECTION[currentBlock] ?? currentBlock;

  const completedSet = useMemo(
    () => new Set(blocksCompleted.map((b) => BLOCK_TO_SECTION[b] ?? b)),
    [blocksCompleted]
  );

  return (
    <div className="flex-1 overflow-hidden">
      <ScrollArea className="h-full">
        <div className="space-y-3 p-4">
          {SECTIONS.map((section) => {
            const isActive = activeSection === section.key;
            const isCompleted = completedSet.has(section.key);
            const progress = computeSectionProgress(data, section.fields);

            return (
              <div
                key={section.key}
                data-section={section.key}
                className={cn(
                  "rounded-lg border border-white/10 bg-white/[0.02] p-3 transition-all",
                  isActive && "ring-1 ring-orange-500/50 border-orange-500/30",
                  isCompleted && "border-green-500/20"
                )}
              >
                {/* Section header */}
                <div className="flex items-center justify-between mb-2">
                  <h4
                    className={cn(
                      "text-xs font-semibold",
                      isActive
                        ? "text-orange-400"
                        : isCompleted
                          ? "text-green-400"
                          : "text-muted-foreground"
                    )}
                  >
                    {section.label}
                  </h4>
                  <span className="text-[10px] text-muted-foreground">
                    {progress}%
                  </span>
                </div>

                {/* Progress bar */}
                <Progress
                  value={progress}
                  className="h-1 mb-2"
                  indicatorClassName={cn(
                    isActive
                      ? "bg-orange-500"
                      : isCompleted
                        ? "bg-green-500"
                        : "bg-muted-foreground/30"
                  )}
                />

                {/* Section content */}
                <SectionContent sectionKey={section.key} data={data} />
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
