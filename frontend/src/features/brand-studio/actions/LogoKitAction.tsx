"use client";

import { Image as ImageIcon, Plus } from "lucide-react";
import NextImage from "next/image";
import { useCallback, useMemo } from "react";

import { Card } from "@/components/ui/card";
import { config } from "@/lib/config";
import { cn } from "@/lib/utils";

import { SingleImagePicker } from "./SingleImagePickerAction";

import type { BrandLogos } from "@/features/brand-studio/types";
import type { ActionComponentProps } from "@/lib/form-runtime/actions";

interface LogoSlot {
  key: keyof BrandLogos;
  label: string;
  description: string;
  bgClass: string;
  aspectClass: string;
  colSpanClass: string;
}

const SLOTS: LogoSlot[] = [
  {
    key: "primary",
    label: "Logo principal",
    description: "Versión completa a color. Se usa en cabeceras y documentos.",
    bgClass: "bg-slate-100",
    aspectClass: "aspect-video",
    colSpanClass: "col-span-2",
  },
  {
    key: "secondary",
    label: "Isotipo / favicon",
    description: "Versión reducida cuadrada (icono).",
    bgClass: "bg-slate-50",
    aspectClass: "aspect-square",
    colSpanClass: "col-span-1",
  },
  {
    key: "dark_mode",
    label: "Para fondo oscuro",
    description: "Logo blanco o claro. Se valida sobre fondo negro.",
    bgClass: "bg-slate-950",
    aspectClass: "aspect-video",
    colSpanClass: "col-span-2 sm:col-span-1",
  },
  {
    key: "light_mode",
    label: "Para fondo claro",
    description: "Logo negro u oscuro. Se valida sobre fondo blanco.",
    bgClass: "bg-white border",
    aspectClass: "aspect-video",
    colSpanClass: "col-span-2 sm:col-span-1",
  },
];

function isHttpUrl(path: string): boolean {
  return path.startsWith("http://") || path.startsWith("https://");
}

function buildFullUrl(path: string | undefined, baseUrl: string): string {
  if (!path) return "";
  return isHttpUrl(path) ? path : `${baseUrl}${path}`;
}

interface LogoSlotCardProps {
  slot: LogoSlot;
  currentUrl: string | undefined;
  onChange: (url: string) => void;
}

function LogoSlotCard({ slot, currentUrl, onChange }: LogoSlotCardProps) {
  const fullUrl = buildFullUrl(currentUrl, config.api.baseUrl);

  return (
    <Card className={cn("flex flex-col gap-3 p-4", slot.colSpanClass)}>
      <div className="flex flex-col gap-1">
        <span className="text-sm font-medium">{slot.label}</span>
        <span className="text-xs text-muted-foreground">{slot.description}</span>
      </div>
      <SingleImagePicker value={currentUrl} onChange={onChange} previewLabel={slot.label}>
        <div
          className={cn(
            "group relative flex w-full cursor-pointer items-center justify-center overflow-hidden rounded-md border-2 border-dashed border-muted-foreground/20 transition-colors hover:border-primary/50",
            slot.bgClass,
            slot.aspectClass,
          )}
        >
          {fullUrl ? (
            <>
              <NextImage
                src={fullUrl}
                alt={slot.label}
                fill
                className="object-contain p-4 transition-transform group-hover:scale-105"
                unoptimized
              />
              <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
                <span className="flex items-center gap-2 text-xs font-medium text-white">
                  <ImageIcon className="h-4 w-4" aria-hidden />
                  Cambiar
                </span>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground/50 transition-colors group-hover:text-primary/80">
              <Plus className="h-8 w-8" aria-hidden />
              <span className="text-xs font-medium">Subir</span>
            </div>
          )}
        </div>
      </SingleImagePicker>
    </Card>
  );
}

/**
 * LogoKit action — manages the four logo variants a brand ships with:
 * primary (full colour), isotipo (icon square), dark-mode and light-mode
 * variants. Composes `SingleImagePicker` four times with per-slot background
 * previews so the user validates contrast immediately.
 */
const EMPTY_LOGOS: BrandLogos = {};

export function LogoKitAction({ value, onChange }: ActionComponentProps<BrandLogos | null>) {
  const logos = useMemo(() => value ?? EMPTY_LOGOS, [value]);

  const updateSlot = useCallback(
    (key: keyof BrandLogos, url: string) => {
      onChange({ ...logos, [key]: url });
    },
    [logos, onChange],
  );

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium">Kit de logos</h3>
        <p className="text-sm text-muted-foreground">
          Gestiona las variantes de tu marca para cada contexto.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {SLOTS.map((slot) => (
          <LogoSlotCard
            key={slot.key}
            slot={slot}
            currentUrl={logos[slot.key]}
            onChange={(url) => updateSlot(slot.key, url)}
          />
        ))}
      </div>
    </div>
  );
}
