"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { galleryApi } from "@/lib/api/gallery";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Upload, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

interface SingleImagePickerProps {
    value?: string;
    onChange: (url: string) => void;
    children: React.ReactNode;
}

export function SingleImagePicker({ 
    value, 
    onChange, 
    children 
}: SingleImagePickerProps) {
    const { getToken } = useAuth();
    const queryClient = useQueryClient();
    const [isOpen, setIsOpen] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [uploadDesc, setUploadDesc] = useState("");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
        enabled: isOpen
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
            // Optionally switch tab, but keeping it simple for now
        },
        onError: () => toast.error("Error al subir imagen")
    });

    const handleSelect = (url: string) => {
        onChange(url);
        setIsOpen(false);
    };

    const getFullUrl = (path: string) => {
        if (!path) return "";
        if (path.startsWith("http")) return path;
        return `${apiUrl}${path}`;
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                {children}
            </DialogTrigger>
            <DialogContent className="max-w-3xl h-[80vh] flex flex-col p-0 gap-0">
                <DialogHeader className="p-6 pb-2">
                    <DialogTitle>Seleccionar Logo</DialogTitle>
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
                                Subir Nuevo
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
                                        No hay imágenes. Sube una primero.
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
                                                <img src={fullUrl} alt="Gallery" className="w-full h-full object-contain p-2 bg-muted/20" />
                                                
                                                {isSelected && (
                                                    <div className="absolute top-1 right-1 bg-primary text-primary-foreground p-0.5 rounded-full shadow-sm">
                                                        <Check className="h-3 w-3" />
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
                                        <p className="font-medium">Arrastra tu logo aquí</p>
                                        <Input 
                                            type="file" 
                                            accept="image/*" 
                                            className="cursor-pointer"
                                            onChange={(e) => e.target.files && setUploadFile(e.target.files[0])}
                                        />
                                    </div>
                                </div>
                            </div>

                            {uploadFile && (
                                <div className="space-y-4 bg-muted/30 p-4 rounded-lg border">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded bg-muted overflow-hidden">
                                             {/* eslint-disable-next-line @next/next/no-img-element */}
                                            <img src={URL.createObjectURL(uploadFile)} alt="Preview" className="h-full w-full object-contain" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium truncate">{uploadFile.name}</p>
                                        </div>
                                    </div>
                                    
                                    <Button 
                                        className="w-full" 
                                        onClick={() => uploadMutation.mutate()} 
                                        disabled={uploadMutation.isPending}
                                    >
                                        {uploadMutation.isPending ? "Subiendo..." : "Subir a Galería"}
                                    </Button>
                                </div>
                            )}
                        </div>
                    </TabsContent>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
