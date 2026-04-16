"use client";

import { Loader2 } from "lucide-react";
import { usePathname, useRouter, useParams } from "next/navigation";
import { useCallback, useMemo } from "react";

import { BrandEmptyState } from "@/features/brand/components/empty-state/BrandEmptyState";
import { EditSheetManager } from "@/features/brand/components/forms/EditSheetManager";
import { SmartFillDialog } from "@/features/brand/components/smart-fill/SmartFillDialog";
import { BrandStudioTabs } from "@/features/brand/components/tabs/BrandStudioTabs";
import { BRAND_SECTIONS, type BrandSectionId } from "@/features/brand/config/sections";
import { BrandStudioProvider, useBrandStudio } from "@/features/brand/context/brand-studio-context";
import { useBrandSettings } from "@/features/brand/hooks/use-brand-settings";
import { BrandVisualsWizard } from "@/features/brand/sections/visuals/brand-visuals-wizard";
import { ThemeInjector } from "@/features/brand/sections/visuals/theme-injector";

import type {
  BrandIdentity,
  ContactData,
  KeyFigure,
  TestimonialItem,
  BrandVisuals,
} from "@/features/brand/types";

/**
 * Inner layout that consumes both BrandStudioContext and useBrandSettings.
 * Renders the shared overlay layer (edit sheets, wizards, dialogs) and
 * delegates page content to children.
 */
function BrandStudioInner({ children }: { children: React.ReactNode }) {
  const {
    settings,
    loading,
    error,
    refetch,
    saving,
    updateIdentity,
    updateTeam,
    updateVault,
    updateContact,
    updateVisuals,
    updateStory,
    updateStrategy,
    updateTestimonials,
  } = useBrandSettings();

  const {
    editMode,
    selectedItem,
    closeSheet,
    isSmartFillOpen,
    smartFillMode,
    closeSmartFill,
    hasDismissedEmptyState,
    dismissEmptyState,
  } = useBrandStudio();

  const pathname = usePathname();
  const router = useRouter();
  const params = useParams();
  const tenantId = params.tenantId as string;

  const activeTab = useMemo<BrandSectionId>(() => {
    const segment = pathname.split("/brand-studio/")[1]?.split("/")[0];
    if (segment && segment in BRAND_SECTIONS) return segment as BrandSectionId;
    return "esencia";
  }, [pathname]);

  const handleTabChange = useCallback(
    (tab: BrandSectionId) => {
      router.push(`/${tenantId}/brand-studio/${BRAND_SECTIONS[tab].slug}`);
    },
    [tenantId, router],
  );

  // When the wizard completes extraction, refetch settings and dismiss empty state.
  const handleWizardComplete = useCallback(() => {
    void refetch();
    dismissEmptyState();
  }, [refetch, dismissEmptyState]);

  // --- Loading ---
  if (loading) {
    return (
      <div className="flex justify-center items-center h-[calc(100vh-4rem)]">
        <Loader2 className="animate-spin h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  // --- Error ---
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-4rem)] p-4">
        <div className="bg-destructive/10 text-destructive p-6 rounded-lg max-w-md text-center">
          <h3 className="font-semibold text-lg mb-2">Error al cargar configuración</h3>
          <p className="text-sm mb-4 opacity-90">
            {error.message || "Ocurrió un error inesperado."}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-background border border-destructive/20 rounded hover:bg-background/80 text-sm font-medium transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-8 text-center text-muted-foreground">No se encontró la configuración.</div>
    );
  }

  // --- Empty state (first-time user) ---
  const hasExistingData = !!settings.identity?.brand_name;
  const showEmptyState = !hasExistingData && !hasDismissedEmptyState;

  if (showEmptyState) {
    return (
      <div className="relative w-full h-[calc(100vh-4rem)] bg-background flex flex-col overflow-hidden">
        <BrandEmptyState onStartAI={handleWizardComplete} onStartManual={dismissEmptyState} />
      </div>
    );
  }

  // --- Handlers that close sheet after save ---
  const handleUpdateIdentity = async (data: BrandIdentity) => {
    await updateIdentity(data);
    closeSheet();
  };
  const handleUpdateContact = async (data: ContactData) => {
    await updateContact(data);
    closeSheet();
  };
  const handleUpdateTeam = async (data: KeyFigure[]) => {
    await updateTeam(data);
    closeSheet();
  };
  const handleUpdateTestimonials = async (data: TestimonialItem[]) => {
    await updateTestimonials(data);
    closeSheet();
  };
  const handleUpdateVisuals = async (data: BrandVisuals) => {
    await updateVisuals(data);
    closeSheet();
  };

  return (
    <div className="relative w-full h-full">
      <ThemeInjector visuals={settings.visuals ?? {}} />

      {/* Tab navigation between Brand Studio sections */}
      <BrandStudioTabs activeTab={activeTab} onTabChange={handleTabChange} settings={settings} />

      {/* Page content (section view) */}
      {children}

      {/* Shared overlay layer — persists across section navigation */}
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
          onUpdateVault: updateVault,
          onUpdateVisuals: handleUpdateVisuals,
          onUpdateTestimonials: handleUpdateTestimonials,
          onUpdateStory: updateStory,
          onUpdateStrategy: updateStrategy,
        }}
      />

      <BrandVisualsWizard
        isOpen={editMode === "visuals-wizard"}
        onOpenChange={(open) => !open && closeSheet()}
        currentVisuals={settings.visuals ?? {}}
        logoUrl={settings.visuals?.logo_url}
        websiteUrl={settings.identity?.website}
        onSave={handleUpdateVisuals}
      />

      {/* SmartFillDialog remains in overlay — used for "Refinar con IA" (update mode) */}
      <SmartFillDialog
        open={isSmartFillOpen}
        onOpenChange={(open) => !open && closeSmartFill()}
        mode={smartFillMode}
        onSuccess={() => {
          window.location.reload();
        }}
        currentUrl={settings.identity?.website}
      />
    </div>
  );
}

/**
 * Next.js layout for /brand-studio/* routes.
 *
 * Wraps all sub-pages with:
 * - BrandStudioProvider (edit/smartfill state)
 * - Brand settings data loading
 * - Shared overlays (edit sheets, wizards, dialogs)
 * - Theme injection
 * - BrandStudioTabs for section navigation
 *
 * This ensures navigating between sections doesn't re-mount
 * the overlay layer or re-fetch settings.
 */
export default function BrandStudioLayout({ children }: { children: React.ReactNode }) {
  return (
    <BrandStudioProvider>
      <BrandStudioInner>{children}</BrandStudioInner>
    </BrandStudioProvider>
  );
}
