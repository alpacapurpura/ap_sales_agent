"use client";

import { HelpCircle } from "lucide-react";

import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

import type { FieldSchema } from "@/lib/form-runtime/schema";

export interface FieldLabelWithHelpProps {
  field: FieldSchema;
  htmlFor: string;
  className?: string;
}

/**
 * Label + icono de ayuda contextual para campos del form-runtime.
 *
 * Muestra el label con un icono HelpCircle que abre un Popover cuando
 * el campo tiene al menos uno de: hint, examples, formula, downstreamUses.
 * Si el campo no tiene ninguno de esos bloques de ayuda, solo muestra el label.
 */
export function FieldLabelWithHelp({ field, htmlFor, className }: FieldLabelWithHelpProps) {
  const hasHelp = Boolean(
    field.hint || field.examples?.length || field.formula || field.downstreamUses?.length,
  );

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <Label htmlFor={htmlFor} className="text-sm">
        {field.label}
        {field.required && <span className="ml-1 text-destructive">*</span>}
      </Label>

      {hasHelp && (
        <Popover>
          <PopoverTrigger asChild>
            <button
              type="button"
              aria-label={`Ayuda sobre ${field.label}`}
              className="inline-flex h-4 w-4 items-center justify-center rounded-full text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <HelpCircle className="h-3.5 w-3.5" />
            </button>
          </PopoverTrigger>

          <PopoverContent className="w-80 p-0" align="start">
            <div className="rounded-md border border-border bg-popover text-popover-foreground">
              {/* Header */}
              <div className="border-b border-border bg-primary/5 px-4 py-2.5">
                <p className="text-xs font-semibold text-foreground">{field.label}</p>
              </div>

              <div className="space-y-3 p-4">
                {/* Descripción / hint */}
                {field.hint && (
                  <p className="text-xs leading-relaxed text-muted-foreground">{field.hint}</p>
                )}

                {/* Fórmula sugerida */}
                {field.formula && (
                  <div>
                    <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-foreground">
                      Fórmula sugerida
                    </p>
                    <FormulaTemplate template={field.formula.template} />
                  </div>
                )}

                {/* Ejemplos */}
                {field.examples && field.examples.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-foreground">
                      Ejemplos
                    </p>
                    <ul className="space-y-2">
                      {field.examples.map((ex, i) => (
                        <li key={i} className="rounded-md border border-border bg-muted/40 p-2.5">
                          <p className="mb-0.5 text-[11px] font-medium text-foreground">
                            {ex.brand}
                          </p>
                          <p className="text-xs text-muted-foreground">{ex.text}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Dónde se usa */}
                {field.downstreamUses && field.downstreamUses.length > 0 && (
                  <div>
                    <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-foreground">
                      Dónde se usa
                    </p>
                    <ul className="space-y-1">
                      {field.downstreamUses.map((use, i) => (
                        <li
                          key={i}
                          className="flex items-center gap-1.5 text-xs text-muted-foreground"
                        >
                          <span className="h-1 w-1 rounded-full bg-primary/60 shrink-0" />
                          {use.href ? (
                            <a
                              href={use.href}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-foreground hover:underline"
                            >
                              {use.label}
                            </a>
                          ) : (
                            <span>{use.label}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}

FieldLabelWithHelp.displayName = "FieldLabelWithHelp";

/**
 * Renderiza la plantilla de fórmula reemplazando etiquetas <slot>...</slot>
 * con spans resaltados en text-primary font-medium.
 */
function FormulaTemplate({ template }: { template: string }) {
  // Split en slots preservando el contenido
  const parts = template.split(/(<slot>[^<]*<\/slot>)/g);

  return (
    <p className="rounded-md border border-border bg-muted/40 px-3 py-2 text-xs text-foreground leading-relaxed">
      {parts.map((part, i) => {
        const match = part.match(/^<slot>(.*)<\/slot>$/);
        if (match) {
          return (
            <span key={i} className="text-primary font-medium">
              {match[1]}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}
