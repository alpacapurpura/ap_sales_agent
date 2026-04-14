import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Check, Shield, Star } from "lucide-react";
import { getContrastColor } from "@/lib/utils/colors";
import { useLandingTheme } from "@/features/offer-studio/components/landing/context/LandingThemeContext";

export interface BonusItem {
  title: string;
  description: string;
}

export interface OfferSectionProps {
  offer_headline: string;
  price_anchor: string;
  price_offer: string;
  cta_text: string;
  bonuses?: BonusItem[];
}

export function OfferSection({
  offer_headline,
  price_anchor,
  price_offer,
  cta_text,
  bonuses,
}: OfferSectionProps) {
  const theme = useLandingTheme();
  const primaryColor = theme.primary_color;
  const primaryTextColor = getContrastColor(primaryColor);

  return (
    <section className="py-24 px-6 bg-slate-50 border-t">
      <div className="max-w-3xl mx-auto bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-100">
        <div className="p-8 md:p-12 text-center space-y-8">
          <div className="space-y-2">
            <h3 className="text-2xl font-bold text-slate-900">{offer_headline}</h3>
            <p className="text-slate-500">Oferta Especial por Tiempo Limitado</p>
          </div>

          <div className="flex items-center justify-center gap-6">
            <div className="text-left">
              <p className="text-sm text-slate-400 line-through font-medium">Valor Real</p>
              <p className="text-2xl font-bold text-slate-400 decoration-slate-400 line-through w-auto text-center">
                {price_anchor}
              </p>
            </div>
            <div className="h-12 w-px bg-slate-200"></div>
            <div className="text-left">
              <p className="text-sm font-bold text-green-600">Hoy Oferta</p>
              <p className="text-5xl font-extrabold text-slate-900 w-auto text-center">
                {price_offer}
              </p>
            </div>
          </div>

          {/* Bonuses */}
          {bonuses && bonuses.length > 0 && (
            <div className="bg-slate-50 rounded-xl p-6 text-left space-y-4">
              <p className="font-bold text-sm uppercase tracking-wide text-slate-500 mb-4">
                Incluye estos Regalos:
              </p>
              {bonuses.map((bonus, i) => (
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
              {cta_text} <ArrowRight className="ml-2" />
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
  );
}
