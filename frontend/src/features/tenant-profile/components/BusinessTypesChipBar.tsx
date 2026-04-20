"use client";

import { Settings } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { resolveIconByName } from "@/features/offer-studio/lib/icon-name-resolver";
import { cn } from "@/lib/utils";

import { useBusinessTypesCatalog } from "../hooks/use-business-types-catalog";
import { useTenantProfile } from "../hooks/use-tenant-profile";

interface BusinessTypesChipBarProps {
  className?: string;
}

/**
 * Compact horizontal row showing the tenant's declared business_types.
 *
 * Reads from the tenant-profile feature (not brand-studio).
 * Clicking the settings icon routes to /settings/perfil-negocio.
 *
 * CONTRACT §6.1 — components/BusinessTypesChipBar.tsx
 * CONTRACT §6.2 — global shell integration
 */
export function BusinessTypesChipBar({ className }: BusinessTypesChipBarProps) {
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";
  const { data: profile, isLoading: profileLoading } = useTenantProfile();
  const { data: catalog } = useBusinessTypesCatalog();

  if (profileLoading) return null;

  const declared = profile?.business_types ?? [];
  const selectedMetadata = declared
    .map((slug) => catalog?.business_types.find((t) => t.slug === slug))
    .filter((meta): meta is NonNullable<typeof meta> => Boolean(meta));

  const editHref = tenantId ? `/${tenantId}/settings/perfil-negocio` : undefined;

  if (declared.length === 0) {
    return (
      <div
        className={cn("flex flex-wrap items-center gap-2 text-xs text-muted-foreground", className)}
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
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <span className="text-xs font-medium text-muted-foreground">Mostrando ofertas para:</span>
      {selectedMetadata.map((meta) => {
        const Icon = resolveIconByName(meta.icon_name);
        return (
          <Badge
            key={meta.slug}
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
          title="Editar en Perfil de Negocio"
        >
          <Settings className="h-3 w-3" />
        </Link>
      ) : null}
    </div>
  );
}
