"use client";

import { Suspense, lazy } from "react";

import { Skeleton } from "@/components/ui/skeleton";

import { DASHBOARD_COMPONENT_MAP } from "../lib/registries/dashboard-registry";

import type { GrowthStudioChannelSlug } from "./channel-slugs";
import type { ComponentType } from "react";

// ─── Loading fallback ─────────────────────────────────────────────────────────

/**
 * Fallback mientras el chunk del dashboard resuelve.
 * Espejo de `SectionPageLoading` pero para dashboards de canal.
 */
function DashboardLoading() {
  return (
    <div className="flex flex-col gap-4 p-6" aria-busy>
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-64 w-full" />
    </div>
  );
}

// ─── Module-level lazy component map ─────────────────────────────────────────

/**
 * Mapa module-level slug → componente lazy pre-instanciado.
 *
 * Construido una sola vez al cargar el módulo (no durante render).
 * Cada `lazy(factory)` se crea una vez por slug — estable entre renders.
 * Respeta `react-hooks/static-components`: ningún componente se crea en render.
 *
 * El `Record<string, ...>` en lugar de `Record<GrowthStudioChannelSlug, ...>` evita
 * circularidad de tipo entre el factory `ComponentType` (varía por dashboard) y
 * el acceso dinámico por slug string en ChannelDispatcher.
 */

/* eslint-disable @typescript-eslint/no-explicit-any -- prop types vary per dashboard */
const LAZY_DASHBOARD_MAP: Record<
  string,
  React.LazyExoticComponent<ComponentType<any>>
> = Object.fromEntries(
  Object.entries(DASHBOARD_COMPONENT_MAP).map(([slug, factory]) => [slug, lazy(factory)]),
);
/* eslint-enable @typescript-eslint/no-explicit-any */

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ChannelDispatcherProps {
  /** Slug canónico del canal (validado por `isGrowthStudioChannel` en el Server Component). */
  slug: GrowthStudioChannelSlug;
  /** Tab inicial que se activa al montar el dashboard. */
  initialTab?: string;
  /** Si true, el dashboard está embebido en una ruta propia (no en sidebar flotante). */
  isRouteBased?: boolean;
}

// ─── Dispatcher ───────────────────────────────────────────────────────────────

/**
 * Dispatcher client-side que carga lazy el dashboard del canal correspondiente.
 *
 * Lee el componente lazy desde `LAZY_DASHBOARD_MAP` (construido a nivel de módulo
 * desde `DASHBOARD_COMPONENT_MAP`). Contiene CERO hardcoded slug→component branches
 * — el mapa es SSoT único. Arch test `test-no-hardcoded-channel-slugs.test.ts` (T-6).
 *
 * Props comunes (`initialTab`, `isRouteBased`) se pasan al componente resultante.
 */
export function ChannelDispatcher({
  slug,
  initialTab,
  isRouteBased = true,
}: ChannelDispatcherProps) {
  const LazyComponent = LAZY_DASHBOARD_MAP[slug];

  if (!LazyComponent) {
    return (
      <div className="flex items-center justify-center py-24 text-sm text-muted-foreground">
        Dashboard no disponible para este canal
      </div>
    );
  }

  return (
    <Suspense fallback={<DashboardLoading />}>
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any -- prop types vary per dashboard */}
      <LazyComponent initialTab={initialTab} isRouteBased={isRouteBased} {...({} as any)} />
    </Suspense>
  );
}
