"use client";

import { BrandLogos } from "@/features/brand/types";
import { SingleImagePicker } from "../visuals/single-image-picker";
import { Card } from "@/components/ui/card";
import { Plus, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { config } from "@/lib/config";

interface LogoKitProps {
    logos: BrandLogos;
    onChange: (logos: BrandLogos) => void;
}

export function LogoKit({ logos, onChange }: LogoKitProps) {
    const API_URL = config.api.baseUrl;

    const getFullUrl = (path?: string) => {
        if (!path) return "";
        if (path.startsWith("http")) return path;
        return `${API_URL}${path}`;
    };

    const updateLogo = (key: keyof BrandLogos, url: string) => {
        const updated = { ...logos, [key]: url };
        console.log("[LogoKit] updateLogo:", key, url, "-> full logos:", updated);
        onChange(updated);
    };

    const slots = [
        {
            key: "primary" as const,
            label: "Logo Principal",
            description: "Versión completa a color. Se usa en cabeceras y documentos.",
            bg: "bg-slate-100", // Light gray for neutral context
            aspect: "aspect-video",
            colSpan: "col-span-2"
        },
        {
            key: "secondary" as const,
            label: "Isotipo / Favicon",
            description: "Versión reducida cuadrada (Icono).",
            bg: "bg-slate-50",
            aspect: "aspect-square",
            colSpan: "col-span-1"
        },
        {
            key: "dark_mode" as const,
            label: "Para Fondo Oscuro",
            description: "Logo blanco o claro. Se validará sobre fondo negro.",
            bg: "bg-slate-950",
            aspect: "aspect-video",
            colSpan: "col-span-2 sm:col-span-1"
        },
        {
            key: "light_mode" as const,
            label: "Para Fondo Claro",
            description: "Logo negro u oscuro. Se validará sobre fondo blanco.",
            bg: "bg-white border",
            aspect: "aspect-video",
            colSpan: "col-span-2 sm:col-span-1"
        }
    ];

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-medium">Kit de Logos</h3>
                    <p className="text-sm text-muted-foreground">Gestiona las variantes de tu marca para cada contexto.</p>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                {slots.map((slot) => {
                    const currentUrl = logos?.[slot.key];
                    
                    return (
                        <Card key={slot.key} className={cn("p-4 flex flex-col gap-3", slot.colSpan)}>
                            <div className="flex flex-col gap-1">
                                <span className="font-medium text-sm">{slot.label}</span>
                                <span className="text-xs text-muted-foreground">{slot.description}</span>
                            </div>

                            <SingleImagePicker 
                                value={currentUrl} 
                                onChange={(url) => updateLogo(slot.key, url)}
                            >
                                <div className={cn(
                                    "relative w-full rounded-md overflow-hidden border-2 border-dashed border-muted-foreground/20 hover:border-primary/50 transition-colors cursor-pointer flex items-center justify-center group",
                                    slot.bg,
                                    slot.aspect
                                )}>
                                    {currentUrl ? (
                                        <>
                                            {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img 
                                                src={getFullUrl(currentUrl)} 
                                                alt={slot.label} 
                                                className="w-full h-full object-contain p-4 transition-transform group-hover:scale-105" 
                                            />
                                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                                <span className="text-white font-medium text-xs flex items-center gap-2">
                                                    <ImageIcon className="h-4 w-4" />
                                                    Cambiar
                                                </span>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex flex-col items-center gap-2 text-muted-foreground/50 group-hover:text-primary/80 transition-colors">
                                            <Plus className="h-8 w-8" />
                                            <span className="text-xs font-medium">Subir</span>
                                        </div>
                                    )}
                                </div>
                            </SingleImagePicker>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}
