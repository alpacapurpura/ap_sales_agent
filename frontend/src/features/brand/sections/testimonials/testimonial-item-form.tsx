"use client";

import NextImage from "next/image";
import { User } from "lucide-react";
import { useState } from "react";
import { v4 as uuidv4 } from "uuid";

import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";

import type { TestimonialItem } from "@/features/brand/types";

interface TestimonialItemFormProps {
  initialData?: TestimonialItem;
  onSave: (item: TestimonialItem) => void;
  onCancel: () => void;
  isSaving?: boolean;
}

export function TestimonialItemForm({
  initialData,
  onSave,
  onCancel,
  isSaving = false,
}: TestimonialItemFormProps) {
  const [currentItem, setCurrentItem] = useState<TestimonialItem>(
    () =>
      initialData ?? {
        id: uuidv4(),
        type: "text",
        content: "",
        author_name: "",
        author_role: "",
        rating: 5,
        author_avatar: "",
      },
  );

  const handleSubmit = () => {
    onSave(currentItem);
  };

  return (
    <div className="flex flex-col gap-6 py-4">
      {/* Type Selection */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Label>Tipo de Testimonio</Label>
          <Select
            value={currentItem.type}
            onValueChange={(val: "text" | "video") => setCurrentItem({ ...currentItem, type: val })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="text">Texto (Cita)</SelectItem>
              <SelectItem value="video">Video (YouTube)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-2">
          <Label>Calificación (Estrellas)</Label>
          <Select
            value={currentItem.rating?.toString()}
            onValueChange={(val) => setCurrentItem({ ...currentItem, rating: parseInt(val) })}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">5 Estrellas</SelectItem>
              <SelectItem value="4">4 Estrellas</SelectItem>
              <SelectItem value="3">3 Estrellas</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Author Info */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-2">
          <Label>Nombre del Autor</Label>
          <Input
            value={currentItem.author_name}
            onChange={(e) => setCurrentItem({ ...currentItem, author_name: e.target.value })}
            placeholder="Ej: María Pérez"
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label>Rol / Empresa</Label>
          <Input
            value={currentItem.author_role || ""}
            onChange={(e) => setCurrentItem({ ...currentItem, author_role: e.target.value })}
            placeholder="CEO, Tech Solutions"
          />
        </div>
      </div>

      {/* Avatar URL */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full overflow-hidden bg-muted border flex-shrink-0">
          {currentItem.author_avatar ? (
            <NextImage
              src={currentItem.author_avatar}
              alt="Preview"
              fill
              className="object-cover"
              unoptimized
            />
          ) : (
            <div className="h-full w-full flex items-center justify-center text-muted-foreground">
              <User className="h-6 w-6" />
            </div>
          )}
        </div>
        <div className="flex-1 flex flex-col gap-2">
          <Label>Foto del Autor (URL)</Label>
          <Input
            value={currentItem.author_avatar || ""}
            onChange={(e) => setCurrentItem({ ...currentItem, author_avatar: e.target.value })}
            placeholder="https://..."
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-col gap-2">
        <Label>
          {currentItem.type === "video" ? "URL del Video (YouTube/Vimeo)" : "Cita Textual"}
        </Label>
        {currentItem.type === "video" ? (
          <Input
            value={currentItem.content}
            onChange={(e) => setCurrentItem({ ...currentItem, content: e.target.value })}
            placeholder="https://youtube.com/watch?v=..."
          />
        ) : (
          <WithCopilot
            fieldId="testimonial_content"
            fieldLabel="Cita del Testimonio"
            getValue={() => currentItem.content || ""}
          >
            <Textarea
              value={currentItem.content}
              onChange={(e) => setCurrentItem({ ...currentItem, content: e.target.value })}
              placeholder="Escribe lo que dijo el cliente..."
              className="min-h-[100px]"
            />
          </WithCopilot>
        )}
      </div>

      <DialogFooter>
        <Button variant="outline" onClick={onCancel} disabled={isSaving}>
          Cancelar
        </Button>
        <Button onClick={handleSubmit} disabled={isSaving}>
          {isSaving ? "Guardando..." : "Guardar"}
        </Button>
      </DialogFooter>
    </div>
  );
}
