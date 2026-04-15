"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";

interface ConnectionBadgeProps {
  connected: boolean;
  onConfigure?: () => void;
  /** When true, shows a disabled "Próximamente.." badge instead of "Configurar" */
  comingSoon?: boolean;
}

export function ConnectionBadge({ connected, onConfigure, comingSoon }: ConnectionBadgeProps) {
  const params = useParams();
  const tenantId = params?.tenantId as string;
  if (connected) {
    return (
      <Badge variant="outline" className="border-green-500/50 text-green-600 dark:text-green-400">
        Conectado
      </Badge>
    );
  }

  if (comingSoon) {
    return (
      <Badge
        variant="outline"
        className="border-muted-foreground/20 text-muted-foreground/50 cursor-default"
      >
        Próximamente..
      </Badge>
    );
  }

  const badge = (
    <Badge
      variant="outline"
      className="border-muted-foreground/30 text-muted-foreground hover:border-primary hover:text-primary cursor-pointer transition-colors"
    >
      Configurar
    </Badge>
  );

  if (onConfigure) {
    return (
      <button type="button" onClick={onConfigure}>
        {badge}
      </button>
    );
  }

  return <Link href={`/${tenantId}/connections`}>{badge}</Link>;
}
