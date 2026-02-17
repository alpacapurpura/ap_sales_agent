import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Loader2, AlertTriangle, CheckCircle2, Globe, Wand2, ArrowRight, FileText, Info, UploadCloud, File as FileIcon, X } from "lucide-react";
import { brandApi, BrandSettings } from "@/lib/api/brand";
import { toast } from "sonner";

interface SmartFillCardProps {
    mode: "initial" | "update";
    onSuccess: (data: Partial<BrandSettings>) => void;
    onPreview?: (data: Partial<BrandSettings> | null) => void;
    currentUrl?: string;
}

export function SmartFillCard({ mode, onSuccess, onPreview, currentUrl = "" }: SmartFillCardProps) {
    const { getToken } = useAuth();
    const [url, setUrl] = useState(currentUrl);
    const [text, setText] = useState("");
    const [instructions, setInstructions] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState<string>("");
    const [extractedData, setExtractedData] = useState<Partial<BrandSettings> | null>(null);

    const handleExtract = async () => {
        if (!url && !text && !instructions && files.length === 0) {
            toast.error("Por favor ingresa una URL, texto, archivos o instrucciones.");
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
            setExtractedData(null);
            setProgress(5);
            setStage("Conectando con el asistente...");

            // Simulación de progreso
            progressInterval = setInterval(() => {
                setProgress((prev) => {
                    if (prev >= 90) return prev;
                    // Incremento variable para parecer natural
                    const increment = Math.random() * 5; 
                    return Math.min(prev + increment, 90);
                });
            }, 800);

            // Cambios de estado simulados basados en tiempo esperado
            setTimeout(() => setStage("Analizando sitio web y documentos..."), 2000);
            setTimeout(() => setStage("Extrayendo identidad visual y tono..."), 5000);
            setTimeout(() => setStage("Generando estrategia y narrativa..."), 10000);
            setTimeout(() => setStage("Estructurando equipo y testimonios..."), 15000);

            // Prepare FormData
            const formData = new FormData();
            if (url) formData.append("url", url);
            if (text) formData.append("text", text);
            formData.append("mode", mode);
            if (instructions) formData.append("update_instructions", instructions);
            
            // Enable dry_run for updates to allow preview
            if (mode === "update") {
                formData.append("dry_run", "true");
            }
            
            files.forEach(file => {
                formData.append("files", file);
            });

            const data = await brandApi.extractFullBrand(formData, token);
            
            console.log("📊 [SmartFill] Data received from API:", data);

            if (progressInterval) clearInterval(progressInterval);
            setProgress(100);
            setStage("¡Análisis completado!");
            setExtractedData(data);
            
            // Trigger preview immediately if handler exists
            if (onPreview) {
                onPreview(data);
                toast.success("Vista previa generada. Revisa los cambios antes de aplicar.");
            } else {
                toast.success("Datos extraídos exitosamente");
            }

        } catch (error: any) {
            if (progressInterval) clearInterval(progressInterval);
            console.error("[SmartFill] Error:", error);
            
            // Show more detailed error message
            const errorMessage = error?.message || "Error desconocido al procesar la información";
            toast.error(`Error: ${errorMessage}`);
            
            setStage("Error en el proceso");
            setProgress(0);
        } finally {
            setIsProcessing(false);
        }
    };

    const handleApply = () => {
        if (extractedData) {
            onSuccess(extractedData);
            
            // Clear preview mode if active
            if (onPreview) {
                onPreview(null);
            }
            
            setExtractedData(null); // Reset after apply
            // Clear sensitive inputs
            setFiles([]);
            setText("");
            setInstructions("");
            setProgress(0);
            setStage("");
            toast.success("Cambios aplicados exitosamente.");
        }
    };

    const getSummaryItems = (data: Partial<BrandSettings>) => {
        const items = [];
        if (data.identity?.brand_name) items.push({ label: "Identidad", value: data.identity.brand_name, icon: <CheckCircle2 className="w-4 h-4 text-green-500" /> });
        if (data.visuals?.primary_color) items.push({ label: "Visuals", value: "Paleta detectada", icon: <CheckCircle2 className="w-4 h-4 text-green-500" /> });
        if (data.strategy?.unique_value_proposition) items.push({ label: "Estrategia", value: "Propuesta de valor", icon: <CheckCircle2 className="w-4 h-4 text-green-500" /> });
        if (data.story?.origin_story) items.push({ label: "Historia", value: "Origen generado", icon: <CheckCircle2 className="w-4 h-4 text-green-500" /> });
        if (data.team?.length) items.push({ label: "Equipo", value: `${data.team.length} miembros`, icon: <CheckCircle2 className="w-4 h-4 text-green-500" /> });
        return items;
    };

    return (
        <Card className="w-full border-2 border-primary/10 shadow-lg bg-card/50 backdrop-blur-sm">
            <CardHeader className="space-y-1">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-2xl font-bold flex items-center gap-2">
                        <Wand2 className="w-6 h-6 text-primary" />
                        {mode === "initial" ? "Llenado Inteligente" : "Refinamiento de Marca"}
                    </CardTitle>
                    <Badge variant={mode === "initial" ? "default" : "secondary"}>
                        {mode === "initial" ? "Configuración Inicial" : "Actualización"}
                    </Badge>
                </div>
                <CardDescription>
                    {mode === "initial" 
                        ? "Acelera tu configuración analizando tu web y documentos. Web y Docs son complementarios."
                        : "Actualiza o mejora secciones específicas usando nueva información o instrucciones."
                    }
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                
                {/* Inputs Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Column 1: URL */}
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="url">Sitio Web (Opcional)</Label>
                            <div className="relative">
                                <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Input 
                                    id="url"
                                    placeholder="https://tumarca.com" 
                                    className="pl-9"
                                    value={url}
                                    onChange={(e) => setUrl(e.target.value)}
                                    disabled={isProcessing}
                                />
                            </div>
                            <p className="text-xs text-muted-foreground">Analizaremos también páginas de 'Nosotros', 'Equipo', etc.</p>
                        </div>

                        {mode === "update" && (
                             <div className="space-y-2">
                                <Label htmlFor="instructions">Instrucciones de Actualización</Label>
                                <Textarea 
                                    id="instructions"
                                    placeholder="Ej: Actualiza solo la historia y mantén los colores actuales..."
                                    className="min-h-[100px]"
                                    value={instructions}
                                    onChange={(e) => setInstructions(e.target.value)}
                                    disabled={isProcessing}
                                />
                            </div>
                        )}
                    </div>

                    {/* Column 2: Context/Docs */}
                    <div className="space-y-2">
                        <Label htmlFor="context">Documentos / Contexto Adicional (Opcional)</Label>
                        <div className="space-y-3">
                            {/* Text Area */}
                            <div className="relative">
                                <FileText className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                <Textarea 
                                    id="context"
                                    placeholder="Pega texto aquí o sube archivos..."
                                    className="pl-9 min-h-[100px]"
                                    value={text}
                                    onChange={(e) => setText(e.target.value)}
                                    disabled={isProcessing}
                                />
                            </div>
                            
                            {/* File Upload Area */}
                            <div className="border-2 border-dashed rounded-lg p-4 hover:bg-muted/50 transition-colors text-center relative group">
                                <input 
                                    type="file" 
                                    multiple 
                                    accept=".pdf,.docx,.txt,.md"
                                    className="absolute inset-0 opacity-0 cursor-pointer disabled:cursor-not-allowed z-10"
                                    disabled={isProcessing}
                                    onChange={(e) => {
                                        if (e.target.files) {
                                            setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
                                        }
                                        // Reset input value to allow re-uploading same file if deleted
                                        e.target.value = "";
                                    }}
                                />
                                <div className="flex flex-col items-center gap-1 text-sm text-muted-foreground group-hover:text-foreground transition-colors">
                                    <UploadCloud className="h-8 w-8 text-muted-foreground/50 group-hover:text-primary/50" />
                                    <p><span className="font-medium text-foreground">Click para subir</span> o arrastra archivos</p>
                                    <p className="text-xs">PDF, DOCX, TXT (Máx 10MB)</p>
                                </div>
                            </div>

                            {/* File List */}
                            {files.length > 0 && (
                                <div className="space-y-2 max-h-[150px] overflow-y-auto pr-1">
                                    {files.map((file, idx) => (
                                        <div key={idx} className="flex items-center justify-between p-2 bg-secondary/50 rounded-md text-sm border border-border/50">
                                            <div className="flex items-center gap-2 overflow-hidden">
                                                <FileIcon className="h-4 w-4 flex-shrink-0 text-blue-500" />
                                                <span className="truncate max-w-[180px]" title={file.name}>{file.name}</span>
                                                <span className="text-xs text-muted-foreground">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-6 w-6 hover:text-destructive"
                                                onClick={() => setFiles(prev => prev.filter((_, i) => i !== idx))}
                                                disabled={isProcessing}
                                            >
                                                <X className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Warnings */}
                {(!extractedData && !isProcessing) && (
                    <Alert className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
                        <Info className="h-4 w-4 text-blue-600 dark:text-blue-500" />
                        <AlertTitle className="text-blue-800 dark:text-blue-400">Información Sensible</AlertTitle>
                        <AlertDescription className="text-blue-700 dark:text-blue-300 text-xs">
                            Datos legales (RUC, Representante) y fiscales deben ser verificados manualmente por seguridad.
                        </AlertDescription>
                    </Alert>
                )}

                {/* Action Button */}
                {!extractedData && (
                    <div className="flex justify-end">
                         <Button 
                            onClick={handleExtract} 
                            disabled={isProcessing || (!url && !text && !instructions && files.length === 0)}
                            className="min-w-[150px]"
                            size="lg"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Procesando...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="mr-2 h-4 w-4" />
                                    {mode === "initial" ? "Analizar y Llenar" : "Refinar Información"}
                                </>
                            )}
                        </Button>
                    </div>
                )}

                {/* Progress Section */}
                {(isProcessing || progress > 0) && !extractedData && (
                    <div className="space-y-2 animate-in fade-in slide-in-from-top-4 duration-500 bg-secondary/20 p-4 rounded-lg">
                        <div className="flex justify-between text-sm font-medium">
                            <span>{stage}</span>
                            <span>{Math.round(progress)}%</span>
                        </div>
                        <Progress value={progress} className="h-2" />
                        <p className="text-xs text-muted-foreground text-center pt-2">
                            Esto puede tomar unos segundos. Estamos analizando tu información...
                        </p>
                    </div>
                )}

                {/* Results Section (Summary) */}
                {extractedData && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center justify-between border-b pb-4">
                            <h3 className="text-lg font-semibold text-green-600 flex items-center gap-2">
                                <CheckCircle2 className="w-5 h-5" /> Análisis Exitoso
                            </h3>
                            <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">Listo para aplicar</Badge>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {getSummaryItems(extractedData).map((item, i) => (
                                <div key={i} className="flex items-start p-3 bg-secondary/50 rounded-lg border border-border/50">
                                    <div className="mr-3 mt-1 p-1 bg-background rounded-full shadow-sm">
                                        {item.icon}
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-foreground">{item.label}</p>
                                        <p className="text-xs text-muted-foreground line-clamp-2">{item.value}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        
                        <Alert className="bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800">
                            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-500" />
                            <AlertTitle className="text-amber-800 dark:text-amber-400">Revisión Requerida</AlertTitle>
                            <AlertDescription className="text-amber-700 dark:text-amber-300 text-xs">
                                Hemos llenado los campos con la mejor información disponible. Por favor revisa cada sección para asegurar la precisión.
                            </AlertDescription>
                        </Alert>
                    </div>
                )}
            </CardContent>
            
            {extractedData && (
                <CardFooter className="flex justify-end gap-3 bg-secondary/10 pt-6 rounded-b-lg">
                    <Button variant="ghost" onClick={() => setExtractedData(null)}>
                        Cancelar
                    </Button>
                    <Button onClick={handleApply} className="bg-green-600 hover:bg-green-700 text-white shadow-md">
                        Aplicar Cambios <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                </CardFooter>
            )}
        </Card>
    );
}
