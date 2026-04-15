"use client";

import {
  Download,
  Eye,
  FileText,
  Film,
  Image as ImageIcon,
  LayoutGrid,
  Pencil,
  Sparkles,
} from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import type { AssetResponse } from "../../types/assets";

/**
 * Gradient background classes by asset type. Matches the UX preview aesthetic
 * (flyers=info/blue, videos=danger/red, carousels=success/green, docs=warning/amber).
 */
const TYPE_GRADIENT: Record<AssetResponse["type"], string> = {
  flyer: "from-info/20 via-info/5 to-transparent text-info/40",
  video: "from-destructive/20 via-destructive/5 to-transparent text-destructive/40",
  carousel: "from-success/20 via-success/5 to-transparent text-success/40",
  document: "from-warning/20 via-warning/5 to-transparent text-warning/40",
  image: "from-primary/20 via-primary/5 to-transparent text-primary/40",
};

function AssetTypeIcon({ type }: { type: AssetResponse["type"] }) {
  const common = "h-12 w-12";
  switch (type) {
    case "video":
      return <Film className={common} aria-hidden />;
    case "carousel":
      return <LayoutGrid className={common} aria-hidden />;
    case "document":
      return <FileText className={common} aria-hidden />;
    case "image":
      return <ImageIcon className={common} aria-hidden />;
    case "flyer":
    default:
      return <FileText className={common} aria-hidden />;
  }
}

function formatRelativeDate(iso: string): string {
  const then = new Date(iso).getTime();
  const diffMs = Date.now() - then;
  const minutes = Math.floor(diffMs / 60_000);
  if (minutes < 60) return `Hace ${Math.max(1, minutes)}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Hace ${days}d`;
  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `Hace ${weeks} sem`;
  const months = Math.floor(days / 30);
  return `Hace ${months} mes${months === 1 ? "" : "es"}`;
}

// eslint-disable-next-line sonarjs/cognitive-complexity -- TODO: extract per-type duration resolvers
function resolveDurationBadge(asset: AssetResponse): string | null {
  const meta = asset.metadata;
  if (!meta) return null;
  if (asset.type === "video") {
    const duration = meta.duration_seconds;
    if (typeof duration === "number" && duration > 0) {
      const mins = Math.floor(duration / 60);
      const secs = Math.floor(duration % 60);
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    }
    return null;
  }
  if (asset.type === "carousel") {
    const slides = meta.slide_count;
    if (typeof slides === "number" && slides > 0) return `${slides} slides`;
    return null;
  }
  if (asset.type === "document") {
    const pages = meta.page_count;
    if (typeof pages === "number" && pages > 0) {
      return `${pages} pág${pages === 1 ? "" : "s"}`;
    }
    return null;
  }
  return null;
}

export interface AssetCardProps {
  asset: AssetResponse;
  onPreview?: (asset: AssetResponse) => void;
  onDownload?: (asset: AssetResponse) => void;
  onEdit?: (asset: AssetResponse) => void;
}

export function AssetCard({ asset, onPreview, onDownload, onEdit }: AssetCardProps) {
  const gradient = TYPE_GRADIENT[asset.type] ?? TYPE_GRADIENT.flyer;
  const corner = useMemo(() => resolveDurationBadge(asset), [asset]);
  const isExternal = asset.source === "external";
  const canEditInPuck = asset.editable_in_puck && !isExternal;

  return (
    <div className="group space-y-2" role="listitem" aria-label={asset.name}>
      <div
        className={cn(
          "relative aspect-[4/5] overflow-hidden rounded-lg border border-border bg-gradient-to-br",
          gradient,
        )}
      >
        {asset.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element -- server returns signed CDN URLs, next/image not configured for arbitrary hosts
          <img
            src={asset.thumbnail_url}
            alt={asset.name}
            className="h-full w-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <AssetTypeIcon type={asset.type} />
          </div>
        )}

        {/* Top-left source badge */}
        <div
          className={cn(
            "absolute left-2 top-2 flex items-center gap-1 rounded border bg-background/80 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide backdrop-blur",
            isExternal ? "border-warning/30 text-warning" : "border-info/30 text-info",
          )}
        >
          {isExternal ? null : <Sparkles className="h-2.5 w-2.5" aria-hidden />}
          {isExternal ? "Externo" : "IA"}
        </div>

        {/* Top-right duration/slides/pages badge */}
        {corner ? (
          <div className="absolute right-2 top-2 rounded bg-background/80 px-1.5 py-0.5 text-[9px] font-semibold text-foreground backdrop-blur">
            {corner}
          </div>
        ) : null}

        {/* Hover overlay with actions */}
        <div className="absolute inset-0 flex items-center justify-center gap-2 bg-background/80 opacity-0 backdrop-blur-sm transition-opacity group-hover:opacity-100">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={() => onPreview?.(asset)}
                  aria-label={`Visualizar ${asset.name}`}
                >
                  <Eye className="h-4 w-4" aria-hidden />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Visualizar</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={() => onDownload?.(asset)}
                  aria-label={`Descargar ${asset.name}`}
                >
                  <Download className="h-4 w-4" aria-hidden />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Descargar</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    type="button"
                    size="icon"
                    variant={canEditInPuck ? "default" : "outline"}
                    disabled={!canEditInPuck}
                    onClick={() => canEditInPuck && onEdit?.(asset)}
                    aria-label={`Editar ${asset.name} en Puck`}
                  >
                    <Pencil className="h-4 w-4" aria-hidden />
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {canEditInPuck ? "Editar en Puck" : "Los assets externos no se editan en Puck"}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <div>
        <p className="truncate text-xs font-medium">{asset.name}</p>
        <p className="text-[10px] text-muted-foreground">
          {formatRelativeDate(asset.created_at)} · {isExternal ? "Externo" : "IA"}
        </p>
      </div>
    </div>
  );
}
