'use client';

import type { StageId, StageSummary, MetricClickData } from '../../types/metrics';
import { StageCard } from './StageCard';

interface StageSummaryRowProps {
  stages: StageSummary[];
  activeStage: StageId | null;
  onStageClick: (id: StageId) => void;
  /** Optional: called when a metric inside a detail panel is clicked to open the sidebar */
  onMetricClick?: (metric: MetricClickData) => void;
  /** Per-stage loading map — when a stage id is true, its StageCard shows skeleton */
  loadingMap?: Partial<Record<StageId, boolean>>;
  /** Per-stage mock map — when a stage id is true, its StageCard shows 'datos simulados' badge */
  mockMap?: Partial<Record<StageId, boolean>>;
}

/**
 * Horizontal scrolling row of StageCard components.
 *
 * Passes isLoading and isMock through to each StageCard for progressive loading UI.
 * The onMetricClick prop is threaded through for use in Plan 11-02 detail panel wiring.
 */
export function StageSummaryRow({
  stages,
  activeStage,
  onStageClick,
  onMetricClick: _onMetricClick,
  loadingMap = {},
  mockMap = {},
}: StageSummaryRowProps) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin">
      {stages.map((stage) => (
        <StageCard
          key={stage.id}
          stage={stage}
          isActive={activeStage === stage.id}
          onClick={() => onStageClick(stage.id)}
          isLoading={loadingMap[stage.id] ?? false}
          isMock={mockMap[stage.id] ?? false}
        />
      ))}
    </div>
  );
}
