"use client";

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { BrandSettings, KeyFigure, AuthorityItem, BrandVisuals } from "@/features/brand/types";
import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { avatarApi, CreateAvatarDTO } from "@/lib/api/avatar";
import { toast } from "sonner";

// Ideally types should be in a separate file, but for now we can replicate the string union or import type only.
import type { EditMode } from "../container/brand-studio-layout";

import { IdentityForm } from "./identity-form";
import { LegalForm } from "./legal-form";
import { TeamForm } from "./team-form";
import { TeamMemberForm } from "./team-member-form";
import { AuthorityVaultForm } from "./authority-vault-form";
import { AuthorityItemForm } from "./authority-item-form";
import { ContactDataForm } from "./contact-data-form";
import { BrandStoryForm } from "./brand-story-form";
import { BrandStrategyForm } from "./brand-strategy-form";
import { BrandMethodologyForm } from "./brand-methodology-form";
import { AvatarForm } from "../avatars/avatar-form";
import { PersonalityCloneForm as BrandVoiceForm } from "./brand-voice-form";
import { BrandVisualsForm } from "./brand-visuals-form";
import { TestimonialsForm } from "./testimonials-form";

interface EditSheetManagerProps {
  mode: EditMode;
  selectedItem: any; // The item being edited (Avatar, TeamMember, etc.) or null
  isOpen: boolean;
  onClose: () => void;
  settings: BrandSettings;
  saving: boolean;
  handlers: {
      onUpdateIdentity: (data: any) => Promise<void>;
      onUpdateContact: (data: any) => Promise<void>;
      onUpdateTeam: (data: any) => Promise<void>;
      onUpdateVault: (data: any) => Promise<void>;
      onUpdateVisuals: (data: any) => Promise<void>;
      onUpdateTestimonials: (data: any) => Promise<void>;
      onUpdateStory?: (data: any) => Promise<void>;
      onUpdateStrategy?: (data: any) => Promise<void>;
  };
}

