"use client";

import { Suspense, lazy, useMemo } from "react";
import { Loader2 } from "lucide-react";
import { useCopilotStore } from "../store/copilot-store";
import { getPreviewEntry } from "../config/interview-preview-registry";
import type { PreviewRegistryEntry } from "../config/interview-preview-registry";
import type { ComponentType } from "react";
import type {
  PreviewSummaryProps,
  PreviewSectionsProps,
} from "../config/interview-preview-registry";

// ── Lazy component cache (stable references across renders) ───────────────
const lazyCache = new Map<
  string,
  {
    Summary: ComponentType<PreviewSummaryProps>;
    Sections: ComponentType<PreviewSectionsProps>;
  }
>();

function getLazyComponents(domain: string, entry: PreviewRegistryEntry) {
  const cached = lazyCache.get(domain);
  if (cached) return cached;

  const pair = {
    Summary: lazy(entry.summaryComponent),
    Sections: lazy(entry.sectionsComponent),
  };
  lazyCache.set(domain, pair);
  return pair;
}

function PreviewLoader() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
    </div>
  );
}

export function CopilotPreviewPane() {
  const focusEntity = useCopilotStore((s) => s.focusEntity);
  const previewData = useCopilotStore((s) => s.previewData);
  const focusSnapshot = useCopilotStore((s) => s.focusSnapshot);

  const domain = focusEntity?.domain ?? null;

  const entry = useMemo(() => (domain ? getPreviewEntry(domain) : null), [domain]);

  if (!focusEntity || !entry || !domain) return null;

  const { Summary, Sections } = getLazyComponents(domain, entry);
  const data = previewData ?? focusSnapshot ?? {};
  const hasData = Object.keys(data).length > 0;

  return (
    <div
      className="flex h-full w-full flex-col bg-slate-50 dark:bg-slate-800/50 animate-in fade-in-0 slide-in-from-left-2 duration-200"
      data-testid="copilot-preview-pane"
    >
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300">Vista previa</h3>
        <p className="mt-0.5 text-xs text-slate-500">{focusEntity.label}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {hasData ? (
          <Suspense fallback={<PreviewLoader />}>
            <Summary data={data} completenessScore={0} />
            <Sections data={data} currentBlock="" blocksCompleted={[]} />
          </Suspense>
        ) : (
          <div className="flex h-full items-center justify-center text-center">
            <p className="text-sm text-slate-400">{entry.emptyStateMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
