'use client';

import { Loader2, Youtube } from 'lucide-react';
import Image from 'next/image';
import { useYoutubeTopVideos } from '../../../../hooks/useYoutubeAnalytics';

function formatDuration(iso: string): string {
  // Parse ISO 8601 duration like PT1H2M30S
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return iso;
  const h = match[1] ? `${match[1]}:` : '';
  const m = (match[2] || '0').padStart(h ? 2 : 1, '0');
  const s = (match[3] || '0').padStart(2, '0');
  return `${h}${m}:${s}`;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toLocaleString('es-ES');
}

interface YouTubeTopVideosListProps {
  enabled: boolean;
}

export function YouTubeTopVideosList({ enabled }: YouTubeTopVideosListProps) {
  const { data, isLoading, error } = useYoutubeTopVideos(enabled);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        <span className="ml-2 text-xs text-muted-foreground">Cargando videos...</span>
      </div>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <p className="text-xs text-muted-foreground py-4 text-center">Sin datos de videos</p>
    );
  }

  return (
    <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
      {data.map((video, idx) => (
        <div key={video.videoId || idx} className="flex gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
          {/* Thumbnail with duration overlay */}
          <div className="relative flex-shrink-0 w-[120px] h-[68px] rounded-md overflow-hidden bg-muted">
            {video.thumbnailUrl ? (
              <Image
                src={video.thumbnailUrl}
                alt={video.title}
                fill
                className="object-cover"
                sizes="120px"
                loading="lazy"
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <Youtube className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            {video.duration && (
              <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1 rounded">
                {formatDuration(video.duration)}
              </span>
            )}
          </div>
          {/* Video info */}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium leading-tight line-clamp-2">{video.title}</p>
            <div className="flex items-center gap-2 mt-1 text-[10px] text-muted-foreground">
              <span>{formatNumber(video.views)} vistas</span>
              <span>·</span>
              <span>{formatNumber(video.likes)} likes</span>
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5">
              {formatNumber(video.watchTimeMinutes)} min vistos
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
