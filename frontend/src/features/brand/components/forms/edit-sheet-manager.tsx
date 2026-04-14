"use client";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  BrandSettings,
  BrandIdentity,
  KeyFigure,
  AuthorityItem,
  ContactData,
  BrandVisuals,
  BrandStrategy,
  BrandStory,
  TestimonialItem,
} from "@/features/brand/types";
import type { EditMode } from "../../types/edit-mode";
import { EDIT_MODE_META } from "../../config/sections";
import { useAuth } from "@clerk/nextjs";
import { useQueryClient } from "@tanstack/react-query";
import { avatarApi, type CreateAvatarDTO, type Avatar } from "@/lib/api/avatar";
import { config } from "@/lib/config";
import { toast } from "sonner";

// New Managers
import { IdentityManager } from "../../sections/identity/identity-manager";
import { LegalManager } from "../legal/legal-manager";
import { ContactManager } from "../../sections/contact/contact-manager";
import { StoryManager } from "../../sections/story/story-manager";

import { MethodologyManager } from "../../sections/methodology/methodology-manager";
import { VoiceManager } from "../../sections/voice/voice-manager";
import { VisualsManager } from "../../sections/visuals/visuals-manager";
import { LogoKitManager } from "../../sections/logos/logo-kit-manager";
import { PositioningManager } from "../../sections/positioning/positioning-manager";
import { ValuesEssenceManager } from "../../sections/positioning/values-essence-manager";
import { NarrativeManager } from "../../sections/narrative/narrative-manager";
import { AssetsManager } from "../../sections/communication-assets/assets-manager";

// Existing Components for Complex Types (Team, Authority, Avatars)
import { TeamManager } from "../../sections/team/team-manager";
import { TeamMemberForm } from "../../sections/team/team-member-form";
import { AuthorityItemForm } from "../../sections/authority/authority-item-form";
import { AuthorityManager } from "../../sections/authority/authority-manager";
import { AvatarForm } from "../../sections/avatars/avatar-form";
import { TestimonialsManager } from "../../sections/testimonials/testimonials-manager";

// Component registry for modes that need no special props
const MODE_COMPONENT: Partial<Record<EditMode, React.ComponentType>> = {
  identity: IdentityManager,
  legal: LegalManager,
  contact: ContactManager,
  story: StoryManager,
  methodology: MethodologyManager,
  voice: VoiceManager,
  visuals: VisualsManager,
  logos: LogoKitManager,
  testimonials: TestimonialsManager,
  positioning: PositioningManager,
  "values-essence": ValuesEssenceManager,
  storybrand: NarrativeManager,
  "communication-assets": AssetsManager,
};

type SelectedEditItem = KeyFigure | AuthorityItem | TestimonialItem | Avatar | null;

interface EditSheetManagerProps {
  mode: EditMode;
  selectedItem: SelectedEditItem;
  isOpen: boolean;
  onClose: () => void;
  settings: BrandSettings;
  saving: boolean;
  handlers: {
    onUpdateIdentity: (data: BrandIdentity) => Promise<void>;
    onUpdateContact: (data: ContactData) => Promise<void>;
    onUpdateTeam: (data: KeyFigure[]) => Promise<void>;
    onUpdateVault: (data: AuthorityItem[]) => Promise<void>;
    onUpdateVisuals: (data: BrandVisuals) => Promise<void>;
    onUpdateTestimonials: (data: TestimonialItem[]) => Promise<void>;
    onUpdateStory?: (data: BrandStory) => Promise<void>;
    onUpdateStrategy?: (data: BrandStrategy) => Promise<void>;
  };
}

const PlaceholderForm = ({ name }: { name: string }) => (
  <div className="p-8 text-center border-2 border-dashed rounded-xl bg-muted/20">
    <p className="text-muted-foreground">
      El formulario de <strong>{name}</strong> esta en construccion.
    </p>
    <p className="text-xs text-muted-foreground mt-2">Pronto podras editar esta seccion.</p>
  </div>
);

export function EditSheetManager({
  mode,
  selectedItem,
  isOpen,
  onClose,
  settings,
  saving,
  handlers,
}: EditSheetManagerProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { title, desc } = EDIT_MODE_META[mode] ?? EDIT_MODE_META.none;

  // Avatar Handler
  const handleAvatarSubmit = async (data: CreateAvatarDTO) => {
    try {
      const token = await getToken();
      if (!token) return;

      if (selectedItem && "id" in selectedItem && selectedItem.id) {
        await fetch(`${config.api.baseUrl}/api/v1/avatars/${selectedItem.id}`, {
          method: "PATCH",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify(data),
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
    let newTeam = [...(settings.team ?? [])];
    const index = newTeam.findIndex((m) => m.id === member.id);

    if (member.is_primary_voice) {
      newTeam = newTeam.map((m) => ({ ...m, is_primary_voice: false }));
    }

    if (index >= 0) {
      newTeam[index] = member;
    } else {
      newTeam.push(member);
    }
    await handlers.onUpdateTeam(newTeam);
    onClose();
  };

  // Authority Item Handler
  const handleAuthorityItemSave = async (item: AuthorityItem) => {
    let newVault = [...(settings.authority_vault ?? [])];
    const index = newVault.findIndex((i) => i.id === item.id);

    if (index >= 0) {
      newVault[index] = item;
    } else {
      newVault.push(item);
    }
    await handlers.onUpdateVault(newVault);
    onClose();
  };

  const renderContent = () => {
    // Special cases that require props
    if (mode === "team") {
      return selectedItem ? (
        <TeamMemberForm
          initialData={selectedItem as KeyFigure}
          onSave={handleTeamMemberSave}
          isSaving={saving}
          embedded
        />
      ) : (
        <TeamManager />
      );
    }
    if (mode === "authority") {
      return selectedItem ? (
        <AuthorityItemForm
          initialData={selectedItem as AuthorityItem}
          onSave={handleAuthorityItemSave}
          isSaving={saving}
        />
      ) : (
        <AuthorityManager />
      );
    }
    if (mode === "avatars") {
      return (
        <AvatarForm
          initialData={(selectedItem as Partial<CreateAvatarDTO>) || undefined}
          onSubmit={handleAvatarSubmit}
          isSubmitting={saving}
          embedded
        />
      );
    }

    // Registry lookup
    const Component = MODE_COMPONENT[mode];
    return Component ? <Component /> : <PlaceholderForm name={mode} />;
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
