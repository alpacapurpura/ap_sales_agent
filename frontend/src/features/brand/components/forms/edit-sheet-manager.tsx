"use client";

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { BrandSettings, KeyFigure, AuthorityItem } from "@/features/brand/types";
import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { avatarApi, CreateAvatarDTO } from "@/lib/api/avatar";
import { toast } from "sonner";

// Ideally types should be in a separate file, but for now we can replicate the string union or import type only.
import type { EditMode } from "../container/brand-studio-layout";

// New Managers
import { IdentityManager } from "../../sections/identity/identity-manager";
import { LegalManager } from "../legal/legal-manager";
import { ContactManager } from "../../sections/contact/contact-manager";
import { StoryManager } from "../../sections/story/story-manager";
import { StrategyManager } from "../../sections/strategy/strategy-manager";
import { MethodologyManager } from "../../sections/methodology/methodology-manager";
import { VoiceManager } from "../../sections/voice/voice-manager";
import { VisualsManager } from "../../sections/visuals/visuals-manager";

// Existing Components for Complex Types (Team, Authority, Avatars)
import { TeamManager } from "../../sections/team/team-manager";
import { TeamMemberForm } from "../../sections/team/team-member-form";
import { AuthorityItemForm } from "../../sections/authority/authority-item-form";
import { AuthorityManager } from "../../sections/authority/authority-manager";
import { AvatarForm } from "../../sections/avatars/avatar-form";
import { TestimonialsManager } from "../../sections/testimonials/testimonials-manager";

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
              return <IdentityManager />;
          
          case "legal":
              return <LegalManager />;
          
          case "team":
              if (selectedItem) {
                  return <TeamMemberForm initialData={selectedItem} onSave={handleTeamMemberSave} isSaving={saving} embedded />;
              }
              return <TeamManager />;
          
          case "authority":
            if (selectedItem) {
                return <AuthorityItemForm initialData={selectedItem} onSave={handleAuthorityItemSave} isSaving={saving} />;
            }
            return <AuthorityManager />;
          
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
              return <ContactManager />;
          
          case "story":
              return <StoryManager />;
          
          case "strategy":
              return <StrategyManager />;
          
          case "methodology":
              return <MethodologyManager />;
          
          case "voice":
              return <VoiceManager />;

          case "visuals":
               return <VisualsManager />;

          case "testimonials":
              return <TestimonialsManager />;

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
