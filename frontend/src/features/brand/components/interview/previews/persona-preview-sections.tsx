"use client";

import { forwardRef, useRef, useEffect } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import type { PreviewSectionsProps } from "@/features/copilot/config/interview-preview-registry";

// ── Section configuration ──────────────────────────────────────────────────

interface SectionConfig {
  key: string;
  label: string;
  /** Visual variant for item cards */
  variant?: "pain" | "desire" | "objection" | "default";
  /** How to extract items from the data */
  type: "key-value" | "list-items" | "list-strings";
}

const SECTIONS: SectionConfig[] = [
  { key: "demographics", label: "Demografía", type: "key-value" },
  { key: "psychographics", label: "Psicografía", type: "key-value" },
  { key: "pain_points", label: "Puntos de dolor", variant: "pain", type: "list-items" },
  { key: "desires", label: "Deseos", variant: "desire", type: "list-items" },
  { key: "objections", label: "Objeciones", variant: "objection", type: "list-items" },
  { key: "channels", label: "Canales", type: "list-strings" },
  { key: "journey", label: "Journey", type: "key-value" },
];

// ── Label maps for display ─────────────────────────────────────────────────

const DEMOGRAPHICS_LABELS: Record<string, string> = {
  age_range: "Edad",
  gender: "Género",
  location: "Ubicación",
  education: "Educación",
  income_level: "Nivel de ingreso",
  occupation: "Ocupación",
  marital_status: "Estado civil",
};

const PSYCHOGRAPHICS_LABELS: Record<string, string> = {
  values: "Valores",
  interests: "Intereses",
  personality: "Personalidad",
  lifestyle: "Estilo de vida",
  motivations: "Motivaciones",
  fears: "Miedos",
};

const JOURNEY_LABELS: Record<string, string> = {
  awareness: "Descubrimiento",
  consideration: "Consideración",
  decision: "Decisión",
  retention: "Retención",
  advocacy: "Promoción",
};

function getFieldLabel(sectionKey: string, fieldKey: string): string {
  if (sectionKey === "demographics") return DEMOGRAPHICS_LABELS[fieldKey] ?? fieldKey;
  if (sectionKey === "psychographics") return PSYCHOGRAPHICS_LABELS[fieldKey] ?? fieldKey;
  if (sectionKey === "journey") return JOURNEY_LABELS[fieldKey] ?? fieldKey;
  return fieldKey;
}

// ── Variant styles ─────────────────────────────────────────────────────────

const VARIANT_CLASSES: Record<string, string> = {
  pain: "bg-destructive/10 border-l-2 border-destructive",
  desire: "bg-green-500/10 border-l-2 border-green-500",
  objection: "bg-amber-500/10 border-l-2 border-amber-500",
  default: "bg-muted/30 border-l-2 border-muted-foreground/20",
};

// ── Item count helpers ─────────────────────────────────────────────────────

// eslint-disable-next-line sonarjs/cognitive-complexity -- TODO: split per field-type strategy
function countFilledFields(
  data: Record<string, unknown>,
  sectionKey: string,
  type: SectionConfig["type"],
): { filled: number; total: number } {
  const sectionData = data[sectionKey];

  if (type === "list-items") {
    const items = Array.isArray(sectionData) ? sectionData : [];
    return { filled: items.length, total: Math.max(items.length, 3) };
  }

  if (type === "list-strings") {
    const items = Array.isArray(sectionData) ? sectionData : [];
    return { filled: items.length, total: Math.max(items.length, 3) };
  }

  // key-value
  if (typeof sectionData === "object" && sectionData !== null && !Array.isArray(sectionData)) {
    const entries = Object.entries(sectionData as Record<string, unknown>);
    const filled = entries.filter(([, v]) => {
      if (v === null || v === undefined || v === "") return false;
      if (Array.isArray(v) && v.length === 0) return false;
      return true;
    }).length;
    const expectedFields =
      sectionKey === "demographics"
        ? Object.keys(DEMOGRAPHICS_LABELS).length
        : sectionKey === "psychographics"
          ? Object.keys(PSYCHOGRAPHICS_LABELS).length
          : sectionKey === "journey"
            ? Object.keys(JOURNEY_LABELS).length
            : entries.length;
    return { filled, total: Math.max(filled, expectedFields) };
  }

  return { filled: 0, total: 3 };
}