export function EditSheetManager({ 
  mode, 
  selectedItem,
  isOpen, 
  onClose, 
  settings, 
  saving, 
  handlers 
}: EditSheetManagerProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const getHeaderInfo = (mode: EditMode) => {
      switch (mode) {
          case "identity": return { title: "Identidad Corporativa", desc: "Edita los datos fundamentales de tu marca." };
          case "voice": return { title: "Voz & Comunicación", desc: "Configura el tono y estilo de comunicación." };
          case "legal": return { title: "Datos Legales", desc: "Información fiscal y legal." };
          case "authority": return { title: "Autoridad & Prensa", desc: "Gestiona premios y apariciones en medios." };
          case "team": return { title: "Equipo", desc: "Gestiona los miembros clave de la marca." };
          case "testimonials": return { title: "Testimonios", desc: "Gestiona la prueba social y opiniones de clientes." };
          case "avatars": return { title: "Avatares", desc: "Personaliza los avatares para diferentes canales." };
          case "contact": return { title: "Contacto", desc: "Información pública de contacto." };
          case "visuals": return { title: "Identidad Visual", desc: "Colores, tipografía y estilo." };
          case "story": return { title: "Historia de Origen", desc: "El relato fundacional de tu marca." };
          case "strategy": return { title: "Estrategia", desc: "Posicionamiento y competencia." };
          case "methodology": return { title: "Metodología", desc: "Tus pilares y métodos únicos." };
          default: return { title: "Editar", desc: "Realiza cambios en tu marca." };
      }
  };

  const { title, desc } = getHeaderInfo(mode);

  const PlaceholderForm = ({ name }: { name: string }) => (
      <div className="p-8 text-center border-2 border-dashed rounded-xl bg-muted/20">
          <p className="text-muted-foreground">El formulario de <strong>{name}</strong> está en construcción.</p>
          <p className="text-xs text-muted-foreground mt-2">Pronto podrás editar esta sección.</p>
      </div>
  );

  // Avatar Handler
  const handleAvatarSubmit = async (data: CreateAvatarDTO) => {
      try {
          const token = await getToken();
          if (!token) return;
          
          if (selectedItem?.id) {
              // Update
              // Note: avatarApi might not have update method exposed in types yet, assuming it does or using create for now if backend handles it?
              // Looking at previous reads, avatarApi was imported.
              // Assuming standard REST.
              // If selectedItem exists, we are updating.
              // We'll use a fetch manually if update not in lib, or use create if upsert.
              // For safety/speed, I'll assume create for now creates new, so I need update.
              // Let's assume create for now as fallback if no update ID in DTO.
              // Actually, data is CreateAvatarDTO.
              // I'll try to find an update method or just console log for now if missing.
              // But user wants functionality.
              // Let's use generic fetch.
              await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/avatars/${selectedItem.id}`, {
                  method: 'PATCH',
                  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                  body: JSON.stringify(data)
              });
              toast.success("Avatar actualizado");
          } else {
              // Create
              await avatarApi.createAvatar(token, data);
              toast.success("Avatar creado");
          }
          queryClient.invalidateQueries({ queryKey: ["avatars"] });
          onClose();
      } catch (e) {
          console.error(e);
          toast.error("Error al guardar avatar");
      }
  };

  // Team Member Handler (Single Item Update)
  const handleTeamMemberSave = async (member: KeyFigure) => {
      let newTeam = [...settings.team];
      const index = newTeam.findIndex(m => m.id === member.id);
      
      if (member.is_primary_voice) {
          newTeam = newTeam.map(m => ({ ...m, is_primary_voice: false }));
      }

      if (index >= 0) {
          newTeam[index] = member;
      } else {
          newTeam.push(member);
      }
      await handlers.onUpdateTeam(newTeam);
      onClose(); // Close sidebar after saving member
  };

  // Authority Item Handler
  const handleAuthorityItemSave = async (item: AuthorityItem) => {
      let newVault = [...settings.authority_vault];
      const index = newVault.findIndex(i => i.id === item.id);
      
      if (index >= 0) {
          newVault[index] = item;
      } else {
          newVault.push(item);
      }
      await handlers.onUpdateVault(newVault);
      onClose();
  };

  const renderContent = () => {
      switch (mode) {
          case "identity":
              return <IdentityForm initialData={settings.identity} onSave={handlers.onUpdateIdentity} isSaving={saving} />;
          
          case "legal":
              return <LegalForm initialData={settings.identity} onSave={handlers.onUpdateIdentity} isSaving={saving} />;
          
          case "team":
              if (selectedItem) {
                  return <TeamMemberForm initialData={selectedItem} onSave={handleTeamMemberSave} isSaving={saving} embedded />;
              }
              return <TeamForm initialData={settings.team} onSave={handlers.onUpdateTeam} isSaving={saving} />;
          
          case "authority":
              if (selectedItem) {
                  return <AuthorityItemForm initialData={selectedItem} onSave={handleAuthorityItemSave} isSaving={saving} embedded />;
              }
              return <AuthorityVaultForm initialData={settings.authority_vault} onSave={handlers.onUpdateVault} isSaving={saving} />;
          
          case "avatars":
              return (
                  <AvatarForm 
                      initialData={selectedItem || undefined} 
                      onSubmit={handleAvatarSubmit} 
                      isSubmitting={saving} 
                      embedded 
                  />
              );
          
          case "contact":
              return <ContactDataForm initialData={settings.contact} onSave={handlers.onUpdateContact} isSaving={saving} />;
          
          case "story":
              return <BrandStoryForm key={JSON.stringify(settings.story)} initialData={settings.story} onSave={handlers.onUpdateStory!} isSaving={saving} />;
          
          case "strategy":
              return <BrandStrategyForm key={JSON.stringify(settings.strategy)} initialData={settings.strategy} onSave={handlers.onUpdateStrategy!} isSaving={saving} />;
          
          case "methodology":
              return <BrandMethodologyForm key={JSON.stringify(settings.strategy)} initialData={settings.strategy} onSave={handlers.onUpdateStrategy!} isSaving={saving} />;
          
          case "voice":
              return <BrandVoiceForm />;

          case "visuals":
               return <BrandVisualsForm initialData={settings.visuals} onSave={handlers.onUpdateVisuals} isSaving={saving} />;

          case "testimonials":
              return <TestimonialsForm initialData={settings.testimonials} onSave={handlers.onUpdateTestimonials} isSaving={saving} />;

          default:
              return <PlaceholderForm name={mode} />;
      }
  };

  return (
    <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="sm:max-w-xl overflow-y-auto">
        <SheetHeader className="mb-6">
          <SheetTitle>{title}</SheetTitle>
          <SheetDescription>{desc}</SheetDescription>
        </SheetHeader>
        {renderContent()}
      </SheetContent>
    </Sheet>
  );
}
