'use client';

import Link from 'next/link';
import { Badge } from '@/components/ui/badge';

interface ConnectionBadgeProps {
  connected: boolean;
}

export function ConnectionBadge({ connected }: ConnectionBadgeProps) {
  if (connected) {
    return (
      <Badge variant="outline" className="border-green-500/50 text-green-600 dark:text-green-400">
        Conectado
      </Badge>
    );
  }

  return (
    <Link href="/connections">
      <Badge variant="outline" className="border-muted-foreground/30 text-muted-foreground hover:border-primary hover:text-primary cursor-pointer transition-colors">
        Configurar
      </Badge>
    </Link>
  );
}
