import { AuthoritySection } from "../components/blocks/AuthoritySection";
import { HeroSection } from "../components/blocks/HeroSection";
import { OfferSection } from "../components/blocks/OfferSection";
import { PasGridSection } from "../components/blocks/PasGridSection";
import { SolutionSection } from "../components/blocks/SolutionSection";
import { StackSection } from "../components/blocks/StackSection";
import { LandingThemeProvider } from "../context/LandingThemeContext";
import { LandingPageFont } from "../types/schema";

import type { AuthoritySectionProps } from "../components/blocks/AuthoritySection";
import type { HeroSectionProps } from "../components/blocks/HeroSection";
import type { OfferSectionProps } from "../components/blocks/OfferSection";
import type { PasGridSectionProps } from "../components/blocks/PasGridSection";
import type { SolutionSectionProps } from "../components/blocks/SolutionSection";
import type { StackSectionProps } from "../components/blocks/StackSection";
import type { LandingPageTheme } from "../types/schema";
import type { Config } from "@puckeditor/core";

export interface Props {
  HeroSection: HeroSectionProps;
  PasGridSection: PasGridSectionProps;
  SolutionSection: SolutionSectionProps;
  AuthoritySection: AuthoritySectionProps;
  StackSection: StackSectionProps;
  OfferSection: OfferSectionProps;
}

export interface RootProps {
  children: React.ReactNode;
  theme: LandingPageTheme;
}

export const config: Config<Props, RootProps> = {
  categories: {
    hero: { components: ["HeroSection"], title: "🏁 Hero & Apertura" },
    problem: { components: ["PasGridSection"], title: "🧠 Problema & Agitación" },
    solution: { components: ["SolutionSection"], title: "💡 Solución & Método" },
    authority: { components: ["AuthoritySection"], title: "⭐ Autoridad" },
    offer: { components: ["StackSection", "OfferSection"], title: "💰 Oferta" },
  },
  root: {
    fields: {
      theme: {
        type: "object",
        objectFields: {
          primary_color: { type: "text", label: "Color Primario" },
          secondary_color: { type: "text", label: "Color Secundario" },
          font_pair: {
            type: "select",
            label: "Tipografía",
            options: [
              { label: "Sans Serif", value: "SANS_SERIF" },
              { label: "Serif", value: "SERIF" },
              { label: "Modern", value: "MODERN" },
            ],
          },
          dark_mode: {
            type: "radio",
            label: "Modo Oscuro",
            options: [
              { label: "No", value: false },
              { label: "Sí", value: true },
            ],
          },
        },
      },
    },
    render: ({ children, theme }) => {
      // Default fallback if theme is undefined (e.g. new page)
      const safeTheme = theme || {
        primary_color: "#3b82f6",
        secondary_color: "#eff6ff",
        font_pair: "SANS_SERIF",
        dark_mode: false,
      };

      return (
        <LandingThemeProvider theme={safeTheme}>
          <div className="min-h-screen bg-white font-sans">{children}</div>
        </LandingThemeProvider>
      );
    },
  },
  components: {
    HeroSection: {
      fields: {
        headline: { type: "text" },
        subheadline: { type: "textarea" },
        cta_text: { type: "text" },
        scarcity_text: { type: "text" },
        layout: {
          type: "select",
          options: [
            { label: "Centrado (Classic)", value: "centered" },
            { label: "Dividido (Split)", value: "split" },
            { label: "Fondo Inmersivo (Background)", value: "background" },
            { label: "Video Sales Letter (VSL)", value: "vsl" },
            { label: "Urgencia (Countdown)", value: "urgency" },
            { label: "Quiz (Micro-compromiso)", value: "quiz" },
          ],
        },
        image_url: { type: "text", label: "URL Imagen/Video (Fondo/Lado)" },
        video_url: { type: "text", label: "URL Video (Solo VSL)" },
      },
      render: (props) => <HeroSection {...props} />,
    },
    PasGridSection: {
      fields: {
        problem_text: { type: "textarea" },
        agitation_text: { type: "textarea" },
        solution_text: { type: "textarea" },
      },
      render: (props) => <PasGridSection {...props} />,
    },
    SolutionSection: {
      fields: {
        method_name: { type: "text" },
        method_description: { type: "textarea" },
      },
      render: (props) => <SolutionSection {...props} />,
    },
    AuthoritySection: {
      fields: {
        authority_name: { type: "text" },
        authority_bio: { type: "textarea" },
        authority_image_url: { type: "text" },
        story_hook: { type: "textarea" },
      },
      render: (props) => <AuthoritySection {...props} />,
    },
    StackSection: {
      fields: {
        modules: {
          type: "array",
          getItemSummary: (item) => item.title || "Módulo",
          arrayFields: {
            title: { type: "text" },
            description: { type: "textarea" },
          },
        },
      },
      render: (props) => <StackSection {...props} />,
    },
    OfferSection: {
      fields: {
        offer_headline: { type: "text" },
        price_anchor: { type: "text" },
        price_offer: { type: "text" },
        cta_text: { type: "text" },
        bonuses: {
          type: "array",
          getItemSummary: (item) => item.title || "Bonus",
          arrayFields: {
            title: { type: "text" },
            description: { type: "textarea" },
          },
        },
      },
      render: (props) => <OfferSection {...props} />,
    },
  },
};
