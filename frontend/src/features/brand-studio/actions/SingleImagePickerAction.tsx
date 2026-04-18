"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Image as ImageIcon, Loader2, Plus, Sparkles, Upload } from "lucide-react";
import NextImage from "next/image";
import { useCallback, useState, type ReactNode } from "react";
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

function isHttpUrl(path: string): boolean {
  return path.startsWith("http://") || path.startsWith("https://");
}

function buildFullUrl(path: string | undefined, baseUrl: string): string {
  if (!path) return "";
  return isHttpUrl(path) ? path : `${baseUrl}${path}`;
}

function GallerySkeleton({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="aspect-square animate-pulse rounded-md bg-muted" />
      ))}
    </>
  );
}

interface SingleImagePickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  value?: string;
  onSelect: (url: string) => void;
}

/**
 *
 */
export function SingleImagePickerDialog({
  open,
  onOpenChange,
  value,
  onSelect,
}: SingleImagePickerDialogProps) {
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

  const pick = useCallback(
    (url: string) => {
      onSelect(url);
      onOpenChange(false);
    },
    [onSelect, onOpenChange],
  );

  const uploadMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !uploadFile) return null;
      return assetsApi.upload(token, uploadFile, uploadDesc);
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ASSETS_QUERY_KEY });
      setUploadFile(null);
      setUploadDesc("");
      if (data?.public_url) {
        pick(data.public_url);
        toast.success("Imagen subida y seleccionada");
      } else {
        toast.success("Imagen subida a la galería");
      }
    },
    onError: () => toast.error("Error al subir imagen"),
  });

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) setUploadFile(e.target.files[0]);
  }, []);

  const onDescChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => setUploadDesc(e.target.value),
    [],
  );

  const handleUploadClick = useCallback(() => {
    uploadMutation.mutate();
  }, [uploadMutation]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] max-w-3xl flex-col gap-0 p-0">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>Seleccionar imagen</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="gallery" className="flex min-h-0 flex-1 flex-col">
          <div className="border-b px-6">
            <TabsList className="h-auto w-full justify-start rounded-none border-b bg-transparent p-0">
              <TabsTrigger
                value="gallery"
                className="rounded-none border-b-2 border-transparent px-4 py-2 data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                Galería
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
                  <GallerySkeleton count={10} />
                ) : !galleryImages || galleryImages.length === 0 ? (
                  <div className="col-span-full py-10 text-center text-muted-foreground">
                    No hay imágenes en la galería. Subí una primero.
                  </div>
                ) : (
                  galleryImages.map((img) => {
                    const isSelected = value === img.public_url;
                    return (
                      <GalleryTile
                        key={img.id}
                        url={img.public_url}
                        fullUrl={buildFullUrl(img.public_url, apiBaseUrl)}
                        isSelected={isSelected}
                        hasDescription={Boolean(img.ai_description)}
                        onPick={pick}
                      />
                    );
                  })
                )}
              </div>
            </ScrollArea>
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
                  onDescriptionChange={onDescChange}
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

interface GalleryTileProps {
  url: string;
  fullUrl: string;
  isSelected: boolean;
  hasDescription: boolean;
  onPick: (url: string) => void;
}

function GalleryTile({ url, fullUrl, isSelected, hasDescription, onPick }: GalleryTileProps) {
  const onClick = useCallback(() => onPick(url), [onPick, url]);
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
      <NextImage
        src={fullUrl || "/placeholder.svg"}
        alt="Miniatura"
        fill
        className="object-cover"
        unoptimized
      />
      {isSelected && (
        <div className="absolute right-1 top-1 rounded-full bg-primary p-0.5 text-primary-foreground shadow-sm">
          <Check className="h-3 w-3" />
        </div>
      )}
      {hasDescription && (
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
  onDescriptionChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onUpload: () => void;
}

function UploadPreview({
  file,
  description,
  isUploading,
  onDescriptionChange,
  onUpload,
}: UploadPreviewProps) {
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
        <label htmlFor="upload-desc" className="text-xs font-medium">
          Descripción (opcional)
        </label>
        <Textarea
          id="upload-desc"
          placeholder="Ej: Logo principal…"
          value={description}
          onChange={onDescriptionChange}
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

// ── Default trigger + public wrapper ─────────────────────────────────────────

interface SingleImagePickerProps {
  value?: string;
  onChange: (url: string) => void;
  /** Optional custom trigger. Defaults to an image-preview card. */
  children?: ReactNode;
  previewLabel?: string;
}

/**
 * Reusable wrapper: click the trigger → open the picker dialog → pick →
 * calls onChange and closes. Exposed publicly because `LogoKit` composes it
 * four times with custom triggers (one per logo variant).
 */
export function SingleImagePicker({
  value,
  onChange,
  children,
  previewLabel = "Seleccionar imagen",
}: SingleImagePickerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const open = useCallback(() => setIsOpen(true), []);
  const apiBaseUrl = config.api.baseUrl;
  const previewUrl = buildFullUrl(value, apiBaseUrl);

  return (
    <>
      <button
        type="button"
        onClick={open}
        aria-label={previewLabel}
        className="block w-full cursor-pointer border-0 bg-transparent p-0 text-left"
      >
        {children ?? <DefaultTrigger previewUrl={previewUrl} label={previewLabel} />}
      </button>
      <SingleImagePickerDialog
        open={isOpen}
        onOpenChange={setIsOpen}
        value={value}
        onSelect={onChange}
      />
    </>
  );
}

function DefaultTrigger({ previewUrl, label }: { previewUrl: string; label: string }) {
  return (
    <div className="relative flex aspect-video w-full items-center justify-center overflow-hidden rounded-md border-2 border-dashed border-muted-foreground/20 bg-muted/40 transition-colors group-hover:border-primary/50 hover:border-primary/50">
      {previewUrl ? (
        <>
          <NextImage src={previewUrl} alt={label} fill className="object-contain p-4" unoptimized />
          <div className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity hover:opacity-100">
            <span className="flex items-center gap-2 text-xs font-medium text-white">
              <ImageIcon className="h-4 w-4" aria-hidden />
              Cambiar
            </span>
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center gap-2 text-muted-foreground">
          <Plus className="h-8 w-8" aria-hidden />
          <span className="text-xs font-medium">{label}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Action entry point — ActionComponent contract. Wraps the reusable
 * `SingleImagePicker` with the default trigger so schemas can reference
 * `action: "single-image"` without passing children.
 */
export function SingleImagePickerAction({ value, onChange }: ActionComponentProps<string>) {
  return <SingleImagePicker value={value} onChange={onChange} />;
}
