"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface PlatformSubdomainProps {
  tenantSlug: string;
  className?: string;
}

export function PlatformSubdomain({ tenantSlug, className }: PlatformSubdomainProps) {
  const [copied, setCopied] = useState(false);
  const hostname = `${tenantSlug}.nicolify.com`;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(hostname);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className={cn("p-4", className)}>
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-muted-foreground">Tu dominio de plataforma</p>
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-semibold">{hostname}</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={handleCopy}
            aria-label="Copiar dominio"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-green-500" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">Para usar un dominio propio, añádelo abajo.</p>
      </div>
    </Card>
  );
}
