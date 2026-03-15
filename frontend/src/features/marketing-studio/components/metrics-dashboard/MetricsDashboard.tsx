'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { StageId } from '../../types/metrics';
import { STAGE_SUMMARIES } from '../../api/metrics-mock-data';
import { StageSummaryRow } from './StageSummaryRow';
import { AttractionDetail } from './detail-panels/AttractionDetail';
import { PlaceholderDetail } from './detail-panels/PlaceholderDetail';

export function MetricsDashboard() {
  const [activeStage, setActiveStage] = useState<StageId | null>('ATRACCION');

  const handleStageClick = (id: StageId) => {
    setActiveStage(activeStage === id ? null : id);
  };

  const activeStageData = activeStage
    ? STAGE_SUMMARIES.find((s) => s.id === activeStage)
    : null;

  return (
    <div className="space-y-4">
      <StageSummaryRow
        stages={STAGE_SUMMARIES}
        activeStage={activeStage}
        onStageClick={handleStageClick}
      />

      {activeStageData && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">
              Detalle: {activeStageData.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activeStage === 'ATRACCION' ? (
              <AttractionDetail />
            ) : (
              <PlaceholderDetail stage={activeStageData} />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
