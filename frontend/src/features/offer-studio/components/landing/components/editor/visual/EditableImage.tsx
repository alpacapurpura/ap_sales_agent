"use client";

import NextImage from "next/image";
import { ImagePlus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface EditableImageProps {
  src?: string;
  alt: string;
  onChange?: (newUrl: string) => void;
  className?: string;
  aspectRatio?: "video" | "square" | "portrait";
}

export function EditableImage({
  src,
  alt,
  onChange,
  className,
  aspectRatio = "video",
}: EditableImageProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [inputValue, setInputValue] = useState(src ?? "");

  const handleEdit = () => {
    if (!onChange) return;
    setInputValue(src ?? "");
    setDialogOpen(true);
  };

  const handleConfirm = () => {
    if (onChange && inputValue) {
      onChange(inputValue);
    }
    setDialogOpen(false);
  };

  const ratioClasses = {
    video: "aspect-video",
    square: "aspect-square",
    portrait: "aspect-[3/4]",
  };

  return (
    <>
      <div
        className={cn(
          "relative group overflow-hidden rounded-lg bg-slate-100",
          ratioClasses[aspectRatio],
          className,
        )}
      >
        {src ? (
          <NextImage src={src} alt={alt} fill className="object-cover" unoptimized />
        ) : (
          <div className="flex items-center justify-center h-full text-slate-400">
            <ImagePlus className="w-8 h-8" />
          </div>
        )}

        {onChange && (
          <div
            className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center cursor-pointer"
            onClick={handleEdit}
          >
            <Button variant="secondary" size="sm">
              Cambiar Imagen
            </Button>
          </div>
        )}
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>URL de la imagen</DialogTitle>
          </DialogHeader>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="https://ejemplo.com/imagen.jpg"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleConfirm();
            }}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleConfirm}>Confirmar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
