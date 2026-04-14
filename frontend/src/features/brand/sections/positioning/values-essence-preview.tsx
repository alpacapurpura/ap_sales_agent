"use client";

import { BrandPositioning } from "@/features/brand/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sparkles, Pencil, ShieldCheck } from "lucide-react";

interface ValuesEssencePreviewProps {
  positioning: BrandPositioning;
  onEdit: () => void;
}

export function ValuesEssencePreview({ positioning, onEdit }: ValuesEssencePreviewProps) {
  const values = positioning.values;
  const rtbs = positioning.reasons_to_believe ?? [];

  const hasValues =
    (values?.core_values && values.core_values.length > 0) ||
    (values?.personality_traits && values.personality_traits.length > 0) ||
    values?.archetype;

  const hasContent =
    hasValues || rtbs.length > 0 || positioning.discriminator || positioning.brand_essence;

  if (!hasContent) {
    return (
      <section
        onClick={onEdit}
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
      >
        <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Valores & Esencia</h3>
        </div>
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Una marca es una promesa. La esencia es el corazón de esa promesa.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Definir Valores y Esencia
          </span>
        </div>
      </section>
    );
  }

  const rtbTypeLabels: Record<string, string> = {
    dato: "Dato",
    caso_exito: "Caso de Éxito",
    certificacion: "Certificación",
    tecnologia: "Tecnología",
    proceso: "Proceso",
  };

  return (
    <section className="relative -mx-4 p-6 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Valores & Esencia</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Pencil className="w-4 h-4 mr-2" />
          Editar
        </Button>
      </div>

      <div className="pl-0 md:pl-14 space-y-10">
        {/* Brand Essence */}
        {positioning.brand_essence && (
          <div className="text-center py-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
              Esencia de Marca
            </p>
            <p className="text-2xl md:text-3xl font-serif font-medium text-foreground tracking-tight">
              {positioning.brand_essence}
            </p>
          </div>
        )}

        {/* Discriminator */}
        {positioning.discriminator && (
          <div className="border-l-2 border-primary/30 pl-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Discriminador
            </p>
            <p className="text-sm text-foreground font-medium">{positioning.discriminator}</p>
          </div>
        )}

        {/* Values & Traits + Archetype */}
        {hasValues && (
          <div className="space-y-4">
            {values?.core_values && values.core_values.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Valores Centrales
                </p>
                <div className="flex flex-wrap gap-2">
                  {values.core_values.map((v, i) => (
                    <Badge key={i} variant="secondary" className="text-xs">
                      {v}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {values?.personality_traits && values.personality_traits.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Rasgos de Personalidad
                </p>
                <div className="flex flex-wrap gap-2">
                  {values.personality_traits.map((t, i) => (
                    <Badge key={i} variant="outline" className="text-xs">
                      {t}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {values?.archetype && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Arquetipo
                </p>
                <Badge className="text-xs">{values.archetype}</Badge>
              </div>
            )}
          </div>
        )}

        {/* Reasons to Believe */}
        {rtbs.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <ShieldCheck className="w-4 h-4" />
              <p className="text-xs font-semibold uppercase tracking-wider">Razones para Creer</p>
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
