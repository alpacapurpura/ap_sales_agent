"use client";

import { BrandNarrative } from "@/features/brand/types";
import { cn } from "@/lib/utils";
import {
  Pencil,
  BookOpen,
  User,
  AlertTriangle,
  Compass,
  ListOrdered,
  Megaphone,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

interface NarrativePreviewProps {
  narrative: BrandNarrative;
  onEdit: () => void;
}

export function NarrativePreview({ narrative, onEdit }: NarrativePreviewProps) {
  const hasHero = narrative.hero?.identity || narrative.hero?.desire;
  const hasProblem =
    narrative.problem?.villain ||
    narrative.problem?.external_problem ||
    narrative.problem?.internal_problem ||
    narrative.problem?.philosophical_problem;
  const hasGuide =
    narrative.guide?.empathy_statement || narrative.guide?.authority_statement;
  const hasPlan = narrative.plan && narrative.plan.length > 0;
  const hasCta =
    narrative.cta?.direct_cta || narrative.cta?.transitional_cta;
  const hasOutcome =
    narrative.outcome?.success_transformation ||
    narrative.outcome?.failure_consequence;
  const hasOneLiner = !!narrative.one_liner;

  const isEmpty =
    !hasHero &&
    !hasProblem &&
    !hasGuide &&
    !hasPlan &&
    !hasCta &&
    !hasOutcome &&
    !hasOneLiner;

  if (isEmpty) {
    return (
      <section
        onClick={onEdit}
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
      >
        <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <BookOpen className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Narrativa StoryBrand
          </h3>
        </div>
        <div className="pl-0 md:pl-14">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Si confundes, pierdes. Clarifica tu mensaje con StoryBrand.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Pencil className="w-4 h-4" />
            Construir Narrativa
          </span>
        </div>
      </section>
    );
  }

  return (
    <section
      onClick={onEdit}
      className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3 text-muted-foreground group-hover:text-primary transition-colors">
          <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <BookOpen className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Narrativa StoryBrand
          </h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            onEdit();
          }}
        >
          <Pencil className="w-4 h-4" />
        </Button>
      </div>

      <div className="pl-0 md:pl-14 space-y-8">
        {/* One-liner */}
        {hasOneLiner && (
          <div className="border-l-4 border-primary/30 pl-6 py-2">
            <p className="text-xl font-serif leading-relaxed text-foreground italic">
              &ldquo;{narrative.one_liner}&rdquo;
            </p>
            <span className="text-xs text-muted-foreground mt-2 block uppercase tracking-wide">
              One-liner
            </span>
          </div>
        )}

        {hasOneLiner && (hasHero || hasProblem) && <Separator />}

        {/* Hero */}
        {hasHero && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <User className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                El Heroe
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 1
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {narrative.hero?.identity && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Identidad
                  </span>
                  <p className="text-sm leading-relaxed text-foreground">
                    {narrative.hero.identity}
                  </p>
                </div>
              )}
              {narrative.hero?.desire && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Deseo
                  </span>
                  <p className="text-sm leading-relaxed text-foreground">
                    {narrative.hero.desire}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Problem */}
        {hasProblem && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                El Problema
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 2
              </Badge>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {narrative.problem?.villain && (
                <div className="p-3 rounded-lg bg-muted/30">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Villano
                  </span>
                  <p className="text-sm text-foreground font-medium">
                    {narrative.problem.villain}
                  </p>
                </div>
              )}
              {narrative.problem?.external_problem && (
                <div className="p-3 rounded-lg bg-muted/30">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Externo
                  </span>
                  <p className="text-sm text-foreground">
                    {narrative.problem.external_problem}
                  </p>
                </div>
              )}
              {narrative.problem?.internal_problem && (
                <div className="p-3 rounded-lg bg-muted/30">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Interno
                  </span>
                  <p className="text-sm text-foreground">
                    {narrative.problem.internal_problem}
                  </p>
                </div>
              )}
              {narrative.problem?.philosophical_problem && (
                <div className="p-3 rounded-lg bg-muted/30">
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Filosofico
                  </span>
                  <p className="text-sm text-foreground">
                    {narrative.problem.philosophical_problem}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Guide */}
        {hasGuide && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Compass className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                El Guia
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 3
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {narrative.guide?.empathy_statement && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Empatia
                  </span>
                  <p className="text-sm leading-relaxed text-foreground italic">
                    &ldquo;{narrative.guide.empathy_statement}&rdquo;
                  </p>
                </div>
              )}
              {narrative.guide?.authority_statement && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    Autoridad
                  </span>
                  <p className="text-sm leading-relaxed text-foreground">
                    {narrative.guide.authority_statement}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Plan */}
        {hasPlan && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <ListOrdered className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                El Plan
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 4
              </Badge>
            </div>
            <div className="flex items-start gap-0 overflow-x-auto pb-2">
              {narrative.plan.map((step, idx) => (
                <div key={step.id} className="flex items-start">
                  <div className="flex flex-col items-center min-w-[140px] max-w-[180px] text-center px-2">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary/10 text-primary text-sm font-bold mb-2">
                      {step.step_number}
                    </div>
                    {step.title && (
                      <span className="text-sm font-medium text-foreground leading-tight">
                        {step.title}
                      </span>
                    )}
                    {step.description && (
                      <span className="text-xs text-muted-foreground mt-1 leading-snug">
                        {step.description}
                      </span>
                    )}
                  </div>
                  {idx < narrative.plan.length - 1 && (
                    <div className="flex items-center pt-3 text-muted-foreground/40 mx-1">
                      <div className="w-6 h-px bg-border" />
                      <span className="text-xs">&rarr;</span>
                      <div className="w-6 h-px bg-border" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        {hasCta && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Megaphone className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Llamada a la Accion
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 5
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {narrative.cta?.direct_cta && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    CTA Directo
                  </span>
                  <p className="text-sm font-semibold text-primary">
                    {narrative.cta.direct_cta}
                  </p>
                </div>
              )}
              {narrative.cta?.transitional_cta && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase tracking-wide block mb-1">
                    CTA Transicional
                  </span>
                  <p className="text-sm text-foreground">
                    {narrative.cta.transitional_cta}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Outcome */}
        {hasOutcome && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wider">
                Resultado
              </span>
              <Badge variant="outline" className="text-[10px] ml-1">
                Paso 6
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {narrative.outcome?.success_transformation && (
                <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 uppercase tracking-wide block mb-1 font-medium">
                    Exito
                  </span>
                  <p className="text-sm leading-relaxed text-foreground">
                    {narrative.outcome.success_transformation}
                  </p>
                </div>
              )}
              {narrative.outcome?.failure_consequence && (
                <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/20">
                  <span className="text-[11px] text-red-600 dark:text-red-400 uppercase tracking-wide block mb-1 font-medium">
                    Fracaso
                  </span>
                  <p className="text-sm leading-relaxed text-foreground">
                    {narrative.outcome.failure_consequence}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
