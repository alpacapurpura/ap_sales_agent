"use client";

import { cn } from "@/lib/utils";

import type { VideoBlock as VideoBlockType } from "../../types/message-blocks";

interface VideoBlockProps {
  block: VideoBlockType;
  className?: string;
}

/**
 * Video block with native HTML5 controls.
 * Shows poster image as thumbnail until user interacts.
 */
export function VideoBlock({ block, className }: VideoBlockProps) {
  return (
    <div className={cn("max-w-[320px]", className)}>
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <video
        src={block.url}
        poster={block.poster_url}
        controls
        preload="metadata"
        width={block.width}
        height={block.height}
        className="w-full max-w-[320px] rounded-xl border border-border bg-black"
        aria-label="Reproductor de video"
      />
    </div>
  );
}

VideoBlock.displayName = "VideoBlock";
