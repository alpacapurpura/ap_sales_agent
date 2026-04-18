"use client";

/**
 * LEGACY team-member-form adapter for offer-studio's InstructorsSelector.
 * Ported verbatim from features/brand/sections/team/team-member-form.tsx
 * minus the WithCopilot wrappers (plain inputs — this form lives inside a
 * modal so copilot focus is not helpful here).
 *
 * Delete together with the rest of ``legacy-team/`` once Sprint 6 refactors
 * offer-studio to route-per-field form-runtime.
 */

import NextImage from "next/image";
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
import { config } from "@/lib/config";

import { ImageGalleryPicker } from "./ImageGalleryPicker";

import type { KeyFigure } from "@/features/brand-studio/types";

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

  useEffect(() => {
    setCurrentMember(initialData);
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(currentMember);
  };

  const FormContent = (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="member-name">Nombre</Label>
          <Input
            id="member-name"
            value={currentMember.name}
            onChange={(e) => setCurrentMember({ ...currentMember, name: e.target.value })}
            placeholder="Nombre completo"
            required
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="member-role">Rol / Título</Label>
          <Input
            id="member-role"
            value={currentMember.role || ""}
            onChange={(e) => setCurrentMember({ ...currentMember, role: e.target.value })}
            placeholder="Ej. Fundador, CEO"
          />
        </div>
      </div>

      <div className="space-y-4">
        <Label>Fotos de Perfil</Label>
        <div className="p-4 border rounded-lg bg-muted/5 space-y-4">
          <div className="flex items-center gap-4">
            <div className="h-16 w-16 rounded-full overflow-hidden bg-background border-2 border-primary/20 flex-shrink-0 shadow-sm relative">
              {currentMember.headshot_url ? (
                <NextImage
                  src={
                    currentMember.headshot_url.startsWith("http")
                      ? currentMember.headshot_url
                      : `${apiUrl}${currentMember.headshot_url}`
                  }
                  alt="Active Profile"
                  fill
                  className="object-cover"
                  unoptimized
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

      <div className="flex flex-col gap-2">
        <Label htmlFor="member-bio">Bio Corta (Hook)</Label>
        <Textarea
          id="member-bio"
          value={currentMember.bio || ""}
          onChange={(e) => setCurrentMember({ ...currentMember, bio: e.target.value })}
          placeholder="Breve descripción para dar contexto a la IA..."
          className="min-h-[80px]"
        />
      </div>

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

      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground border-b pb-2">
          Redes y Contacto
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-website">Website</Label>
            <Input
              id="member-website"
              value={currentMember.personal_website || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_website: e.target.value })
              }
              placeholder="https://..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-linkedin">LinkedIn</Label>
            <Input
              id="member-linkedin"
              value={currentMember.personal_linkedin || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_linkedin: e.target.value })
              }
              placeholder="https://linkedin.com/in/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-instagram">Instagram</Label>
            <Input
              id="member-instagram"
              value={currentMember.personal_instagram || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_instagram: e.target.value })
              }
              placeholder="https://instagram.com/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-tiktok">TikTok</Label>
            <Input
              id="member-tiktok"
              value={currentMember.personal_tiktok || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_tiktok: e.target.value })
              }
              placeholder="https://tiktok.com/@..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-facebook">Facebook</Label>
            <Input
              id="member-facebook"
              value={currentMember.personal_facebook || ""}
              onChange={(e) =>
                setCurrentMember({ ...currentMember, personal_facebook: e.target.value })
              }
              placeholder="https://facebook.com/..."
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="member-whatsapp">WhatsApp (Trabajo)</Label>
            <Input
              id="member-whatsapp"
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