// ── Section renderers ──────────────────────────────────────────────────────

function KeyValueSection({
  data,
  sectionKey,
}: {
  data: Record<string, unknown>;
  sectionKey: string;
}) {
  const sectionData = data[sectionKey];

  if (typeof sectionData !== "object" || sectionData === null || Array.isArray(sectionData)) {
    return <EmptyPlaceholder />;
  }

  const entries = Object.entries(sectionData as Record<string, unknown>);
  if (entries.length === 0) return <EmptyPlaceholder />;

  return (
    <div className="space-y-1.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-2 text-xs">
          <span className="text-muted-foreground shrink-0 min-w-[90px]">
            {getFieldLabel(sectionKey, key)}:
          </span>
          <span className="text-foreground">{formatValue(value)}</span>
        </div>
      ))}
    </div>
  );
}

function ListItemsSection({
  data,
  sectionKey,
  variant,
}: {
  data: Record<string, unknown>;
  sectionKey: string;
  variant: string;
}) {
  const sectionData = data[sectionKey];
  const items = Array.isArray(sectionData) ? sectionData : [];

  if (items.length === 0) return <EmptyPlaceholder />;

  return (
    <div className="space-y-2">
      {items.map((item, idx) => {
        const description =
          typeof item === "object" && item !== null
            ? ((item as Record<string, unknown>).description as string)
            : String(item);

        return (
          <div
            key={`${sectionKey}-${idx}`}
            className={cn(
              "rounded-md px-3 py-2 text-xs text-foreground",
              VARIANT_CLASSES[variant] ?? VARIANT_CLASSES.default,
            )}
          >
            {description}
          </div>
        );
      })}
    </div>
  );
}

function ListStringsSection({
  data,
  sectionKey,
}: {
  data: Record<string, unknown>;
  sectionKey: string;
}) {
  const sectionData = data[sectionKey];
  const items = Array.isArray(sectionData) ? sectionData : [];

  if (items.length === 0) return <EmptyPlaceholder />;

  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, idx) => (
        <span
          key={`${sectionKey}-${idx}`}
          className="rounded-full bg-muted/50 px-2.5 py-1 text-xs text-foreground"
        >
          {String(item)}
        </span>
      ))}
    </div>
  );
}

function EmptyPlaceholder() {
  return <span className="text-xs italic text-muted-foreground">Pendiente...</span>;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

// ── Main component ─────────────────────────────────────────────────────────

export const PersonaPreviewSections = forwardRef<HTMLDivElement, PreviewSectionsProps>(
  ({ data, currentBlock, blocksCompleted: _blocksCompleted, ...props }, ref) => {
    const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

    // Auto-scroll to active section when currentBlock changes
    useEffect(() => {
      if (!currentBlock) return;
      const el = sectionRefs.current[currentBlock];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, [currentBlock]);

    return (
      <div ref={ref} className="flex-1 overflow-hidden" {...props}>
        <ScrollArea className="h-full">
          <div className="space-y-4 p-4">
            {SECTIONS.map((section) => {
              const isActive = currentBlock === section.key;
              const { filled, total } = countFilledFields(data, section.key, section.type);

              return (
                <div
                  key={section.key}
                  ref={(el) => {
                    sectionRefs.current[section.key] = el;
                  }}
                  className={cn(
                    "rounded-lg border p-3 transition-colors",
                    isActive ? "border-purple-500/50 bg-purple-500/5" : "border-white/5 bg-card/50",
                  )}
                >
                  {/* Section header */}
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-semibold text-foreground">{section.label}</h4>
                    <span className="text-[10px] text-muted-foreground">
                      {filled}/{total}
                    </span>
                  </div>

                  {/* Section content */}
                  {section.type === "key-value" && (
                    <KeyValueSection data={data} sectionKey={section.key} />
                  )}
                  {section.type === "list-items" && (
                    <ListItemsSection
                      data={data}
                      sectionKey={section.key}
                      variant={section.variant ?? "default"}
                    />
                  )}
                  {section.type === "list-strings" && (
                    <ListStringsSection data={data} sectionKey={section.key} />
                  )}
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </div>
    );
  },
);

PersonaPreviewSections.displayName = "PersonaPreviewSections";
