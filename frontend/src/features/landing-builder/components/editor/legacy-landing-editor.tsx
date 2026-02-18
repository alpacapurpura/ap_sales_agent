"use client";

import { useState, useEffect } from "react";
import { LandingPageConfig, SqueezeContent, TransformerContent, LandingPageFont } from "@/features/landing-builder/types/schema";
import { SqueezeServerTpl } from "@/features/landing-builder/templates/server/SqueezeServerTpl";
import { TransformerVisualEditor } from "./visual/TransformerVisualEditor";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@clerk/nextjs";
import { offerApi } from "@/features/offer-studio/api";
import { settingsApi, BrandSettings } from "@/lib/api/settings";
import { toast } from "sonner";
import { Loader2, Sparkles, ArrowLeft, ExternalLink, Globe, Palette, Type, Lightbulb } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

// MOCK INITIAL STATE (Fallback)
const INITIAL_CONFIG: LandingPageConfig = {
    slug: 'demo',
    archetype: 'THE_SQUEEZE' as any,
    is_published: false,
    theme: {
        primary_color: '#3b82f6',
        secondary_color: '#eff6ff',
        font_pair: LandingPageFont.SANS_SERIF,
        dark_mode: false,
    },
    content: {
        headline: 'Tu Titular Irresistible Aquí',
        subheadline: 'Subtítulo que rompe objeciones y aclara la promesa.',
        bullets: ['Beneficio 1', 'Beneficio 2', 'Beneficio 3'],
        cta_text: '¡Lo quiero ahora!',
    } as SqueezeContent
};

// ARCHETYPE METADATA DEFINITIONS
const ARCHETYPE_INFO: Record<string, { 
    name: string; 
    description: string; 
    best_for: string; 
    structure: string[]; 
    icon: any 
}> = {
    'THE_SQUEEZE': {
        name: 'The Squeeze',
        description: 'Página ultra-minimalista diseñada con un único objetivo: capturar el email del visitante. Sin distracciones, sin menú, solo una promesa irresistible.',
        best_for: 'Lead Magnets gratuitos (Ebooks, Guías, Checklists), Listas de Espera, Webinars gratuitos.',
        structure: ['Gancho (Titular)', 'Promesa (Subtítulo)', 'Beneficios (Bullets)', 'Llamada a la Acción (CTA)'],
        icon: Sparkles
    },
    'THE_TRANSFORMER': {
        name: 'The Transformer',
        description: 'Landing de venta larga (Sales Letter) estructurada psicológicamente para vender productos de alto valor o transformación profunda.',
        best_for: 'Cursos, Mentorías Grupales, Coaching, Programas de Transformación.',
        structure: ['Promesa (Hook)', 'Problema & Agitación', 'Solución (Tu Método)', 'Autoridad', 'Oferta Irresistible (Stack)', 'Prueba Social', 'Cierre (Escasez)'],
        icon: Lightbulb
    },
    'THE_EVENT': {
        name: 'The Event',
        description: 'Diseñada para generar anticipación y registro masivo a un evento en vivo o lanzamiento.',
        best_for: 'Webinars, Challenges, Masterclasses en vivo, Lanzamientos.',
        structure: ['Fecha & Urgencia', 'Promesa del Evento', 'Oradores/Expertos', 'Qué aprenderás', 'Formulario de Registro'],
        icon: Globe
    },
    'THE_FLASH_OFFER': {
        name: 'The Flash Offer',
        description: 'Oferta directa de bajo costo (Tripwire) o descuento temporal. Urgencia visual y foco en el precio/valor.',
        best_for: 'Tripwires, Ofertas de Black Friday, Ventas Flash, Productos Low-Ticket.',
        structure: ['Oferta Limitada', 'Descuento Masivo', 'Garantía', 'Botón de Compra Directa'],
        icon: Palette
    },
    'THE_VELVET_ROPE': {
        name: 'The Velvet Rope',
        description: 'Exclusividad y Misterio. No vendes, invitas a aplicar. Filtra a los curiosos y atrae a los comprometidos.',
        best_for: 'Consultoría 1 a 1, Masterminds High-Ticket, Servicios VIP.',
        structure: ['Manifiesto', 'Para quién es/no es', 'Escasez Real', 'Botón de Aplicación (No compra)'],
        icon: Type
    },
    'THE_BROCHURE': {
        name: 'The Brochure',
        description: 'Portafolio de servicios profesional. Muestra credibilidad, procesos y casos de éxito.',
        best_for: 'Agencias, Freelancers, Servicios Corporativos (B2B).',
        structure: ['Logos de Clientes', 'Nuestros Servicios', 'Proceso de Trabajo', 'Casos de Éxito', 'Contacto'],
        icon: Globe
    }
};

