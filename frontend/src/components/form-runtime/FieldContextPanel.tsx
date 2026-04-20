"use client";

import { ChevronDown, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { cn } from "@/lib/utils";

import { useFormRuntime } from "./FormRuntimeContext";

import type {
  FieldDownstreamUse,
  FieldFormulaHint,
  FieldLengthHint,
  FieldRelated,
  FieldSchema,
  FieldSwipeExample,
} from "@/lib/form-runtime/schema";

const STORAGE_KEY = "brand-studio.reco-expanded";

export interface FieldContextPanelProps {
  activeFieldId: string | null;
  className?: string;
}

interface BlockMeta {
  key: string;
  title: string;
  tag: string;
  emphasis?: boolean;
  body: React.ReactNode;
}

/**
 * Recommendations panel mounted BELOW the editor. Collapsible — persists
 * expanded state per-user in localStorage so toggling once is enough.
 * Renders only the blocks that carry data; the AiHint block is always
 * available so the copilot can suggest even on fully-authored fields.
 */
export function FieldContextPanel({ activeFieldId, className }: FieldContextPanelProps) {
  const [expanded, setExpanded] = useState<boolean>(() => readExpanded());
  const { schema, values } = useFormRuntime();
  const field = useMemo(
    () => (activeFieldId ? (schema.fields.find((f) => f.id === activeFieldId) ?? null) : null),
    [activeFieldId, schema.fields],
  );

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(expanded));
    } catch {
      /* storage disabled — no-op */
    }
  }, [expanded]);

  const blocks = useMemo<BlockMeta[]>(
    () => (field ? buildBlocks(field, values[field.path]) : []),
    [field, values],
  );

  const toggle = useCallback(() => setExpanded((v) => !v), []);

  return (
    <section
      aria-label="Recomendaciones"
      className={cn(
        "flex shrink-0 flex-col overflow-hidden border-t border-border bg-muted/20",
        "transition-[max-height] duration-200 ease-out",
        expanded ? "max-h-[45%]" : "max-h-[var(--brand-reco-header-h)]",
        className,
      )}
    >
      <button
        type="button"
        onClick={toggle}
        aria-expanded={expanded}
        aria-label={expanded ? "Ocultar recomendaciones" : "Mostrar recomendaciones"}
        className={cn(
          "flex h-[var(--brand-reco-header-h)] shrink-0 items-center gap-3 px-6",
          "text-left transition-colors hover:bg-muted/30",
        )}
      >
        <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/40 bg-brand/[0.18] px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-[0.04em] text-brand">
          <Sparkles className="h-3 w-3" aria-hidden="true" />
          Recomendaciones
        </span>
        <span className="truncate text-xs italic text-muted-foreground">
          {blocks.length > 0
            ? `${blocks.length} ayudas disponibles · no obligatorias`
            : "No hay recomendaciones para este campo"}
        </span>
        <span className="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-[11px] text-muted-foreground">
          {blocks.length}
        </span>
        <span className="ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-muted-foreground">
          <span>{expanded ? "Ocultar" : "Mostrar"}</span>
          <ChevronDown
            className={cn("h-3 w-3 transition-transform", expanded && "rotate-180")}
            aria-hidden="true"
          />
        </span>
      </button>

      {expanded && (
        <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-1">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {blocks.map((block) => (
              <RecoBlock key={block.key} meta={block} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function readExpanded(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === null) return false;
    return JSON.parse(raw) === true;
  } catch {
    return false;
  }
}

function RecoBlock({ meta }: { meta: BlockMeta }) {
  return (
    <article
      className={cn(
        "rounded-lg border border-border bg-background p-4",
        meta.emphasis && "border-brand/35 bg-brand/[0.06]",
      )}
    >
      <header className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        <span>{meta.title}</span>
        <span className="ml-auto rounded border border-border px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-[0.06em] text-muted-foreground">
          {meta.tag}
        </span>
      </header>
      {meta.body}
    </article>
  );
}

function buildBlocks(field: FieldSchema, currentValue: unknown): BlockMeta[] {
  const blocks: BlockMeta[] = [];

  if (field.formula) {
    blocks.push({
      key: "formula",
      title: "Fórmula",
      tag: "Guía",
      body: <FormulaBlock formula={field.formula} />,
    });
  }

  if (field.examples && field.examples.length > 0) {
    blocks.push({
      key: "examples",
      title: "Ejemplos de referencia",
      tag: "Swipe file",
      body: <SwipeBlock items={field.examples} />,
    });
  }

  if (field.downstreamUses && field.downstreamUses.length > 0) {
    blocks.push({
      key: "downstream",
      title: "Dónde se usa",
      tag: "Trazabilidad",
      body: <DownstreamBlock items={field.downstreamUses} />,
    });
  }

  if (field.relatedFields && field.relatedFields.length > 0) {
    blocks.push({
      key: "related",
      title: "Campos relacionados",
      tag: "Contexto",
      body: <RelatedBlock items={field.relatedFields} />,
    });
  }

  blocks.push({
    key: "metadata",
    title: "Metadata",
    tag: "Histórico",
    body: <MetadataBlock value={currentValue} lengthHint={field.lengthHint} />,
  });

  return blocks;
}

function FormulaBlock({ formula }: { formula: FieldFormulaHint }) {
  return (
    <div
      className="text-[13px] leading-relaxed text-muted-foreground [&_.reco-slot]:rounded [&_.reco-slot]:bg-brand/20 [&_.reco-slot]:px-1.5 [&_.reco-slot]:text-xs [&_.reco-slot]:font-medium [&_.reco-slot]:text-brand [&_b]:font-medium [&_b]:text-foreground"
      dangerouslySetInnerHTML={{ __html: formula.template }}
    />
  );
}

function SwipeBlock({ items }: { items: FieldSwipeExample[] }) {
  return (
    <ul className="divide-y divide-dashed divide-border text-[13px] leading-relaxed text-muted-foreground">
      {items.map((item, index) => (
        <li key={`${item.brand}-${index}`} className="py-2 first:pt-0 last:pb-0">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.05em] text-brand">
            {item.brand}
          </p>
          <p>{item.text}</p>
        </li>
      ))}
    </ul>
  );
}

function DownstreamBlock({ items }: { items: FieldDownstreamUse[] }) {
  return (
    <ul className="flex flex-col gap-1">
      {items.map((item, index) => (
        <li
          key={`${item.label}-${index}`}
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:bg-muted/40 hover:text-foreground"
        >
          <span>{item.label}</span>
          {item.href && (
            <a
              href={item.href}
              className="ml-auto text-[11px] text-brand underline-offset-2 hover:underline"
            >
              Ver
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}

function RelatedBlock({ items }: { items: FieldRelated[] }) {
  return (
    <ul className="flex flex-col gap-1">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs text-muted-foreground"
        >
          <span>{item.label}</span>
        </li>
      ))}
    </ul>
  );
}

function MetadataBlock({
  value,
  lengthHint,
}: {
  value: unknown;
  lengthHint: FieldLengthHint | undefined;
}) {
  const chars = typeof value === "string" ? value.length : 0;
  const idealRange =
    lengthHint?.ideal?.length === 2 ? `ideal ${lengthHint.ideal[0]}–${lengthHint.ideal[1]}` : null;
  return (
    <dl className="flex flex-col gap-1 text-xs text-muted-foreground">
      <div className="flex justify-between">
        <dt>Longitud</dt>
        <dd className="text-foreground">
          {chars} {idealRange && <span className="text-muted-foreground">· {idealRange}</span>}
        </dd>
      </div>
    </dl>
  );
}
