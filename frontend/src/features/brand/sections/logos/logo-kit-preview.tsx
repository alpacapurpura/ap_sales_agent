"use client";

import NextImage from "next/image";
import { Image as ImageIcon, Upload } from "lucide-react";

import { getAssetUrl } from "@/lib/utils/assets";

import type { BrandVisuals, BrandLogos } from "@/features/brand/types";

interface LogoKitPreviewProps {
  visuals: BrandVisuals;
  onEdit: () => void;
}

export function LogoKitPreview({ visuals, onEdit }: LogoKitPreviewProps) {
  const { logos } = visuals;
  const hasLogos = logos?.primary || logos?.secondary || logos?.dark_mode || logos?.light_mode;

  const logoSlots: {
    key: keyof BrandLogos;
    label: string;
    bg: string;
    minW: string;
    aspect?: string;
  }[] = [
    {
      key: "primary",
      label: "Principal",
      bg: "bg-white",
      minW: "min-w-[140px]",
      aspect: "aspect-video",
    },
    { key: "secondary", label: "Icono", bg: "bg-muted/20", minW: "w-20", aspect: "aspect-square" },
    {
      key: "dark_mode",
      label: "Fondo Oscuro",
      bg: "bg-slate-950",
      minW: "min-w-[140px]",
      aspect: "aspect-video",
    },
    {
      key: "light_mode",
      label: "Fondo Claro",
      bg: "bg-white",
      minW: "min-w-[140px]",
      aspect: "aspect-video",
    },
  ];

  return (
    <section
      onClick={onEdit}
      className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer border border-transparent hover:border-border/50"
    >
      {/* Header */}
      <div className="flex items-center gap-3 text-muted-foreground group-hover:text-primary transition-colors mb-6">
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <ImageIcon className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Kit de Logos</h3>
      </div>

      {!hasLogos ? (
        <div className="pl-0 md:pl-14 cursor-pointer">
          <p className="text-lg text-muted-foreground italic mb-2">
            &quot;Tu logo es la primera impresión de tu marca. Sube tus variantes aquí.&quot;
          </p>
          <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
            <Upload className="w-4 h-4" />
            Subir Logos
          </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
          <div className="flex flex-wrap gap-6 items-end">
            {logoSlots.map((slot) => {
              const url = logos?.[slot.key];
              if (!url) return null;
              return (
                <div key={slot.key} className="space-y-2">
                  <div
                    className={`relative h-20 px-4 py-2 border rounded-lg ${slot.bg} flex items-center justify-center ${slot.minW}`}
                  >
                    <NextImage
                      src={getAssetUrl(url) || "/placeholder.svg"}
                      alt={slot.label}
                      fill
                      className="object-contain"
                      unoptimized
                    />
                  </div>
                  <p className="text-[10px] text-muted-foreground font-mono uppercase">
                    {slot.label}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
