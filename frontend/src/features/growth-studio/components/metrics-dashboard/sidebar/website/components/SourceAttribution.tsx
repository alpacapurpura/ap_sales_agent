'use client';

import { cn } from '@/lib/utils';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

interface AlternativeSource {
  source: 'meta_pixel' | 'shopify' | string;
  label: string;
  value: number;
  formattedValue: string;
}

interface SourceAttributionProps {
  primarySource?: string;
  alternatives?: AlternativeSource[];
}

const SOURCE_COLORS: Record<string, string> = {
  ga4: 'bg-amber-500',
  meta_pixel: 'bg-blue-500',
  shopify: 'bg-green-500',
};

const SOURCE_LABELS: Record<string, string> = {
  ga4: 'GA4',
  meta_pixel: 'Meta Pixel',
  shopify: 'Shopify',
};

function getSourceColor(source: string): string {
  return SOURCE_COLORS[source] ?? 'bg-gray-400';
}

function getSourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

export function SourceAttribution({ primarySource, alternatives }: SourceAttributionProps) {
  if (!primarySource) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {/* Primary source badge */}
      <span
        className={cn(
          'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5',
          'bg-muted text-muted-foreground',
        )}
        style={{ fontSize: '9px', lineHeight: '12px' }}
      >
        <span
          className={cn('h-1.5 w-1.5 rounded-full', getSourceColor(primarySource))}
          aria-hidden="true"
        />
        {getSourceLabel(primarySource)}
      </span>

      {/* Alternative source badges with popover */}
      {alternatives?.map((alt) => (
        <Popover key={alt.source}>
          <PopoverTrigger asChild>
            <button
              type="button"
              className={cn(
                'inline-flex items-center gap-1 rounded-full px-1.5 py-0.5',
                'bg-muted/60 text-muted-foreground hover:bg-muted transition-colors',
                'cursor-pointer',
              )}
              style={{ fontSize: '9px', lineHeight: '12px' }}
            >
              <span
                className={cn('h-1.5 w-1.5 rounded-full', getSourceColor(alt.source))}
                aria-hidden="true"
              />
              {alt.label}
            </button>
          </PopoverTrigger>
          <PopoverContent
            className="w-auto p-2 text-xs"
            side="top"
            align="start"
          >
            <div className="flex items-center gap-1.5">
              <span
                className={cn('h-2 w-2 rounded-full', getSourceColor(alt.source))}
                aria-hidden="true"
              />
              <span className="font-medium">{alt.label}:</span>
              <span>{alt.formattedValue}</span>
            </div>
          </PopoverContent>
        </Popover>
      ))}
    </div>
  );
}
