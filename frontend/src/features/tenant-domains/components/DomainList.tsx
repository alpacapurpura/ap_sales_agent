"use client";

import { Loader2, Star, Trash2, RefreshCw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

import { useDeleteDomain, useSetPrimary, useVerifyDomain } from "../hooks/use-domains";

import { DomainStatusBadge } from "./DomainStatusBadge";

import type { TenantDomain } from "../types";

interface DomainListProps {
  domains: TenantDomain[];
  isLoading: boolean;
}

interface DomainRowProps {
  domain: TenantDomain;
}

function DomainRow({ domain }: DomainRowProps) {
  const deleteDomain = useDeleteDomain();
  const setPrimary = useSetPrimary();
  const verifyDomain = useVerifyDomain();

  const canSetPrimary = !domain.is_primary && domain.status === "active";
  const canVerify = domain.status === "pending_verification" || domain.status === "failed";
  const isActionPending = deleteDomain.isPending || setPrimary.isPending || verifyDomain.isPending;

  return (
    <div className="flex items-center gap-3 rounded-lg border px-4 py-3">
      <div className="flex flex-1 flex-col gap-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-sm font-medium truncate">{domain.hostname}</span>
          {domain.is_primary && (
            <Badge variant="outline" className="text-xs shrink-0">
              Principal
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {domain.domain_type === "platform" ? "Plataforma" : "Personalizado"}
          </Badge>
          <DomainStatusBadge status={domain.status} />
        </div>
      </div>

      <div className="flex items-center gap-1 shrink-0">
        {canVerify && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => verifyDomain.mutate(domain.id)}
            disabled={isActionPending}
            aria-label="Verificar dominio"
          >
            {verifyDomain.isPending && verifyDomain.variables === domain.id ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            Verificar
          </Button>
        )}

        {canSetPrimary && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => setPrimary.mutate(domain.id)}
            disabled={isActionPending}
            aria-label="Establecer como principal"
          >
            {setPrimary.isPending && setPrimary.variables === domain.id ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Star className="h-3.5 w-3.5" />
            )}
            Principal
          </Button>
        )}

        {domain.domain_type === "custom" && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 text-destructive hover:text-destructive"
            onClick={() => deleteDomain.mutate(domain.id)}
            disabled={isActionPending}
            aria-label="Eliminar dominio"
          >
            {deleteDomain.isPending && deleteDomain.variables === domain.id ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

/**
 *
 */
export function DomainList({ domains, isLoading }: DomainListProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (domains.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        No hay dominios configurados.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {domains.map((domain) => (
        <DomainRow key={domain.id} domain={domain} />
      ))}
    </div>
  );
}
