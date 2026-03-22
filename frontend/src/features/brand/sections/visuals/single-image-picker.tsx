"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { assetsApi } from "@/lib/api/assets";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Image as ImageIcon, Loader2, Upload, Check, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { config } from "@/lib/config";

interface SingleImagePickerProps {
    value?: string;
    onChange: (url: string) => void;
    children: React.ReactNode;
}

export function SingleImagePicker({ value, onChange, children }: SingleImagePickerProps) {
    const { getToken } = useAuth();
    const queryClient = useQueryClient();
    const [isPickerOpen, setIsPickerOpen] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadDesc, setUploadDesc] = useState("");
    const API_URL = config.api.baseUrl;

    const { data: galleryImages, isLoading } = useQuery({
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
        },
        enabled: isPickerOpen
    });

    const uploadMutation = useMutation({
        mutationFn: async () => {
            const token = await getToken();
            if (!token || !uploadFile) return null;
            return assetsApi.upload(token, uploadFile, uploadDesc);
        },
        onSuccess: (data) => {
            console.log("[SingleImagePicker] Upload success, data:", data);
            queryClient.invalidateQueries({ queryKey: ["assets"] });
            setUploadFile(null);
            setUploadDesc("");
            if (data?.public_url) {
                console.log("[SingleImagePicker] Calling handleSelect with:", data.public_url);
                handleSelect(data.public_url);
                toast.success("Imagen subida y seleccionada");
            } else {
                console.warn("[SingleImagePicker] No public_url in upload response!", data);
                toast.success("Imagen subida a la galería");
            }
        },
        onError: () => toast.error("Error al subir imagen")
    });

    const handleSelect = (url: string) => {
        onChange(url);
        setIsPickerOpen(false);
    };

    const getFullUrl = (path: string) => {
        if (!path) return "";
        if (path.startsWith("http")) return path;
        return `${API_URL}${path}`;
    };

    return (
        <>
            <div onClick={() => setIsPickerOpen(true)}>
                {children}
            </div>

            <Dialog open={isPickerOpen} onOpenChange={setIsPickerOpen}>
                <DialogContent className="max-w-3xl h-[80vh] flex flex-col p-0 gap-0">
                    <DialogHeader className="p-6 pb-2">
                        <DialogTitle>Seleccionar Imagen</DialogTitle>
                    </DialogHeader>
                    
                    <Tabs defaultValue="gallery" className="flex-1 flex flex-col min-h-0">
                        <div className="px-6 border-b">
                            <TabsList className="w-full justify-start rounded-none border-b bg-transparent p-0 h-auto">
                                <TabsTrigger 
                                    value="gallery"
                                    className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent px-4 py-2"
                                >
                                    Galería
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
                                            const isSelected = value === img.public_url;
                                            const fullUrl = getFullUrl(img.public_url);

                                            return (
                                                <div 
                                                    key={img.id}
                                                    className={cn(
                                                        "group relative aspect-square rounded-md border cursor-pointer overflow-hidden transition-all",
                                                        isSelected ? "ring-2 ring-primary border-primary" : "hover:border-primary/50"
                                                    )}
                                                    onClick={() => handleSelect(img.public_url)}
                                                >
                                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                                    <img src={fullUrl} alt="Gallery" className="w-full h-full object-cover" />
                                                    
                                                    {isSelected && (
                                                        <div className="absolute top-1 right-1 bg-primary text-primary-foreground p-0.5 rounded-full shadow-sm">
                                                            <Check className="h-3 w-3" />
                                                        </div>
                                                    )}

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
                                                placeholder="Ej: Logo principal..." 
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
        </>
    );
}

function Skeleton({ className }: { className?: string }) {
    return <div className={cn("animate-pulse rounded-md bg-muted", className)} />;
}
