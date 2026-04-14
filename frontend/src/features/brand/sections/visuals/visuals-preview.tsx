import { BrandVisuals } from "@/features/brand/types";
import { Palette, Type, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

interface VisualsSectionProps {
  visuals: BrandVisuals;
  onEdit: () => void;
  onExtract: () => void;
}

// Extracted to module scope for ESLint react-hooks/static-components
function ColorSwatch({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex flex-col gap-2 group/swatch">
      <div
        className="h-16 w-full rounded-lg shadow-sm border border-border/10 ring-1 ring-border/5 transition-transform group-hover/swatch:scale-105"
        style={{ backgroundColor: color }}
      />
      <div className="flex justify-between items-center">
        <span className="text-xs text-muted-foreground font-medium">{label}</span>
        <span className="text-[10px] text-muted-foreground font-mono uppercase opacity-50">
          {color}
        </span>
      </div>
    </div>
  );
}

function SmallSwatch({ color }: { color: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className="w-8 h-8 rounded-md shadow-sm border border-border/10"
        style={{ backgroundColor: color }}
      />
      <span className="text-[9px] text-muted-foreground font-mono opacity-50">{color}</span>
    </div>
  );
}

export function VisualsSection({ visuals, onEdit, onExtract }: VisualsSectionProps) {
  const hasData =
    visuals.primary_color &&
    visuals.primary_color.length > 0 &&
    visuals.primary_color !== "#000000" &&
    visuals.primary_color !== "#ffffff";

  return (
    <section
      onClick={onEdit}
      className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer border border-transparent hover:border-border/50"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <Palette className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Identidad Visual</h3>
        </div>

        {hasData && (
          <Button
            variant="outline"
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity gap-2 bg-background/50 backdrop-blur-sm"
            onClick={(e) => {
              e.stopPropagation();
              onExtract();
            }}
          >
            <Sparkles className="w-3 h-3 text-purple-500" />
            Extraer
          </Button>
        )}
      </div>

      {!hasData ? (
        <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
          <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-4 shadow-sm">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Sin Identidad Visual</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm leading-relaxed">
            No tienes colores ni tipografias definidas. Extrae tu marca automaticamente desde tu web
            o logo.
          </p>
          <div className="flex flex-col gap-3 w-full max-w-xs">
            <Button
              onClick={(e) => {
                e.stopPropagation();
                onExtract();
              }}
              className="w-full shadow-lg shadow-purple-500/20 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Extraer Identidad
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
            >
              Configurar Manualmente
            </Button>
          </div>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
          <div className="grid md:grid-cols-2 gap-10">
            {/* Colors */}
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-4">Paleta Cromatica</h4>
                <div className="grid grid-cols-3 gap-4">
                  <ColorSwatch color={visuals.primary_color ?? "#000000"} label="Primario" />
                  {visuals.secondary_color && (
                    <ColorSwatch color={visuals.secondary_color} label="Secundario" />
                  )}
                  <ColorSwatch color={visuals.accent_color ?? "#000000"} label="Acento" />
                  <ColorSwatch color={visuals.background_color || "#ffffff"} label="Fondo" />
                </div>
              </div>

              {/* Extended Palette */}
              {visuals.color_palette && visuals.color_palette.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-3">
                    Paleta Extendida
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {visuals.color_palette.map((color, i) => (
                      <SmallSwatch key={i} color={color} />
                    ))}
                  </div>
                </div>
              )}

              {/* Gradients */}
              {visuals.gradient_definitions && visuals.gradient_definitions.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-3">Gradientes</h4>
                  <div className="flex gap-2">
                    {visuals.gradient_definitions.map((grad, i) => (
                      <div
                        key={i}
                        className="h-8 flex-1 rounded-md shadow-sm border"
                        style={{ background: grad }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Typography */}
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                <Type className="w-4 h-4" /> Tipografia
              </h4>
              <div className="space-y-6">
                <div className="border-l-2 border-primary/20 pl-4 transition-colors group-hover:border-primary/40">
                  <p
                    className="text-4xl font-bold text-foreground leading-tight"
                    style={{ fontFamily: visuals.font_heading }}
                  >
                    Heading Display
                  </p>
                  <p className="text-xs text-muted-foreground mt-2 font-mono">
                    {visuals.font_heading || "Sin definir"} (Titulos)
                  </p>
                </div>
                <div className="border-l-2 border-muted pl-4">
                  <p
                    className="text-lg text-foreground/80 leading-relaxed"
                    style={{ fontFamily: visuals.font_body }}
                  >
                    El diseno es el embajador silencioso de tu marca. Una buena tipografia establece
                    la jerarquia y el tono de voz visual.
                  </p>
                  <p className="text-xs text-muted-foreground mt-2 font-mono">
                    {visuals.font_body || "Sin definir"} (Cuerpo)
                  </p>
                </div>
                {visuals.font_accent && (
                  <div className="border-l-2 border-accent/20 pl-4">
                    <p
                      className="text-xl italic text-foreground/70"
                      style={{ fontFamily: visuals.font_accent }}
                    >
                      Texto decorativo de ejemplo
                    </p>
                    <p className="text-xs text-muted-foreground mt-2 font-mono">
                      {visuals.font_accent} (Accent)
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Brand Mood & Design Style badges */}
          {(visuals.brand_mood?.adjectives?.length ||
            visuals.design_style ||
            visuals.visual_density) && (
            <div className="mt-8 flex flex-wrap gap-2">
              {visuals.design_style && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary border border-primary/20">
                  {visuals.design_style}
                </span>
              )}
              {visuals.visual_density && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border">
                  {visuals.visual_density}
                </span>
              )}
              {visuals.brand_mood?.adjectives?.map((adj, i) => (
                <span
                  key={i}
                  className="px-3 py-1 rounded-full text-xs font-medium bg-accent/10 text-accent-foreground border border-accent/20"
                >
                  {adj}
                </span>
              ))}
              {visuals.brand_mood?.energy && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-muted text-muted-foreground border">
                  Energia: {visuals.brand_mood.energy}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
