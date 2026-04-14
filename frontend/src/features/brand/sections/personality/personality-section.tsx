"use client";

import { Theater, Pencil, Sparkles, Bot } from "lucide-react";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { useActivePersonality } from "../../api/personality";
import { DIMENSION_LABELS, getDimensionLevelName } from "../../types/personality";

import type { PersonalityDimensions } from "../../types/personality";

const DIMENSION_ORDER: (keyof PersonalityDimensions)[] = [
  "energy",
  "warmth",
  "humor",
  "expressiveness",
  "narrative",
  "verbosity",
];

const PROFILE_TYPE_LABELS: Record<string, string> = {
  preset: "Preset",
  cloned: "Clonado",
  interview: "Entrevista",
  manual: "Manual",
};

interface PersonalitySectionProps {
  onConfigure: () => void;
}

export function PersonalitySection({ onConfigure }: PersonalitySectionProps) {
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";

  const { data: profile, isLoading } = useActivePersonality(tenantId);

  if (isLoading) {
    return (
      <section className="relative -mx-4 p-6 rounded-xl">
        <div className="h-32 flex items-center justify-center text-muted-foreground text-sm animate-pulse">
          Cargando perfil de personalidad…
        </div>
      </section>
    );
  }

  // ── Empty state ──────────────────────────────────────────────────────────
  if (!profile) {
    return (
      <section className="relative -mx-4 p-6 rounded-xl border-2 border-dashed border-muted hover:border-primary/30 transition-colors">
        <div className="flex items-center gap-3 mb-6 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Theater className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Voz & Personalidad</h3>
        </div>

        <div className="pl-0 md:pl-14 space-y-4">
          <p className="text-sm text-muted-foreground">
            Define la personalidad de tu agente de ventas. ¿Cómo habla? ¿Qué tan cálido, enérgico o
            expresivo es?
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Button size="sm" onClick={onConfigure}>
              <Sparkles className="w-4 h-4 mr-2" />
              Elegir preset
            </Button>
            <Button variant="outline" size="sm" onClick={onConfigure}>
              <Bot className="w-4 h-4 mr-2" />
              Clonar personalidad
            </Button>
          </div>
        </div>
      </section>
    );
  }

  // ── Configured state ─────────────────────────────────────────────────────
  return (
    <section className="relative -mx-4 p-6 rounded-xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Theater className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">Voz & Personalidad</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onConfigure}>
          <Pencil className="w-4 h-4 mr-2" />
          Editar
        </Button>
      </div>

      <div className="pl-0 md:pl-14 space-y-6">
        {/* Profile identity */}
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-2xl">
            {(profile.source_metadata?.icon as string) ?? "🎭"}
          </div>
          <div>
            <p className="font-semibold text-foreground">{profile.name}</p>
            <Badge variant="secondary" className="text-xs mt-1">
              {PROFILE_TYPE_LABELS[profile.profile_type] ?? profile.profile_type}
            </Badge>
          </div>
        </div>

        {/* Dimension bars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DIMENSION_ORDER.map((dim) => {
            const value = profile.dimensions[dim];
            const { label, low, high } = DIMENSION_LABELS[dim];
            const levelName = getDimensionLevelName(dim, value);
            return (
              <div key={dim} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-muted-foreground">{label}</span>
                  <span className="text-foreground font-semibold">{levelName}</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] text-muted-foreground/60">
                  <span>{low}</span>
                  <span>{high}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Sample message */}
        {profile.sample_exchanges.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Muestra de voz
            </p>
            <div className="rounded-lg bg-muted/40 p-3">
              <p className="text-xs text-muted-foreground mb-1 italic">
                {profile.sample_exchanges[0].other_message}
              </p>
              <p className="text-sm text-foreground">
                {profile.sample_exchanges[0].author_response}
              </p>
            </div>
          </div>
        )}

        {/* Linguistic chips */}
        {profile.linguistic_patterns.filler_phrases.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {profile.linguistic_patterns.filler_phrases.slice(0, 4).map((phrase, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                &ldquo;{phrase}&rdquo;
              </Badge>
            ))}
            {profile.linguistic_patterns.filler_phrases.length > 4 && (
              <Badge variant="outline" className="text-xs text-muted-foreground">
                +{profile.linguistic_patterns.filler_phrases.length - 4} más
              </Badge>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
