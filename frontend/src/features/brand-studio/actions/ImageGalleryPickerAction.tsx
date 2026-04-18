"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Image as ImageIcon, Loader2, Plus, Sparkles, Trash2, Upload } from "lucide-react";
import NextImage from "next/image";
import { useCallback, useMemo, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { assetsApi } from "@/lib/api/assets";
import { config } from "@/lib/config";
import { cn } from "@/lib/utils";

import type { ActionComponentProps } from "@/lib/form-runtime/actions";

const ASSETS_QUERY_KEY = ["assets"] as const;
const DEFAULT_MAX_IMAGES = 5;
const EMPTY_IMAGES: string[] = [];

interface ImageGalleryProps {
  value: string[] | null | undefined;
  onChange: (next: string[]) => void;
  maxImages?: number;
}

function isHttpUrl(path: string): boolean {
  return path.startsWith("http://") || path.startsWith("https://");
}

function buildFullUrl(path: string | undefined, baseUrl: string): string {
  if (!path) return "";
  return isHttpUrl(path) ? path : `${baseUrl}${path}`;
}

interface SelectedTileProps {
  url: string;
  fullUrl: string;
  onRemove: (url: string) => void;
}

function SelectedTile({ url, fullUrl, onRemove }: SelectedTileProps) {
  const onClick = useCallback(() => onRemove(url), [onRemove, url]);
  return (
    <div className="group relative aspect-square overflow-hidden rounded-lg border">
      <NextImage
        src={fullUrl}
        alt="Imagen seleccionada"
        fill
        className="object-cover"
        unoptimized
      />
      <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100">
        <Button
          type="button"
          size="icon"
          variant="destructive"
          className="h-7 w-7 rounded-full"
          onClick={onClick}
          aria-label="Quitar"
        >
          <Trash2 className="h-3 w-3" aria-hidden />
        </Button>
      </div>
    </div>
  );
}

interface GalleryTileProps {
  url: string;
  fullUrl: string;
  isSelected: boolean;
  hasAi: boolean;
  onToggle: (url: string) => void;
}

function GalleryTile({ url, fullUrl, isSelected, hasAi, onToggle }: GalleryTileProps) {
  const onClick = useCallback(() => onToggle(url), [onToggle, url]);
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isSelected}
      className={cn(
        "group relative aspect-square cursor-pointer overflow-hidden rounded-md border transition-all",
        isSelected ? "border-primary ring-2 ring-primary" : "hover:border-primary/50",
      )}
    >
      <NextImage src={fullUrl} alt="Miniatura" fill className="object-cover" unoptimized />
      {isSelected && (
        <div className="absolute right-1 top-1 rounded-full bg-primary p-0.5 text-primary-foreground shadow-sm">
          <Check className="h-3 w-3" aria-hidden />
        </div>
      )}
      {hasAi && (
        <div className="absolute bottom-0 left-0 right-0 bg-black/50 p-1" aria-hidden>
          <Sparkles className="mx-auto h-3 w-3 text-yellow-300" />
        </div>
      )}
    </button>
  );
}

interface UploadPreviewProps {
  file: File;
  description: string;
  isUploading: boolean;
  onDescriptionChange: (value: string) => void;
  onUpload: () => void;
}

function UploadPreview({
  file,
  description,
  isUploading,
  onDescriptionChange,
  onUpload,
}: UploadPreviewProps) {
  const onDescChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => onDescriptionChange(e.target.value),
    [onDescriptionChange],
  );

  return (
    <div className="space-y-4 rounded-lg border bg-muted/30 p-4">
      <div className="flex items-center gap-3">
        <div className="relative h-10 w-10 overflow-hidden rounded bg-muted">
          <NextImage
            src={URL.createObjectURL(file)}
            alt="Preview"
            fill
            className="object-cover"
            unoptimized
          />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{file.name}</p>
          <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
        </div>
      </div>
      <div className="space-y-2">
        <label htmlFor="gallery-upload-desc" className="text-xs font-medium">
          Descripción (opcional)
        </label>
        <Textarea
          id="gallery-upload-desc"
          placeholder="Ej: Retrato profesional…"
          value={description}
          onChange={onDescChange}
          className="h-20 resize-none text-sm"
        />
      </div>
      <Button className="w-full" onClick={onUpload} disabled={isUploading}>
        {isUploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
            Subiendo…
          </>
        ) : (
          "Subir a galería"
        )}
      </Button>
    </div>
  );
}

/**
 * ImageGalleryPicker action — multi-select picker. The user opens the
 * dialog, toggles images from the shared asset gallery, confirms, and the
 * action emits the new URL array via onChange. Also supports uploading
 * new assets from within the dialog (reinvalidates the assets query).
 *
 * Maximum images enforced at `maxImages` (default 5); exceeding it shows a
 * warning toast and rejects the toggle.
 */
export function ImageGalleryPickerAction({
  value,
  onChange,
}: ActionComponentProps<string[] | null>) {
  return <ImageGalleryPicker value={value} onChange={onChange} />;
}

