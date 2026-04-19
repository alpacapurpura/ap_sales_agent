"use client";

import { Settings } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { useBrandSettings } from "@/features/brand-studio/hooks/use-brand-settings";
import { useExpertBusinessTypesCatalog } from "@/features/brand-studio/hooks/use-expert-business-types-catalog";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";

/**
 * Compact horizontal row showing the tenant's declared business_types.
 *
 * Designed for page headers (Offer Studio dashboard, wizard) where space
 * is tight but context matters. Not clickable-in-place — edits live in
 * Brand Studio; a small gear icon links there for discoverability.
 *
 * New-tenant UX: if ``business_types`` is empty the component renders a
 * prompt that invites the user to declare it. This is intentional — it
 * primes the conversation about the user's expertise without forcing the
 * onboarding dialog to appear (which has its own trigger conditions in
 * the dashboard-level wiring).
 */
export function BusinessTypesChipBar({ className }: { className?: string }) {
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";
  const { settings, loading } = useBrandSettings();
  const { data: catalog } = useExpertBusinessTypesCatalog();

  if (loading) return null;

  const declared = settings?.identity?.business_types ?? [];
  const selectedMetadata = declared
    .map((type) => catalog?.business_types.find((t) => t.business_type === type))
    .filter((meta): meta is NonNullable<typeof meta> => Boolean(meta));

  const editHref = tenantId ? `/${tenantId}/brand-studio/identity` : undefined;

  if (declared.length === 0) {
    return (
      <div
        className={`flex flex-wrap items-center gap-2 text-xs text-muted-foreground ${className ?? ""}`}
      >
        <span>Aún no declaraste tu tipo de negocio.</span>
        {editHref ? (
          <Link
            href={editHref}
            className="inline-flex items-center gap-1 font-medium text-primary underline-offset-2 hover:underline"
          >
            Declararlo ahora
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className ?? ""}`}>
      <span className="text-xs font-medium text-muted-foreground">Mostrando ofertas para:</span>
      {selectedMetadata.map((meta) => {
        const Icon = resolveIconByName(meta.icon_name);
        return (
          <Badge
            key={meta.business_type}
            variant="outline"
            className="gap-1.5 text-xs border-transparent bg-primary/8 text-primary"
            title={meta.description_es}
          >
            <Icon className="h-3 w-3" aria-hidden />
            {meta.label_es}
          </Badge>
        );
      })}
      {editHref ? (
        <Link
          href={editHref}
          className="inline-flex h-5 w-5 items-center justify-center rounded text-muted-foreground hover:text-primary hover:bg-primary/10 transition"
          aria-label="Administrar tipos de negocio"
          title="Administrar en Brand Studio"
        >
          <Settings className="h-3 w-3" />
        </Link>
      ) : null}
    </div>
  );
}
