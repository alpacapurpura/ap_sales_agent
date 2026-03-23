"use client";

import { BrandPositioning } from "@/features/brand/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Crosshair, Quote, Pencil, Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface MarketPreviewProps {
  positioning: BrandPositioning;
  onEdit: () => void;
}

const TOOLTIPS: Record<string, string> = {
  "Enemigo Real": "No es tu competidor -- es el problema o creencia contra la que luchas",
  "Insight del Cliente": "La verdad oculta que tu cliente siente pero no sabe expresar",
};

function SectionLabel({ label }: { label: string }) {
  const tip = TOOLTIPS[label];
  return (
    <div className="flex items-center gap-1.5">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
      {tip && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="w-3 h-3 text-muted-foreground/60 cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-[250px]"><p className="text-xs">{tip}</p></TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
}

export function MarketPreview({ positioning, onEdit }: MarketPreviewProps) {
  const env = positioning.competitive_environment;
  const insight = positioning.insight;

  const hasEnvironment =
    env?.technical_enemy ||
    env?.philosophical_enemy ||
    (env?.direct_competitors && env.direct_competitors.length > 0) ||
    (env?.indirect_competitors && env.indirect_competitors.length > 0);

  const hasInsight = insight?.tension || insight?.observation || insight?.implication;

  const hasContent = hasEnvironment || hasInsight;

  if (!hasContent) {
    return (
      <section
        onClick={onEdit}
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
      >
        <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <Crosshair className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">El Mercado</h3>
        </div>
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Conoce a tu enemigo y conoce a tu cliente. El posicionamiento nace de ambos.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Definir Mercado
          </span>
        </div>
      </section>
    );
  }

  return (
    <section className="relative -mx-4 p-6 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Crosshair className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">El Mercado</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Pencil className="w-4 h-4 mr-2" />
          Editar
        </Button>
      </div>

      <div className="pl-0 md:pl-14 space-y-10">
        {/* Competitive Environment */}
        {hasEnvironment && (
          <div className="space-y-4">
            {env?.technical_enemy && (
              <div>
                <SectionLabel label="Enemigo Real" />
                <p className="text-sm text-foreground mt-1">{env.technical_enemy}</p>
              </div>
            )}
            {env?.philosophical_enemy && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Enemigo Filosofico</p>
                <p className="text-sm text-foreground">{env.philosophical_enemy}</p>
              </div>
            )}

            {env?.direct_competitors && env.direct_competitors.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Competidores Directos</p>
                <div className="flex flex-wrap gap-2">
                  {env.direct_competitors.map((c) => (
                    <Badge key={c.id} variant="secondary" className="text-xs">
                      {c.name}
                      {c.differentiation && (
                        <span className="ml-1 text-muted-foreground">-- {c.differentiation}</span>
                      )}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {env?.indirect_competitors && env.indirect_competitors.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">Competidores Indirectos</p>
                <div className="flex flex-wrap gap-2">
                  {env.indirect_competitors.map((c) => (
                    <Badge key={c.id} variant="outline" className="text-xs">
                      {c.name}
                      {c.differentiation && (
                        <span className="ml-1 text-muted-foreground">-- {c.differentiation}</span>
                      )}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Consumer Insight */}
        {hasInsight && (
          <div className="border-l-2 border-primary/30 pl-6 space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground mb-2">
              <Quote className="w-4 h-4" />
              <SectionLabel label="Insight del Cliente" />
            </div>
            {insight?.tension && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Tension</p>
                <p className="text-sm text-foreground italic font-serif">{insight.tension}</p>
              </div>
            )}
            {insight?.observation && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Observacion</p>
                <p className="text-sm text-foreground italic font-serif">{insight.observation}</p>
              </div>
            )}
            {insight?.implication && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Implicacion</p>
                <p className="text-sm text-foreground italic font-serif">{insight.implication}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
