"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { galleryApi, GalleryImage } from "@/lib/api/gallery";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Image as ImageIcon, Loader2, Plus, Star, Check, Trash2, Sparkles, Upload } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface ImageGalleryPickerProps {
    images: string[]; // List of selected URLs (KeyFigure.gallery)
    primaryImage: string | undefined; // KeyFigure.headshot_url
    onImagesChange: (images: string[]) => void;
    onPrimaryChange: (url: string) => void;
    maxImages?: number;
}

export function ImageGalleryPicker({ 
    images = [], 
    primaryImage, 
    onImagesChange, 
    onPrimaryChange, 
    maxImages = 5 
}: ImageGalleryPickerProps) {
    const { getToken } = useAuth();
    const queryClient = useQueryClient();
    const [isPickerOpen, setIsPickerOpen] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadDesc, setUploadDesc] = useState("");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    // Ensure local state tracks props, but for selection inside dialog we might need temp state
    // For simplicity, we'll select directly into the props when confirming.
    const [tempSelected, setTempSelected] = useState<string[]>([]);

    const { data: galleryImages, isLoading } = useQuery({
        queryKey: ["gallery"],
        queryFn: async () => {
            const token = await getToken();
            if (!token) return [];
            try {
                return await galleryApi.list(token);
            } catch (e) {
                console.error(e);
                return [];
            }
        },
        enabled: isPickerOpen
    });

    const uploadMutation = useMutation({
        mutationFn: async () => {
            const token = await getToken();
            if (!token || !uploadFile) return;
            return galleryApi.upload(token, uploadFile, uploadDesc);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["gallery"] });
            setUploadFile(null);
            setUploadDesc("");
            toast.success("Imagen subida a la galería");
        },
        onError: () => toast.error("Error al subir imagen")
    });

    const handleOpenPicker = () => {
        setTempSelected([...images]);
        setIsPickerOpen(true);
    };

    const handleToggleSelect = (url: string) => {
        // If already selected, remove
        if (tempSelected.includes(url)) {
            setTempSelected(tempSelected.filter(u => u !== url));
            return;
        }
        
        // If not selected, check limit
        if (tempSelected.length >= maxImages) {
            toast.warning(`Máximo ${maxImages} imágenes permitidas`);
            return;
        }

        setTempSelected([...tempSelected, url]);
    };

    const handleConfirmSelection = () => {
        onImagesChange(tempSelected);
        // If primary image is no longer in selection, clear it or set first
        if (primaryImage && !tempSelected.includes(primaryImage)) {
            if (tempSelected.length > 0) {
                onPrimaryChange(tempSelected[0]);
            } else {
                onPrimaryChange("");
            }
        } else if (!primaryImage && tempSelected.length > 0) {
            onPrimaryChange(tempSelected[0]);
        }
        setIsPickerOpen(false);
    };

    const getFullUrl = (path: string) => {
        if (!path) return "";
        if (path.startsWith("http")) return path;
        return `${apiUrl}${path}`;
    };

    const handleRemoveImage = (url: string) => {
        const newImages = images.filter(img => img !== url);
        onImagesChange(newImages);
        if (primaryImage === url) {
            onPrimaryChange(newImages.length > 0 ? newImages[0] : "");
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Galería Personal ({images.length}/{maxImages})</label>
                <Button 
                    type="button" 
                    variant="outline" 
                    size="sm" 
                    onClick={handleOpenPicker}
                    className="h-8 gap-2"
                >
                    <Plus className="h-3 w-3" />
                    Gestionar Galería
                </Button>
            </div>

            {/* Selected Images Grid */}
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                {images.map((url, idx) => {
                    const isPrimary = url === primaryImage;
                    const fullUrl = getFullUrl(url);
                    
                    return (
                        <div 
                            key={idx} 
                            className={cn(
                                "group relative aspect-square rounded-lg border overflow-hidden cursor-pointer transition-all",
                                isPrimary ? "ring-2 ring-primary border-primary" : "hover:border-primary/50"
                            )}
                            onClick={() => onPrimaryChange(url)}
                        >
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img src={fullUrl} alt="Member photo" className="w-full h-full object-cover" />
                            
                            {/* Primary Indicator */}
                            {isPrimary && (
                                <div className="absolute top-1 right-1 bg-primary text-primary-foreground p-1 rounded-full shadow-sm z-10">
                                    <Star className="h-3 w-3 fill-current" />
                                </div>
                            )}

                            {/* Hover Actions */}
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                {!isPrimary && (
                                    <Button 
                                        size="icon" 
                                        variant="secondary" 
                                        className="h-7 w-7 rounded-full" 
                                        title="Hacer Principal"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onPrimaryChange(url);
                                        }}
                                    >
                                        <Star className="h-3 w-3" />
                                    </Button>
                                )}
                                <Button 
                                    size="icon" 
                                    variant="destructive" 
                                    className="h-7 w-7 rounded-full" 
                                    title="Quitar"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleRemoveImage(url);
                                    }}
                                >
                                    <Trash2 className="h-3 w-3" />
                                </Button>
                            </div>
                        </div>
                    );
                })}

                {/* Empty State / Add Placeholder */}
                {images.length === 0 && (
                    <div 
                        className="col-span-full flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-lg text-muted-foreground bg-muted/20 hover:bg-muted/40 cursor-pointer transition-colors"
                        onClick={handleOpenPicker}
                    >
                        <ImageIcon className="h-8 w-8 mb-2 opacity-50" />
                        <p className="text-xs text-center">Sin imágenes asociadas</p>
                        <p className="text-[10px] text-center opacity-70">Click para seleccionar</p>
                    </div>
                )}
            </div>

            {/* Picker Dialog */}
            <Dialog open={isPickerOpen} onOpenChange={setIsPickerOpen}>
                <DialogContent className="max-w-3xl h-[80vh] flex flex-col p-0 gap-0">
                    <DialogHeader className="p-6 pb-2">
                        <DialogTitle>Seleccionar Imágenes</DialogTitle>
                    </DialogHeader>
                    
                    <Tabs defaultValue="gallery" className="flex-1 flex flex-col min-h-0">
                        <div className="px-6 border-b">
                            <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0 h-auto">
                                <TabsTrigger 
                                    value="gallery"
                                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                                >
                                    Galería de Marca
                                </TabsTrigger>
                                <TabsTrigger 
                                    value="upload"
                                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                                >
                                    Subir Nueva
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        <TabsContent value="gallery" className="flex-1 min-h-0 p-0 m-0 relative">
                            <ScrollArea className="h-full">
                                <div className="p-6 grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-4">
                                    {isLoading ? (
                                        Array.from({ length: 10 }).map((_, i) => (
                                            <Skeleton key={i} className="aspect-square rounded-md" />
                                        ))
                                    ) : galleryImages?.length === 0 ? (
                                        <div className="col-span-full py-10 text-center text-muted-foreground">
                                            No hay imágenes en la galería. Sube una primero.
                                        </div>
                                    ) : (
                                        galleryImages?.map((img) => {
                                            const isSelected = tempSelected.includes(img.public_url);
                                            const fullUrl = getFullUrl(img.public_url);

                                            return (
                                                <div 
                                                    key={img.id}
                                                    className={cn(
                                                        "group relative aspect-square rounded-md border cursor-pointer overflow-hidden transition-all",
                                                        isSelected ? "ring-2 ring-primary border-primary" : "hover:border-primary/50"
                                                    )}
                                                    onClick={() => handleToggleSelect(img.public_url)}
                                                >
                                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                                    <img src={fullUrl} alt="Gallery" className="w-full h-full object-cover" />
                                                    
                                                    {isSelected && (
                                                        <div className="absolute top-1 right-1 bg-primary text-primary-foreground p-0.5 rounded-full shadow-sm">
                                                            <Check className="h-3 w-3" />
                                                        </div>
                                                    )}

                                                    {/* AI Badge Overlay */}
                                                    {img.ai_description && (
                                                        <div className="absolute bottom-0 left-0 right-0 bg-black/50 p-1">
                                                            <Sparkles className="h-3 w-3 text-yellow-300 mx-auto" />
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </ScrollArea>
                            {/* Selection Footer */}
                            <div className="absolute bottom-0 left-0 right-0 p-4 bg-background border-t flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">
                                    Seleccionadas: {tempSelected.length} / {maxImages}
                                </span>
                                <Button onClick={handleConfirmSelection}>
                                    Confirmar Selección
                                </Button>
                            </div>
                        </TabsContent>

                        <TabsContent value="upload" className="flex-1 p-6 m-0">
                            <div className="max-w-md mx-auto space-y-4 pt-10">
                                <div className="border-2 border-dashed rounded-lg p-10 text-center hover:bg-muted/50 transition-colors">
                                    <div className="flex flex-col items-center gap-4">
                                        <div className="p-4 bg-primary/10 rounded-full">
                                            <Upload className="h-8 w-8 text-primary" />
                                        </div>
                                        <div className="space-y-1">
                                            <p className="font-medium">Arrastra tu imagen aquí</p>
                                            <p className="text-sm text-muted-foreground">o haz click para seleccionar</p>
                                        </div>
                                        <Input 
                                            type="file" 
                                            accept="image/*" 
                                            className="cursor-pointer"
                                            onChange={(e) => e.target.files && setUploadFile(e.target.files[0])}
                                        />
                                    </div>
                                </div>

                                {uploadFile && (
                                    <div className="space-y-4 bg-muted/30 p-4 rounded-lg border">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded bg-muted overflow-hidden">
                                                 {/* eslint-disable-next-line @next/next/no-img-element */}
                                                <img src={URL.createObjectURL(uploadFile)} alt="Preview" className="h-full w-full object-cover" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{uploadFile.name}</p>
                                                <p className="text-xs text-muted-foreground">{(uploadFile.size / 1024).toFixed(1)} KB</p>
                                            </div>
                                        </div>
                                        
                                        <div className="space-y-2">
                                            <label className="text-xs font-medium">Descripción (Opcional)</label>
                                            <Textarea 
                                                placeholder="Ej: Retrato profesional de CEO..." 
                                                value={uploadDesc}
                                                onChange={(e) => setUploadDesc(e.target.value)}
                                                className="h-20 text-sm resize-none"
                                            />
                                        </div>

                                        <Button 
                                            className="w-full" 
                                            onClick={() => uploadMutation.mutate()} 
                                            disabled={uploadMutation.isPending}
                                        >
                                            {uploadMutation.isPending ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Subiendo...
                                                </>
                                            ) : "Subir a Galería"}
                                        </Button>
                                    </div>
                                )}
                            </div>
                        </TabsContent>
                    </Tabs>
                </DialogContent>
            </Dialog>
        </div>
    );
}
