"use client";

import { useFormRuntime } from "@/components/form-runtime";
import { getContrastColor } from "@/lib/utils/colors";

import type { BrandVisuals } from "@/features/brand-studio/types";
import type { ActionComponentProps } from "@/lib/form-runtime/actions";

const DEFAULT_FONT_STACK = "sans-serif";

function Swatch({ color, label }: { color: string; label: string }) {
  const textColor = getContrastColor(color);
  return (
    <div className="flex items-center gap-2">
      <div
        aria-hidden
        className="h-6 w-6 rounded border border-border"
        style={{ backgroundColor: color, color: textColor }}
      />
      <div className="font-mono text-xs text-muted-foreground">{label}</div>
      <div className="font-mono text-xs">{color}</div>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <div className="h-6 w-6 rounded border border-dashed border-border" aria-hidden />
      <span>
        {label} <span className="italic">sin definir</span>
      </span>
    </div>
  );
}

/**
 * ThemeInjector action — live preview card for the active BrandVisuals
 * (colors + fonts). No global CSS injection: the preview uses inline `style`
 * on the headline/body samples. A future Sprint 3 layout-level injector can
 * hoist the brand theme to the whole brand-studio route tree with proper
 * sanitization of user-provided tokens.
 *
 * Reads the full BrandVisuals slice from `useFormRuntime()` — the action
 * lives inside a FormRuntimeProvider whose `values` is the visuals slice
 * by construction.
 */
export function ThemeInjectorAction(_props: ActionComponentProps) {
  const { values } = useFormRuntime();
  const visuals = values as unknown as BrandVisuals;

  const primary = visuals.primary_color ?? null;
  const secondary = visuals.secondary_color ?? null;
  const accent = visuals.accent_color ?? null;
  const fontHeading = visuals.font_heading ?? DEFAULT_FONT_STACK;
  const fontBody = visuals.font_body ?? DEFAULT_FONT_STACK;

  return (
    <div className="space-y-4 rounded-lg border border-border bg-background p-4">
      <section className="space-y-2" aria-label="Paleta activa">
        <h3 className="text-sm font-medium">Paleta</h3>
        {primary ? <Swatch color={primary} label="Primario" /> : <Empty label="Primario" />}
        {secondary ? <Swatch color={secondary} label="Secundario" /> : <Empty label="Secundario" />}
        {accent ? <Swatch color={accent} label="Acento" /> : <Empty label="Acento" />}
      </section>

      <section className="space-y-2" aria-label="Tipografía activa">
        <h3 className="text-sm font-medium">Tipografía</h3>
        <div className="text-lg" style={{ fontFamily: `${fontHeading}, ${DEFAULT_FONT_STACK}` }}>
          Titulares · {fontHeading}
        </div>
        <div className="text-sm" style={{ fontFamily: `${fontBody}, ${DEFAULT_FONT_STACK}` }}>
          Cuerpo · {fontBody}
        </div>
      </section>

      <p className="text-xs text-muted-foreground">
        Editá colores y tipografías en los campos de arriba; la vista previa se actualiza
        automáticamente.
      </p>
    </div>
  );
}
