"use client";

import NextImage from "next/image";
import { useAuth } from "@clerk/nextjs";
import ColorThief from "colorthief";
import {
  Globe,
  Upload,
  Palette,
  CheckCircle2,
  Loader2,
  Sparkles,
  RefreshCcw,
  AlertTriangle,
  WifiOff,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { brandApi } from "@/features/brand/api";

import type { BrandVisuals } from "@/features/brand/types";

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
  {
    id: "corporate",
    name: "Corporate & Trust",
    primary: "#0f172a",
    accent: "#3b82f6",
    fontHeading: "Inter",
    fontBody: "Inter",
  },
  {
    id: "luxury",
    name: "Luxury & Elegant",
    primary: "#1c1917",
    accent: "#d4af37",
    fontHeading: "Playfair Display",
    fontBody: "Lato",
  },
  {
    id: "playful",
    name: "Playful & Vivid",
    primary: "#7c3aed",
    accent: "#f43f5e",
    fontHeading: "Poppins",
    fontBody: "Nunito",
  },
  {
    id: "minimal",
    name: "Minimal & Clean",
    primary: "#171717",
    accent: "#525252",
    fontHeading: "DM Sans",
    fontBody: "DM Sans",
  },
];

interface WizardSelectSourceProps {
  analyzing: boolean;
  progress: number;
  stage: string;
  errorState: { type: "timeout" | "generic"; message: string } | null;
  webUrl: string;
  logoUrl?: string;
  onWebUrlChange: (url: string) => void;
  onAnalyzeWeb: () => void;
  onAnalyzeLogo: () => void;
  onSelectKit: (kit: (typeof VIBE_KITS)[0]) => void;
  onClearError: () => void;
}

