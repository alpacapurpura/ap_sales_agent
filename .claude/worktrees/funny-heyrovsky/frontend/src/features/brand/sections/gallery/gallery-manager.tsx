"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { assetsApi, Asset } from "@/lib/api/assets";
import { getAssetUrl } from "@/lib/utils/assets";
import { BrandVisuals } from "@/features/brand/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Image as ImageIcon, Loader2, Trash2, Plus, Info, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";

interface GalleryManagerProps {
  visuals: BrandVisuals;
}

export function GalleryManager({ visuals }: GalleryManagerProps) {
    const { getToken } = useAuth();
    const queryClient = useQueryClient();
    const [isUploadOpen, setIsUploadOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState<Asset | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [description, setDescription] = useState("");


    const { data: images, isLoading } = useQuery({
        queryKey: ["assets"],
        queryFn: async () => {
            const token = await getToken();
            if (!token) return [];
            try {
                return await assetsApi.list(token);
            } catch (e) {
                console.error(e);
                return [];
            }
        }
    });

    const uploadMutation = useMutation({
        mutationFn: async () => {
            const token = await getToken();
            if (!token || !file) return;
            return assetsApi.upload(token, file, description);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["assets"] });
            setIsUploadOpen(false);
            setFile(null);
            setDescription("");
            toast.success("Imagen subida correctamente");
        },
        onError: () => toast.error("Error al subir imagen")
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            const token = await getToken();
            if (!token) return;
            return assetsApi.delete(token, id);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["assets"] });
            toast.success("Imagen eliminada");
        }
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    if (isLoading) {
        return (
            <section className="space-y-6 py-8" id="gallery-section">
                <div className="flex items-center justify-between px-2">
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-9 w-32" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Skeleton className="h-40" />
                    <Skeleton className="h-40" />
                </div>
            </section>
        );
    }
    
    const logoUrls = new Set(
        Object.values(visuals.logos || {})
            .filter((url): url is string => typeof url === 'string' && url.length > 0)
    );

    const filteredImages = images?.filter(img => !logoUrls.has(img.public_url)) || [];
    const hasContent = filteredImages.length > 0;

    return (
        <section 
            className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40"
            id="gallery-section"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors cursor-pointer" onClick={() => setIsUploadOpen(true)}>
                <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
                    <ImageIcon className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-semibold uppercase tracking-wider">Galería de Marca</h3>
            </div>
            
            <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Subir Imagen a Galería</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Seleccionar Imagen</label>
                            <Input 
                                type="file" 
                                accept="image/*" 
                                onChange={handleFileChange} 
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Descripción de Uso (Opcional)</label>
                            <Textarea 
                                placeholder="Ej: Foto del equipo para la sección Nosotros..." 
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                Ayuda a la IA a saber cuándo usar esta imagen.
                            </p>
                        </div>
                        <Button 
                            className="w-full" 
                            onClick={() => uploadMutation.mutate()} 
                            disabled={!file || uploadMutation.isPending}
                        >
                            {uploadMutation.isPending ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Subiendo...
                                </>
                            ) : "Subir y Analizar"}
                        </Button>
                    </div>
                </DialogContent>
            </Dialog>

            {!hasContent ? (
                <div className="pl-0 md:pl-14 cursor-pointer" onClick={() => setIsUploadOpen(true)}>
                    <p className="text-lg text-muted-foreground italic mb-2">
                        &quot;Una imagen vale más que mil palabras. Sube tus recursos visuales aquí.&quot;
                    </p>
                    <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                        <Plus className="w-4 h-4" />
                        Subir Imágenes
                    </span>
                </div>
            ) : (
                <div className="pl-0 md:pl-14">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredImages.map((img) => (
                            <div key={img.id} className="group/card relative bg-card rounded-xl border border-border overflow-hidden shadow-sm hover:shadow-md transition-all">
                                <div 
                                    className="relative aspect-video w-full bg-muted cursor-zoom-in"
                                    onClick={() => setSelectedImage(img)}
                                >
                                    <img 
                                        src={getAssetUrl(img.public_url)}
                                        alt="Gallery Image" 
                                        className="object-cover w-full h-full"
                                    />
                                    <div className="absolute top-2 right-2 flex gap-2">
                                        {img.status === "processing" ? (
                                            <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 border-yellow-200">
                                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                                IA Analizando...
                                            </Badge>
                                        ) : img.status === "failed" ? (
                                            <Badge variant="destructive">Error</Badge>
                                        ) : (
                                            <Badge variant="secondary" className="bg-green-100 text-green-800 border-green-200 backdrop-blur-sm">
                                                <Sparkles className="h-3 w-3 mr-1" />
                                                IA Ready
                                            </Badge>
                                        )}
                                    </div>
                                    <button 
                                        className="absolute bottom-2 right-2 p-1.5 bg-background/80 hover:bg-destructive/90 hover:text-white text-muted-foreground rounded-full opacity-0 group-hover/card:opacity-100 transition-opacity"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            deleteMutation.mutate(img.id);
                                        }}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </button>
                                </div>
                                
                                <div className="p-4 space-y-3">
                                    {img.user_description && (
                                        <div>
                                            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Uso</p>
                                            <p className="text-sm text-foreground line-clamp-2">{img.user_description}</p>
                                        </div>
                                    )}
                                    
                                    {img.ai_description && (
                                        <div className="bg-primary/5 p-3 rounded-lg border border-primary/10">
                                            <p className="text-xs font-semibold text-primary mb-1 flex items-center">
                                                <Sparkles className="h-3 w-3 mr-1" />
                                                Análisis IA
                                            </p>
                                            <p className="text-xs text-muted-foreground line-clamp-3 italic">
                                                &quot;{img.ai_description}&quot;
                                            </p>
                                            
                                            {img.ai_colors && img.ai_colors.length > 0 && (
                                                <div className="flex gap-1 mt-2">
                                                    {img.ai_colors.map((color, idx) => (
                                                        <div 
                                                            key={idx} 
                                                            className="w-4 h-4 rounded-full border border-border shadow-sm"
                                                            style={{ backgroundColor: color }}
                                                            title={color}
                                                        />
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        
                         {/* Add New Trigger (Visual) */}
                         <div className="flex flex-col items-center justify-center text-center group/add cursor-pointer min-h-[200px] border-2 border-dashed border-muted-foreground/20 rounded-lg hover:border-primary/50 hover:bg-primary/5 transition-colors" onClick={() => setIsUploadOpen(true)}>
                            <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3 group-hover/add:bg-primary/10 transition-colors">
                                <Plus className="w-5 h-5 text-muted-foreground group-hover/add:text-primary" />
                            </div>
                            <span className="text-sm font-medium text-muted-foreground group-hover/add:text-primary">Agregar Imagen</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Lightbox Dialog */}
            <Dialog open={!!selectedImage} onOpenChange={(open) => !open && setSelectedImage(null)}>
                <DialogContent className="max-w-4xl p-0 overflow-hidden bg-transparent border-none shadow-none flex items-center justify-center">
                    <VisuallyHidden>
                        <DialogTitle>Vista previa de imagen</DialogTitle>
                    </VisuallyHidden>
                    {selectedImage && (
                        <div className="relative">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img 
                                src={getAssetUrl(selectedImage.public_url)}
                                alt="Full size preview" 
                                className="w-full h-auto max-h-[85vh] rounded-md object-contain shadow-2xl"
                            />
                            {selectedImage.user_description && (
                                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white p-4 backdrop-blur-sm rounded-b-md">
                                    <p className="text-sm font-medium">{selectedImage.user_description}</p>
                                </div>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>
        </section>
    );
}
