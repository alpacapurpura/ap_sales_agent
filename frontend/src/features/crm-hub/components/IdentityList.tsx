import { Mail, Phone, MessageCircle, Instagram, Star, CheckCircle, Clock } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

import type { ContactIdentity } from "../types";

interface IdentityListProps {
  identities: ContactIdentity[];
  className?: string;
}

const TYPE_ICONS: Record<string, React.ReactNode> = {
  email: <Mail className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />,
  phone: <Phone className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />,
  telegram: <MessageCircle className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />,
  whatsapp: <MessageCircle className="h-4 w-4 shrink-0 text-blue-500" aria-hidden />,
  instagram: <Instagram className="h-4 w-4 shrink-0 text-pink-500" aria-hidden />,
};

function VerificationIcon({ status }: { status: string }) {
  if (status === "verified") {
    return <CheckCircle className="h-3 w-3 text-green-500" aria-label="verificado" />;
  }
  if (status === "pending") {
    return <Clock className="h-3 w-3 text-amber-500" aria-label="pendiente" />;
  }
  return null;
}

/**
 * Lista vertical de identidades multi-canal de un contacto.
 * Muestra icono por tipo, valor, estrella si es primaria, y estado de verificación.
 */
export function IdentityList({ identities, className }: IdentityListProps) {
  if (identities.length === 0) {
    return (
      <p className={cn("text-sm text-muted-foreground", className)}>Sin identidades registradas.</p>
    );
  }

  return (
    <ul className={cn("flex flex-col gap-2", className)} role="list">
      {identities.map((identity, i) => (
        <li
          key={`${identity.type}-${identity.value}-${i}`}
          className="flex items-center gap-2 text-sm"
        >
          {TYPE_ICONS[identity.type] ?? (
            <span className="h-4 w-4 shrink-0 text-muted-foreground text-xs">
              {identity.type[0]?.toUpperCase()}
            </span>
          )}
          <span className="flex-1 truncate">{identity.value}</span>
          {identity.is_primary && (
            <Star className="h-3 w-3 text-amber-500 shrink-0" aria-label="primaria" />
          )}
          <VerificationIcon status={identity.verification_status} />
        </li>
      ))}
    </ul>
  );
}
