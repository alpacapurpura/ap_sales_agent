"use client";

import { useState, useMemo } from "react";
import { BrandSettings, BrandIdentity, KeyFigure, AuthorityItem, ContactData, BrandVisuals, BrandStory, BrandStrategy, TestimonialItem } from "@/features/brand/types";
import { Info } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

// Preview Components (The "Live Document")
import { HeaderSection } from "../../sections/identity/identity-header-preview";
import { FooterSection } from "../../sections/contact/contact-footer-preview";
import { DifferentiationPreview } from "../../sections/differentiation/differentiation-preview";
import { MarketPreview } from "../../sections/market/market-preview";
import { VoiceSection } from "../../sections/voice/voice-preview";
import { TrustSection } from "../../sections/authority/authority-preview";
import { MethodologySection } from "../../sections/methodology/methodology-preview";
import { StorySection } from "../../sections/story/story-preview";
import { TeamSection } from "../../sections/team/team-preview";
import { AvatarsSection } from "../../sections/avatars/avatars-preview";
import { VisualsSection } from "../../sections/visuals/visuals-preview";
import { GalleryManager } from "../../sections/gallery/gallery-manager";
import { LogoKitPreview } from "../../sections/logos/logo-kit-preview";
import { TestimonialsSection } from "../../sections/testimonials/testimonials-preview";

import { ValuesEssencePreview } from "../../sections/positioning/values-essence-preview";
import { NarrativePreview } from "../../sections/narrative/narrative-preview";
import { AssetsPreview } from "../../sections/communication-assets/assets-preview";

// Forms & Managers
import { EditSheetManager } from "../forms/edit-sheet-manager";
import { BrandVisualsWizard } from "../../sections/visuals/brand-visuals-wizard";
import { ThemeInjector } from "../../sections/visuals/theme-injector";
import { BrandEmptyState } from "../empty-state/brand-empty-state";
import { SmartFillDialog } from "../smart-fill/smart-fill-dialog";

