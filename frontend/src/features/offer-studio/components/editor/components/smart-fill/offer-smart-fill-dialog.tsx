"use client";

import { useState, useRef, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
    AlertTriangle, Wand2, Globe, UploadCloud, File as FileIcon, X, Sparkles,
} from "lucide-react";
import { offerApi } from "@/features/offer-studio/api";
import { toast } from "sonner";

interface OfferSmartFillDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    offerId: string;
    onSuccess: () => void;
}

export function OfferSmartFillDialog({
    open,
    onOpenChange,
    offerId,
    onSuccess,
}: OfferSmartFillDialogProps) {
    const { getToken } = useAuth();

    // Form State
    const [sourceType, setSourceType] = useState<"web" | "manual">("web");
    const [url, setUrl] = useState("");
    const [text, setText] = useState("");
    const [instructions, setInstructions] = useState("");
    const [files, setFiles] = useState<File[]>([]);

    // Process State
    const [isProcessing, setIsProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [stage, setStage] = useState<string>("");
    const [errorState, setErrorState] = useState<{ type: "generic"; message: string } | null>(null);
    const activeJobRef = useRef<string | null>(null);
    const pollTimerRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        return () => {
            activeJobRef.current = null;
            if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
        };
    }, []);

    const resetForm = () => {
        setErrorState(null);
        setProgress(0);
        setStage("");
        setIsProcessing(false);
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

        try {
            const token = await getToken();
            if (!token) {
                toast.error("No autenticado");
                return;
            }

            setIsProcessing(true);
            setErrorState(null);
            setProgress(0);
            setStage("Iniciando análisis de oferta...");

            const formData = new FormData();
            formData.append("mode", "initial");

            if (sourceType === "web") {
                formData.append("url", url);
            } else {
                if (text) formData.append("text", text);
                files.forEach(file => formData.append("files", file));
            }

            if (instructions) formData.append("update_instructions", instructions);

            const { job_id } = await offerApi.extractFullOffer(offerId, formData, token);
            activeJobRef.current = job_id;

            const poll = async () => {
                if (activeJobRef.current !== job_id) return;

                try {
                    const freshToken = await getToken();
                    if (!freshToken) {
                        pollTimerRef.current = setTimeout(poll, 3000);
                        return;
                    }
                    const status = await offerApi.pollOfferExtractionStatus(job_id, freshToken);
                    if (activeJobRef.current !== job_id) return;

                    setProgress(status.progress);
                    if (status.stage) setStage(status.stage);

                    if (status.status === "completed") {
                        toast.success("¡Oferta completada con IA exitosamente!");
                        setTimeout(() => {
                            resetForm();
                            onOpenChange(false);
                            onSuccess();
                        }, 800);
                        return;
                    }

                    if (status.status === "failed") {
                        setErrorState({
                            type: "generic",
                            message: status.error || "Error desconocido en la extracción",
                        });
                        setStage("Proceso interrumpido");
                        setProgress(0);
                        setIsProcessing(false);
                        return;
                    }
                } catch (err) {
                    console.warn("[OfferSmartFill] Poll error, retrying:", err);
                }

                pollTimerRef.current = setTimeout(poll, 3000);
            };

            pollTimerRef.current = setTimeout(poll, 1000);
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : "Error al iniciar la extracción";
            console.error("[OfferSmartFill] Error starting extraction:", error);
            setErrorState({
                type: "generic",
                message,
            });
            setStage("Proceso interrumpido");
            setProgress(0);
            setIsProcessing(false);
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
                <div className="bg-gradient-to-r from-primary/10 to-primary/5 p-6 border-b">
                    <DialogHeader>
                        <DialogTitle className="text-2xl flex items-center gap-2">
                            <Wand2 className="w-6 h-6 text-primary" />
                            Completar oferta con IA
                        </DialogTitle>
                        <DialogDescription className="text-base">
                            Analiza tu producto desde web o documentos para completar automáticamente los campos de la oferta.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="p-6">
                    <div className="space-y-6">
                        {errorState && (
                            <Alert variant="destructive" className="animate-in shake">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertTitle>Error en el análisis</AlertTitle>
                                <AlertDescription className="mt-2 text-sm">
                                    {errorState.message}
                                </AlertDescription>
                                <div className="mt-4">
                                    <Button variant="outline" size="sm" onClick={() => setErrorState(null)} className="bg-background/50">
                                        Intentar de nuevo
                                    </Button>
                                </div>
                            </Alert>
                        )}

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
                                    <p className="text-sm text-muted-foreground">Esto puede tomar hasta 3 minutos...</p>
                                </div>
                            </div>
                        ) : (
                            !errorState && (
                                <Tabs value={sourceType} onValueChange={(v) => setSourceType(v as "web" | "manual")} className="w-full">
                                    <TabsList className="grid w-full grid-cols-2 mb-6">
                                        <TabsTrigger value="web">Desde Sitio Web</TabsTrigger>
                                        <TabsTrigger value="manual">Documentos / Texto</TabsTrigger>
                                    </TabsList>

                                    <TabsContent value="web" className="space-y-4 animate-in fade-in slide-in-from-left-2">
                                        <div className="space-y-2">
                                            <Label className="text-base font-semibold">URL de tu Producto u Oferta</Label>
                                            <div className="relative">
                                                <Globe className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                                                <Input
                                                    placeholder="https://tusitio.com/products/mi-producto"
                                                    className="pl-10 h-11 text-lg"
                                                    value={url}
                                                    onChange={(e) => setUrl(e.target.value)}
                                                />
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                Analizaremos la página del producto y páginas relacionadas para extraer la información de tu oferta.
                                            </p>
                                        </div>
                                    </TabsContent>

                                    <TabsContent value="manual" className="space-y-4 animate-in fade-in slide-in-from-right-2">
                                        <div className="space-y-2">
                                            <Label>Pega información sobre tu oferta</Label>
                                            <Textarea
                                                placeholder="Describe tu producto, beneficios, precio, garantía, entregables..."
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

                        {!isProcessing && !errorState && (
                            <div className="pt-4 border-t">
                                <Label>Instrucciones adicionales (Opcional)</Label>
                                <Input
                                    placeholder="Ej: Enfócate en los beneficios principales, el precio es $497 USD..."
                                    value={instructions}
                                    onChange={(e) => setInstructions(e.target.value)}
                                    className="mt-1.5"
                                />
                            </div>
                        )}
                    </div>
                </div>

                <DialogFooter className="p-6 bg-secondary/20 border-t gap-2 sm:gap-0">
                    {!isProcessing && (
                        <>
                            <Button variant="ghost" onClick={() => onOpenChange(false)}>Cancelar</Button>
                            <Button onClick={handleExtract} disabled={isProcessing} className="gap-2 min-w-[140px]">
                                <Sparkles className="w-4 h-4" />
                                Completar con IA
                            </Button>
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
