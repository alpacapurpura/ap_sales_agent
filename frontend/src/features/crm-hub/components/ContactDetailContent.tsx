import * as React from "react";

import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { IdentityList } from "./IdentityList";
import { LifecycleStageChip } from "./LifecycleStageChip";
import { ScoreBadge } from "./ScoreBadge";

import type { ContactDetail } from "../types";

interface ContactDetailContentProps {
  detail: ContactDetail | null;
  isLoading?: boolean;
  className?: string;
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  );
}

function TraitsSection({ label, traits }: { label: string; traits: Record<string, unknown> }) {
  const entries = Object.entries(traits);
  if (entries.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <SectionHeader>{label}</SectionHeader>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        {entries.map(([key, value]) => (
          <React.Fragment key={key}>
            <dt className="text-muted-foreground truncate">{key}</dt>
            <dd className="truncate">{String(value ?? "—")}</dd>
          </React.Fragment>
        ))}
      </dl>
    </div>
  );
}

function ScoreRow({ label, score }: { label: string; score: number | null }) {
  if (score === null) return null;
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="tabular-nums font-medium">{score}/100</span>
    </div>
  );
}

/**
 * Contenido del panel de detalle de un contacto.
 *
 * AISLADO: no importa Sheet/Dialog/Drawer.
 * Reutilizable: drawer (PR-11) + página completa (PI-3) importan igual.
 *
 * Arch test: test_contact_detail_content_isolated.test.ts enforces.
 */
export function ContactDetailContent({
  detail,
  isLoading = false,
  className,
}: ContactDetailContentProps) {
  if (isLoading) {
    return (
      <div className={cn("flex flex-col gap-4 p-1", className)} aria-busy>
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-32" />
        <Separator />
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  if (!detail) {
    return (
      <div className={cn("p-4 text-sm text-muted-foreground", className)}>
        Selecciona un contacto para ver sus detalles.
      </div>
    );
  }

  const displayName = detail.full_name ?? detail.primary_email ?? "Contacto sin nombre";

  return (
    <div
      className={cn("flex flex-col gap-4 overflow-y-auto", className)}
      role="region"
      aria-label="Detalle de contacto"
    >
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 id="contact-detail-title" className="text-lg font-semibold leading-tight">
          {displayName}
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          <LifecycleStageChip stage={detail.lifecycle_stage} />
          <ScoreBadge score={Math.round(detail.lead_score)} />
          {detail.temperature && (
            <span className="text-xs text-muted-foreground capitalize">{detail.temperature}</span>
          )}
        </div>
      </div>

      <Separator />

      {/* Identidades */}
      <div className="flex flex-col gap-2">
        <SectionHeader>Identidades</SectionHeader>
        <IdentityList identities={detail.identities} />
      </div>

      <Separator />

      {/* Canales */}
      {(detail.telegram_id || detail.whatsapp_id || detail.instagram_id || detail.tiktok_id) && (
        <>
          <div className="flex flex-col gap-2">
            <SectionHeader>Canales</SectionHeader>
            <dl className="flex flex-col gap-1 text-sm">
              {detail.telegram_id && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground shrink-0">Telegram</dt>
                  <dd className="truncate">{detail.telegram_id}</dd>
                </div>
              )}
              {detail.whatsapp_id && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground shrink-0">WhatsApp</dt>
                  <dd className="truncate">{detail.whatsapp_id}</dd>
                </div>
              )}
              {detail.instagram_id && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground shrink-0">Instagram</dt>
                  <dd className="truncate">{detail.instagram_id}</dd>
                </div>
              )}
              {detail.tiktok_id && (
                <div className="flex gap-2">
                  <dt className="text-muted-foreground shrink-0">TikTok</dt>
                  <dd className="truncate">{detail.tiktok_id}</dd>
                </div>
              )}
            </dl>
          </div>
          <Separator />
        </>
      )}

      {/* Scoring */}
      <div className="flex flex-col gap-2">
        <SectionHeader>Scoring</SectionHeader>
        <div className="flex flex-col gap-1">
          <ScoreRow label="Lead score" score={Math.round(detail.lead_score)} />
          <ScoreRow label="Fit score" score={detail.fit_score} />
          <ScoreRow label="Intent score" score={detail.intent_score} />
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Valor de vida</span>
            <span className="tabular-nums font-medium">${detail.lifetime_value.toFixed(0)}</span>
          </div>
        </div>
      </div>

      <Separator />

      {/* Actividad */}
      <div className="flex flex-col gap-2">
        <SectionHeader>Actividad</SectionHeader>
        <dl className="flex flex-col gap-1 text-sm">
          <div className="flex gap-2">
            <dt className="text-muted-foreground shrink-0">Última actividad</dt>
            <dd>{detail.last_activity_at ? formatRelativeDate(detail.last_activity_at) : "—"}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-muted-foreground shrink-0">Primera conversión</dt>
            <dd>
              {detail.first_conversion_at ? formatRelativeDate(detail.first_conversion_at) : "—"}
            </dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-muted-foreground shrink-0">Origen</dt>
            <dd>{detail.lead_source ?? "—"}</dd>
          </div>
          {detail.country && (
            <div className="flex gap-2">
              <dt className="text-muted-foreground shrink-0">País</dt>
              <dd>{detail.country.toUpperCase()}</dd>
            </div>
          )}
        </dl>
      </div>

      {detail.conversation_summary && (
        <>
          <Separator />
          <div className="flex flex-col gap-2">
            <SectionHeader>Resumen de conversación</SectionHeader>
            <p className="text-sm leading-relaxed text-foreground">{detail.conversation_summary}</p>
          </div>
        </>
      )}

      {Object.keys(detail.traits).length > 0 && (
        <>
          <Separator />
          <TraitsSection label="Características" traits={detail.traits} />
        </>
      )}

      {Object.keys(detail.computed_traits).length > 0 && (
        <>
          <Separator />
          <TraitsSection label="Características calculadas" traits={detail.computed_traits} />
        </>
      )}
    </div>
  );
}

/** Simple relative date formatter. Does NOT use toLocaleDateString(). */
function formatRelativeDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return "hoy";
    if (diffDays === 1) return "hace 1 día";
    if (diffDays < 30) return `hace ${diffDays} días`;
    if (diffDays < 365) return `hace ${Math.floor(diffDays / 30)} meses`;
    return `hace ${Math.floor(diffDays / 365)} años`;
  } catch {
    return isoString;
  }
}
