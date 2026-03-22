"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
    Loader2, AlertTriangle, CheckCircle2, Globe, Wand2, ArrowRight, FileText, Info, UploadCloud, File as FileIcon, X, Sparkles, WifiOff
} from "lucide-react";
import { BrandSettings } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface SmartFillDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    mode: "initial" | "update";
    onSuccess: (data: Partial<BrandSettings>) => void;
    onPreview?: (data: Partial<BrandSettings> | null) => void;
    currentUrl?: string;
}

export function SmartFillDialog({ 
    open, 
    onOpenChange, 
    mode, 
    onSuccess, 
    onPreview, 
    currentUrl = "" 
}: SmartFillDialogProps) {
    const { getToken } = useAuth();
    
    // Form State
    const [sourceType, setSourceType] = useState<"web" | "manual">("web");
    const [url, setUrl] = useState(currentUrl || "");
    const [text, setText] = useState("");
    const [instructions, setInstructions] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [includeVisuals, setIncludeVisuals] = useState(false);
    
    // Process State
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState<string>("");
    const [extractedData, setExtractedData] = useState<Partial<BrandSettings> | null>(null);
    const [errorState, setErrorState] = useState<{ type: "timeout" | "generic", message: string } | null>(null);

    const resetForm = () => {
        setExtractedData(null);
        setErrorState(null);
        setProgress(0);
        setStage("");
        setIsProcessing(false);
        if (onPreview) onPreview(null);
    };

    const handleExtract = async () => {
        if (sourceType === "web" && !url) {
            toast.error("Por favor ingresa una URL válida.");
            return;
        }
        if (sourceType === "manual" && !text && files.length === 0 && !instructions) {
            toast.error("Ingresa texto, sube archivos o escribe instrucciones.");
            return;
        }

        let progressInterval: NodeJS.Timeout | undefined;

        try {
            const token = await getToken();
            if (!token) {
                toast.error("No autenticado");
                return;
            }

            setIsProcessing(true);
            setErrorState(null);
            setExtractedData(null);
            setProgress(5);
            setStage("Iniciando asistente de marca...");

            // Simulation of progress
            progressInterval = setInterval(() => {
                setProgress((prev) => {
                    if (prev >= 90) return prev;
                    // Slower increment as it approaches 90
                    const increment = Math.max(0.5, (90 - prev) / 50); 
                    return Math.min(prev + increment, 90);
                });
            }, 800);

            // Dynamic Stage Messages
            setTimeout(() => setStage(sourceType === "web" ? "Escaneando sitio web..." : "Leyendo documentos..."), 2000);
            if (includeVisuals) {
                setTimeout(() => setStage("Extrayendo identidad visual (Esto puede tardar)..."), 5000);
            }
            setTimeout(() => setStage("Analizando tono de voz y narrativa..."), includeVisuals ? 15000 : 8000);
            setTimeout(() => setStage("Estructurando estrategia de marca..."), includeVisuals ? 25000 : 12000);

            // Prepare FormData
            const formData = new FormData();
            formData.append("mode", mode);
            
            if (sourceType === "web") {
                formData.append("url", url);
                if (includeVisuals) formData.append("include_visuals", "true");
            } else {
                if (text) formData.append("text", text);
                files.forEach(file => formData.append("files", file));
            }

            if (instructions) formData.append("update_instructions", instructions);
            if (mode === "update") formData.append("dry_run", "true");

            // API Call
            const data = await brandApi.extractFullBrand(formData, token);
            
            if (progressInterval) clearInterval(progressInterval);
            setProgress(100);
            setStage("¡Análisis completado!");
            setExtractedData(data);
            
            if (onPreview) {
                onPreview(data);
                toast.success("Vista previa lista para revisar.");
            } else {
                toast.success("Datos extraídos exitosamente");
            }

        } catch (error: any) {
            if (progressInterval) clearInterval(progressInterval);
            console.error("[SmartFill] Error:", error);
            
            const isTimeout = error.message?.includes("Failed to fetch") || error.message?.includes("Network request failed");
            
            setErrorState({
                type: isTimeout ? "timeout" : "generic",
                message: error.message || "Error desconocido"
            });
            
            setStage("Proceso interrumpido");
            setProgress(0);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleApply = () => {
        if (extractedData) {
            onSuccess(extractedData);
            resetForm();
            onOpenChange(false); // Close dialog
            toast.success("Cambios aplicados a tu marca.");
        }
    };

    return (
        <Dialog open={open} onOpenChange={(val) => {
            if (!isProcessing) {
                onOpenChange(val);
                if (!val) resetForm();
            }
        }}>
            <DialogContent className="sm:max-w-2xl gap-0 p-0 overflow-hidden border-none shadow-2xl">
                {/* Header with Brand Gradient */}
                <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-6 border-b">
                    <DialogHeader>
                        <DialogTitle className="text-2xl flex items-center gap-2">
                            <Wand2 className="w-6 h-6 text-primary" />
                            {mode === "initial" ? "Configuración con IA" : "Refinamiento de Marca"}
                        </DialogTitle>
                        <DialogDescription className="text-base">
                            {mode === "initial" 
                                ? "Déjanos analizar tu presencia digital para construir tu ADN de marca."
                                : "Actualiza tu estrategia o identidad con nueva información."}
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-6">
                    {/* VIEW: SUCCESS / REVIEW */}
                    {extractedData ? (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                            <div className="flex items-center gap-4 bg-green-50 dark:bg-green-950/30 p-4 rounded-lg border border-green-200 dark:border-green-800">
                                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-full">
                                    <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-green-800 dark:text-green-300">Análisis Completado</h3>
                                    <p className="text-sm text-green-700 dark:text-green-400">
                                        Hemos extraído {Object.keys(extractedData).length} secciones clave de tu marca.
                                    </p>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                {extractedData.identity?.brand_name && (
                                    <div className="p-3 bg-secondary/50 rounded-md text-sm border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Identidad</span>
                                        <span className="font-medium">{extractedData.identity.brand_name}</span>
                                    </div>
                                )}
                                {extractedData.strategy?.value_proposition && (
                                    <div className="p-3 bg-secondary/50 rounded-md text-sm border">
                                        <span className="text-muted-foreground block text-xs uppercase tracking-wider">Estrategia</span>
                                        <span className="font-medium truncate block">Propuesta de Valor detectada</span>
                                    </div>
                                )}
                                {extractedData.visuals?.primary_color && (
                                    <div className="p-3 bg-secondary/50 rounded-md text-sm border flex items-center gap-2">
                                        <div className="w-4 h-4 rounded-full border" style={{ background: extractedData.visuals.primary_color }} />
                                        <span className="font-medium">Paleta de Colores</span>
                                    </div>
                                )}
                            </div>

                            <Alert>
                                <Info className="h-4 w-4" />
                                <AlertTitle>Modo Previsualización</AlertTitle>
                                <AlertDescription>
                                    Puedes ver los cambios aplicados en el fondo. Si te gusta lo que ves, haz click en Aplicar.
                                </AlertDescription>
                            </Alert>
                        </div>
                    ) : (
                        /* VIEW: FORM INPUT */
                        <div className="space-y-6">
                            {/* Error State */}
                            {errorState && (
                                <Alert variant="destructive" className="animate-in shake">
                                    {errorState.type === "timeout" ? <WifiOff className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
                                    <AlertTitle>
                                        {errorState.type === "timeout" ? "El análisis tardó demasiado" : "Error en el análisis"}
                                    </AlertTitle>
                                    <AlertDescription className="mt-2 text-sm">
                                        {errorState.type === "timeout" ? (
                                            <div className="space-y-2">
                                                <p>La extracción de identidad visual es un proceso pesado y la conexión se cerró.</p>
                                                <p className="font-semibold">Sugerencia: Intenta desactivar &quot;Extraer Identidad Visual&quot; o sube la información como texto.</p>
                                            </div>
                                        ) : (
                                            errorState.message
                                        )}
                                    </AlertDescription>
                                    <div className="mt-4">
                                        <Button variant="outline" size="sm" onClick={() => setErrorState(null)} className="bg-background/50">
                                            Intentar de nuevo
                                        </Button>
                                    </div>
                                </Alert>
                            )}

                            {/* Processing State */}
                            {isProcessing ? (
                                <div className="py-8 space-y-6 text-center">
                                    <div className="relative mx-auto w-24 h-24 flex items-center justify-center">
                                        <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
                                        <div className="absolute inset-0 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                                        <Wand2 className="w-8 h-8 text-primary animate-pulse" />
                                    </div>
                                    <div className="space-y-2">
                                        <h3 className="text-lg font-medium">{stage}</h3>
                                        <Progress value={progress} className="h-2 w-full max-w-xs mx-auto" />
                                        <p className="text-sm text-muted-foreground">Esto puede tomar hasta 2 minutos...</p>
                                    </div>
                                </div>
                            ) : (
                                /* Input Form */
                                !errorState && (
                                    <Tabs value={sourceType} onValueChange={(v) => setSourceType(v as any)} className="w-full">
                                        <TabsList className="grid w-full grid-cols-2 mb-6">
                                            <TabsTrigger value="web">Desde Sitio Web</TabsTrigger>
                                            <TabsTrigger value="manual">Documentos / Texto</TabsTrigger>
                                        </TabsList>

                                        <TabsContent value="web" className="space-y-4 animate-in fade-in slide-in-from-left-2">
                                            <div className="space-y-2">
                                                <Label className="text-base font-semibold">URL de tu Sitio Web</Label>
                                                <div className="relative">
                                                    <Globe className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                                                    <Input 
                                                        placeholder="https://tumarca.com" 
                                                        className="pl-10 h-11 text-lg"
                                                        value={url}
                                                        onChange={(e) => setUrl(e.target.value)}
                                                    />
                                                </div>
                                                <p className="text-sm text-muted-foreground">
                                                    Analizaremos la página principal y secciones clave como &quot;Nosotros&quot; o &quot;Servicios&quot;.
                                                </p>
                                            </div>

                                            <div className="bg-secondary/30 p-4 rounded-lg border border-border/50 space-y-3">
                                                <div className="flex items-start space-x-3">
                                                    <Checkbox 
                                                        id="includeVisuals" 
                                                        checked={includeVisuals}
                                                        onCheckedChange={(c) => setIncludeVisuals(!!c)}
                                                        className="mt-1"
                                                    />
                                                    <div className="space-y-1">
                                                        <Label 
                                                            htmlFor="includeVisuals" 
                                                            className="text-base font-medium cursor-pointer"
                                                        >
                                                            Extraer también Identidad Visual
                                                        </Label>
                                                        <p className="text-xs text-muted-foreground">
                                                            Intentaremos detectar tu logo, colores y tipografías automáticamente.
                                                            <span className="block text-amber-600 dark:text-amber-500 font-medium mt-1">
                                                                Nota: Esto aumenta significativamente el tiempo de análisis.
                                                            </span>
                                                        </p>
                                                    </div>
                                                </div>
                                            </div>
                                        </TabsContent>

                                        <TabsContent value="manual" className="space-y-4 animate-in fade-in slide-in-from-right-2">
                                            <div className="space-y-2">
                                                <Label>Pega información sobre tu marca</Label>
                                                <Textarea 
                                                    placeholder="Describe tu historia, valores, equipo y productos..."
                                                    className="min-h-[150px]"
                                                    value={text}
                                                    onChange={(e) => setText(e.target.value)}
                                                />
                                            </div>
                                            
                                            <div className="space-y-2">
                                                <Label>O sube documentos (PDF, DOCX)</Label>
                                                <div className="border-2 border-dashed rounded-lg p-6 hover:bg-muted/50 transition-colors text-center relative group cursor-pointer">
                                                    <input 
                                                        type="file" 
                                                        multiple 
                                                        accept=".pdf,.docx,.txt,.md"
                                                        className="absolute inset-0 opacity-0 cursor-pointer z-10"
                                                        onChange={(e) => {
                                                            if (e.target.files) setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
                                                            e.target.value = "";
                                                        }}
                                                    />
                                                    <UploadCloud className="h-8 w-8 mx-auto text-muted-foreground group-hover:text-primary mb-2 transition-colors" />
                                                    <p className="text-sm font-medium">Arrastra archivos aquí</p>
                                                </div>
                                                
                                                {files.length > 0 && (
                                                    <div className="flex flex-wrap gap-2 mt-2">
                                                        {files.map((f, i) => (
                                                            <Badge key={i} variant="secondary" className="pl-2 pr-1 py-1 flex items-center gap-1">
                                                                <FileIcon className="w-3 h-3" />
                                                                <span className="max-w-[100px] truncate">{f.name}</span>
                                                                <Button variant="ghost" size="icon" className="h-4 w-4 ml-1 hover:bg-destructive/20 rounded-full" onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}>
                                                                    <X className="w-3 h-3" />
                                                                </Button>
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </TabsContent>
                                    </Tabs>
                                )
                            )}
                            
                            {/* Update Instructions (Only in Update Mode) */}
                            {(mode === "update" && !isProcessing && !errorState && !extractedData) && (
                                <div className="pt-4 border-t">
                                    <Label>Instrucciones de Actualización (Opcional)</Label>
                                    <Input 
                                        placeholder="Ej: Solo actualiza la historia, mantén el resto igual..."
                                        value={instructions}
                                        onChange={(e) => setInstructions(e.target.value)}
                                        className="mt-1.5"
                                    />
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <DialogFooter className="p-6 bg-secondary/20 border-t gap-2 sm:gap-0">
                    {extractedData ? (
                        <>
                            <Button variant="outline" onClick={resetForm}>Volver a empezar</Button>
                            <Button onClick={handleApply} className="bg-green-600 hover:bg-green-700 text-white gap-2">
                                Aplicar Cambios <CheckCircle2 className="w-4 h-4" />
                            </Button>
                        </>
                    ) : (
                        !isProcessing && (
                            <>
                                <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancelar</Button>
                                <Button onClick={handleExtract} disabled={isProcessing} className="gap-2 min-w-[140px]">
                                    <Sparkles className="w-4 h-4" />
                                    {mode === "initial" ? "Generar Marca" : "Actualizar"}
                                </Button>
                            </>
                        )
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
