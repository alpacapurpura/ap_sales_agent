"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Globe, Upload, Palette, CheckCircle2, Loader2, Sparkles, RefreshCcw } from "lucide-react";
import { BrandVisuals } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import ColorThief from "colorthief";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";

interface BrandVisualsWizardProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  currentVisuals: BrandVisuals;
  logoUrl?: string;
  websiteUrl?: string;
  onSave: (visuals: BrandVisuals) => Promise<void>;
}

// Preset Kits
const VIBE_KITS = [
  { id: "corporate", name: "Corporate & Trust", primary: "#0f172a", accent: "#3b82f6", fontHeading: "Inter", fontBody: "Inter" },
  { id: "luxury", name: "Luxury & Elegant", primary: "#1c1917", accent: "#d4af37", fontHeading: "Playfair Display", fontBody: "Lato" },
  { id: "playful", name: "Playful & Vivid", primary: "#7c3aed", accent: "#f43f5e", fontHeading: "Poppins", fontBody: "Nunito" },
  { id: "minimal", name: "Minimal & Clean", primary: "#171717", accent: "#525252", fontHeading: "DM Sans", fontBody: "DM Sans" },
];

export function BrandVisualsWizard({
  isOpen,
  onOpenChange,
  currentVisuals,
  logoUrl,
  websiteUrl,
  onSave
}: BrandVisualsWizardProps) {
  const [step, setStep] = useState<"select-source" | "preview">("select-source");
  const [selectedVisuals, setSelectedVisuals] = useState<BrandVisuals>(currentVisuals);
  const [analyzing, setAnalyzing] = useState(false);
  const { getToken } = useAuth();

  // --- ACTIONS ---

  const handleAnalyzeWeb = async () => {
    if (!websiteUrl) return;
    setAnalyzing(true);
    
    try {
        const token = await getToken();
        if (!token) throw new Error("No auth token");

        toast.info("Analizando sitio web... Esto puede tomar unos segundos.");
        const extracted = await brandApi.extractBrandVisuals(websiteUrl, token);
        
        setSelectedVisuals({
            ...selectedVisuals,
            primary_color: extracted.primary_color,
            accent_color: extracted.accent_color,
            font_heading: extracted.font_heading || selectedVisuals.font_heading,
            font_body: extracted.font_body || selectedVisuals.font_body,
            style_preset: "custom-web",
            // New fields
            background_color: extracted.background_color,
            text_primary_color: extracted.text_primary_color,
            text_on_primary: extracted.text_on_primary,
            design_style: extracted.design_style,
            usage_guidelines: extracted.usage_guidelines
        });
        
        setStep("preview");
        toast.success("¡Identidad visual detectada!");
        
    } catch (error) {
        console.error(error);
        toast.error("Error al analizar el sitio web. Verifica la URL.");
    } finally {
        setAnalyzing(false);
    }
  };

  const handleAnalyzeLogo = async () => {
    if (!logoUrl) return;
    setAnalyzing(true);
    
    try {
        const img = new Image();
        img.crossOrigin = "Anonymous";
        img.src = logoUrl;
        
        img.onload = () => {
            const colorThief = new ColorThief();
            const palette = colorThief.getPalette(img, 3); // Get top 3 colors
            
            if (palette && palette.length >= 2) {
                const [r1, g1, b1] = palette[0];
                const [r2, g2, b2] = palette[1];
                
                const rgbToHex = (r: number, g: number, b: number) => 
                    "#" + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');

                setSelectedVisuals({
                    ...selectedVisuals,
                    primary_color: rgbToHex(r1, g1, b1),
                    accent_color: rgbToHex(r2, g2, b2),
                    style_preset: "custom-logo"
                });
            }
            setAnalyzing(false);
            setStep("preview");
        };

        img.onerror = () => {
            console.error("Error loading image for color extraction");
            setAnalyzing(false);
        }
    } catch (e) {
        console.error(e);
        setAnalyzing(false);
    }
  };

  const handleSelectKit = (kit: typeof VIBE_KITS[0]) => {
    setSelectedVisuals({
      primary_color: kit.primary,
      accent_color: kit.accent,
      font_heading: kit.fontHeading,
      font_body: kit.fontBody,
      style_preset: kit.id
    });
    setStep("preview");
  };

  const handleSave = async () => {
    await onSave(selectedVisuals);
    onOpenChange(false);
    setStep("select-source"); // Reset
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent 
        className="max-w-4xl h-[80vh] flex flex-col p-0 overflow-hidden"
        onInteractOutside={(e) => e.preventDefault()}
      >
        
        {step === "select-source" ? (
            <>
                {/* Standard Header for Selection Step */}
                <div className="p-6 border-b bg-muted/20">
                    <DialogHeader>
                    <DialogTitle className="text-xl">Definir ADN Visual</DialogTitle>
                    <DialogDescription>
                        Elige la fuente de verdad para los colores y tipografía de tu marca.
                    </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="flex-1 overflow-y-auto p-6 bg-muted/10">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full items-center">
                        {/* Option 1: Website */}
                        <Card className="cursor-pointer hover:border-primary/50 transition-all hover:shadow-md h-full flex flex-col">
                            <CardHeader>
                                <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mb-2">
                                    <Globe className="h-6 w-6" />
                                </div>
                                <CardTitle>Tengo Sitio Web</CardTitle>
                                <CardDescription>Extraeremos la paleta de tu sitio actual.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4 mt-auto">
                                <div className="space-y-2">
                                    <Label>URL del Sitio</Label>
                                    <Input defaultValue={websiteUrl || "https://"} disabled={!!websiteUrl} />
                                </div>
                                <Button className="w-full" onClick={handleAnalyzeWeb} disabled={analyzing}>
                                    {analyzing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Escanear Web"}
                                </Button>
                            </CardContent>
                        </Card>

                        {/* Option 2: Logo */}
                        <Card className="cursor-pointer hover:border-primary/50 transition-all hover:shadow-md h-full flex flex-col">
                            <CardHeader>
                                <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-2">
                                    <Upload className="h-6 w-6" />
                                </div>
                                <CardTitle>Tengo Logo</CardTitle>
                                <CardDescription>Analizaremos los píxeles de tu logo.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4 mt-auto">
                                    {logoUrl ? (
                                    <div className="flex flex-col items-center gap-4">
                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                        <img src={logoUrl} alt="Logo" className="h-16 object-contain" />
                                        <Button className="w-full" onClick={handleAnalyzeLogo} disabled={analyzing}>
                                            {analyzing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Extraer de Logo"}
                                        </Button>
                                    </div>
                                    ) : (
                                    <div className="text-center py-4 text-sm text-muted-foreground bg-muted/20 rounded-lg border border-dashed">
                                        Sube tu logo primero en &quot;Identidad&quot;
                                    </div>
                                    )}
                            </CardContent>
                        </Card>

                        {/* Option 3: Kits */}
                        <Card className="cursor-pointer hover:border-primary/50 transition-all hover:shadow-md h-full flex flex-col">
                            <CardHeader>
                                <div className="w-12 h-12 rounded-full bg-pink-100 text-pink-600 flex items-center justify-center mb-2">
                                    <Palette className="h-6 w-6" />
                                </div>
                                <CardTitle>Empezar de Cero</CardTitle>
                                <CardDescription>Elige un estilo pre-diseñado.</CardDescription>
                            </CardHeader>
                            <CardContent className="mt-auto">
                                    <div className="grid grid-cols-2 gap-2">
                                    {VIBE_KITS.map(kit => (
                                        <button 
                                            key={kit.id}
                                            onClick={() => handleSelectKit(kit)}
                                            className="p-2 text-xs border rounded hover:bg-muted text-left flex flex-col gap-1"
                                        >
                                            <div className="flex gap-1">
                                                <div className="w-3 h-3 rounded-full" style={{ background: kit.primary }} />
                                                <div className="w-3 h-3 rounded-full" style={{ background: kit.accent }} />
                                            </div>
                                            <span className="font-medium">{kit.name}</span>
                                        </button>
                                    ))}
                                    </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </>
        ) : (
            // --- CHAMELEON PREVIEW MODE ---
            // This container adopts the extracted brand identity completely
            <div 
                className="flex-1 flex flex-col transition-colors duration-500 overflow-hidden"
                style={{ 
                    backgroundColor: selectedVisuals.background_color || '#ffffff',
                    color: selectedVisuals.text_primary_color || '#000000',
                    fontFamily: selectedVisuals.font_body || 'inherit'
                }}
            >
                {/* Chameleon Header */}
                <div className="p-8 pb-0 flex items-center justify-between flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <Sparkles className="w-6 h-6" style={{ color: selectedVisuals.accent_color }} />
                        <h2 className="text-2xl font-bold" style={{ fontFamily: selectedVisuals.font_heading }}>
                            Identidad Detectada
                        </h2>
                    </div>
                    <div className="px-3 py-1 rounded-full text-xs font-medium border"
                         style={{ borderColor: selectedVisuals.text_primary_color, opacity: 0.6 }}>
                        {selectedVisuals.design_style || "Personalizado"}
                    </div>
                </div>

                {/* Chameleon Content */}
                <div className="flex-1 p-8 flex gap-8 items-start overflow-y-auto min-h-0">
                    
                    {/* Left: Brand Card */}
                    <div className="w-1/3 space-y-6">
                        <div className="aspect-square rounded-2xl shadow-xl flex flex-col items-center justify-center p-6 text-center border transition-all"
                             style={{ 
                                 borderColor: selectedVisuals.primary_color,
                                 backgroundColor: selectedVisuals.background_color 
                             }}>
                             <div className="w-24 h-24 rounded-full mb-4 shadow-lg" 
                                  style={{ backgroundColor: selectedVisuals.primary_color }} />
                             <h3 className="text-xl font-bold mb-1" style={{ fontFamily: selectedVisuals.font_heading }}>
                                Tu Marca
                             </h3>
                             <p className="text-sm opacity-80">
                                Así se ven tus colores principales en contexto.
                             </p>
                             <button className="mt-6 px-6 py-2 rounded-lg text-sm font-bold shadow-md transition-transform hover:scale-105"
                                     style={{ 
                                         backgroundColor: selectedVisuals.primary_color,
                                         color: selectedVisuals.text_on_primary 
                                     }}>
                                Call to Action
                             </button>
                        </div>
                    </div>

                    {/* Right: Details & Palette */}
                    <div className="flex-1 space-y-8">
                        {/* Colors Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-xl border bg-black/5">
                                <span className="text-xs uppercase tracking-wider opacity-60 block mb-2">Primario</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg shadow-sm" style={{ background: selectedVisuals.primary_color }} />
                                    <span className="font-mono text-sm font-medium">{selectedVisuals.primary_color}</span>
                                </div>
                            </div>
                            <div className="p-4 rounded-xl border bg-black/5">
                                <span className="text-xs uppercase tracking-wider opacity-60 block mb-2">Acento</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg shadow-sm" style={{ background: selectedVisuals.accent_color }} />
                                    <span className="font-mono text-sm font-medium">{selectedVisuals.accent_color}</span>
                                </div>
                            </div>
                            <div className="p-4 rounded-xl border bg-black/5">
                                <span className="text-xs uppercase tracking-wider opacity-60 block mb-2">Fondo</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg shadow-sm border" style={{ background: selectedVisuals.background_color }} />
                                    <span className="font-mono text-sm font-medium">{selectedVisuals.background_color}</span>
                                </div>
                            </div>
                            <div className="p-4 rounded-xl border bg-black/5">
                                <span className="text-xs uppercase tracking-wider opacity-60 block mb-2">Texto</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg shadow-sm" style={{ background: selectedVisuals.text_primary_color }} />
                                    <span className="font-mono text-sm font-medium">{selectedVisuals.text_primary_color}</span>
                                </div>
                            </div>
                        </div>

                        {/* Usage Guidelines */}
                        {selectedVisuals.usage_guidelines && selectedVisuals.usage_guidelines.length > 0 && (
                            <div className="space-y-3">
                                <h4 className="font-bold text-sm uppercase opacity-70 flex items-center gap-2">
                                    <Sparkles className="w-4 h-4" />
                                    Reglas de Diseño
                                </h4>
                                <ul className="space-y-2">
                                    {selectedVisuals.usage_guidelines.map((rule, i) => (
                                        <li key={i} className="flex gap-3 text-sm opacity-90 p-3 rounded-lg bg-black/5">
                                            <CheckCircle2 className="w-5 h-5 flex-shrink-0" style={{ color: selectedVisuals.primary_color }} />
                                            {rule}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>

                {/* Chameleon Footer */}
                <div className="p-6 border-t bg-black/5 flex justify-between items-center flex-shrink-0">
                    <button 
                        onClick={() => setStep("select-source")}
                        className="px-6 py-2 rounded-lg text-sm font-medium hover:bg-black/5 transition-colors flex items-center gap-2"
                        style={{ color: selectedVisuals.text_primary_color }}
                    >
                        <RefreshCcw className="w-4 h-4" />
                        Reintentar
                    </button>
                    <button 
                        onClick={handleSave}
                        className="px-8 py-3 rounded-xl text-sm font-bold shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 flex items-center gap-2"
                        style={{ 
                            backgroundColor: selectedVisuals.primary_color,
                            color: selectedVisuals.text_on_primary 
                        }}
                    >
                        <CheckCircle2 className="w-5 h-5" />
                        Aplicar Identidad
                    </button>
                </div>
            </div>
        )}

      </DialogContent>
    </Dialog>
  );
}
