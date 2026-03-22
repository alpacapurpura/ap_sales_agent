import { BrandVisuals } from "@/features/brand/types";
import { Palette, Type, Sparkles, Image as ImageIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { config } from "@/lib/config";
import Image from "next/image";

interface VisualsSectionProps {
  visuals: BrandVisuals;
  onEdit: () => void;
  onExtract: () => void;
}

export function VisualsSection({ visuals, onEdit, onExtract }: VisualsSectionProps) {
  const API_URL = config.api.baseUrl;
  const getFullUrl = (path?: string) => {
      if (!path) return "";
      if (path.startsWith("http")) return path;
      return `${API_URL}${path}`;
  };

  // Determine if we have data. Assuming valid hex code implies data.
  // If it's just empty string or default placeholder (depends on init), we treat as empty.
  const hasData = visuals.primary_color && visuals.primary_color.length > 0 && visuals.primary_color !== "#000000" && visuals.primary_color !== "#ffffff";

  // Helpers
  const ColorSwatch = ({ color, label }: { color: string, label: string }) => (
    <div className="flex flex-col gap-2 group/swatch">
        <div 
            className="h-16 w-full rounded-lg shadow-sm border border-border/10 ring-1 ring-border/5 transition-transform group-hover/swatch:scale-105" 
            style={{ backgroundColor: color }}
        />
        <div className="flex justify-between items-center">
            <span className="text-xs text-muted-foreground font-medium">{label}</span>
            <span className="text-[10px] text-muted-foreground font-mono uppercase opacity-50">{color}</span>
        </div>
    </div>
  );

  return (
    <section 
        onClick={onEdit}
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40 cursor-pointer border border-transparent hover:border-border/50"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3 text-muted-foreground group-hover:text-primary transition-colors">
            <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
                <Palette className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold uppercase tracking-wider">Identidad Visual</h3>
        </div>

        {hasData && (
             <Button 
                variant="outline" 
                size="sm" 
                className="opacity-0 group-hover:opacity-100 transition-opacity gap-2 bg-background/50 backdrop-blur-sm"
                onClick={(e) => {
                    e.stopPropagation();
                    onExtract();
                }}
            >
                <Sparkles className="w-3 h-3 text-purple-500" />
                Extraer
            </Button>
        )}
      </div>

      {!hasData ? (
         <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
            <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-4 shadow-sm">
                <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Sin Identidad Visual</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm leading-relaxed">
                No tienes colores ni tipografías definidas. Extrae tu marca automáticamente desde tu web o logo.
            </p>
            <div className="flex flex-col gap-3 w-full max-w-xs">
                <Button 
                    onClick={(e) => {
                        e.stopPropagation();
                        onExtract();
                    }}
                    className="w-full shadow-lg shadow-purple-500/20 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none"
                >
                    <Sparkles className="w-4 h-4 mr-2" />
                    Extraer Identidad
                </Button>
                <Button 
                    variant="ghost" 
                    size="sm"
                    className="text-muted-foreground hover:text-foreground"
                    onClick={(e) => {
                         e.stopPropagation();
                         onEdit();
                    }}
                >
                    Configurar Manualmente
                </Button>
            </div>
         </div>
      ) : (
        <div className="pl-0 md:pl-14">
            
            {/* Logos Section */}
            {(visuals.logos?.primary || visuals.logos?.secondary || visuals.logos?.dark_mode) && (
                <div className="mb-10">
                    <h4 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <ImageIcon className="w-4 h-4" /> Activos de Marca
                    </h4>
                    <div className="flex flex-wrap gap-6 items-end">
                        {visuals.logos?.primary && (
                            <div className="space-y-2">
                                <div className="relative h-20 px-4 py-2 border rounded-lg bg-[url('/checkerboard.png')] bg-white flex items-center justify-center min-w-[140px]">
                                    <Image 
                                        src={getFullUrl(visuals.logos.primary)} 
                                        alt="Principal" 
                                        fill
                                        className="object-contain p-2"
                                        sizes="(max-width: 768px) 100vw, 33vw"
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground font-mono uppercase">Principal</p>
                            </div>
                        )}
                        {visuals.logos?.secondary && (
                            <div className="space-y-2">
                                <div className="relative h-20 w-20 p-2 border rounded-lg bg-muted/20 flex items-center justify-center">
                                    <Image 
                                        src={getFullUrl(visuals.logos.secondary)} 
                                        alt="Icono" 
                                        fill
                                        className="object-contain p-2"
                                        sizes="(max-width: 768px) 100vw, 33vw"
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground font-mono uppercase">Icono</p>
                            </div>
                        )}
                        {visuals.logos?.dark_mode && (
                            <div className="space-y-2">
                                <div className="relative h-20 px-4 py-2 border rounded-lg bg-slate-950 flex items-center justify-center min-w-[140px]">
                                    <Image 
                                        src={getFullUrl(visuals.logos.dark_mode)} 
                                        alt="Dark Mode" 
                                        fill
                                        className="object-contain p-2"
                                        sizes="(max-width: 768px) 100vw, 33vw"
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground font-mono uppercase">Fondo Oscuro</p>
                            </div>
                        )}
                        {visuals.logos?.light_mode && (
                            <div className="space-y-2">
                                <div className="relative h-20 px-4 py-2 border rounded-lg bg-white flex items-center justify-center min-w-[140px]">
                                    <Image 
                                        src={getFullUrl(visuals.logos.light_mode)} 
                                        alt="Light Mode" 
                                        fill
                                        className="object-contain p-2"
                                        sizes="(max-width: 768px) 100vw, 33vw"
                                    />
                                </div>
                                <p className="text-[10px] text-muted-foreground font-mono uppercase">Fondo Claro</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-10">
                {/* Colors */}
                <div>
                    <h4 className="text-sm font-medium text-muted-foreground mb-4">Paleta Cromática</h4>
                    <div className="grid grid-cols-3 gap-4">
                        <ColorSwatch color={visuals.primary_color ?? "#000000"} label="Primario" />
                        <ColorSwatch color={visuals.accent_color ?? "#000000"} label="Acento" />
                        <ColorSwatch color={visuals.background_color || "#ffffff"} label="Fondo" />
                    </div>
                </div>

                {/* Typography */}
                <div>
                    <h4 className="text-sm font-medium text-muted-foreground mb-4 flex items-center gap-2">
                        <Type className="w-4 h-4" /> Tipografía
                    </h4>
                    <div className="space-y-6">
                        <div className="border-l-2 border-primary/20 pl-4 transition-colors group-hover:border-primary/40">
                            <p className="text-4xl font-bold text-foreground leading-tight" style={{ fontFamily: visuals.font_heading }}>
                                Heading Display
                            </p>
                            <p className="text-xs text-muted-foreground mt-2 font-mono">{visuals.font_heading || "Sin definir"} (Títulos)</p>
                        </div>
                        <div className="border-l-2 border-muted pl-4">
                            <p className="text-lg text-foreground/80 leading-relaxed" style={{ fontFamily: visuals.font_body }}>
                                El diseño es el embajador silencioso de tu marca. Una buena tipografía establece la jerarquía y el tono de voz visual.
                            </p>
                            <p className="text-xs text-muted-foreground mt-2 font-mono">{visuals.font_body || "Sin definir"} (Cuerpo)</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      )}
    </section>
  );
}
