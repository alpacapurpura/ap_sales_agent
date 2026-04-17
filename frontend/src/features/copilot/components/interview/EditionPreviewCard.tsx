"use client";

import { cn } from "@/lib/utils";

export interface EditionPreviewCardProps {
  /** Edition number to display (defaults to 1 for the first edition). */
  editionNumber?: number;
  /** Tentative start date (null / undefined = "skip" path). */
  startDate: Date | string | null;
  /** Estimated capacity carried over from interview context. */
  capacity?: number;
  /** Noun shown in the title — "cohorte", "salida", "convocatoria", etc. */
  editionNoun?: string;
}

function toDate(value: Date | string | null): Date | null {
  if (!value) return null;
  if (value instanceof Date) return value;
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? null : parsed;
}

function formatFullDate(date: Date): string {
  return date.toLocaleDateString("es-PE", {
    weekday: "short",
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

/**
 * Live preview of the edition that will be created when the interview
 * closes. When `startDate` is set the card renders the "Próxima + Pública"
 * style (solid blue ring); when null it shows the DRAFT "Se publicará"
 * amber dashed style matching the prototype at
 * `prototype/copilot/interview-date.html`.
 */
export function EditionPreviewCard({
  editionNumber = 1,
  startDate,
  capacity = 50,
  editionNoun = "Edición",
}: EditionPreviewCardProps) {
  const resolved = toDate(startDate);
  const isDraft = resolved === null;

  return (
    <div
      className={cn(
        "rounded-xl bg-background p-4",
        isDraft
          ? "border-2 border-dashed border-amber-300"
          : "border border-blue-200 ring-1 ring-blue-100",
      )}
      role="article"
      aria-label={`Vista previa de ${editionNoun} #${editionNumber}`}
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold">
          {editionNoun} #{editionNumber}
        </span>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
            isDraft ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700",
          )}
        >
          {isDraft ? "Se publicará" : "Próxima"}
        </span>
      </div>
      <dl className="space-y-2 text-xs text-muted-foreground">
        <Row label="Inicio">
          {resolved ? (
            <span className="text-foreground">{formatFullDate(resolved)}</span>
          ) : (
            <span className="font-medium text-amber-600">Pendiente de confirmar</span>
          )}
        </Row>
        <Row label="Capacidad">
          <span className="text-foreground">{capacity} estudiantes</span>
        </Row>
        <Row label="Visibilidad">
          <span
            className={cn(
              "rounded-full px-2 py-0.5 text-[10px] font-semibold",
              isDraft ? "bg-muted text-muted-foreground" : "bg-purple-100 text-purple-700",
            )}
          >
            {isDraft ? "🔒 Privada" : "🌐 Pública"}
          </span>
        </Row>
      </dl>
      <p className="mt-3 border-t border-muted-foreground/10 pt-2 text-[11px] text-muted-foreground">
        {isDraft
          ? "Mientras no confirmes fecha, los leads interesados van a waitlist."
          : "Cuando confirmes, pasará a Próxima + Pública y el agente podrá venderla."}
      </p>
    </div>
  );
}

interface RowProps {
  label: string;
  children: React.ReactNode;
}

function Row({ label, children }: RowProps) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-muted-foreground">{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
