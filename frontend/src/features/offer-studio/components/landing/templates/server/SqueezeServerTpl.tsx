import Image from "next/image";
import React from "react";

import { Button } from "@/components/ui/button"; // Assuming we have shadcn button
import { Card } from "@/components/ui/card";
import { getContrastColor } from "@/lib/utils/colors";

import { LandingPageFont } from "../../types/schema";

import type { SqueezeContent, LandingPageTheme } from "../../types/schema";

// SERVER COMPONENT - NO "use client"
// This template is optimized for SEO and Speed.
// It receives raw data props and renders pure HTML/CSS.

interface SqueezeTemplateProps {
  content: SqueezeContent;
  theme: LandingPageTheme;
}

/**
 *
 */
export function SqueezeServerTpl({ content, theme }: SqueezeTemplateProps) {
  // Theme injection via inline styles for zero-runtime CSS-in-JS overhead
  // In a real prod app, we might use Tailwind dynamic classes or CSS variables
  const secondaryBg = theme.secondary_color;
  const secondaryText = getContrastColor(secondaryBg);
  const primaryBg = theme.primary_color;
  const primaryText = getContrastColor(primaryBg);

  const themeStyles = {
    "--primary": primaryBg,
    "--secondary": secondaryBg,
    backgroundColor: secondaryBg,
    color: secondaryText,
    fontFamily: theme.font_pair === LandingPageFont.SERIF ? "serif" : "sans-serif",
  } as React.CSSProperties;

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6 text-center"
      style={themeStyles}
    >
      <main className="max-w-2xl w-full space-y-8">
        {/* HERO SECTION */}
        <header className="space-y-4">
          <h1
            className="text-4xl md:text-6xl font-extrabold tracking-tight"
            style={{ color: theme.primary_color }}
          >
            {content.headline}
          </h1>
          <p className="text-xl md:text-2xl opacity-90">{content.subheadline}</p>
        </header>

        {/* VISUAL / MOCKUP */}
        {content.visual_url && (
          <div className="relative mx-auto w-full max-w-md aspect-video rounded-xl overflow-hidden shadow-2xl my-8 bg-gray-200">
            <Image
              src={content.visual_url}
              alt="Resource Mockup"
              width={640}
              height={360}
              className="object-cover w-full h-full"
              priority
              unoptimized
            />
          </div>
        )}

        {/* BENEFITS BULLETS */}
        <Card className="p-8 text-left bg-white/5 backdrop-blur-sm border-none shadow-none">
          <h3 className="text-lg font-semibold mb-4 uppercase tracking-wider opacity-70">
            Lo que descubrirás dentro:
          </h3>
          <ul className="space-y-3">
            {content.bullets.map((bullet, idx) => (
              <li key={idx} className="flex items-start gap-3 text-lg">
                <span className="text-primary text-xl">✓</span>
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </Card>

        {/* CTA SECTION */}
        <div className="pt-8 space-y-4">
          <Button
            size="lg"
            className="w-full md:w-auto text-xl px-12 py-8 rounded-full font-bold shadow-xl hover:scale-105 transition-transform"
            style={{ backgroundColor: theme.primary_color, color: primaryText }}
          >
            {content.cta_text}
          </Button>

          {content.privacy_text && <p className="text-sm opacity-60">🔒 {content.privacy_text}</p>}
        </div>
      </main>

      {/* FOOTER */}
      <footer className="mt-16 text-sm opacity-50">
        <p>© {new Date().getFullYear()} Todos los derechos reservados.</p>
      </footer>
    </div>
  );
}
