"use client";

import { Cable } from "lucide-react";

import { NavLink } from "@/components/shared/navigation";
import { Badge } from "@/components/ui/badge";
import { BrandIcon } from "@/components/ui/brand-icons";
import { Card, CardContent } from "@/components/ui/card";
import { type ProviderDefinition } from "@/features/connections/config/provider-registry";
import { type ProviderStatus } from "@/features/connections/hooks/use-all-connections-status";
import { cn } from "@/lib/utils";

interface ConnectionCardProps {
  provider: ProviderDefinition;
  status?: ProviderStatus;
  tenantId: string;
}

/** Known icon names that BrandIcon can render */
const KNOWN_ICONS = new Set([
  "facebook",
  "fb",
  "meta",
  "instagram",
  "ig",
  "whatsapp",
  "wa",
  "youtube",
  "yt",
  "tiktok",
  "linkedin",
  "google",
  "ga4",
  "manychat",
  "telegram",
  "shopify",
  "mailerlite",
]);

/** Renders BrandIcon with Cable fallback for unknown names */
function ProviderIcon({ name, className }: { name: string; className?: string }) {
  const normalized = name.toLowerCase();
  const isKnown = Array.from(KNOWN_ICONS).some((k) => normalized.includes(k) || normalized === k);
  if (isKnown) return <BrandIcon name={name} className={className} />;
  return <Cable className={className} />;
}

/**
 *
 */
export function ConnectionCard({ provider, status, tenantId }: ConnectionCardProps) {
  const isConnected = status?.isConnected ?? false;
  const isComingSoon = provider.status === "coming_soon";

  const iconColorClass = isConnected
    ? "text-green-700 dark:text-green-400"
    : "text-muted-foreground group-hover:text-primary";

  const iconBgClass = isConnected
    ? "bg-green-100 dark:bg-green-900/30"
    : "bg-muted group-hover:bg-primary/10";

  if (isComingSoon) {
    return (
      <Card className="group relative overflow-hidden opacity-60 cursor-default">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
              <ProviderIcon name={provider.icon} className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-sm truncate">{provider.name}</h3>
                <Badge variant="secondary" className="text-[10px] shrink-0">
                  Próximamente
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {provider.description}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <NavLink
      href={`/${tenantId}/connections/${provider.id}`}
      className="block"
      loadingClassName="opacity-70"
    >
      <Card
        className={cn(
          "group relative overflow-hidden transition-all hover:shadow-md hover:border-primary/30 cursor-pointer",
          isConnected && "border-green-500/30 bg-green-50/50 dark:bg-green-950/10",
        )}
      >
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div
              className={cn(
                "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                iconBgClass,
              )}
            >
              <ProviderIcon name={provider.icon} className={cn("h-5 w-5", iconColorClass)} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-sm truncate">{provider.name}</h3>
                {isConnected ? (
                  <Badge
                    variant="secondary"
                    className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-[10px] shrink-0"
                  >
                    Conectado
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px] shrink-0">
                    Conectar
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {provider.description}
              </p>
              {isConnected && status?.displayName && (
                <p className="text-xs text-muted-foreground/70 mt-1.5 truncate">
                  {status.displayName}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </NavLink>
  );
}
