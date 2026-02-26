"use client";

import { useState } from "react";
import { BrandStudioLayout } from "@/features/brand/components/container/brand-studio-layout";
import { BrandNavRail } from "@/features/brand/components/navigation/brand-nav-rail";
import { Loader2 } from "lucide-react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

export default function BrandSettingsPage() {
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
    updateAllSettings
  } = useBrandSettings();

  const [activeSection, setActiveSection] = useState("identity");

  const handleNavigate = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (loading) {
    return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin" /></div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4">
        <div className="bg-destructive/10 text-destructive p-6 rounded-lg max-w-md text-center">
          <h3 className="font-semibold text-lg mb-2">Error al cargar configuración</h3>
          <p className="text-sm mb-4 opacity-90">{error.message || "Ocurrió un error inesperado."}</p>
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
    return <div>No se encontró la configuración.</div>;
  }

  return (
    <div className="flex flex-col md:flex-row bg-muted/30 relative h-[calc(100vh-4rem)]">
      
      {/* 1. The "Brand DNA Rail" (Sticky Left) */}
      <BrandNavRail 
        settings={settings} 
        activeSection={activeSection}
        onNavigate={handleNavigate}
        className="hidden md:flex shrink-0"
      />

      {/* 2. Main Content (Right) - Live Preview */}
      <main className="flex-1 overflow-hidden flex flex-col bg-muted/30 transition-all duration-300 min-w-0">
         
         {/* Mobile Header (Keep for mobile users) */}
         <div className="md:hidden p-4 border-b bg-background flex items-center justify-between">
            <h2 className="text-lg font-bold tracking-tight">Brand Studio</h2>
            {/* Mobile Nav could go here */}
         </div>

         <div className="flex-1 overflow-hidden">
             <BrandStudioLayout 
                settings={settings}
                loading={loading}
                saving={saving}
                onUpdateIdentity={updateIdentity}
                onUpdateTeam={updateTeam}
                onUpdateVault={updateVault}
                onUpdateContact={updateContact}
                onUpdateVisuals={updateVisuals}
                onUpdateStory={updateStory}
                onUpdateStrategy={updateStrategy}
                onUpdateTestimonials={updateTestimonials}
                onUpdateAll={updateAllSettings}
             />
         </div>
      </main>
    </div>
  );
}
