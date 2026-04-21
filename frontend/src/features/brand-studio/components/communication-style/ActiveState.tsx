"use client";

import { Bot, ChevronDown, Image, Layout } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { DimensionsPanel } from "./DimensionsPanel";
import { FingerprintPanel } from "./FingerprintPanel";
import { SampleExchangesPanel } from "./SampleExchangesPanel";
import { SimulateDrawer } from "./SimulateDrawer";

import type { PersonalityProfile } from "@/features/brand-studio/types/personality";

const PROFILE_TYPE_LABELS: Record<PersonalityProfile["profile_type"], string> = {
  preset: "preset",
  cloned: "clonado",
  interview: "entrevista",
  manual: "manual",
  migrated_from_voice_tone: "migrado",
};

function getProfileIcon(profile: PersonalityProfile): string {
  if (profile.profile_type === "cloned") return "🧬";
  if (profile.profile_type === "migrated_from_voice_tone") return "✨";
  return "🌟";
}

interface ActiveStateProps {
  profile: PersonalityProfile;
}

/**
 * Active personality profile view. Shows the profile header with name, badges
 * and "Cambiar estilo" dropdown, plus the three main panels: dimensions,
 * linguistic fingerprint and sample exchanges. Footer CTAs open the simulate
 * drawer and the compiled system instruction modal.
 */
export function ActiveState({ profile }: ActiveStateProps) {
  const params = useParams<{ tenantId: string }>();
  const { tenantId } = params;

  const [simulateOpen, setSimulateOpen] = useState(false);
  const [instructionOpen, setInstructionOpen] = useState(false);

  const typeLabel = PROFILE_TYPE_LABELS[profile.profile_type];
  const icon = getProfileIcon(profile);

  const updatedDate = new Date(profile.updated_at).toLocaleDateString("es-MX", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Profile header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-muted text-2xl">
            {icon}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-base font-semibold text-foreground">{profile.name}</p>
              <Badge variant="secondary" className="text-xs">
                {typeLabel}
              </Badge>
              <Badge
                variant="outline"
                className="border-green-200 bg-green-50 text-xs text-green-700 dark:border-green-900/40 dark:bg-green-950/20 dark:text-green-400"
              >
                activo
              </Badge>
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">Actualizado el {updatedDate}</p>
          </div>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              aria-label="Cambiar estilo comunicacional"
            >
              Cambiar estilo
              <ChevronDown className="h-3.5 w-3.5" aria-hidden />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
            <DropdownMenuItem asChild>
              <Link href={`/${tenantId}/brand-studio/estilo?view=preset`}>Elegir otro preset</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={`/${tenantId}/brand-studio/estilo?view=clone`}>
                Clonar un estilo nuevo
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem disabled aria-label="Perfil desde cero (próximamente)">
              Perfil desde cero
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Dimensions */}
      <DimensionsPanel profileId={profile.id} dimensions={profile.dimensions} />

      {/* Linguistic fingerprint */}
      <div className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Huella lingüística
        </p>
        <FingerprintPanel patterns={profile.linguistic_patterns} />
      </div>

      {/* Sample exchanges */}
      <SampleExchangesPanel profileId={profile.id} initialExchanges={profile.sample_exchanges} />

      {/* Actions footer */}
      <div className="flex flex-wrap gap-3 border-t border-border pt-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSimulateOpen(true)}
          aria-label="Probar el estilo en una conversación simulada"
        >
          Probar en conversación →
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setInstructionOpen(true)}
          aria-label="Ver la instrucción del sistema compilada"
        >
          Ver instrucción compilada
        </Button>
      </div>

      {/* Downstream note */}
      <div className="flex flex-wrap gap-4 rounded-lg border border-border bg-muted/30 px-4 py-3">
        <p className="w-full text-xs font-medium text-muted-foreground">Este estilo se usa en:</p>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Bot className="h-3.5 w-3.5" aria-hidden />
          <span>SDR (agente de ventas)</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Layout className="h-3.5 w-3.5" aria-hidden />
          <span>Copy de landings</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Image className="h-3.5 w-3.5" aria-hidden />
          <span>Captions de assets</span>
        </div>
      </div>

      {/* Simulate drawer */}
      <SimulateDrawer
        profileId={profile.id}
        profileName={profile.name}
        open={simulateOpen}
        onOpenChange={setSimulateOpen}
      />

      {/* Compiled instruction modal */}
      <Dialog open={instructionOpen} onOpenChange={setInstructionOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-base">Instrucción compilada</DialogTitle>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-auto rounded-lg border border-border bg-muted/30 p-4">
            <pre className="whitespace-pre-wrap text-xs text-foreground/80">
              {profile.system_instruction ?? "(sin instrucción compilada aún)"}
            </pre>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
