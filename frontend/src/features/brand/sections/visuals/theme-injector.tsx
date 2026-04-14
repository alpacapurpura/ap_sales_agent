"use client";

import { BrandVisuals } from "@/features/brand/types";
import { getContrastColor, hexToHsl } from "@/lib/utils/colors";

interface ThemeInjectorProps {
  visuals: BrandVisuals;
}

export function ThemeInjector({ visuals }: ThemeInjectorProps) {
  if (!visuals) return null;

  // --- HYBRID STRATEGY ---
  // Only inject Fonts and Primary Colors.
  // Leave Background, Card, Foreground, Muted, Popover as System Default (Clean).

  // 1. Primary
  const primaryHsl = visuals.primary_color ? hexToHsl(visuals.primary_color) : null;
  // Calculate smart text-on-primary
  const smartOnPrimary = visuals.primary_color
    ? getContrastColor(visuals.primary_color)
    : "#ffffff";
  const onPrimaryHsl = hexToHsl(smartOnPrimary);

  return (
    <style jsx global>{`
      .brand-theme-scope {
        /* Core Colors - Only inject these to accent the system UI */
        ${primaryHsl ? `--primary: ${primaryHsl};` : ""}
        ${onPrimaryHsl ? `--primary-foreground: ${onPrimaryHsl};` : ""}
        ${primaryHsl ? `--ring: ${primaryHsl};` : ""}
        
        /* Font Family Injection */
        ${visuals.font_heading ? `--font-heading: ${visuals.font_heading}, sans-serif;` : ""}
        ${visuals.font_body ? `--font-body: ${visuals.font_body}, sans-serif;` : ""}
      }

      /* Force overrides for specific utility classes to ensure primary accent works */
      .brand-theme-scope .bg-primary {
        background-color: ${visuals.primary_color} !important;
        color: ${smartOnPrimary} !important;
      }
      .brand-theme-scope .text-primary {
        color: ${visuals.primary_color} !important;
      }
      .brand-theme-scope .border-primary {
        border-color: ${visuals.primary_color} !important;
      }

      /* Typography Application */
      .brand-theme-scope h1,
      .brand-theme-scope h2,
      .brand-theme-scope h3,
      .brand-theme-scope h4 {
        font-family: var(--font-heading, inherit);
      }
      .brand-theme-scope p,
      .brand-theme-scope span,
      .brand-theme-scope div {
        font-family: var(--font-body, inherit);
      }
    `}</style>
  );
}