export function LegacyLandingPageEditor({ 
    initialConfig,
    offerId
}: { 
    initialConfig?: LandingPageConfig,
    offerId?: string 
}) {
    const { getToken } = useAuth();
    const params = useParams();
    const tenantId = params?.tenantId as string;
    const [config, setConfig] = useState<LandingPageConfig>(initialConfig || INITIAL_CONFIG);
    const [brandSettings, setBrandSettings] = useState<BrandSettings | null>(null);
    const [isLoading, setIsLoading] = useState(!initialConfig && !!offerId);
    const [isSaving, setIsSaving] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Fetch config if not provided
    useEffect(() => {
        const fetchConfig = async () => {
            if (!offerId) return;
            
            try {
                const token = await getToken();
                if (!token) return;
                
                // Fetch Brand Settings in parallel
                settingsApi.getBrandSettings(token)
                    .then(data => {
                        setBrandSettings(data);
                        // Auto-fill logic: If config is default (Blue #3b82f6), overwrite with brand colors
                        // We check against the INITIAL_CONFIG default to know if it's "virgin"
                        setConfig(prev => {
                            if (prev.theme.primary_color === '#3b82f6') {
                                // Heuristic for font
                                const headingFont = data.visuals.font_heading.toLowerCase();
                                let fontPair: LandingPageFont = LandingPageFont.SANS_SERIF;
                                if (headingFont.includes('serif') && !headingFont.includes('sans')) fontPair = LandingPageFont.SERIF;
                                else if (['montserrat', 'poppins', 'raleway', 'futura'].some(f => headingFont.includes(f))) fontPair = LandingPageFont.MODERN;

                                return {
                                    ...prev,
                                    theme: {
                                        ...prev.theme,
                                        primary_color: data.visuals.primary_color,
                                        // Use accent or background depending on what's available, default to accent
                                        secondary_color: data.visuals.accent_color, 
                                        font_pair: fontPair
                                    }
                                };
                            }
                            return prev;
                        });
                    })
                    .catch(err => console.error("Failed to load brand settings", err));

                if (!initialConfig) {
                    setIsLoading(true);
                    const data = await offerApi.getLandingConfig(offerId, token);
                    if (data) {
                        setConfig(data);
                    } else {
                        // No config exists yet
                        console.log("No landing config found, ready to generate.");
                    }
                    setIsLoading(false);
                }
            } catch (error) {
                console.error("Failed to load landing config", error);
                toast.error("Error al cargar la configuración de la landing.");
                setIsLoading(false);
            }
        };

        fetchConfig();
    }, [offerId, initialConfig, getToken]);

    // Helper to update nested content
    const updateContent = (field: string, value: any) => {
        setConfig(prev => ({
            ...prev,
            content: { ...prev.content, [field]: value }
        }));
    };

    const updateTheme = (field: string, value: any) => {
        setConfig(prev => ({
            ...prev,
            theme: { ...prev.theme, [field]: value }
        }));
    };

    const applyBrandTheme = () => {
        if (!brandSettings) return;
        
        // Map brand settings to landing page theme
        const fontMap: Record<string, LandingPageFont> = {
            'inter': LandingPageFont.SANS_SERIF,
            'roboto': LandingPageFont.SANS_SERIF,
            'playfair display': LandingPageFont.SERIF,
            'merriweather': LandingPageFont.SERIF,
            'montserrat': LandingPageFont.MODERN,
            'raleway': LandingPageFont.MODERN
        };

        // Simple heuristic for font
        const headingFont = brandSettings.visuals.font_heading.toLowerCase();
        let fontPair: LandingPageFont = LandingPageFont.SANS_SERIF;
        
        if (headingFont.includes('serif') && !headingFont.includes('sans')) {
            fontPair = LandingPageFont.SERIF;
        } else if (['montserrat', 'poppins', 'raleway', 'futura'].some(f => headingFont.includes(f))) {
            fontPair = LandingPageFont.MODERN;
        }

        setConfig(prev => ({
            ...prev,
            theme: {
                ...prev.theme,
                primary_color: brandSettings.visuals.primary_color,
                secondary_color: brandSettings.visuals.accent_color,
                font_pair: fontPair
            }
        }));
        
        toast.success("Estilo de marca aplicado correctamente");
    };

    const handleGenerate = async () => {
        if (!offerId) return;
        
        setIsGenerating(true);
        try {
            const token = await getToken();
            if (!token) return;
            
            toast.info("Generando landing page con IA Magic... esto puede tardar unos segundos.");
            const newConfig = await offerApi.generateLandingPage(offerId, token);
            setConfig(newConfig);
            toast.success("¡Landing Page generada exitosamente!");
        } catch (error) {
            console.error(error);
            toast.error("Error al generar la landing page.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        if (!offerId) {
            toast.error("Modo Demo: No se puede guardar sin un ID de oferta.");
            return;
        }

        setIsSaving(true);
        try {
            const token = await getToken();
            if (!token) return;

            await offerApi.saveOffer(offerId, { landing_page_config: config }, token);
            toast.success("¡Landing Page guardada y publicada!");
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar los cambios.");
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>;
    }

    // Brand Color Palette Component
    const BrandColorPalette = ({ onSelect }: { onSelect: (color: string) => void }) => {
        if (!brandSettings) return null;
        
        const colors = [
            { name: 'Primario', value: brandSettings.visuals.primary_color },
            { name: 'Acento', value: brandSettings.visuals.accent_color },
            { name: 'Fondo', value: brandSettings.visuals.background_color },
            { name: 'Texto Principal', value: brandSettings.visuals.text_primary_color },
            { name: 'Texto en Primario', value: brandSettings.visuals.text_on_primary },
        ].filter(c => c.value); // Filter undefined

        return (
            <div className="flex flex-wrap gap-2 mt-2 p-2 bg-slate-50 rounded border border-slate-100">
                {colors.map((c, i) => (
                    <div 
                        key={i}
                        className="group relative cursor-pointer"
                        onClick={() => onSelect(c.value!)}
                    >
                        <div 
                            className="w-6 h-6 rounded-full border border-slate-200 shadow-sm transition-transform group-hover:scale-110" 
                            style={{ backgroundColor: c.value }} 
                        />
                        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1.5 py-0.5 bg-slate-800 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 whitespace-nowrap z-10 pointer-events-none">
                            {c.name}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 h-screen overflow-hidden">
            {/* LEFT PANEL: CONTROLS */}
            <div className="lg:col-span-3 border-r bg-muted/10 flex flex-col h-full z-20 shadow-xl">
                {/* Header */}
                <div className="p-4 border-b bg-background flex flex-col gap-4">
                     <div className="flex items-center gap-2">
                        <Link href={`/${tenantId}/offer-studio/offer/${offerId}`}>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                                <ArrowLeft className="h-4 w-4" />
                            </Button>
                        </Link>
                        <h2 className="font-bold text-lg">Visionary Canvas</h2>
                    </div>
                    <div className="flex gap-2 w-full">
                         <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={handleGenerate}
                            disabled={isGenerating || isSaving}
                            className="flex-1 text-purple-600 border-purple-200 hover:bg-purple-50"
                        >
                            {isGenerating ? <Loader2 className="h-3 w-3 animate-spin mr-2" /> : <Sparkles className="h-3 w-3 mr-2" />}
                            {isGenerating ? "Generando..." : "IA Magic"}
                        </Button>
                        <Button 
                            size="sm" 
                            variant="default" 
                            onClick={handleSave}
                            disabled={isSaving}
                            className="flex-1"
                        >
                            {isSaving ? "Guardando..." : "Publicar"}
                        </Button>
                    </div>
                </div>

                {/* Scrollable Form Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    <Tabs defaultValue="style">
                        <TabsList className="w-full grid grid-cols-2">
                            <TabsTrigger value="style">Estilo</TabsTrigger>
                            <TabsTrigger value="settings">Config</TabsTrigger>
                        </TabsList>
                        
                        {/* STYLE TAB */}
                        <TabsContent value="style" className="space-y-6 mt-4">
                            
                            {/* Brand Context Card */}
                            {brandSettings && (
                                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-3">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                                            <Lightbulb className="w-3 h-3 text-amber-500" />
                                            <span>ADN de Marca Detectado</span>
                                        </div>
                                        <Button 
                                            size="sm" 
                                            variant="ghost" 
                                            className="h-6 text-[10px] text-blue-600 hover:bg-blue-50"
                                            onClick={applyBrandTheme}
                                        >
                                            Sincronizar
                                        </Button>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div>
                                            <span className="text-slate-400 block mb-1">Colores</span>
                                            <div className="flex gap-1">
                                                <div className="w-4 h-4 rounded-full border" style={{ background: brandSettings.visuals.primary_color }} title="Primario" />
                                                <div className="w-4 h-4 rounded-full border" style={{ background: brandSettings.visuals.accent_color }} title="Acento" />
                                            </div>
                                        </div>
                                        <div>
                                            <span className="text-slate-400 block mb-1">Tipografía</span>
                                            <span className="text-slate-700 truncate block" title={brandSettings.visuals.font_heading}>
                                                {brandSettings.visuals.font_heading}
                                            </span>
                                        </div>
                                    </div>

                                    {brandSettings.strategy.unique_value_proposition && (
                                        <div className="pt-2 border-t border-slate-200">
                                            <span className="text-slate-400 block mb-1 text-[10px] uppercase tracking-wider">Propuesta de Valor (UVP)</span>
                                            <p className="text-slate-600 italic leading-snug text-[11px]">
                                                &quot;{brandSettings.strategy.unique_value_proposition}&quot;
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="space-y-3">
                                <Label>Color Primario (Marca)</Label>
                                <BrandColorPalette onSelect={(color) => updateTheme('primary_color', color)} />
                                <div className="flex gap-2 items-center">
                                    <div className="relative w-10 h-10 rounded-full overflow-hidden border shadow-sm" style={{ backgroundColor: config.theme.primary_color }}>
                                        <input 
                                            type="color" 
                                            value={config.theme.primary_color}
                                            onChange={(e) => updateTheme('primary_color', e.target.value)}
                                            className="absolute -top-4 -left-4 w-20 h-20 cursor-pointer p-0 border-0 opacity-0"
                                        />
                                    </div>
                                    <Input 
                                        value={config.theme.primary_color}
                                        onChange={(e) => updateTheme('primary_color', e.target.value)}
                                        className="flex-1 font-mono"
                                    />
                                </div>
                            </div>

                            <div className="space-y-3">
                                <Label>Color Secundario (Fondo)</Label>
                                <BrandColorPalette onSelect={(color) => updateTheme('secondary_color', color)} />
                                <div className="flex gap-2 items-center">
                                    <div className="relative w-10 h-10 rounded-full overflow-hidden border shadow-sm" style={{ backgroundColor: config.theme.secondary_color }}>
                                        <input 
                                            type="color" 
                                            value={config.theme.secondary_color}
                                            onChange={(e) => updateTheme('secondary_color', e.target.value)}
                                            className="absolute -top-4 -left-4 w-20 h-20 cursor-pointer p-0 border-0 opacity-0"
                                        />
                                    </div>
                                    <Input 
                                        value={config.theme.secondary_color}
                                        onChange={(e) => updateTheme('secondary_color', e.target.value)}
                                        className="flex-1 font-mono"
                                    />
                                </div>
                            </div>
                        </TabsContent>

                        {/* SETTINGS TAB */}
                        <TabsContent value="settings" className="space-y-4 mt-4">
                            {/* Rich Archetype Display */}
                            {ARCHETYPE_INFO[config.archetype] ? (
                                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-4 rounded-lg border border-indigo-100 shadow-sm">
                                    <div className="flex items-center gap-2 mb-2 text-indigo-700">
                                        {(() => {
                                            const Icon = ARCHETYPE_INFO[config.archetype].icon;
                                            return <Icon className="w-5 h-5" />;
                                        })()}
                                        <h3 className="font-bold text-sm">{ARCHETYPE_INFO[config.archetype].name}</h3>
                                    </div>
                                    
                                    <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                                        {ARCHETYPE_INFO[config.archetype].description}
                                    </p>

                                    <div className="space-y-2">
                                        <div className="flex items-start gap-2">
                                            <div className="bg-green-100 text-green-700 text-[10px] px-1.5 py-0.5 rounded font-medium mt-0.5">Ideal para</div>
                                            <p className="text-[11px] text-slate-500 leading-tight">
                                                {ARCHETYPE_INFO[config.archetype].best_for}
                                            </p>
                                        </div>

                                        <div className="bg-white/60 rounded p-2 border border-indigo-50/50">
                                            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">Estructura Psicológica</span>
                                            <div className="flex flex-wrap gap-1">
                                                {ARCHETYPE_INFO[config.archetype].structure.map((step, i) => (
                                                    <span key={i} className="text-[10px] bg-white border px-1.5 py-0.5 rounded text-slate-600 shadow-sm">
                                                        {i + 1}. {step}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="bg-blue-50 p-3 rounded text-xs text-blue-700 mb-4">
                                    Arquetipo: <strong>{config.archetype}</strong>
                                </div>
                            )}
                            
                             <div className="pt-4 border-t">
                                <Label>URL Pública</Label>
                                <div className="flex items-center gap-2 mt-2 bg-slate-100 p-2 rounded border">
                                    <Globe className="w-4 h-4 text-muted-foreground" />
                                    <span className="text-xs text-muted-foreground flex-1 truncate">
                                        {config.is_published 
                                            ? `${process.env.NEXT_PUBLIC_APP_URL || ''}${config.slug}` 
                                            : "No publicada"}
                                    </span>
                                    {config.is_published ? (
                                        <Link href={`/p/${config.slug.replace('/p/', '')}`} target="_blank">
                                            <Button size="icon" variant="ghost" className="h-6 w-6" title="Ver Landing Pública">
                                                <ExternalLink className="h-3 w-3" />
                                            </Button>
                                        </Link>
                                    ) : (
                                        <Link href={`/preview/${offerId}`} target="_blank">
                                            <Button size="icon" variant="ghost" className="h-6 w-6" title="Vista Previa (Borrador)">
                                                <ExternalLink className="h-3 w-3 text-amber-500" />
                                            </Button>
                                        </Link>
                                    )}
                                </div>
                                {!config.is_published && (
                                    <p className="text-[10px] text-amber-600 mt-1">
                                        * Usa el botón <ExternalLink className="w-3 h-3 inline" /> para ver la Vista Previa segura antes de publicar.
                                    </p>
                                )}
                            </div>
                        </TabsContent>
                    </Tabs>

                    <div className="p-4 bg-yellow-50 text-yellow-800 text-xs rounded-lg border border-yellow-200">
                        <strong>Tip Visionario:</strong> Haz clic en cualquier texto o imagen de la derecha para editarlo directamente.
                    </div>
                </div>
            </div>

            {/* RIGHT PANEL: LIVE PREVIEW (CANVAS) */}
            <div className="lg:col-span-9 bg-slate-200 flex flex-col h-full overflow-hidden relative">
                <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20 bg-white/90 backdrop-blur px-4 py-1 rounded-full shadow-sm text-xs font-medium text-slate-500 border">
                    Visionary Canvas • Desktop View
                </div>
                
                <div className="flex-1 overflow-y-auto p-4 md:p-8 flex items-start justify-center">
                    <div className="w-full max-w-[1200px] bg-white shadow-2xl min-h-[800px] rounded-lg overflow-hidden border ring-1 ring-black/5 transition-all">
                        {config.archetype === 'THE_TRANSFORMER' ? (
                            <TransformerVisualEditor 
                                content={config.content as TransformerContent} 
                                onChange={updateContent as any}
                                theme={config.theme}
                            />
                        ) : (
                            <SqueezeServerTpl 
                                content={config.content as SqueezeContent} 
                                theme={config.theme} 
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