function ImageGalleryPicker({
  value,
  onChange,
  maxImages = DEFAULT_MAX_IMAGES,
}: ImageGalleryProps) {
  const selected = useMemo(() => value ?? EMPTY_IMAGES, [value]);
  const apiBaseUrl = config.api.baseUrl;

  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const [tempSelected, setTempSelected] = useState<string[]>(selected);

  const openPicker = useCallback(() => {
    setTempSelected(selected);
    setIsPickerOpen(true);
  }, [selected]);

  const handleRemove = useCallback(
    (url: string) => {
      onChange(selected.filter((u) => u !== url));
    },
    [selected, onChange],
  );

  const handleToggle = useCallback(
    (url: string) => {
      setTempSelected((prev) => {
        if (prev.includes(url)) return prev.filter((u) => u !== url);
        if (prev.length >= maxImages) {
          toast.warning(`Máximo ${maxImages} imágenes permitidas`);
          return prev;
        }
        return [...prev, url];
      });
    },
    [maxImages],
  );

  const handleConfirm = useCallback(() => {
    onChange(tempSelected);
    setIsPickerOpen(false);
  }, [tempSelected, onChange]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          Galería ({selected.length}/{maxImages})
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={openPicker}
          className="h-8 gap-2"
        >
          <Plus className="h-3 w-3" aria-hidden />
          Gestionar galería
        </Button>
      </div>

      {selected.length === 0 ? (
        <button
          type="button"
          onClick={openPicker}
          className="flex w-full flex-col items-center justify-center rounded-lg border-2 border-dashed bg-muted/20 p-6 text-muted-foreground transition-colors hover:bg-muted/40"
        >
          <ImageIcon className="mb-2 h-8 w-8 opacity-50" aria-hidden />
          <p className="text-xs">Sin imágenes asociadas</p>
          <p className="text-[10px] opacity-70">Click para seleccionar</p>
        </button>
      ) : (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
          {selected.map((url) => (
            <SelectedTile
              key={url}
              url={url}
              fullUrl={buildFullUrl(url, apiBaseUrl)}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}

      <PickerDialog
        open={isPickerOpen}
        onOpenChange={setIsPickerOpen}
        tempSelected={tempSelected}
        onToggle={handleToggle}
        onConfirm={handleConfirm}
        maxImages={maxImages}
      />
    </div>
  );
}

interface PickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tempSelected: string[];
  onToggle: (url: string) => void;
  onConfirm: () => void;
  maxImages: number;
}

function PickerDialog({
  open,
  onOpenChange,
  tempSelected,
  onToggle,
  onConfirm,
  maxImages,
}: PickerDialogProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDesc, setUploadDesc] = useState("");
  const apiBaseUrl = config.api.baseUrl;

  const { data: galleryImages, isLoading } = useQuery({
    queryKey: ASSETS_QUERY_KEY,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      try {
        return await assetsApi.list(token);
      } catch (err) {
        console.warn("assets list failed", err);
        return [];
      }
    },
    enabled: open,
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !uploadFile) return null;
      return assetsApi.upload(token, uploadFile, uploadDesc);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ASSETS_QUERY_KEY });
      setUploadFile(null);
      setUploadDesc("");
      toast.success("Imagen subida a la galería");
    },
    onError: () => toast.error("Error al subir imagen"),
  });

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setUploadFile(e.target.files[0]);
  }, []);

  const handleUploadClick = useCallback(() => {
    uploadMutation.mutate();
  }, [uploadMutation]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-w-3xl flex-col gap-0 p-0">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>Seleccionar imágenes</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="gallery" className="flex min-h-0 flex-1 flex-col">
          <div className="border-b px-6">
            <TabsList className="h-auto w-full justify-start rounded-none border-b bg-transparent p-0">
              <TabsTrigger
                value="gallery"
                className="rounded-none border-b-2 border-transparent px-4 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Galería de marca
              </TabsTrigger>
              <TabsTrigger
                value="upload"
                className="rounded-none border-b-2 border-transparent px-4 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Subir nueva
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="gallery" className="relative m-0 min-h-0 flex-1 p-0">
            <ScrollArea className="h-full">
              <div className="grid grid-cols-3 gap-4 p-6 sm:grid-cols-4 md:grid-cols-5">
                {isLoading ? (
                  Array.from({ length: 10 }).map((_, i) => (
                    <div key={i} className="aspect-square animate-pulse rounded-md bg-muted" />
                  ))
                ) : !galleryImages || galleryImages.length === 0 ? (
                  <div className="col-span-full py-10 text-center text-muted-foreground">
                    No hay imágenes en la galería. Subí una primero.
                  </div>
                ) : (
                  galleryImages.map((img) => (
                    <GalleryTile
                      key={img.id}
                      url={img.public_url}
                      fullUrl={buildFullUrl(img.public_url, apiBaseUrl)}
                      isSelected={tempSelected.includes(img.public_url)}
                      hasAi={Boolean(img.ai_description)}
                      onToggle={onToggle}
                    />
                  ))
                )}
              </div>
            </ScrollArea>
            <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between border-t bg-background p-4">
              <span className="text-sm text-muted-foreground">
                Seleccionadas: {tempSelected.length} / {maxImages}
              </span>
              <Button onClick={onConfirm}>Confirmar selección</Button>
            </div>
          </TabsContent>

          <TabsContent value="upload" className="m-0 flex-1 p-6">
            <div className="mx-auto max-w-md space-y-4 pt-10">
              <div className="rounded-lg border-2 border-dashed p-10 text-center transition-colors hover:bg-muted/50">
                <div className="flex flex-col items-center gap-4">
                  <div className="rounded-full bg-primary/10 p-4">
                    <Upload className="h-8 w-8 text-primary" aria-hidden />
                  </div>
                  <div className="space-y-1">
                    <p className="font-medium">Arrastrá tu imagen aquí</p>
                    <p className="text-sm text-muted-foreground">o hacé click para seleccionar</p>
                  </div>
                  <Input
                    type="file"
                    accept="image/*"
                    className="cursor-pointer"
                    onChange={onFileChange}
                  />
                </div>
              </div>

              {uploadFile && (
                <UploadPreview
                  file={uploadFile}
                  description={uploadDesc}
                  isUploading={uploadMutation.isPending}
                  onDescriptionChange={setUploadDesc}
                  onUpload={handleUploadClick}
                />
              )}
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
