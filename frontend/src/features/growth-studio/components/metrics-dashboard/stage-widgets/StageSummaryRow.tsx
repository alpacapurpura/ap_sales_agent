'use client';

import { useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { useNavigation } from '@/components/shared/navigation';
import type { StageId, StageSummary } from '../../../types/metrics';
import { StageCard } from './StageCard';
import { STAGE_TO_SLUG } from '../context/GrowthStudioContext';
import { cn } from '@/lib/utils';

interface StageSummaryRowProps {
  stages: StageSummary[];
  activeStage: StageId | null;
  /** Per-stage loading map — when a stage id is true, its StageCard shows skeleton */
  loadingMap?: Partial<Record<StageId, boolean>>;
  /** Per-stage mock map — when a stage id is true, its StageCard shows 'datos simulados' badge */
  mockMap?: Partial<Record<StageId, boolean>>;
}

/**
 * Horizontal scrolling row of StageCard components formatted as a Bowtie Funnel.
 * Clicking a card navigates to the corresponding stage route.
 */
export function StageSummaryRow({
  stages,
  activeStage,
  loadingMap = {},
  mockMap = {},
}: StageSummaryRowProps) {
  const { navigate } = useNavigation();
  const pathname = usePathname();

  // Derive tenantId + base path from current pathname
  const segments = pathname?.split('/').filter(Boolean) ?? [];
  const tenantId = segments[0] ?? '';

  const handleStageClick = useCallback((id: StageId) => {
    const slug = STAGE_TO_SLUG[id as keyof typeof STAGE_TO_SLUG];
    if (slug) {
      navigate(`/${tenantId}/growth-studio/${slug}`);
    }
  }, [navigate, tenantId]);

  return (
    <div className="w-full overflow-x-auto pb-4 scrollbar-thin">
      <div
        className={cn(
          "min-w-[800px] flex items-stretch justify-center relative rounded-2xl overflow-hidden h-[120px]",
          "bg-gradient-to-r from-blue-600 via-violet-600 via-emerald-600 via-amber-500 to-rose-600"
        )}
        style={{
          clipPath: "polygon(0 0, 50% 12%, 100% 0, 100% 100%, 50% 88%, 0 100%)"
        }}
      >
        {stages.map((stage, index) => {
          const isActive = activeStage === stage.id;
          const isNextActive = stages[index + 1] && activeStage === stages[index + 1].id;
          const isLast = index === stages.length - 1;

          return (
            <div
              key={stage.id}
              className="flex-1 relative flex"
            >
              <StageCard
                stage={stage}
                isActive={isActive}
                onClick={() => handleStageClick(stage.id)}
                isLoading={loadingMap[stage.id] ?? false}
                isMock={mockMap[stage.id] ?? false}
              />
              {/* Separator Line */}
              {!isLast && !isActive && !isNextActive && (
                <div className="absolute right-0 top-[20%] w-[1px] h-[60%] bg-white/10 z-10 pointer-events-none transition-opacity duration-300" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
