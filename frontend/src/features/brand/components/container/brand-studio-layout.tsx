"use client";

import { useState, useMemo } from "react";
import { BrandSettings, BrandIdentity, KeyFigure, AuthorityItem, ContactData, BrandVisuals, BrandStory, BrandStrategy, TestimonialItem } from "@/features/brand/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Eye, X, Save } from "lucide-react";

// Preview Components (The "Live Document")
import { HeaderSection } from "../../sections/identity/identity-header-preview";
import { FooterSection } from "../../sections/contact/contact-footer-preview";
import { StrategySection } from "../../sections/strategy/strategy-preview";
import { VoiceSection } from "../../sections/voice/voice-preview";
import { TrustSection } from "../../sections/authority/authority-preview";
import { MethodologySection } from "../../sections/methodology/methodology-preview";
import { StorySection } from "../../sections/story/story-preview";
import { TeamSection } from "../../sections/team/team-preview";
import { AvatarsSection } from "../../sections/avatars/avatars-preview";
import { VisualsSection } from "../../sections/visuals/visuals-preview";
import { GalleryManager } from "../../sections/gallery/gallery-manager";
import { TestimonialsSection } from "../../sections/testimonials/testimonials-preview";

// Forms & Managers
import { EditSheetManager } from "../forms/edit-sheet-manager";
import { BrandVisualsWizard } from "../../sections/visuals/brand-visuals-wizard";
import { ThemeInjector } from "../../sections/visuals/theme-injector";
import { BrandEmptyState } from "../empty-state/brand-empty-state";
import { SmartFillDialog } from "../smart-fill/smart-fill-dialog";

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
  onUpdateStrategy,
  onUpdateAll
}: BrandStudioLayoutProps) {
  const [editMode, setEditMode] = useState<EditMode>("none");
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [previewData, setPreviewData] = useState<Partial<BrandSettings> | null>(null);
  
  // UX State
  const [isSmartFillOpen, setIsSmartFillOpen] = useState(false);
  const [smartFillMode, setSmartFillMode] = useState<"initial" | "update">("initial");
  const [hasDismissedEmptyState, setHasDismissedEmptyState] = useState(false);

  const displaySettings = useMemo(() => {
    if (!previewData) return settings;
    
    // Helper to merge objects safely
    const mergeObjects = (original: any, preview: any) => {
        return { ...(original || {}), ...(preview || {}) };
    };

    return {
        ...settings,
        ...previewData,
        identity: mergeObjects(settings.identity, previewData.identity),
        story: mergeObjects(settings.story, previewData.story),
        strategy: mergeObjects(settings.strategy, previewData.strategy),
        visuals: { 
            ...settings.visuals, 
            ...previewData.visuals,
            logos: {
                ...(settings.visuals?.logos || {}),
                ...(previewData.visuals?.logos || {})
            }
        },
        contact: mergeObjects(settings.contact, previewData.contact),
        
        // Arrays: Prefer previewData if it exists (even if empty, though unlikely from extraction)
        // If previewData is partial and MISSING these keys, fallback to settings.
        // We use !== undefined to catch empty arrays too (which are valid new data)
        team: previewData.team !== undefined ? previewData.team : settings.team,
        testimonials: previewData.testimonials !== undefined ? previewData.testimonials : settings.testimonials,
        authority_vault: previewData.authority_vault !== undefined ? previewData.authority_vault : settings.authority_vault,
    };
  }, [settings, previewData]);

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

  const handlePreview = (data: Partial<BrandSettings> | null) => {
    setPreviewData(data);
    if (data) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleApplyPreview = async () => {
    if (!previewData) return;
    await handleSmartFillSuccess(previewData);
    setPreviewData(null);
  };

  const handleSmartFillSuccess = async (data: Partial<BrandSettings>) => {
    // 0. Prefer atomic update if available (Prevents race conditions)
    if (onUpdateAll) {
        await onUpdateAll(data);
        window.location.reload();
        return;
    }

    // Fallback: Sequential Updates (May have race conditions)
    // 1. Update Identity (Always)
    if (data.identity) {
        await onUpdateIdentity(data.identity);
    }
    
    // 2. Update Story (If handler exists)
    if (data.story && onUpdateStory) {
        await onUpdateStory(data.story);
    }
    
    // 3. Update Strategy (If handler exists)
    if (data.strategy && onUpdateStrategy) {
        await onUpdateStrategy(data.strategy);
    }
    
    // 4. Update Visuals
    if (data.visuals) {
        await onUpdateVisuals(data.visuals);
    }
    
    // 5. Update Team
    if (data.team) {
        await onUpdateTeam(data.team);
    }
    
    // 6. Update Testimonials
    if (data.testimonials) {
        await onUpdateTestimonials(data.testimonials);
    }
    
    // 7. Update Contact
    if (data.contact) {
        await onUpdateContact(data.contact);
    }
    
    // 8. Update Vault
    if (data.authority_vault) {
        await onUpdateVault(data.authority_vault);
    }

    // Force refresh or notify user
    window.location.reload(); // Simple brute force refresh to ensure data is seen
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
                onSuccess={(data) => {
                    handleSmartFillSuccess(data);
                    setHasDismissedEmptyState(true);
                }}
                onPreview={handlePreview}
                currentUrl={settings.contact?.website}
            />
        </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-background flex flex-col overflow-hidden">
      <ThemeInjector visuals={displaySettings.visuals ?? {}} />

      {/* Main Content Area - "The Live Document" */}
      <ScrollArea className="flex-1 w-full">
        {previewData && (
             <div className="sticky top-0 z-50 p-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-primary/20 animate-in slide-in-from-top">
                <Alert className="border-primary/50 bg-primary/5">
                    <Eye className="h-4 w-4 text-primary" />
                    <AlertTitle className="text-primary font-semibold flex items-center gap-2">
                        Modo Previsualización
                        <span className="text-xs font-normal text-muted-foreground ml-2 hidden sm:inline-block">
                            Estás viendo datos extraídos no guardados.
                        </span>
                    </AlertTitle>
                    <AlertDescription className="mt-2 flex items-center gap-4">
                        <Button size="sm" onClick={handleApplyPreview} className="gap-2">
                            <Save className="h-4 w-4" /> Aplicar Cambios
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setPreviewData(null)} className="gap-2 text-muted-foreground hover:text-destructive">
                            <X className="h-4 w-4" /> Descartar
                        </Button>
                    </AlertDescription>
                </Alert>
            </div>
        )}
        <div className="max-w-5xl mx-auto pb-20">
            
            {/* HEADER - Visual Anchor (Full Brand Style) */}
            <div id="identity" className="mb-12 p-4 md:p-8">
                <HeaderSection
                    identity={displaySettings.identity ?? {}}
                    visuals={displaySettings.visuals ?? {}}
                    contact={displaySettings.contact ?? {}}
                    onEdit={() => openEdit("identity")}
                    onEditVisuals={() => openEdit("visuals")}
                    onRefine={() => {
                        setSmartFillMode("update");
                        setIsSmartFillOpen(true);
                    }}
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
                            strategy={displaySettings.strategy}
                            visuals={displaySettings.visuals ?? {}}
                            onEdit={() => openEdit("strategy")}
                        />
                        <MethodologySection
                            strategy={displaySettings.strategy}
                            visuals={displaySettings.visuals ?? {}}
                            onEdit={() => openEdit("methodology")}
                        />
                    </div>

                    <div id="story" className="space-y-12">
                         <StorySection
                            story={displaySettings.story ?? {}}
                            visuals={displaySettings.visuals ?? {}}
                            onEdit={() => openEdit("story")}
                        />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <VoiceSection
                                identity={displaySettings.identity ?? {}}
                                onEdit={() => openEdit("voice")}
                            />
                            <AvatarsSection
                                visuals={displaySettings.visuals ?? {}}
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
                            visuals={displaySettings.visuals ?? {}}
                            onEdit={() => openEdit("visuals")}
                            onExtract={() => openEdit("visuals-wizard")}
                        />
                    </div>

                    <div id="gallery">
                        <GalleryManager visuals={displaySettings.visuals ?? {}} />
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
                            team={displaySettings.team ?? []}
                            visuals={displaySettings.visuals ?? {}}
                            onEdit={(item) => openEdit("team", item)}
                        />
                        <TestimonialsSection
                            testimonials={displaySettings.testimonials ?? []}
                            onEdit={(item) => openEdit("testimonials", item)}
                        />
                    </div>

                    <div id="authority">
                        <TrustSection
                            identity={displaySettings.identity ?? {}}
                            authority={displaySettings.authority_vault ?? []}
                            visuals={displaySettings.visuals ?? {}}
                            onEditIdentity={() => openEdit("identity")}
                            onEditAuthority={(item) => openEdit("authority", item)}
                        />
                    </div>
                </div>
            </div>

            {/* FOOTER - Visual Anchor (Full Brand Style) */}
            <div id="contact" className="mt-20">
                <FooterSection
                    contact={displaySettings.contact ?? {}}
                    identity={displaySettings.identity ?? {}}
                    visuals={displaySettings.visuals ?? {}}
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
        settings={displaySettings}
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
        currentVisuals={displaySettings.visuals ?? {}}
        logoUrl={displaySettings.visuals?.logo_url}
        websiteUrl={displaySettings.contact?.website}
        onSave={handleUpdateVisuals}
      />

      <SmartFillDialog
        open={isSmartFillOpen}
        onOpenChange={setIsSmartFillOpen}
        mode={smartFillMode}
        onSuccess={(data) => {
            handleSmartFillSuccess(data);
            setHasDismissedEmptyState(true);
        }}
        onPreview={handlePreview}
        currentUrl={settings.contact?.website}
      />
    </div>
  );
}