function WizardSelectSource({
  analyzing,
  progress,
  stage,
  errorState,
  webUrl,
  logoUrl,
  onWebUrlChange,
  onAnalyzeWeb,
  onAnalyzeLogo,
  onSelectKit,
  onClearError,
}: WizardSelectSourceProps) {
  return (
    <>
      <div className="p-6 border-b bg-muted/20">
        <DialogHeader>
          <DialogTitle className="text-xl">Definir ADN Visual</DialogTitle>
          <DialogDescription>
            Elige la fuente de verdad para los colores y tipografía de tu marca.
          </DialogDescription>
        </DialogHeader>
      </div>

      <div className="flex-1 overflow-y-auto p-6 bg-muted/10">
        {errorState && !analyzing && (
          <Alert variant="destructive" className="mb-6 animate-in shake">
            {errorState.type === "timeout" ? (
              <WifiOff className="h-4 w-4" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <AlertTitle>
              {errorState.type === "timeout"
                ? "El analisis tardo demasiado"
                : "Error en el analisis visual"}
            </AlertTitle>
            <AlertDescription className="mt-2 text-sm">
              {errorState.type === "timeout" ? (
                <div className="space-y-2">
                  <p>El analisis tardo mas de lo esperado y la conexion se cerro.</p>
                  <p className="font-semibold">Sugerencia: Intenta de nuevo o verifica la URL.</p>
                </div>
              ) : (
                errorState.message
              )}
            </AlertDescription>
            <div className="mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={onClearError}
                className="bg-background/50"
              >
                Intentar de nuevo
              </Button>
            </div>
          </Alert>
        )}

        {analyzing ? (
          <div className="py-8 space-y-6 text-center flex flex-col items-center justify-center h-full">
            <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
              <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
              <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              <Palette className="w-8 h-8 text-primary animate-pulse" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-medium">{stage}</h3>
              <Progress value={progress} className="h-2 w-full max-w-xs mx-auto" />
              <p className="text-sm text-muted-foreground">Esto puede tomar hasta 1 minuto...</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full items-center">
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
                  <Input
                    value={webUrl}
                    onChange={(e) => onWebUrlChange(e.target.value)}
                    placeholder="https://tusitio.com"
                  />
                </div>
                <Button className="w-full" onClick={onAnalyzeWeb} disabled={analyzing}>
                  {analyzing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Escanear Web"}
                </Button>
              </CardContent>
            </Card>

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
                    <div className="relative h-16 w-full">
                      <NextImage
                        src={logoUrl}
                        alt="Logo"
                        fill
                        className="object-contain"
                        unoptimized
                      />
                    </div>
                    <Button className="w-full" onClick={onAnalyzeLogo} disabled={analyzing}>
                      {analyzing ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        "Extraer de Logo"
                      )}
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-4 text-sm text-muted-foreground bg-muted/20 rounded-lg border border-dashed">
                    Sube tu logo primero en &quot;Identidad&quot;
                  </div>
                )}
              </CardContent>
            </Card>

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
                  {VIBE_KITS.map((kit) => (
                    <button
                      key={kit.id}
                      onClick={() => onSelectKit(kit)}
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
        )}
      </div>
    </>
  );
}

interface WizardPreviewProps {
  visuals: BrandVisuals;
  onBack: () => void;
  onSave: () => void;
}

function WizardPreview({ visuals, onBack, onSave }: WizardPreviewProps) {
  return (
    <div
      className="flex-1 flex flex-col transition-colors duration-500 overflow-hidden"
      style={{
        backgroundColor: visuals.background_color || "#ffffff",
        color: visuals.text_primary_color || "#000000",
        fontFamily: visuals.font_body || "inherit",
      }}
    >
      <div className="p-8 pb-0 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <Sparkles className="w-6 h-6" style={{ color: visuals.accent_color }} />
          <h2 className="text-2xl font-bold" style={{ fontFamily: visuals.font_heading }}>
            Identidad Detectada
          </h2>
        </div>
        <div
          className="px-3 py-1 rounded-full text-xs font-medium border"
          style={{ borderColor: visuals.text_primary_color, opacity: 0.6 }}
        >
          {visuals.design_style || "Personalizado"}
        </div>
      </div>

      <div className="flex-1 p-8 flex gap-8 items-start overflow-y-auto min-h-0">
        <div className="w-1/3 space-y-6">
          <div
            className="aspect-square rounded-2xl shadow-xl flex flex-col items-center justify-center p-6 text-center border transition-all"
            style={{
              borderColor: visuals.primary_color,
              backgroundColor: visuals.background_color,
            }}
          >
            <div
              className="w-24 h-24 rounded-full mb-4 shadow-lg"
              style={{ backgroundColor: visuals.primary_color }}
            />
            <h3 className="text-xl font-bold mb-1" style={{ fontFamily: visuals.font_heading }}>
              Tu Marca
            </h3>
            <p className="text-sm opacity-80">Así se ven tus colores principales en contexto.</p>
            <button
              className="mt-6 px-6 py-2 rounded-lg text-sm font-bold shadow-md transition-transform hover:scale-105"
              style={{ backgroundColor: visuals.primary_color, color: visuals.text_on_primary }}
            >
              Call to Action
            </button>
          </div>
        </div>

        <div className="flex-1 space-y-8">
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: "Primario", color: visuals.primary_color },
              ...(visuals.secondary_color
                ? [{ label: "Secundario", color: visuals.secondary_color }]
                : []),
              { label: "Acento", color: visuals.accent_color },
              { label: "Fondo", color: visuals.background_color },
              { label: "Texto", color: visuals.text_primary_color },
            ].map(({ label, color }) => (
              <div key={label} className="p-4 rounded-xl border bg-black/5">
                <span className="text-xs uppercase tracking-wider opacity-60 block mb-2">
                  {label}
                </span>
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg shadow-sm border"
                    style={{ background: color }}
                  />
                  <span className="font-mono text-sm font-medium">{color}</span>
                </div>
              </div>
            ))}
          </div>

          {visuals.color_palette && visuals.color_palette.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs uppercase tracking-wider opacity-60">Paleta Extendida</h4>
              <div className="flex flex-wrap gap-2">
                {visuals.color_palette.map((color, i) => (
                  <div key={i} className="flex flex-col items-center gap-1">
                    <div
                      className="w-8 h-8 rounded-md shadow-sm border border-black/10"
                      style={{ background: color }}
                    />
                    <span className="font-mono text-[9px] opacity-50">{color}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {visuals.gradient_definitions && visuals.gradient_definitions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs uppercase tracking-wider opacity-60">Gradientes</h4>
              <div className="flex gap-2">
                {visuals.gradient_definitions.map((grad, i) => (
                  <div
                    key={i}
                    className="h-8 flex-1 rounded-md shadow-sm"
                    style={{ background: grad }}
                  />
                ))}
              </div>
            </div>
          )}

          {visuals.font_accent && (
            <div className="p-3 rounded-lg bg-black/5 border">
              <span className="text-xs uppercase tracking-wider opacity-60 block mb-1">
                Font Accent
              </span>
              <p className="text-lg" style={{ fontFamily: visuals.font_accent }}>
                {visuals.font_accent}
              </p>
            </div>
          )}

          {visuals.brand_mood?.adjectives && visuals.brand_mood.adjectives.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs uppercase tracking-wider opacity-60">Personalidad Visual</h4>
              <div className="flex flex-wrap gap-2">
                {visuals.brand_mood.adjectives.map((adj, i) => (
                  <span
                    key={i}
                    className="px-3 py-1 rounded-full text-xs font-medium border"
                    style={{ borderColor: visuals.accent_color, color: visuals.text_primary_color }}
                  >
                    {adj}
                  </span>
                ))}
                {visuals.brand_mood.energy && (
                  <span
                    className="px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: visuals.primary_color,
                      color: visuals.text_on_primary,
                    }}
                  >
                    Energia: {visuals.brand_mood.energy}
                  </span>
                )}
              </div>
            </div>
          )}

          {visuals.usage_guidelines && visuals.usage_guidelines.length > 0 && (
            <div className="space-y-3">
              <h4 className="font-bold text-sm uppercase opacity-70 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                Reglas de Diseño
              </h4>
              <ul className="space-y-2">
                {visuals.usage_guidelines.map((rule, i) => (
                  <li key={i} className="flex gap-3 text-sm opacity-90 p-3 rounded-lg bg-black/5">
                    <CheckCircle2
                      className="w-5 h-5 flex-shrink-0"
                      style={{ color: visuals.primary_color }}
                    />
                    {rule}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 border-t bg-black/5 flex justify-between items-center flex-shrink-0">
        <button
          onClick={onBack}
          className="px-6 py-2 rounded-lg text-sm font-medium hover:bg-black/5 transition-colors flex items-center gap-2"
          style={{ color: visuals.text_primary_color }}
        >
          <RefreshCcw className="w-4 h-4" />
          Reintentar
        </button>
        <button
          onClick={onSave}
          className="px-8 py-3 rounded-xl text-sm font-bold shadow-lg hover:shadow-xl transition-all hover:-translate-y-0.5 flex items-center gap-2"
          style={{ backgroundColor: visuals.primary_color, color: visuals.text_on_primary }}
        >
          <CheckCircle2 className="w-5 h-5" />
          Aplicar Identidad
        </button>
      </div>
    </div>
  );
}

export function BrandVisualsWizard({
  isOpen,
  onOpenChange,
  currentVisuals,
  logoUrl,
  websiteUrl,
  onSave,
}: BrandVisualsWizardProps) {
  const [step, setStep] = useState<"select-source" | "preview">("select-source");
  const [selectedVisuals, setSelectedVisuals] = useState<BrandVisuals>(currentVisuals);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<string>("");
  const [errorState, setErrorState] = useState<{
    type: "timeout" | "generic";
    message: string;
  } | null>(null);
  const [webUrl, setWebUrl] = useState(websiteUrl || "");
  const { getToken } = useAuth();

  // --- ACTIONS ---

  const handleAnalyzeWeb = async () => {
    const urlToScan = webUrl.trim();
    if (!urlToScan) {
      toast.error("Ingresa la URL de tu sitio web.");
      return;
    }

    let progressInterval: NodeJS.Timeout | undefined;
    const stageTimeouts: NodeJS.Timeout[] = [];

    try {
      const token = await getToken();
      if (!token) throw new Error("No auth token");

      setAnalyzing(true);
      setErrorState(null);
      setProgress(5);
      setStage("Iniciando escaneo visual...");

      // Asymptotic progress simulation
      progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) return prev;
          const increment = Math.max(0.5, (90 - prev) / 50);
          return Math.min(prev + increment, 90);
        });
      }, 800);

      // Stage messages specific to visual extraction
      stageTimeouts.push(setTimeout(() => setStage("Escaneando sitio web..."), 2000));
      stageTimeouts.push(setTimeout(() => setStage("Analizando paleta de colores..."), 6000));
      stageTimeouts.push(setTimeout(() => setStage("Detectando tipografias..."), 12000));
      stageTimeouts.push(setTimeout(() => setStage("Analizando sistema de diseno..."), 18000));
      stageTimeouts.push(setTimeout(() => setStage("Detectando personalidad visual..."), 22000));
      stageTimeouts.push(setTimeout(() => setStage("Generando reglas de uso..."), 26000));

      const extracted = await brandApi.extractBrandVisuals(urlToScan, token);

      if (progressInterval) clearInterval(progressInterval);
      stageTimeouts.forEach((t) => clearTimeout(t));
      setProgress(100);
      setStage("Identidad visual detectada!");

      setTimeout(() => {
        setSelectedVisuals({
          ...selectedVisuals,
          ...extracted,
          style_preset: "custom-web",
        });
        setStep("preview");
        setAnalyzing(false);
        setProgress(0);
        setStage("");
      }, 800);
    } catch (error: unknown) {
      if (progressInterval) clearInterval(progressInterval);
      stageTimeouts.forEach((t) => clearTimeout(t));
      console.error(error);

      const isTimeout =
        error instanceof Error &&
        (error.message?.includes("Failed to fetch") ||
          error.message?.includes("Network request failed") ||
          error.message?.startsWith("TIMEOUT:"));

      setErrorState({
        type: isTimeout ? "timeout" : "generic",
        message: error instanceof Error ? error.message : "Error desconocido",
      });
      setStage("Proceso interrumpido");
      setProgress(0);
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
            `#${[r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("")}`;

          setSelectedVisuals({
            ...selectedVisuals,
            primary_color: rgbToHex(r1, g1, b1),
            accent_color: rgbToHex(r2, g2, b2),
            style_preset: "custom-logo",
          });
        }
        setAnalyzing(false);
        setStep("preview");
      };

      img.onerror = () => {
        console.error("Error loading image for color extraction");
        setAnalyzing(false);
      };
    } catch (e) {
      console.error(e);
      setAnalyzing(false);
    }
  };

  const handleSelectKit = (kit: (typeof VIBE_KITS)[0]) => {
    setSelectedVisuals({
      primary_color: kit.primary,
      accent_color: kit.accent,
      font_heading: kit.fontHeading,
      font_body: kit.fontBody,
      style_preset: kit.id,
    });
    setStep("preview");
  };

  const handleSave = async () => {
    await onSave(selectedVisuals);
    onOpenChange(false);
    setStep("select-source"); // Reset
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(val) => {
        if (!analyzing) onOpenChange(val);
      }}
    >
      <DialogContent
        className="max-w-4xl h-[80vh] flex flex-col p-0 overflow-hidden"
        onInteractOutside={(e) => e.preventDefault()}
      >
        {step === "select-source" ? (
          <WizardSelectSource
            analyzing={analyzing}
            progress={progress}
            stage={stage}
            errorState={errorState}
            webUrl={webUrl}
            logoUrl={logoUrl}
            onWebUrlChange={setWebUrl}
            onAnalyzeWeb={handleAnalyzeWeb}
            onAnalyzeLogo={handleAnalyzeLogo}
            onSelectKit={handleSelectKit}
            onClearError={() => setErrorState(null)}
          />
        ) : (
          <WizardPreview
            visuals={selectedVisuals}
            onBack={() => setStep("select-source")}
            onSave={handleSave}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
