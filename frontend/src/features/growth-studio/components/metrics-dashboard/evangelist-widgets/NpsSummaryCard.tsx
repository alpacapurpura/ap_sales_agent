"use client";

import type { NpsSummaryData } from "../../../types/metrics";

interface Props {
  nps: NpsSummaryData;
  ugcCount: number;
  ugcWritten: number;
  ugcAudio: number;
}

export function NpsSummaryCard({ nps, ugcCount, ugcWritten, ugcAudio }: Props) {
  if (nps.totalResponses === 0) {
    return (
      <div className="rounded-lg border p-3 space-y-1">
        <p className="text-sm text-muted-foreground">Sin datos de satisfaccion</p>
        <p className="text-xs text-muted-foreground">
          Envia tu primera encuesta NPS para conocer como califican tu servicio.
        </p>
      </div>
    );
  }

  const total = nps.promoterCount + nps.passiveCount + nps.detractorCount;

  const promoterPct = total > 0 ? (nps.promoterCount / total) * 100 : 0;
  const passivePct = total > 0 ? (nps.passiveCount / total) * 100 : 0;
  const detractorPct = total > 0 ? (nps.detractorCount / total) * 100 : 0;

  return (
    <div className="rounded-lg border p-3 space-y-3">
      {/* NPS Score */}
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-semibold tabular-nums">
          {nps.npsScore?.toFixed(1) ?? "--"}
        </span>
        <span className="text-xs text-muted-foreground">/ 10</span>
        {nps.standardNps != null && (
          <span className="text-xs text-muted-foreground ml-2">
            (eNPS: {nps.standardNps > 0 ? "+" : ""}
            {nps.standardNps})
          </span>
        )}
      </div>

      {/* Proportional bar */}
      <div className="flex h-3 rounded-full overflow-hidden bg-muted">
        <div
          className="bg-emerald-500 transition-all"
          style={{ width: `${Math.max(promoterPct, nps.promoterCount > 0 ? 1 : 0)}%` }}
        />
        <div
          className="bg-yellow-500 transition-all"
          style={{ width: `${Math.max(passivePct, nps.passiveCount > 0 ? 1 : 0)}%` }}
        />
        <div
          className="bg-red-500 transition-all"
          style={{ width: `${Math.max(detractorPct, nps.detractorCount > 0 ? 1 : 0)}%` }}
        />
      </div>

      {/* Legend */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <span className="text-emerald-600 dark:text-emerald-400">
          9-10: {nps.promoterCount} ({promoterPct.toFixed(0)}%)
        </span>
        <span className="text-yellow-600 dark:text-yellow-400">
          7-8: {nps.passiveCount} ({passivePct.toFixed(0)}%)
        </span>
        <span className="text-red-600 dark:text-red-400">
          0-6: {nps.detractorCount} ({detractorPct.toFixed(0)}%)
        </span>
      </div>

      {/* Survey info */}
      <div className="text-xs text-muted-foreground">
        Encuestas enviadas: {nps.surveysSent} | Tasa de respuesta: {nps.responseRatePct.toFixed(1)}%
      </div>

      {/* UGC */}
      <div className="text-xs text-muted-foreground">
        <span>Testimonios recopilados: {ugcCount}</span>
        <br />
        <span>
          Escritos: {ugcWritten} | Audio: {ugcAudio}
        </span>
      </div>
    </div>
  );
}
