'use client';

import type { ReactNode } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

interface DetailSkeletonProps {
  /** When true, renders animated shimmer skeleton. When false, renders children. */
  isLoading: boolean;
  children: ReactNode;
}

/**
 * Reusable loading skeleton for all 8 detail panels in the metrics dashboard.
 *
 * Layout matches the standard detail panel structure:
 *   1. 3-column header KPI row (60px height each)
 *   2. MiniFunnel visual bar (8px height)
 *   3. 6 ChannelRow skeleton lines (40px height each)
 *
 * Uses shadcn Skeleton component which applies the muted background + shimmer animation
 * from globals.css without any custom CSS needed.
 */
export default function DetailSkeleton({ isLoading, children }: DetailSkeletonProps) {
  if (!isLoading) {
    return <>{children}</>;
  }

  return (
    <div className="space-y-4 p-4 animate-pulse" aria-busy="true" aria-label="Cargando datos...">
      {/* Header KPIs — 3-column grid */}
      <div className="grid grid-cols-3 gap-4">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-[60px] w-full rounded-md" />
        </div>
        <div className="flex flex-col gap-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-[60px] w-full rounded-md" />
        </div>
        <div className="flex flex-col gap-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-[60px] w-full rounded-md" />
        </div>
      </div>

      {/* MiniFunnel bar — single 8px bar per UI-SPEC */}
      <Skeleton className="h-2 w-full rounded-full" />

      {/* Channel rows — 6 stacked skeleton lines */}
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-4 w-4 rounded-full flex-shrink-0" />
            <Skeleton className="h-10 flex-1 rounded-md" />
            <Skeleton className="h-10 w-16 rounded-md flex-shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
}
