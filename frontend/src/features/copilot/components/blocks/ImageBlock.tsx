"use client";

import { ImageOff } from "lucide-react";
import { useState } from "react";

import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import type { ImageBlock as ImageBlockType } from "../../types/message-blocks";

interface ImageBlockProps {
  block: ImageBlockType;
  className?: string;
}

/**
 * Renders an image with lazy loading, skeleton state, error fallback,
 * and a lightbox Dialog on click.
 */
export function ImageBlock({ block, className }: ImageBlockProps) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const alt = block.alt ?? "Imagen adjunta";

  return (
    <div className={cn("max-w-[280px]", className)}>
      {/* Thumbnail */}
      <button
        type="button"
        onClick={() => !error && setLightboxOpen(true)}
        aria-label={`Ver imagen: ${alt}`}
        className="group relative block overflow-hidden rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-purple-500"
        disabled={error}
      >
        {!loaded && !error && <Skeleton className="h-[180px] w-[280px] rounded-lg" />}
        {error ? (
          <div className="flex h-[120px] w-[200px] items-center justify-center rounded-lg bg-muted">
            <ImageOff className="h-8 w-8 text-muted-foreground/50" />
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={block.url}
            alt={alt}
            loading="lazy"
            width={block.width}
            height={block.height}
            onLoad={() => setLoaded(true)}
            onError={() => {
              setLoaded(true);
              setError(true);
            }}
            className={cn(
              "max-w-[280px] rounded-lg object-contain transition-opacity group-hover:opacity-90",
              loaded ? "opacity-100" : "opacity-0 absolute",
            )}
          />
        )}
      </button>
      {block.alt && <p className="mt-1 text-xs text-muted-foreground">{block.alt}</p>}

      {/* Lightbox */}
      <Dialog open={lightboxOpen} onOpenChange={setLightboxOpen}>
        <DialogContent className="max-w-4xl p-2">
          <DialogTitle className="sr-only">{alt}</DialogTitle>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={block.url}
            alt={alt}
            className="max-h-[80vh] w-full rounded-md object-contain"
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

ImageBlock.displayName = "ImageBlock";
