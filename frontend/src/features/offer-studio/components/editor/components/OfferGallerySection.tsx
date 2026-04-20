"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Image as ImageIcon, Loader2, Trash2, Plus, Sparkles } from "lucide-react";
import NextImage from "next/image";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { offerGalleryApi } from "@/lib/api/offer-gallery";
import { getAssetUrl } from "@/lib/utils/assets";

interface OfferGallerySectionProps {
  offerId: string;
}

/**
 *
 */
export function OfferGallerySection({ offerId }: OfferGallerySectionProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");

  const { data: images, isLoading } = useQuery({
    queryKey: ["offer-gallery", offerId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Auth required");
      return offerGalleryApi.list(token, offerId);
    },
    enabled: !!offerId && offerId !== "undefined",
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !file) return;
      return offerGalleryApi.upload(token, offerId, file, description);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offer-gallery", offerId] });
      setIsUploadOpen(false);
      setFile(null);
      setDescription("");
      toast.success("Imagen subida correctamente");
    },
    onError: () => toast.error("Error al subir imagen"),
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) return;
      return offerGalleryApi.delete(token, offerId, id);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["offer-gallery", offerId] });
      toast.success("Imagen eliminada");
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  if (isLoading) {
    return (
      <section className="space-y-6 py-4">
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

  return (
    <section className="space-y-6 py-4">
      <div className="flex items-center justify-between px-1">
        <h3 className="text-base font-semibold text-foreground flex items-center gap-2">
          <ImageIcon className="h-4 w-4 text-primary" />
          Galería Visual de Oferta
        </h3>

        <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
          <DialogTrigger asChild>
            <Button size="sm" variant="outline">
              <Plus className="h-3.5 w-3.5 mr-2" />
              Agregar Imagen
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Subir Imagen Referencial</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Seleccionar Imagen</label>
                <Input type="file" accept="image/*" onChange={handleFileChange} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Descripción de Uso (Opcional)</label>
                <Textarea
                  placeholder="Ej: Foto para el header de la landing page..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Describe para qué sirve esta imagen en el contexto de la oferta.
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
                ) : (
                  "Subir y Analizar"
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {!images || images.length === 0 ? (
        <div className="text-center py-8 bg-muted/20 rounded-xl border border-dashed border-border">
          <ImageIcon className="h-8 w-8 mx-auto text-muted-foreground mb-2 opacity-20" />
          <p className="text-sm text-muted-foreground mb-1">No hay imágenes referenciales.</p>
          <p className="text-xs text-muted-foreground">
            Sube assets para usar en landings y anuncios.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {images.map((img) => (
            <div
              key={img.id}
              className="group relative bg-card rounded-xl border border-border overflow-hidden shadow-sm hover:shadow-md transition-all"
            >
              <div className="relative aspect-video w-full bg-muted">
                <NextImage
                  src={getAssetUrl(img.public_url)}
                  alt="Offer Gallery Image"
                  width={400}
                  height={300}
                  className="object-cover w-full h-full"
                  unoptimized
                />
                <div className="absolute top-2 right-2 flex gap-2">
                  {img.status === "processing" ? (
                    <Badge
                      variant="secondary"
                      className="bg-yellow-100 text-yellow-800 border-yellow-200 text-[10px]"
                    >
                      <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                      Analizando...
                    </Badge>
                  ) : img.status === "failed" ? (
                    <Badge variant="destructive" className="text-[10px]">
                      Error
                    </Badge>
                  ) : (
                    <Badge
                      variant="secondary"
                      className="bg-green-100 text-green-800 border-green-200 backdrop-blur-sm text-[10px]"
                    >
                      <Sparkles className="h-3 w-3 mr-1" />
                      IA Ready
                    </Badge>
                  )}
                </div>
                <button
                  className="absolute bottom-2 right-2 p-1.5 bg-background/80 hover:bg-destructive/90 hover:text-white text-muted-foreground rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => deleteMutation.mutate(img.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>

              <div className="p-3 space-y-2">
                {img.user_description && (
                  <div>
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                      Uso
                    </p>
                    <p className="text-xs text-foreground line-clamp-2">{img.user_description}</p>
                  </div>
                )}

                {img.ai_description && (
                  <div className="bg-primary/5 p-2 rounded border border-primary/10">
                    <p className="text-[10px] font-semibold text-primary mb-0.5 flex items-center">
                      <Sparkles className="h-3 w-3 mr-1" />
                      Análisis IA
                    </p>
                    <p className="text-[10px] text-muted-foreground line-clamp-2 italic leading-tight">
                      &quot;{img.ai_description}&quot;
                    </p>

                    {img.ai_colors && img.ai_colors.length > 0 && (
                      <div className="flex gap-1 mt-1.5">
                        {img.ai_colors.map((color, idx) => (
                          <div
                            key={idx}
                            className="w-3 h-3 rounded-full border border-border shadow-sm"
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
        </div>
      )}
    </section>
  );
}
