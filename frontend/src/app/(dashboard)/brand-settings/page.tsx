"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BrandIdentityForm } from "@/features/brand/components/brand-identity-form";
import { KeyFiguresForm } from "@/features/brand/components/key-figures-form";
import { AuthorityVaultForm } from "@/features/brand/components/authority-vault-form";
import { ContactDataForm } from "@/features/brand/components/contact-data-form";
import { AvatarManager } from "@/features/brand/components/avatar-manager";
import { PersonalityCloneForm } from "@/features/brand/components/personality-clone-form";
import { Loader2, Building2, Phone, Users, Brain, ShieldCheck } from "lucide-react";
import { useBrandSettings } from "@/features/brand/hooks/useBrandSettings";

export default function BrandSettingsPage() {
  const { 
    settings, 
    loading, 
    saving, 
    updateIdentity, 
    updateTeam, 
    updateVault, 
    updateContact 
  } = useBrandSettings();

  if (loading) {
    return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin" /></div>;
  }

  if (!settings) {
    return <div>Error al cargar configuración.</div>;
  }

  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Sobre la Marca (Global Brand Settings)</h2>
        <p className="text-muted-foreground">
          Datos inmutables que definen la Identidad y Credibilidad de tu empresa ante el mundo.
        </p>
      </div>
      <div className="border-t my-6" />

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs defaultValue="identity" className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
          <aside className="-mx-4 lg:w-1/5">
            <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
                
                {/* Grupo: Global */}
                <div className="w-full px-4 mb-2 mt-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Global
                  </h3>
                </div>
                
                <TabsTrigger 
                  value="identity" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Building2 className="mr-2 h-4 w-4" />
                  Información Corporativa
                </TabsTrigger>
                <TabsTrigger 
                  value="contact" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Phone className="mr-2 h-4 w-4" />
                  Datos de Contacto
                </TabsTrigger>

                {/* Grupo: Autoridad */}
                <div className="w-full px-4 mb-2 mt-6">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Autoridad
                  </h3>
                </div>

                <TabsTrigger 
                  value="key_figures" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Users className="mr-2 h-4 w-4" />
                  Key Figures
                </TabsTrigger>

                <TabsTrigger 
                  value="authority_vault" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <ShieldCheck className="mr-2 h-4 w-4" />
                  Respaldo Institucional
                </TabsTrigger>

                {/* Grupo: Marca */}
                <div className="w-full px-4 mb-2 mt-6">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Marca
                  </h3>
                </div>

                <TabsTrigger 
                  value="avatars" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Users className="mr-2 h-4 w-4" />
                  Avatares
                </TabsTrigger>
                <TabsTrigger 
                  value="personality" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Personalidad IA
                </TabsTrigger>

            </TabsList>
          </aside>

          <div className="flex-1 lg:max-w-4xl">
            <TabsContent value="identity" className="mt-0">
            <BrandIdentityForm 
                initialData={settings.identity} 
                onSave={updateIdentity}
                isSaving={saving}
            />
            </TabsContent>
            
            <TabsContent value="contact" className="mt-0">
            <ContactDataForm 
                initialData={settings.contact}
                onSave={updateContact}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="key_figures" className="mt-0">
            <KeyFiguresForm 
                initialData={settings.team}
                onSave={updateTeam}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="authority_vault" className="mt-0">
            <AuthorityVaultForm 
                initialData={settings.authority_vault}
                onSave={updateVault}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="avatars" className="mt-0">
                <AvatarManager />
            </TabsContent>

            <TabsContent value="personality" className="mt-0">
                <PersonalityCloneForm />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
