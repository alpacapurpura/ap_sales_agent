import React from "react";
import { Hero } from "./hero/hero";

export interface HeroSectionProps {
  headline: string;
  subheadline: string;
  cta_text: string;
  scarcity_text?: string;
  layout?: "centered" | "split" | "background" | "vsl" | "urgency" | "quiz";
  image_url?: string;
  video_url?: string;
}

export function HeroSection({
  headline,
  subheadline,
  cta_text,
  scarcity_text,
  layout = "centered",
  image_url,
  video_url,
}: HeroSectionProps) {
  // Default placeholder if no image provided for split/background
  const bgImage =
    image_url ||
    "https://images.unsplash.com/photo-1557804506-669a67965ba0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1574&q=80";

  return (
    <Hero layout={layout} bgImage={bgImage}>
      {/* Urgency Layout Handling */}
      {layout === "urgency" ? (
        <>
          <Hero.Scarcity>{scarcity_text || "¡Atención! Esta oferta expira pronto."}</Hero.Scarcity>
          <section className="relative py-20 px-6 text-center bg-slate-50 w-full">
            <div className="max-w-4xl mx-auto space-y-6">
              <Hero.Headline>{headline}</Hero.Headline>
              <Hero.Subheadline>{subheadline}</Hero.Subheadline>
              <Hero.Actions>
                <Hero.CTA>{cta_text}</Hero.CTA>
              </Hero.Actions>
            </div>
          </section>
        </>
      ) : (
        <>
          {/* Content Wrapper */}
          <Hero.Content>
            {/* Badges */}
            {layout === "vsl" && <Hero.Tag variant="destructive">Video Revelación</Hero.Tag>}
            {layout === "quiz" && <Hero.Tag variant="outline">Evaluación Gratuita</Hero.Tag>}
            {layout === "background" && (
              <Hero.Tag
                variant="outline"
                className="border-white/30 text-white bg-white/10 backdrop-blur-sm"
              >
                Oferta Exclusiva
              </Hero.Tag>
            )}
            {layout === "split" && (
              <Hero.Tag
                variant="secondary"
                className="bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Nuevo Programa
              </Hero.Tag>
            )}
            {layout === "centered" && (
              <Hero.Tag variant="outline" className="border-slate-300 text-slate-500 px-4 py-1">
                Programa de Transformación
              </Hero.Tag>
            )}

            {/* Headlines */}
            <Hero.Headline>{headline}</Hero.Headline>

            {/* Subheadlines (Standard position) */}
            {layout !== "vsl" && <Hero.Subheadline>{subheadline}</Hero.Subheadline>}
          </Hero.Content>

          {/* Media (VSL Video or Split Image) */}
          {layout === "vsl" && <Hero.Media type="video" src={video_url} />}
          {layout === "split" && <Hero.Media type="image" src={bgImage} />}

          {/* Actions / CTA */}
          {layout === "quiz" ? (
            <Hero.Actions>
              {["Opción A: Principiante", "Opción B: Intermedio", "Opción C: Avanzado"].map(
                (opt, i) => (
                  <Hero.CTA key={i} icon={true}>
                    {opt}
                  </Hero.CTA>
                ),
              )}
            </Hero.Actions>
          ) : (
            <Hero.Actions>
              <Hero.CTA>{cta_text}</Hero.CTA>

              {/* VSL Subheadline is below CTA */}
              {layout === "vsl" && <Hero.Subheadline>{subheadline}</Hero.Subheadline>}

              {/* Scarcity Pills (Non-sticky) */}
              {scarcity_text && <Hero.Scarcity>{scarcity_text}</Hero.Scarcity>}
            </Hero.Actions>
          )}
        </>
      )}
    </Hero>
  );
}
