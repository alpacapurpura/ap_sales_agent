"use client";

import { useMemo } from "react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";
import { useBrandStudio } from "@/features/brand/context/brand-studio-context";
import { BrandSectionShell } from "../layout/brand-section-shell";
import { SectionHeader } from "../layout/section-header";
import { BRAND_SECTIONS, buildSectionNavItems } from "../../config/sections";

// Preview components
import { VisualsSection } from "../../sections/visuals/visuals-preview";
import { LogoKitPreview } from "../../sections/logos/logo-kit-preview";
import { GalleryManager } from "../../sections/gallery/gallery-manager";
import { VoiceSection } from "../../sections/voice/voice-preview";
import { AssetsPreview } from "../../sections/communication-assets/assets-preview";

const SECTION = BRAND_SECTIONS["identidad-creativa"];

/**
 * Identidad Creativa — "Tu imagen, voz y mensajes"
 *
 * Unified view combining: Gallery, Design System, Logos, Voice, Creative Concepts, Funnel Assets.
 */
export function IdentidadCreativaView() {
  const { settings } = useBrandSettings();
  const { openEdit } = useBrandStudio();

  const navItems = useMemo(
    () => (settings ? buildSectionNavItems("identidad-creativa", settings) : []),
    [settings],
  );

  if (!settings) return null;

  return (
    <BrandSectionShell title={SECTION.label} subtitle={SECTION.subtitle} navItems={navItems}>
      {/* Galeria de Marca */}
      <div id="gallery" className="space-y-8">
        <SectionHeader title="Galeria de Marca" subtitle="Media assets de la marca." />
        <GalleryManager visuals={settings.visuals ?? {}} />
      </div>

      {/* Sistema de Diseno */}
      <div id="visuals" className="space-y-8">
        <SectionHeader
          title="Sistema de Diseno"
          subtitle="Colores, tipografia y personalidad visual."
        />
        <VisualsSection
          visuals={settings.visuals ?? {}}
          onEdit={() => openEdit("visuals")}
          onExtract={() => openEdit("visuals-wizard")}
        />
      </div>

      {/* Logos */}
      <div id="logos" className="space-y-8">
        <SectionHeader title="Logo Kit" subtitle="Variantes de tu logo para distintos contextos." />
        <LogoKitPreview visuals={settings.visuals ?? {}} onEdit={() => openEdit("logos")} />
      </div>

      {/* Voz AI */}
      <div id="voice" className="space-y-8">
        <SectionHeader title="Voz AI" subtitle="Idioma, tono y estilo de comunicacion." />
        <VoiceSection identity={settings.identity ?? {}} onEdit={() => openEdit("voice")} />
      </div>

      {/* Conceptos Creativos & Funnel Assets */}
      <div id="creative-concepts" className="space-y-8">
        <SectionHeader
          title="Conceptos Creativos & Funnel Assets"
          subtitle="Plantillas de messaging reutilizables y piezas por etapa."
        />
        <div id="funnel-assets">
          <AssetsPreview
            communicationAssets={
              settings.communication_assets ?? {
                creative_concepts: [],
                assets: [],
                custom_asset_types: [],
              }
            }
            onEdit={() => openEdit("communication-assets")}
          />
        </div>
      </div>
    </BrandSectionShell>
  );
}
