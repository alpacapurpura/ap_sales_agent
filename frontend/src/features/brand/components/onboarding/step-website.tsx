"use client";

import { Globe, ArrowRight, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface StepWebsiteProps {
  url: string;
  onUrlChange: (url: string) => void;
  onNext: () => void;
  onBack: () => void;
}

export function StepWebsite({ url, onUrlChange, onNext, onBack }: StepWebsiteProps) {
  const isValidUrl = url.length > 0 && (url.startsWith("http://") || url.startsWith("https://"));

  return (
    <div className="mx-auto max-w-lg animate-in fade-in slide-in-from-right-4 duration-300">
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
          <Globe className="h-6 w-6 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">¿Cuál es tu sitio web?</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Escanearemos tu sitio para extraer tu identidad, historia, equipo y más.
        </p>
      </div>

      <div className="space-y-4">
        <Input
          type="url"
          placeholder="https://tumarca.com"
          value={url}
          onChange={(e) => onUrlChange(e.target.value)}
          className="h-12 text-base"
          autoFocus
        />
        <p className="text-xs text-muted-foreground">
          Incluye https:// — escanearemos las páginas principales automáticamente.
        </p>
      </div>

      <div className="mt-8 flex justify-between">
        <Button variant="ghost" onClick={onBack} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Atrás
        </Button>
        <Button onClick={onNext} disabled={!isValidUrl} className="gap-2">
          Continuar
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
