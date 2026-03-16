'use client';

// STUB: This component is implemented in Plan 11-01.
// This file exists to allow Wave 0 test scaffolding to import it.
// Replace contents with real implementation during Plan 11-01 execution.

import type { ReactNode } from 'react';

interface DetailSkeletonProps {
  isLoading: boolean;
  children: ReactNode;
  className?: string;
}

export function DetailSkeleton({ isLoading: _isLoading, children, className: _className }: DetailSkeletonProps) {
  // TODO (Plan 11-01): Implement skeleton loading state with 3 KPI bars + content rows
  return <>{children}</>;
}
