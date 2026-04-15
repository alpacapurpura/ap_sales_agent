"use client";

import { Trophy, Heart, ShieldCheck, Pencil, Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

import type { BrandPositioning } from "@/features/brand/types";

interface DifferentiationPreviewProps {
  positioning: BrandPositioning;
  onEdit: () => void;
}

const TOOLTIPS: Record<string, string> = {
  "Propuesta Unica": "Lo que te hace irremplazable -- por que alguien te elige a ti y no a otro",
  Discriminador: "La razon especifica por la que eres diferente (no mejor, DIFERENTE)",
  RTBs: "Pruebas concretas de que tu promesa es real (datos, casos, certificaciones)",
};

function SectionLabel({ label }: { label: string }) {
  const tip = TOOLTIPS[label];
  return (
    <div className="flex items-center gap-1.5">
      <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      {tip && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Info className="w-3 h-3 text-muted-foreground/60 cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-[250px]">
              <p className="text-xs">{tip}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  );
}

const rtbTypeLabels: Record<string, string> = {
  dato: "Dato",
  caso_exito: "Caso de Exito",
  certificacion: "Certificacion",
  tecnologia: "Tecnologia",
  proceso: "Proceso",
};

export function DifferentiationPreview({ positioning, onEdit }: DifferentiationPreviewProps) {
  const { benefits } = positioning;
  const rtbs = positioning.reasons_to_believe ?? [];

  const hasUVP = !!positioning.unique_value_proposition;
  const hasDiscriminator = !!positioning.discriminator;
  const hasBenefits =
    (benefits?.functional_benefits && benefits.functional_benefits.length > 0) ||
    (benefits?.emotional_benefits && benefits.emotional_benefits.length > 0);
  const hasRTBs = rtbs.length > 0;

  const hasContent = hasUVP || hasDiscriminator || hasBenefits || hasRTBs;

  if (!hasContent) {
    return (
      <section
        onClick={onEdit}
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
      >
        <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <Trophy className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Diferenciacion</h3>
        </div>
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Si no puedes explicar en una frase por que eres diferente, tu cliente tampoco
            puede.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Definir Propuesta Unica
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
            <Trophy className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Diferenciacion</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Pencil className="w-4 h-4 mr-2" />
          Editar
        </Button>
      </div>

      <div className="pl-0 md:pl-14 space-y-10">
        {/* UVP */}
        {hasUVP && (
          <div className="text-center py-4">
            <SectionLabel label="Propuesta Unica" />
            <p className="text-2xl md:text-3xl font-serif font-medium text-foreground tracking-tight mt-3">
              {positioning.unique_value_proposition}
            </p>
          </div>
        )}

        {/* Discriminator */}
        {hasDiscriminator && (
          <div className="border-l-2 border-primary/30 pl-6">
            <SectionLabel label="Discriminador" />
            <p className="text-sm text-foreground font-medium mt-1">{positioning.discriminator}</p>
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

        {/* RTBs */}
        {hasRTBs && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <ShieldCheck className="w-4 h-4" />
              <SectionLabel label="RTBs" />
            </div>
            <ul className="space-y-2">
              {rtbs.map((rtb) => (
                <li key={rtb.id} className="flex items-start gap-3 text-sm">
                  {rtb.type && (
                    <Badge variant="outline" className="text-[10px] flex-shrink-0 mt-0.5">
                      {rtbTypeLabels[rtb.type] || rtb.type}
                    </Badge>
                  )}
                  <span className="text-foreground">{rtb.statement}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
