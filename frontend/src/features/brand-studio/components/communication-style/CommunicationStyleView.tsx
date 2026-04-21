"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { useActivePersonality } from "@/features/brand-studio/api/personality";

import { ActiveState } from "./ActiveState";
import { CloneWizardView } from "./CloneWizardView";
import { EmptyState } from "./EmptyState";
import { MigrationCard } from "./MigrationCard";
import { PresetPickerView } from "./PresetPickerView";

// ── Loading skeleton ──────────────────────────────────────────────────────────

function SkeletonState() {
  return (
    <div
      className="flex flex-col gap-6"
      aria-busy="true"
      aria-label="Cargando estilo comunicacional"
    >
      <div className="flex items-center gap-3">
        <div className="h-12 w-12 animate-pulse rounded-full bg-muted" />
        <div className="space-y-2">
          <div className="h-4 w-40 animate-pulse rounded bg-muted" />
          <div className="h-3 w-24 animate-pulse rounded bg-muted" />
        </div>
      </div>
      <div className="space-y-3">
        <div className="h-3 w-20 animate-pulse rounded bg-muted" />
        <div className="h-24 animate-pulse rounded-lg bg-muted" />
      </div>
      <div className="space-y-3">
        <div className="h-3 w-28 animate-pulse rounded bg-muted" />
        <div className="h-20 animate-pulse rounded-lg bg-muted" />
      </div>
    </div>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center"
    >
      <p className="text-sm text-destructive">
        No pudimos cargar tu estilo. Revisa tu conexión e intenta de nuevo.
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="text-sm font-medium text-primary underline-offset-2 hover:underline"
        aria-label="Reintentar carga del estilo comunicacional"
      >
        Reintentar
      </button>
    </div>
  );
}

// ── Empty state with optional migration card ──────────────────────────────────

interface EmptyStateWithMigrationProps {
  tenantId: string;
  voiceToneLegacy: string | null;
  voiceToneMigrationDismissed: boolean;
  onConverted: () => void;
}

function EmptyStateWithMigration({
  tenantId,
  voiceToneLegacy,
  voiceToneMigrationDismissed,
  onConverted,
}: EmptyStateWithMigrationProps) {
  return (
    <div className="flex flex-col gap-6">
      {voiceToneLegacy && !voiceToneMigrationDismissed && (
        <MigrationCard voiceToneText={voiceToneLegacy} onConverted={onConverted} />
      )}
      <EmptyState
        onOpenPresetPicker={() => {
          window.location.href = `/${tenantId}/brand-studio/estilo?view=preset`;
        }}
        onOpenCloneWizard={() => {
          window.location.href = `/${tenantId}/brand-studio/estilo?view=clone`;
        }}
      />
    </div>
  );
}

// ── Main orchestrator ─────────────────────────────────────────────────────────

interface CommunicationStyleViewProps {
  tenantId: string;
  voiceToneLegacy: string | null;
  voiceToneMigrationDismissed: boolean;
}

/**
 * Main client orchestrator for the "Estilo Comunicacional" section. Reads the
 * `?view` search param to decide which sub-view to render:
 *  - null  → empty state or active profile
 *  - "preset" → preset picker
 *  - "clone"  → clone wizard
 *
 * Passes voice_tone legacy props from the Server Component so the migration
 * card can be shown without an extra client-side fetch.
 */
export function CommunicationStyleView({
  tenantId,
  voiceToneLegacy,
  voiceToneMigrationDismissed,
}: CommunicationStyleViewProps) {
  const searchParams = useSearchParams();
  const view = searchParams.get("view");

  const { data: active, isLoading, isError, refetch } = useActivePersonality(tenantId);

  const body = (() => {
    // Sub-views take over the full content area — no active check needed
    if (view === "preset") {
      return <PresetPickerView activeProfile={active ?? null} />;
    }

    if (view === "clone") {
      return <CloneWizardView />;
    }

    // Default view: empty or active
    if (isLoading) return <SkeletonState />;
    if (isError) return <ErrorState onRetry={() => void refetch()} />;

    if (!active) {
      return (
        <EmptyStateWithMigration
          tenantId={tenantId}
          voiceToneLegacy={voiceToneLegacy}
          voiceToneMigrationDismissed={voiceToneMigrationDismissed}
          onConverted={() => void refetch()}
        />
      );
    }

    return <ActiveState profile={active} />;
  })();

  return <div className="min-w-0 flex-1 overflow-y-auto px-6 py-6 sm:px-8 sm:py-8">{body}</div>;
}
