"use client";

import { useMemo } from "react";

import { useBrandStudio } from "@/features/brand/context/brand-studio-context";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";

import { BRAND_SECTIONS, buildSectionNavItems } from "../../config/sections";

// Preview components
import { DifferentiationPreview } from "../../sections/differentiation/differentiation-preview";
import { MarketPreview } from "../../sections/market/market-preview";
import { MethodologySection } from "../../sections/methodology/methodology-preview";
import { NarrativePreview } from "../../sections/narrative/narrative-preview";
import { BrandSectionShell } from "../layout/brand-section-shell";
import { SectionHeader } from "../layout/section-header";

import type { BrandStrategy } from "../../types";

const SECTION = BRAND_SECTIONS.estrategia;

/**
 * Estrategia — "Tu plan de juego"
 *
 * Contains: Positioning, Market, StoryBrand narrative, Methodology.
 */
export function EstrategiaView() {
  const { settings } = useBrandSettings();
  const { openEdit } = useBrandStudio();

  const navItems = useMemo(
    () => (settings ? buildSectionNavItems("estrategia", settings) : []),
    [settings],
  );

  if (!settings) return null;

  return (
    <BrandSectionShell title={SECTION.label} subtitle={SECTION.subtitle} navItems={navItems}>
      {/* Posicionamiento */}
      <div id="positioning" className="space-y-8">
        <SectionHeader
          title="Posicionamiento"
          subtitle="Propuesta unica, beneficios y razones para creer."
          tooltip="Basado en Brand Love Key"
        />
        <DifferentiationPreview
          positioning={settings.positioning ?? { reasons_to_believe: [] }}
          onEdit={() => openEdit("positioning")}
        />
      </div>

      {/* Mercado */}
      <div id="market" className="space-y-8">
        <SectionHeader
          title="El Mercado"
          subtitle="Competidores, enemigos e insight del cliente."
          tooltip="Basado en Brand Love Key"
        />
        <MarketPreview
          positioning={settings.positioning ?? { reasons_to_believe: [] }}
          onEdit={() => openEdit("positioning")}
        />
      </div>

      {/* StoryBrand */}
      <div id="storybrand" className="space-y-8">
        <SectionHeader
          title="StoryBrand"
          subtitle="El viaje del heroe: problema, guia, plan y transformacion."
        />
        <NarrativePreview
          narrative={settings.narrative ?? { plan: [] }}
          onEdit={() => openEdit("storybrand")}
        />
      </div>

      {/* Metodologia */}
      <div id="methodology" className="space-y-8">
        <SectionHeader title="Metodologia" subtitle="Tus pilares y metodos unicos." />
        <MethodologySection
          strategy={settings.strategy ?? ({} as BrandStrategy)}
          visuals={settings.visuals ?? {}}
          onEdit={() => openEdit("methodology")}
        />
      </div>
    </BrandSectionShell>
  );
}
