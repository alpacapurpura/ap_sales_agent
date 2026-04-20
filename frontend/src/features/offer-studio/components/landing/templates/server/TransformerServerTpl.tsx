import { ArrowRight, Check, Star, Shield, Clock } from "lucide-react";
import Image from "next/image";
import React from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getContrastColor } from "@/lib/utils/colors";

import type {
  TransformerContent,
  LandingPageTheme,
} from "@/features/offer-studio/components/landing/types/schema";

interface TransformerServerTplProps {
  content: TransformerContent;
  theme: LandingPageTheme;
}

/**
 *
 */
export function TransformerServerTpl({ content, theme }: TransformerServerTplProps) {
  const primaryColor = theme.primary_color;
  const primaryTextColor = getContrastColor(primaryColor);

  return (
    <div className="w-full bg-white min-h-screen font-sans text-slate-800">
      {/* SECTION A: HERO (Identity Shift) */}
      <section className="relative py-20 px-6 text-center border-b overflow-hidden">
        <div
          className="absolute inset-0 opacity-10 pointer-events-none"
          style={{ backgroundColor: primaryColor }}
        />
        <div className="max-w-4xl mx-auto space-y-6 relative z-10">
          <Badge variant="outline" className="mb-4 border-slate-400 text-slate-600">
            Programa de Transformación
          </Badge>
          <div className="space-y-2">
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-900 leading-tight text-center">
              {content.headline}
            </h1>
            <h2 className="text-xl md:text-2xl text-slate-600 font-medium max-w-2xl mx-auto text-center">
              {content.subheadline}
            </h2>
          </div>

          <div className="pt-8">
            <Button
              size="lg"
              className="text-lg px-8 py-6 rounded-full shadow-xl hover:shadow-2xl transition-all transform hover:-translate-y-1"
              style={{ backgroundColor: primaryColor, color: primaryTextColor }}
            >
              {content.cta_text} <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-slate-500">
              <Clock className="w-4 h-4" />
              <span>{content.scarcity_text}</span>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION B: PAS (Problem - Agitation - Solution) */}
      <section className="py-16 px-6 bg-slate-50">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8 text-center md:text-left">
          <div className="space-y-3 p-6 bg-white rounded-xl shadow-sm border border-slate-100">
            <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold mb-2">
              ?
            </div>
            <h3 className="font-bold text-lg">El Problema</h3>
            <p className="text-slate-600 text-sm leading-relaxed min-h-[100px]">
              {content.problem_text}
            </p>
          </div>
          <div className="space-y-3 p-6 bg-white rounded-xl shadow-sm border border-slate-100">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold mb-2">
              !
            </div>
            <h3 className="font-bold text-lg">La Agitación</h3>
            <p className="text-slate-600 text-sm leading-relaxed min-h-[100px]">
              {content.agitation_text}
            </p>
          </div>
          <div
            className="space-y-3 p-6 rounded-xl shadow-sm border border-slate-100"
            style={{ backgroundColor: `${primaryColor}10` }}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center font-bold mb-2"
              style={{ backgroundColor: primaryColor, color: primaryTextColor }}
            >
              ✓
            </div>
            <h3 className="font-bold text-lg" style={{ color: primaryColor }}>
              La Solución
            </h3>
            <p className="text-slate-700 text-sm leading-relaxed font-medium min-h-[100px]">
              {content.solution_text}
            </p>
          </div>
        </div>
      </section>

      {/* SECTION C: MECHANISM */}
      <section className="py-20 px-6 text-center">
        <div className="max-w-3xl mx-auto space-y-6">
          <h2 className="text-sm font-bold tracking-widest uppercase text-slate-400">
            Presentando
          </h2>
          <h2 className="text-4xl md:text-5xl font-serif font-bold text-slate-900 text-center">
            {content.method_name}
          </h2>
          <p className="text-xl text-slate-600 leading-relaxed text-center">
            {content.method_description}
          </p>
        </div>
      </section>

      {/* SECTION D: AUTHORITY */}
      <section className="py-16 px-6 bg-slate-900 text-white overflow-hidden">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center gap-12">
          <div className="w-full md:w-1/3">
            {content.authority_image_url && (
              <Image
                src={content.authority_image_url}
                alt={content.authority_name}
                width={400}
                height={533}
                className="shadow-2xl ring-4 ring-white/10 rotate-3 transform hover:rotate-0 transition-all duration-500 rounded-lg w-full object-cover aspect-[3/4]"
                unoptimized
              />
            )}
          </div>
          <div className="w-full md:w-2/3 space-y-6">
            <div className="space-y-2">
              <p className="text-white/60 font-medium">Tu Mentora</p>
              <h3 className="text-3xl font-bold">{content.authority_name}</h3>
            </div>
            <p className="text-lg text-slate-300 leading-relaxed min-h-[150px]">
              {content.authority_bio}
            </p>

            {/* Story Hook if exists */}
            {content.story_hook && (
              <div className="mt-8 pt-8 border-t border-white/10">
                <h4 className="text-sm font-bold text-white/80 mb-2">Mi Historia</h4>
                <p className="text-slate-400 italic text-sm">{content.story_hook}</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* SECTION E: STACK (Modules) */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Lo que vas a lograr semana a semana</h2>
            <p className="text-slate-600">Un sistema probado paso a paso</p>
          </div>

          <div className="grid gap-6">
            {content.modules.map((mod, i) => (
              <div
                key={i}
                className="flex gap-4 p-6 rounded-xl border border-slate-100 hover:shadow-md transition-shadow bg-white"
              >
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-xl">
                  {i + 1}
                </div>
                <div className="flex-1 space-y-1">
                  <h4 className="font-bold text-lg text-slate-900">{mod.title}</h4>
                  <p className="text-slate-600 text-sm">{mod.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION F: OFFER & ANCHORING */}
      <section className="py-24 px-6 bg-slate-50 border-t">
        <div className="max-w-3xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100">
          <div className="p-8 md:p-12 text-center space-y-8">
            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-slate-900">Únete a {content.headline}</h3>
              <p className="text-slate-500">Oferta Especial por Tiempo Limitado</p>
            </div>

            <div className="flex items-center justify-center gap-6">
              <div className="text-left">
                <p className="text-sm text-slate-400 line-through font-medium">Valor Real</p>
                <p className="text-2xl font-bold text-slate-400 decoration-slate-400 line-through w-auto text-center">
                  {content.price_anchor}
                </p>
              </div>
              <div className="h-12 w-px bg-slate-200"></div>
              <div className="text-left">
                <p className="text-sm font-bold text-green-600">Hoy Oferta</p>
                <p className="text-5xl font-extrabold text-slate-900 w-auto text-center">
                  {content.price_offer}
                </p>
              </div>
            </div>

            {/* Bonuses */}
            {content.bonuses && content.bonuses.length > 0 && (
              <div className="bg-slate-50 rounded-xl p-6 text-left space-y-4">
                <p className="font-bold text-sm uppercase tracking-wide text-slate-500 mb-4">
                  Incluye estos Regalos:
                </p>
                {content.bonuses.map((bonus, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="mt-1 text-green-500">
                      <Check className="w-4 h-4" />
                    </div>
                    <div>
                      <span className="font-bold text-slate-800">{bonus.title}: </span>
                      <span className="text-slate-600 text-sm">{bonus.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="pt-4 space-y-4">
              <Button
                size="lg"
                className="w-full text-xl py-8 rounded-xl shadow-lg hover:shadow-xl transition-all"
                style={{ backgroundColor: primaryColor, color: primaryTextColor }}
              >
                {content.cta_text} <ArrowRight className="ml-2" />
              </Button>

              <div className="flex items-center justify-center gap-4 text-xs text-slate-400">
                <span className="flex items-center gap-1">
                  <Shield className="w-3 h-3" /> Pago Seguro
                </span>
                <span className="flex items-center gap-1">
                  <Star className="w-3 h-3" /> Garantía de 30 días
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
