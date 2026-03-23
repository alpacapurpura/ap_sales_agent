"use client";

import { BrandPositioning } from "@/features/brand/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Crosshair, Quote, Heart, Pencil } from "lucide-react";

interface PositioningPreviewProps {
  positioning: BrandPositioning;
  onEdit: () => void;
}

export function PositioningPreview({ positioning, onEdit }: PositioningPreviewProps) {
  const env = positioning.competitive_environment;
  const insight = positioning.insight;
  const benefits = positioning.benefits;

  const hasEnvironment =
    env?.technical_enemy ||
    env?.philosophical_enemy ||
    (env?.direct_competitors && env.direct_competitors.length > 0) ||
    (env?.indirect_competitors && env.indirect_competitors.length > 0);

  const hasInsight = insight?.tension || insight?.observation || insight?.implication;

  const hasBenefits =
    (benefits?.functional_benefits && benefits.functional_benefits.length > 0) ||
    (benefits?.emotional_benefits && benefits.emotional_benefits.length > 0);

  const hasContent = hasEnvironment || hasInsight || hasBenefits;

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
          <h3 className="text-sm font-semibold uppercase tracking-wider">Entorno Competitivo & Insight</h3>
        </div>
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Conoce a tu enemigo y conoce a tu cliente. El posicionamiento nace de ambos.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Definir Posicionamiento
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
          <h3 className="text-sm font-semibold uppercase tracking-wider">Entorno Competitivo & Insight</h3>
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
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Enemigo Técnico</p>
                <p className="text-sm text-foreground">{env.technical_enemy}</p>
              </div>
            )}
            {env?.philosophical_enemy && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">Enemigo Filosófico</p>
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
                        <span className="ml-1 text-muted-foreground">— {c.differentiation}</span>
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
                        <span className="ml-1 text-muted-foreground">— {c.differentiation}</span>
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
              <p className="text-xs font-semibold uppercase tracking-wider">Consumer Insight</p>
            </div>
            {insight?.tension && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Tensión</p>
                <p className="text-sm text-foreground italic font-serif">{insight.tension}</p>
              </div>
            )}
            {insight?.observation && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Observación</p>
                <p className="text-sm text-foreground italic font-serif">{insight.observation}</p>
              </div>
            )}
            {insight?.implication && (
              <div>
                <p className="text-xs text-muted-foreground font-medium mb-0.5">Implicación</p>
                <p className="text-sm text-foreground italic font-serif">{insight.implication}</p>
              </div>
            )}
          </div>
        )}

        {/* Benefits */}
        {hasBenefits && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground mb-3">
              <Heart className="w-4 h-4" />
              <p className="text-xs font-semibold uppercase tracking-wider">Beneficios</p>
            </div>
            <div className="grid md:grid-cols-2 gap-8">
              {benefits?.functional_benefits && benefits.functional_benefits.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground font-medium mb-2">Funcionales</p>
                  <ul className="space-y-1.5">
                    {benefits.functional_benefits.map((b, i) => (
                      <li key={i} className="text-sm text-foreground flex items-start gap-2">
                        <span className="text-primary mt-1 text-xs">&#9679;</span>
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {benefits?.emotional_benefits && benefits.emotional_benefits.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground font-medium mb-2">Emocionales</p>
                  <ul className="space-y-1.5">
                    {benefits.emotional_benefits.map((b, i) => (
                      <li key={i} className="text-sm text-foreground flex items-start gap-2">
                        <span className="text-primary mt-1 text-xs">&#9679;</span>
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
