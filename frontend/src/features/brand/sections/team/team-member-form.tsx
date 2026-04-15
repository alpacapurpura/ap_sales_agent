"use client";

import { User, Save, Loader2, X } from "lucide-react";
import { useState, useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { config } from "@/lib/config";

import { ImageGalleryPicker } from "./image-gallery-picker";

import type { KeyFigure } from "@/features/brand/types";

interface TeamMemberFormProps {
  initialData: KeyFigure;
  onSave: (member: KeyFigure) => void;
  onCancel?: () => void;
  isSaving?: boolean;
  embedded?: boolean;
}

export function TeamMemberForm({
  initialData,
  onSave,
  onCancel,
  isSaving = false,
  embedded = false,
}: TeamMemberFormProps) {
  const [currentMember, setCurrentMember] = useState<KeyFigure>(initialData);
  const apiUrl = config.api.baseUrl;

  // Actualizar estado si cambia initialData (útil para resets)
  useEffect(() => {
    setCurrentMember(initialData);
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(currentMember);
  };

  const FormContent = (
    <div className="flex flex-col gap-6">
      {/* Identity Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Label>Nombre</Label>
          <WithCopilot
            fieldId="team_member_name"
            fieldLabel="Nombre del Miembro"
            getValue={() => currentMember.name || ""}
          >
            <Input
              value={currentMember.name}
              onChange={(e) => setCurrentMember({ ...currentMember, name: e.target.value })}
              placeholder="Nombre completo"
              required
            />
          </WithCopilot>
        </div>
        <div className="flex flex-col gap-2">
          <Label>Rol / Título</Label>
          <WithCopilot
            fieldId="team_member_role"
            fieldLabel="Rol del Miembro"
            getValue={() => currentMember.role || ""}
          >
            <Input
              value={currentMember.role || ""}
              onChange={(e) => setCurrentMember({ ...currentMember, role: e.target.value })}
              placeholder="Ej. Fundador, CEO"
            />
          </WithCopilot>
        </div>
      </div>

      {/* Gallery & Headshot */}
      <div className="space-y-4">
        <Label>Fotos de Perfil</Label>
        <div className="p-4 border rounded-lg bg-muted/5 space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full overflow-hidden bg-background border-2 border-primary/20 flex-shrink-0 shadow-sm relative">
              {currentMember.headshot_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={
                    currentMember.headshot_url.startsWith("http")
                      ? currentMember.headshot_url
                      : `${apiUrl}${currentMember.headshot_url}`
                  }
                  alt="Active Profile"
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="h-full w-full flex items-center justify-center bg-muted text-muted-foreground">
                  <User className="h-6 w-6" />
                </div>
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">Foto Principal</p>
              <p className="text-xs text-muted-foreground">
                Esta es la imagen que se mostrará en las tarjetas y avatares.
              </p>
            </div>
          </div>

          <ImageGalleryPicker
            images={currentMember.gallery || []}
            primaryImage={currentMember.headshot_url}
            onImagesChange={(images) => setCurrentMember((prev) => ({ ...prev, gallery: images }))}
            onPrimaryChange={(url) => setCurrentMember((prev) => ({ ...prev, headshot_url: url }))}
          />
        </div>
      </div>

      {/* Profile Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Label>Género</Label>
          <Select
            value={currentMember.gender}
            onValueChange={(val) => setCurrentMember({ ...currentMember, gender: val })}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccione" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Masculino">Masculino</SelectItem>
              <SelectItem value="Femenino">Femenino</SelectItem>
              <SelectItem value="Neutro">Neutro</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-2">
          <Label>Estilo de Comunicación</Label>
          <Select
            value={currentMember.communication_style}
            onValueChange={(val) =>
              setCurrentMember({ ...currentMember, communication_style: val })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccione" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Directo/Al Grano">Directo/Al Grano</SelectItem>
              <SelectItem value="Empático/Suave">Empático/Suave</SelectItem>
              <SelectItem value="Técnico/Analítico">Técnico/Analítico</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Bio Section */}
      <div className="flex flex-col gap-2">
        <Label>Bio Corta (Hook)</Label>
        <Textarea
          value={currentMember.bio || ""}
          onChange={(e) => setCurrentMember({ ...currentMember, bio: e.target.value })}
          placeholder="Breve descripción para dar contexto a la IA..."
          className="min-h-[80px]"
        />
      </div>

      {/* Voice Switch */}
      <div className="flex items-center justify-between border p-3 rounded-lg bg-muted/20">
        <div className="space-y-0.5">
          <Label className="text-base">Voz Principal</Label>
          <p className="text-sm text-muted-foreground">
            Si se activa, el bot adoptará esta personalidad al hablar por defecto.
          </p>
        </div>
        <Switch
          checked={currentMember.is_primary_voice}
          onCheckedChange={(checked) =>
            setCurrentMember({ ...currentMember, is_primary_voice: checked })
          }
        />
      </div>

      {/* Social Media & Contact */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground border-b pb-2">
          Redes y Contacto
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <Label>Website</Label>
            <Input
              value={currentMember.personal_website || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_website: e.target.value })
              }
              placeholder="https://..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>LinkedIn</Label>
            <Input
              value={currentMember.personal_linkedin || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_linkedin: e.target.value })
              }
              placeholder="https://linkedin.com/in/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Instagram</Label>
            <Input
              value={currentMember.personal_instagram || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_instagram: e.target.value })
              }
              placeholder="https://instagram.com/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>TikTok</Label>
            <Input
              value={currentMember.personal_tiktok || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_tiktok: e.target.value })
              }
              placeholder="https://tiktok.com/@..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>Facebook</Label>
            <Input
              value={currentMember.personal_facebook || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_facebook: e.target.value })
              }
              placeholder="https://facebook.com/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label>WhatsApp (Trabajo)</Label>
            <Input
              value={currentMember.work_whatsapp || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, work_whatsapp: e.target.value })
              }
              placeholder="+52..."
            />
          </div>
        </div>
      </div>
    </div>
  );

  const ActionButtons = (
    <div className="flex gap-2">
      {onCancel && (
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
          <X className="mr-2 h-4 w-4" />
          Cancelar
        </Button>
      )}
      <Button type="submit" disabled={isSaving || !currentMember.name}>
        {isSaving ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <Save className="mr-2 h-4 w-4" />
        )}
        Guardar Miembro
      </Button>
    </div>
  );

  if (embedded) {
    return (
      <form onSubmit={handleSubmit} className="space-y-6">
        {FormContent}
        <div className="flex justify-end pt-4 border-t mt-6">{ActionButtons}</div>
      </form>
    );
  }

  return (
    <Card className="border-0 shadow-none">
      <CardHeader className="px-0 pt-0">
        <CardTitle>{initialData.id ? "Editar Miembro" : "Nuevo Miembro"}</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <form onSubmit={handleSubmit} className="space-y-6">
          {FormContent}
        </form>
      </CardContent>
      <CardFooter className="px-0 flex justify-end">{ActionButtons}</CardFooter>
    </Card>
  );
}