function ChapterHeader({ number, title, subtitle, tooltip }: { number: number; title: string; subtitle: string; tooltip?: string }) {
  return (
    <div className="border-b pb-4">
      <div className="flex items-center gap-2">
        <h2 className="text-2xl font-bold tracking-tight text-foreground/80">{number}. {title}</h2>
        {tooltip && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="w-4 h-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent><p>{tooltip}</p></TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
      <p className="text-muted-foreground mt-1">{subtitle}</p>
    </div>
  );
}

interface BrandStudioLayoutProps {
  settings: BrandSettings;
  loading: boolean;
  saving: boolean;
  onUpdateIdentity: (data: BrandIdentity) => Promise<void>;
  onUpdateTeam: (data: KeyFigure[]) => Promise<void>;
  onUpdateVault: (data: AuthorityItem[]) => Promise<void>;
  onUpdateContact: (data: ContactData) => Promise<void>;
  onUpdateVisuals: (data: BrandVisuals) => Promise<void>;
  onUpdateTestimonials: (data: TestimonialItem[]) => Promise<void>;
  onUpdateStory?: (data: BrandStory) => Promise<void>;
  onUpdateStrategy?: (data: BrandStrategy) => Promise<void>;
  onUpdateAll?: (data: Partial<BrandSettings>) => Promise<void>;
}

export type EditMode = "none" | "identity" | "voice" | "legal" | "authority" | "team" | "testimonials" | "contact" | "avatars" | "visuals" | "visuals-wizard" | "logos" | "story" | "methodology" | "positioning" | "values-essence" | "storybrand" | "communication-assets";

export function BrandStudioLayout({
  settings,
  loading,
  saving,
  onUpdateIdentity,
  onUpdateTeam,
  onUpdateVault,
  onUpdateContact,
  onUpdateVisuals,
  onUpdateTestimonials,
  onUpdateStory,
  onUpdateStrategy,
  onUpdateAll
}: BrandStudioLayoutProps) {
  const [editMode, setEditMode] = useState<EditMode>("none");
  const [selectedItem, setSelectedItem] = useState<any>(null);

  // UX State
  const [isSmartFillOpen, setIsSmartFillOpen] = useState(false);
  const [smartFillMode, setSmartFillMode] = useState<"initial" | "update">("initial");
  const [hasDismissedEmptyState, setHasDismissedEmptyState] = useState(false);

  const closeSheet = () => {
    setEditMode("none");
    setSelectedItem(null);
  };

  const openEdit = (mode: EditMode, item?: any) => {
    setSelectedItem(item || null);
    setEditMode(mode);
  };

  // Handlers
  const handleUpdateIdentity = async (data: BrandIdentity) => {
    await onUpdateIdentity(data);
    closeSheet();
  };

  const handleUpdateContact = async (data: ContactData) => {
    await onUpdateContact(data);
    closeSheet();
  };

  const handleUpdateTeam = async (data: KeyFigure[]) => {
    await onUpdateTeam(data);
    closeSheet();
  };

  const handleUpdateTestimonials = async (data: TestimonialItem[]) => {
    await onUpdateTestimonials(data);
    closeSheet();
  };

  const handleUpdateVisuals = async (data: BrandVisuals) => {
    await onUpdateVisuals(data);
    setEditMode("none");
  };

  const handleSmartFillSuccess = () => {
    // Data is already saved to DB by the backend — just reload to display it
    window.location.reload();
  };

  const hasExistingData = !!settings.identity?.brand_name;
  const showEmptyState = !hasExistingData && !hasDismissedEmptyState;

  if (showEmptyState) {
    return (
        <div className="relative w-full h-full bg-background flex flex-col overflow-hidden">
             <BrandEmptyState
                onStartAI={() => {
                    setSmartFillMode("initial");
                    setIsSmartFillOpen(true);
                }}
                onStartManual={() => {
                    setHasDismissedEmptyState(true);
                }}
            />
             <SmartFillDialog
                open={isSmartFillOpen}
                onOpenChange={setIsSmartFillOpen}
                mode={smartFillMode}
                onSuccess={() => {
                    handleSmartFillSuccess();
                    setHasDismissedEmptyState(true);
                }}
                currentUrl={settings.contact?.website}
            />
        </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-background flex flex-col overflow-hidden">
      <ThemeInjector visuals={settings.visuals ?? {}} />

      {/* Main Content Area - "The Live Document" */}
      <ScrollArea className="flex-1 w-full">
        <div className="max-w-5xl mx-auto pb-20">

            {/* HEADER - Visual Anchor (Full Brand Style) */}
            <div id="identity" className="mb-12 p-4 md:p-8">
                <HeaderSection
                    identity={settings.identity ?? {}}
                    visuals={settings.visuals ?? {}}
                    contact={settings.contact ?? {}}
                    onEdit={() => openEdit("identity")}
                    onEditVisuals={() => openEdit("visuals")}
                    onRefine={() => {
                        setSmartFillMode("update");
                        setIsSmartFillOpen(true);
                    }}
                />
            </div>

            {/* BODY - Brand Book Narrativo (9 Chapters) */}
            <div className="space-y-20 px-6 md:px-12">

                {/* CAPITULO 1: ORIGEN */}
                <div className="space-y-12">
                    <ChapterHeader number={1} title="Origen" subtitle="Identidad, Historia y Metodologia." />

                    <div id="story">
                        <StorySection
                            story={settings.story ?? {}}
                            visuals={settings.visuals ?? {}}
                            onEdit={() => openEdit("story")}
                        />
                    </div>

                    <div id="methodology">
                        <MethodologySection
                            strategy={settings.strategy ?? {} as BrandStrategy}
                            visuals={settings.visuals ?? {}}
                            onEdit={() => openEdit("methodology")}
                        />
                    </div>
                </div>

                {/* CAPITULO 2: DIFERENCIACION */}
                <div className="space-y-12">
                    <ChapterHeader number={2} title="Diferenciacion" subtitle="Propuesta unica, beneficios y razones para creer." tooltip="Basado en Brand Love Key" />
                    <div id="positioning">
                        <DifferentiationPreview
                            positioning={settings.positioning ?? { reasons_to_believe: [] }}
                            onEdit={() => openEdit("positioning")}
                        />
                    </div>
                </div>

                {/* CAPITULO 3: EL MERCADO */}
                <div className="space-y-12">
                    <ChapterHeader number={3} title="El Mercado" subtitle="Competidores, enemigos e insight del cliente." tooltip="Basado en Brand Love Key" />
                    <div id="market">
                        <MarketPreview
                            positioning={settings.positioning ?? { reasons_to_believe: [] }}
                            onEdit={() => openEdit("positioning")}
                        />
                    </div>
                </div>

                {/* CAPITULO 4: PERSONALIDAD */}
                <div id="values-essence" className="space-y-12">
                    <ChapterHeader number={4} title="Personalidad" subtitle="Valores, arquetipo y esencia de marca." tooltip="Basado en Brand Love Key" />
                    <ValuesEssencePreview
                        positioning={settings.positioning ?? { reasons_to_believe: [] }}
                        onEdit={() => openEdit("values-essence")}
                    />
                </div>

                {/* CAPITULO 5: LA HISTORIA */}
                <div id="storybrand" className="space-y-12">
                    <ChapterHeader number={5} title="La Historia" subtitle="El viaje del heroe: problema, guia, plan y transformacion." />
                    <NarrativePreview
                        narrative={settings.narrative ?? { plan: [] }}
                        onEdit={() => openEdit("storybrand")}
                    />
                </div>

                {/* CAPITULO 6: LA VOZ */}
                <div id="voice" className="space-y-12">
                    <ChapterHeader number={6} title="La Voz" subtitle="Idioma, tono, estilo y activos de comunicacion." />
                    <VoiceSection
                        identity={settings.identity ?? {}}
                        onEdit={() => openEdit("voice")}
                    />
                    <div id="communication-assets">
                        <AssetsPreview
                            communicationAssets={settings.communication_assets ?? { creative_concepts: [], assets: [], custom_asset_types: [] }}
                            onEdit={() => openEdit("communication-assets")}
                        />
                    </div>
                </div>

                {/* CAPITULO 7: EL PUBLICO */}
                <div id="avatars" className="space-y-12">
                    <ChapterHeader number={7} title="El Publico" subtitle="Tu cliente ideal y buyer personas." />
                    <AvatarsSection
                        visuals={settings.visuals ?? {}}
                        onEdit={(item) => openEdit("avatars", item)}
                    />
                </div>

                {/* CAPITULO 8: LA IMAGEN */}
                <div className="space-y-12">
                    <ChapterHeader number={8} title="La Imagen" subtitle="Look & Feel, Colores y Galeria." />
                    <div id="visuals">
                        <VisualsSection
                            visuals={settings.visuals ?? {}}
                            onEdit={() => openEdit("visuals")}
                            onExtract={() => openEdit("visuals-wizard")}
                        />
                    </div>
                    <div id="logos">
                        <LogoKitPreview visuals={settings.visuals ?? {}} onEdit={() => openEdit("logos")} />
                    </div>
                    <div id="gallery">
                        <GalleryManager visuals={settings.visuals ?? {}} />
                    </div>
                </div>

                {/* CAPITULO 9: CREDIBILIDAD */}
                <div className="space-y-12">
                    <ChapterHeader number={9} title="Credibilidad" subtitle="Equipo, Testimonios y Autoridad." />
                    <div id="team" className="grid grid-cols-1 md:grid-cols-2 gap-12">
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
                    <div id="authority">
                        <TrustSection
                            identity={settings.identity ?? {}}
                            authority={settings.authority_vault ?? []}
                            visuals={settings.visuals ?? {}}
                            onEditIdentity={() => openEdit("identity")}
                            onEditAuthority={(item) => openEdit("authority", item)}
                        />
                    </div>
                </div>
            </div>

            {/* FOOTER - Visual Anchor (Full Brand Style) */}
            <div id="contact" className="mt-20">
                <FooterSection
                    contact={settings.contact ?? {}}
                    identity={settings.identity ?? {}}
                    visuals={settings.visuals ?? {}}
                    onEditContact={() => setEditMode("contact")}
                    onEditLegal={() => setEditMode("legal")}
                />
            </div>
        </div>
      </ScrollArea>

      {/* EDIT MANAGER - Sidebar Orchestrator */}
      <EditSheetManager
        mode={editMode}
        selectedItem={selectedItem}
        isOpen={editMode !== "none" && editMode !== "visuals-wizard"}
        onClose={closeSheet}
        settings={settings}
        saving={saving}
        handlers={{
            onUpdateIdentity: handleUpdateIdentity,
            onUpdateContact: handleUpdateContact,
            onUpdateTeam: handleUpdateTeam,
            onUpdateVault: onUpdateVault,
            onUpdateVisuals: handleUpdateVisuals,
            onUpdateTestimonials: handleUpdateTestimonials,
            onUpdateStory,
            onUpdateStrategy
        }}
      />

      {/* Special Wizard for Visuals (Dialog, not Sheet) */}
      <BrandVisualsWizard
        isOpen={editMode === "visuals-wizard"}
        onOpenChange={(open) => !open && closeSheet()}
        currentVisuals={settings.visuals ?? {}}
        logoUrl={settings.visuals?.logo_url}
        websiteUrl={settings.contact?.website}
        onSave={handleUpdateVisuals}
      />

      <SmartFillDialog
        open={isSmartFillOpen}
        onOpenChange={setIsSmartFillOpen}
        mode={smartFillMode}
        onSuccess={() => {
            handleSmartFillSuccess();
            setHasDismissedEmptyState(true);
        }}
        currentUrl={settings.contact?.website}
      />
    </div>
  );
}
