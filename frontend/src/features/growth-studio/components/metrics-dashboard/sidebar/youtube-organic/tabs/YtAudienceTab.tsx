"use client";

import { ChartInfoTooltip } from "../../ig-organic/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";
import { YouTubeDemographicsChart } from "../../youtube/YouTubeDemographicsChart";

export function YtAudienceTab() {
  return (
    <div className="space-y-8">
      <ChartSection slug="demografia">
        <div className="space-y-3">
          <ChartInfoTooltip
            title="Demograf&iacute;a de Audiencia"
            description="Distribuci&oacute;n de tu audiencia por edad, g&eacute;nero y pa&iacute;s. Usa estos datos para ajustar tu contenido al p&uacute;blico que m&aacute;s te consume."
          />
          <YouTubeDemographicsChart enabled />
        </div>
      </ChartSection>
    </div>
  );
}
