"use client";

import { useMemo } from "react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { useBrandStudio } from "@/features/brand/context/brand-studio-context";
import { BrandSectionShell } from "../layout/brand-section-shell";
import { SectionHeader } from "../layout/section-header";
import { BRAND_SECTIONS, buildSectionNavItems } from "../../config/sections";

// Preview components
import { HeaderSection } from "../../sections/identity/identity-header-preview";
import { StorySection } from "../../sections/story/story-preview";
import { ValuesEssencePreview } from "../../sections/positioning/values-essence-preview";
import { TeamSection } from "../../sections/team/team-preview";
import { TestimonialsSection } from "../../sections/testimonials/testimonials-preview";
import { TrustSection } from "../../sections/authority/authority-preview";
import { FooterSection } from "../../sections/contact/contact-footer-preview";

const SECTION = BRAND_SECTIONS.esencia;

/**
 * Esencia — "Tu ADN, quien eres"
 *
 * Contains: Identity, Story, Values & Personality, Team,
 * Authority, Testimonials, Contact.
 */
export function EsenciaView() {
  const { settings } = useBrandSettings();
  const { openEdit, openSmartFill } = useBrandStudio();

  const navItems = useMemo(
    () => (settings ? buildSectionNavItems("esencia", settings) : []),
    [settings],
  );

  if (!settings) return null;

  return (
    <BrandSectionShell title={SECTION.label} subtitle={SECTION.subtitle} navItems={navItems}>
      {/* Identity Header */}
      <div id="identity" className="mb-4">
        <HeaderSection
          identity={settings.identity ?? {}}
          visuals={settings.visuals ?? {}}
          contact={settings.contact ?? {}}
          onEdit={() => openEdit("identity")}
          onEditVisuals={() => openEdit("visuals")}
          onRefine={() => openSmartFill("update")}
        />
      </div>

      {/* Origen */}
      <div id="story" className="space-y-8">
        <SectionHeader title="Origen" subtitle="Historia y relato fundacional." />
        <StorySection
          story={settings.story ?? {}}
          visuals={settings.visuals ?? {}}
          onEdit={() => openEdit("story")}
        />
      </div>

      {/* Personalidad */}
      <div id="values-essence" className="space-y-8">
        <SectionHeader
          title="Personalidad"
          subtitle="Valores, arquetipo y esencia de marca."
          tooltip="Basado en Brand Love Key"
        />
        <ValuesEssencePreview
          positioning={settings.positioning ?? { reasons_to_believe: [] }}
          onEdit={() => openEdit("values-essence")}
        />
      </div>

      {/* Equipo + Testimonios */}
      <div id="team" className="space-y-8">
        <SectionHeader
          title="Equipo & Testimonios"
          subtitle="Las personas detras de la marca y prueba social."
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <TeamSection
            team={settings.team ?? []}
            visuals={settings.visuals ?? {}}
            onEdit={(item) => openEdit("team", item)}
          />
          <TestimonialsSection
            testimonials={settings.testimonials ?? []}
            onEdit={(item) => openEdit("testimonials", item)}
          />
        </div>
      </div>

      {/* Credibilidad */}
      <div id="authority" className="space-y-8">
        <SectionHeader title="Credibilidad" subtitle="Premios, certificaciones y casos de exito." />
        <TrustSection
          identity={settings.identity ?? {}}
          authority={settings.authority_vault ?? []}
          visuals={settings.visuals ?? {}}
          onEditIdentity={() => openEdit("identity")}
          onEditAuthority={(item) => openEdit("authority", item)}
        />
      </div>

      {/* Contacto */}
      <div id="contact" className="space-y-8">
        <SectionHeader title="Contacto" subtitle="Informacion publica de contacto." />
        <FooterSection
          contact={settings.contact ?? {}}
          identity={settings.identity ?? {}}
          visuals={settings.visuals ?? {}}
          onEditContact={() => openEdit("contact")}
          onEditLegal={() => openEdit("legal")}
        />
      </div>
    </BrandSectionShell>
  );
}
