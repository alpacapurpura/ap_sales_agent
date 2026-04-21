"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

/**
 * Small back-link shown at the top of sub-views (preset picker, clone wizard).
 * Reads the tenantId from the URL params so this component can be used
 * without passing props.
 */
export function CommunicationStyleNav() {
  const params = useParams<{ tenantId: string }>();
  const href = `/${params.tenantId}/brand-studio/estilo`;

  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      aria-label="Volver a Estilo Comunicacional"
    >
      <ChevronLeft className="h-4 w-4" aria-hidden />
      Volver a Estilo
    </Link>
  );
}
