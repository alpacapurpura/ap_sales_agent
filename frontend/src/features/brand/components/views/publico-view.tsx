"use client";

import { useMemo } from "react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { BrandSectionShell } from "../layout/brand-section-shell";
import { SectionHeader } from "../layout/section-header";
import { BRAND_SECTIONS, buildSectionNavItems } from "../../config/sections";

// Preview components
import { AvatarsSection } from "../../sections/avatars/avatars-preview";

const SECTION = BRAND_SECTIONS.publico;

/**
 * Publico — "Tus clientes ideales"
 *
 * Contains: Buyer Personas (Avatars).
 */
export function PublicoView() {
  const { settings } = useBrandSettings();

  const navItems = useMemo(
    () => (settings ? buildSectionNavItems("publico", settings) : []),
    [settings],
  );

  if (!settings) return null;

  return (
    <BrandSectionShell title={SECTION.label} subtitle={SECTION.subtitle} navItems={navItems}>
      <div id="avatars" className="space-y-8">
        <SectionHeader title="Buyer Personas" subtitle="Perfiles completos de tu cliente ideal." />
        <AvatarsSection />
      </div>
    </BrandSectionShell>
  );
}
