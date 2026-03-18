'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

interface ConnectionBadgeProps {
  connected: boolean;
  onConfigure?: () => void;
  /** When true, shows a disabled "Proximamente.." badge instead of "Configurar" */
  comingSoon?: boolean;
}

export function ConnectionBadge({ connected, onConfigure, comingSoon }: ConnectionBadgeProps) {
  if (connected) {
    return (
      <Badge variant="outline" className="border-green-500/50 text-green-600 dark:text-green-400">
        Conectado
      </Badge>
    );
  }

  if (comingSoon) {
    return (
      <Badge variant="outline" className="border-muted-foreground/20 text-muted-foreground/50 cursor-default">
        Proximamente..
      </Badge>
    );
  }

  const badge = (
    <Badge variant="outline" className="border-muted-foreground/30 text-muted-foreground hover:border-primary hover:text-primary cursor-pointer transition-colors">
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

  return <Link href="/connections">{badge}</Link>;
}
