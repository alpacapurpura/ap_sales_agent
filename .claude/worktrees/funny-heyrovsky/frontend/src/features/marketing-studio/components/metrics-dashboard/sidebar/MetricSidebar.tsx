'use client';

// STUB: This component is implemented in Plan 11-01.
// This file exists to allow Wave 0 test scaffolding to import it.
// Replace contents with real implementation during Plan 11-01 execution.

import type { ReactNode } from 'react';

interface MetricClickData {
  stageId: string;
  channelSlug: string;
  metricName: string;
  currentValue: number;
}

interface MetricSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  metric: MetricClickData;
  stageId: string;
  children?: ReactNode;
}

export function MetricSidebar({ isOpen, children, metric }: MetricSidebarProps) {
  // TODO (Plan 11-01): Implement sidebar sheet with metric name, value, channel context, and close button
  if (!isOpen) return null;
  return (
    <div data-testid="metric-sidebar">
      <span>{metric.metricName}</span>
      <span>{metric.currentValue}</span>
      {children}
    </div>
  );
}
