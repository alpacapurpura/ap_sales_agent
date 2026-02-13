"use client";

import { useState } from "react";
import { BrandSettings, BrandIdentity, KeyFigure, AuthorityItem, ContactData, BrandVisuals, BrandStory, BrandStrategy, TestimonialItem } from "@/lib/api/brand";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

// Preview Components (The "Live Document")
import { HeaderSection } from "../preview/header-section";
import { FooterSection } from "../preview/footer-section";
import { StrategySection } from "../preview/strategy-section";
import { VoiceSection } from "../preview/voice-section";
import { TrustSection } from "../preview/trust-section";
import { MethodologySection } from "../preview/methodology-section";
import { StorySection } from "../preview/story-section";
import { TeamSection } from "../preview/team-section";
import { AvatarsSection } from "../preview/avatars-section";
import { VisualsSection } from "../preview/visuals-section";
import { GallerySection } from "../live-preview/gallery-section";
import { TestimonialsSection } from "../preview/testimonials-section";

// Forms & Managers
import { EditSheetManager } from "../forms/edit-sheet-manager";
import { BrandVisualsWizard } from "../visuals/brand-visuals-wizard";
import { ThemeInjector } from "../visuals/theme-injector";

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
}

export type EditMode = "none" | "identity" | "voice" | "legal" | "authority" | "team" | "testimonials" | "contact" | "avatars" | "visuals" | "visuals-wizard" | "story" | "strategy" | "methodology";

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
  onUpdateStrategy
}: BrandStudioLayoutProps) {
  const [editMode, setEditMode] = useState<EditMode>("none");
  const [selectedItem, setSelectedItem] = useState<any>(null);

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

  return (
    <div className="relative w-full h-full bg-background flex flex-col overflow-hidden">
      <ThemeInjector visuals={settings.visuals} />

      {/* Main Content Area - "The Live Document" */}
      <ScrollArea className="flex-1 w-full">
        <div className="max-w-5xl mx-auto pb-20">
            
            {/* HEADER - Visual Anchor (Full Brand Style) */}
            <div id="identity" className="mb-12 p-4 md:p-8">
                <HeaderSection 
                    identity={settings.identity} 
                    visuals={settings.visuals}
                    onEdit={() => openEdit("identity")} 
                    onEditVisuals={() => openEdit("visuals")}
                />
            </div>

            {/* BODY - Editorial Style (Clean, No Cards) */}
            <div className="space-y-20 px-6 md:px-12">
                
                {/* BLOQUE 1: EL ADN (Estrategia & Historia) */}
                <div className="space-y-12">
                    <div className="border-b pb-4">
                        <h2 className="text-2xl font-bold tracking-tight text-foreground/80">I. El ADN de Marca</h2>
                        <p className="text-muted-foreground mt-1">Estrategia, Historia y Personalidad.</p>
                    </div>

                    <div id="strategy" className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <StrategySection 
                            strategy={settings.strategy}
                            visuals={settings.visuals}
                            onEdit={() => openEdit("strategy")}
                        />
                        <MethodologySection 
                            strategy={settings.strategy}
                            visuals={settings.visuals}
                            onEdit={() => openEdit("methodology")}
                        />
                    </div>

                    <div id="story" className="grid grid-cols-1 md:grid-cols-2 gap-12">
                         <StorySection 
                            story={settings.story} 
                            visuals={settings.visuals}
                            onEdit={() => openEdit("story")}
                        />
                        <div className="space-y-12">
                            <VoiceSection 
                                identity={settings.identity}
                                onEdit={() => openEdit("voice")}
                            />
                            <AvatarsSection 
                                visuals={settings.visuals}
                                onEdit={(item) => openEdit("avatars", item)}
                            />
                        </div>
                    </div>
                </div>

                {/* BLOQUE 2: UNIVERSO VISUAL */}
                <div className="space-y-12">
                    <div className="border-b pb-4">
                        <h2 className="text-2xl font-bold tracking-tight text-foreground/80">II. Universo Visual</h2>
                        <p className="text-muted-foreground mt-1">Look & Feel, Colores y Galería.</p>
                    </div>

                    <div id="visuals">
                        <VisualsSection 
                            visuals={settings.visuals}
                            onEdit={() => openEdit("visuals")}
                            onExtract={() => openEdit("visuals-wizard")}
                        />
                    </div>
                    
                    <div id="gallery">
                        <GallerySection visuals={settings.visuals} />
                    </div>
                </div>

                {/* BLOQUE 3: VALIDACIÓN SOCIAL */}
                <div className="space-y-12">
                    <div className="border-b pb-4">
                        <h2 className="text-2xl font-bold tracking-tight text-foreground/80">III. Validación Social</h2>
                        <p className="text-muted-foreground mt-1">Equipo, Testimonios y Autoridad.</p>
                    </div>

                    <div id="team" className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <TeamSection 
                            team={settings.team}
                            visuals={settings.visuals}
                            onEdit={(item) => openEdit("team", item)}
                        />
                        <TestimonialsSection 
                            testimonials={settings.testimonials}
                            onEdit={(item) => openEdit("testimonials", item)}
                        />
                    </div>

                    <div id="authority">
                        <TrustSection 
                            identity={settings.identity}
                            authority={settings.authority_vault}
                            visuals={settings.visuals}
                            onEditIdentity={() => openEdit("identity")}
                            onEditAuthority={(item) => openEdit("authority", item)}
                        />
                    </div>
                </div>
            </div>

            {/* FOOTER - Visual Anchor (Full Brand Style) */}
            <div id="contact" className="mt-20">
                <FooterSection 
                    contact={settings.contact}
                    identity={settings.identity}
                    visuals={settings.visuals}
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
        currentVisuals={settings.visuals}
        logoUrl={settings.identity.logo_url}
        websiteUrl={settings.identity.website}
        onSave={handleUpdateVisuals}
      />
    </div>
  );
}
