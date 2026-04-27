"use client";

/**
 * ProposalValuePreview — type-aware renderer for ProposalUpdate.new_value.
 *
 * Backend ``extract_document_to_fields`` (and ``propose_field_updates``)
 * emit raw values matching the field's schema type:
 *   - string  → plain text/textarea
 *   - number  → integer/float
 *   - boolean → checkbox-like
 *   - object  → structured fields (e.g. one pain_point row)
 *   - array   → list (of strings or of objects)
 *
 * Pre-fix the tool JSON-stringified everything so the card showed
 * `[{\"description\":\"X\",\"severity\":5}, ...]` literally and the
 * bridge.patchField forwarded a string for an array field — schema
 * validation rejected it. Now ``new_value`` is the raw shape end-to-end
 * and this component renders it structurally so users read meaningful
 * previews.
 */

interface ProposalValuePreviewProps {
  value: unknown;
}

/** Renders a ProposalUpdate.new_value structurally according to its runtime type. */
export function ProposalValuePreview({ value }: ProposalValuePreviewProps) {
  if (value === null || value === undefined || value === "") {
    return <span className="italic text-slate-400">— vacío —</span>;
  }

  if (typeof value === "string") {
    return <span className="whitespace-pre-wrap break-words">{value}</span>;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return <span>{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="italic text-slate-400">— sin elementos —</span>;
    }
    return (
      <ul className="ml-3 list-disc space-y-1.5">
        {value.map((item, idx) => (
          <li key={idx} className="break-words">
            {renderItem(item)}
          </li>
        ))}
      </ul>
    );
  }

  if (typeof value === "object") {
    return <ObjectPreview obj={value as Record<string, unknown>} />;
  }

  return <span className="break-words">{JSON.stringify(value)}</span>;
}

function renderItem(item: unknown): React.ReactNode {
  if (typeof item === "string") return item;
  if (typeof item === "number" || typeof item === "boolean") return String(item);
  if (item && typeof item === "object") {
    return <ObjectPreview obj={item as Record<string, unknown>} compact />;
  }
  return JSON.stringify(item);
}

interface ObjectPreviewProps {
  obj: Record<string, unknown>;
  /** When true, render inline-style for use inside a list item. */
  compact?: boolean;
}

function ObjectPreview({ obj, compact = false }: ObjectPreviewProps) {
  const entries = Object.entries(obj).filter(([, v]) => v !== null && v !== undefined && v !== "");
  if (entries.length === 0) {
    return <span className="italic text-slate-400">— sin datos —</span>;
  }

  // For pain_points / desires shape ({description, severity}) we surface
  // ``description`` as the line and badge any severity-like number.
  const description = pickPrimaryText(obj);
  const severity = pickSeverity(obj);

  if (description && compact) {
    return (
      <span className="flex flex-wrap items-baseline gap-1.5">
        <span className="break-words">{description}</span>
        {severity !== null && (
          <span className="rounded bg-slate-200 px-1 py-px text-[10px] font-medium uppercase tracking-wide text-slate-700 dark:bg-slate-700 dark:text-slate-200">
            {formatSeverity(severity)}
          </span>
        )}
      </span>
    );
  }

  return (
    <dl className={compact ? "" : "space-y-0.5 text-xs"}>
      {entries.map(([key, val]) => (
        <div key={key} className="flex gap-1.5">
          <dt className="shrink-0 font-medium text-slate-500 dark:text-slate-400">
            {humanizeKey(key)}:
          </dt>
          <dd className="break-words text-slate-700 dark:text-slate-300">{renderItem(val)}</dd>
        </div>
      ))}
    </dl>
  );
}

function pickPrimaryText(obj: Record<string, unknown>): string | null {
  for (const key of ["description", "title", "name", "label", "text", "value"]) {
    const v = obj[key];
    if (typeof v === "string" && v.trim() !== "") return v;
  }
  return null;
}

function pickSeverity(obj: Record<string, unknown>): number | null {
  const candidates = ["severity", "intensity", "priority", "score"];
  for (const key of candidates) {
    const v = obj[key];
    if (typeof v === "number") return v;
  }
  return null;
}

function formatSeverity(n: number): string {
  if (n >= 1 && n <= 5 && Number.isInteger(n)) return `${n}/5`;
  return String(n);
}

function humanizeKey(key: string): string {
  return key.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
}
