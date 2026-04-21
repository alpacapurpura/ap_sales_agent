"use client";

import { Image as ImageIcon, Sparkles, Upload } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { useAssets, useUploadAsset } from "../../hooks/use-assets";

import { AssetCard } from "./AssetCard";
import { AssetGenerationWizardDialog } from "./AssetGenerationWizardDialog";
import { AssetToolbar } from "./AssetToolbar";

import type { AssetListQuery, AssetResponse, AssetSortKey } from "../../types/assets";
import type { OfferAssetSource, OfferAssetType } from "../../types/enums";

/**
 * Main view for the Assets tab. Wraps `useAssets` with local filter state,
 * then renders the toolbar + grid + empty/loading/error states.
 *
 * The filter state lives in React state and is passed as a query to the
 * hook; this way changing a chip triggers a refetch keyed on the new query.
 */
export function AssetsView({ offerId }: { offerId: string }) {
  const [search, setSearch] = useState("");
  const [type, setType] = useState<OfferAssetType | "all">("all");
  const [source, setSource] = useState<OfferAssetSource | "all">("all");
  const [sort, setSort] = useState<AssetSortKey>("created_desc");
  const [wizardOpen, setWizardOpen] = useState(false);

  const query = useMemo<AssetListQuery>(
    () => ({
      search: search || undefined,
      type: type === "all" ? undefined : type,
      source: source === "all" ? undefined : source,
      sort,
    }),
    [search, type, source, sort],
  );

  const { data, isLoading, isError, error, refetch } = useAssets(offerId, query);
  const uploadAsset = useUploadAsset(offerId);

  const handlePreview = (asset: AssetResponse) => {
    if (asset.file_url) {
      window.open(asset.file_url, "_blank", "noopener,noreferrer");
    } else {
      toast.info("Este asset todavía se está procesando");
    }
  };

  const handleDownload = (asset: AssetResponse) => {
    if (!asset.file_url) {
      toast.info("Este asset todavía se está procesando");
      return;
    }
    const link = document.createElement("a");
    link.href = asset.file_url;
    link.download = asset.name;
    link.click();
  };

  const handleEdit = (_asset: AssetResponse) => {
    // Puck editor integration will be wired in a follow-up; for now we just
    // toast so the user knows the action is recognised.
    toast.info("Abriendo el editor Puck — próximamente");
  };

  const handleUpload = (file: File) => {
    uploadAsset.mutate(file);
  };

  return (
    <div
      className="h-full space-y-5 overflow-y-auto p-6"
      role="region"
      aria-label="Biblioteca de assets"
    >
      <AssetToolbar
        search={search}
        onSearchChange={setSearch}
        type={type}
        onTypeChange={setType}
        source={source}
        onSourceChange={setSource}
        sort={sort}
        onSortChange={setSort}
        totalShown={data?.items.length ?? 0}
        totalAssets={data?.total ?? 0}
        onUpload={handleUpload}
        isUploading={uploadAsset.isPending}
        onGenerate={() => setWizardOpen(true)}
      />

      {isLoading && <AssetsGridSkeleton />}

      {isError && !isLoading && (
        <Alert variant="destructive">
          <AlertTitle>Error al cargar los assets</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-2">
            <span>{error?.message ?? "Intentalo nuevamente."}</span>
            <Button type="button" variant="outline" size="sm" onClick={() => refetch()}>
              Reintentar
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {!isLoading && !isError && data?.items.length === 0 && (
        <AssetsEmptyState onUpload={handleUpload} onGenerate={() => setWizardOpen(true)} />
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <div
          role="list"
          aria-label="Lista de assets"
          className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4"
        >
          {data.items.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              onPreview={handlePreview}
              onDownload={handleDownload}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      <AssetGenerationWizardDialog open={wizardOpen} onOpenChange={setWizardOpen} />
    </div>
  );
}

function AssetsGridSkeleton() {
  return (
    <div
      className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4"
      aria-label="Cargando assets"
    >
      {Array.from({ length: 8 }).map((_, idx) => (
        <div key={idx} className="space-y-2">
          <Skeleton className="aspect-[4/5] w-full rounded-lg" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-2 w-1/2" />
        </div>
      ))}
    </div>
  );
}

function AssetsEmptyState({
  onUpload,
  onGenerate,
}: {
  onUpload: (file: File) => void;
  onGenerate: () => void;
}) {
  const handleUploadClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (file) onUpload(file);
    };
    input.click();
  };

  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed p-12 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-border bg-muted/30">
        <ImageIcon className="h-8 w-8 text-muted-foreground" aria-hidden />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold">Todavía no hay assets para esta oferta</h3>
        <p className="max-w-sm text-xs text-muted-foreground">
          Genera tu primer flyer, video o carrusel con IA usando la información de tu oferta.
          También puedes subir assets ya creados.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        <Button variant="outline" size="sm" onClick={handleUploadClick}>
          <Upload className="mr-1.5 h-3.5 w-3.5" aria-hidden />
          Subir externo
        </Button>
        <Button size="sm" onClick={onGenerate}>
          <Sparkles className="mr-1.5 h-3.5 w-3.5" aria-hidden />
          Generar con IA
        </Button>
      </div>
    </div>
  );
}
