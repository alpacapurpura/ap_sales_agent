'use client';

import type { StageId, StageSummary } from '../../types/metrics';
import { StageCard } from './StageCard';

interface StageSummaryRowProps {
  stages: StageSummary[];
  activeStage: StageId | null;
  onStageClick: (id: StageId) => void;
}

export function StageSummaryRow({ stages, activeStage, onStageClick }: StageSummaryRowProps) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2 snap-x snap-mandatory scrollbar-thin">
      {stages.map((stage) => (
        <StageCard
          key={stage.id}
          stage={stage}
          isActive={activeStage === stage.id}
          onClick={() => onStageClick(stage.id)}
        />
      ))}
    </div>
  );
}
