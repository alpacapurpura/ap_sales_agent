"use client";

import { Check, Loader2 } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { cn } from "@/lib/utils";

import { useBuyerPersona } from "../../hooks/useBuyerPersona";

import type { BuyerPersona, BuyerPersonaSectionUpdateDTO } from "@/lib/api/buyer-persona";

// ---------------------------------------------------------------------------
// Section config
// ---------------------------------------------------------------------------

const SECTIONS = [
  {
    id: "demographics",
    label: "Demografía",
  },
  {
    id: "pain_desire",
    label: "Dolores & Deseos",
  },
  {
    id: "psychographics",
    label: "Psicografía",
  },
  {
    id: "objections",
    label: "Objeciones",
  },
  {
    id: "channels_journey",
    label: "Canales & Journey",
  },
] as const;

type SectionId = (typeof SECTIONS)[number]["id"];

// ---------------------------------------------------------------------------
// Save indicator
// ---------------------------------------------------------------------------

interface SaveIndicatorProps {
  isSaving: boolean;
  savedAt: Date | null;
}

function SaveIndicator({ isSaving, savedAt }: SaveIndicatorProps) {
  if (isSaving) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        Guardando...
      </span>
    );
  }
  if (savedAt) {
    return (
      <span className="flex items-center gap-1 text-xs text-green-600">
        <Check className="h-3 w-3" />
        Guardado
      </span>
    );
  }
  return null;
}

// ---------------------------------------------------------------------------
// Loading skeleton
// ---------------------------------------------------------------------------

function LoadingSkeleton() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-20" />
      </div>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-56 shrink-0 border-r border-border/50 p-4">
          <div className="flex flex-col items-center gap-2 mb-6 pt-2">
            <Skeleton className="h-16 w-16 rounded-full" />
            <Skeleton className="h-4 w-28" />
          </div>
          <div className="space-y-2">
            {SECTIONS.map((s) => (
              <Skeleton key={s.id} className="h-8 w-full rounded-lg" />
            ))}
          </div>
        </aside>
        <main className="flex-1 p-8 space-y-6">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </main>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Not found
// ---------------------------------------------------------------------------

function NotFound() {
  const router = useRouter();
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <p className="text-muted-foreground">Persona no encontrada.</p>
      <button
        type="button"
        onClick={() => router.back()}
        className="text-sm text-primary underline-offset-4 hover:underline"
      >
        Volver
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Demographics section
// ---------------------------------------------------------------------------

interface DemographicsProps {
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

const DEMOGRAPHIC_FIELDS: { key: string; label: string }[] = [
  { key: "age_range", label: "Rango de edad" },
  { key: "location", label: "Ubicación" },
  { key: "occupation", label: "Ocupación" },
  { key: "income_range", label: "Rango de ingresos" },
  { key: "education", label: "Educación" },
];

function DemographicsSection({ persona, onSave }: DemographicsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Demografía</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Datos básicos sobre quién es esta persona.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {DEMOGRAPHIC_FIELDS.map(({ key, label }) => {
          const currentValue = safeStr(persona.demographics[key]);
          return (
            <div key={key} className="space-y-2">
              <label htmlFor={`demo-${key}`} className="text-sm font-medium">
                {label}
              </label>
              <WithCopilot
                fieldId={`persona_demographics_${key}`}
                fieldLabel={label}
                getValue={() => currentValue}
              >
                <Input
                  id={`demo-${key}`}
                  defaultValue={currentValue}
                  placeholder={label}
                  onChange={(e) => {
                    onSave({
                      demographics: {
                        ...persona.demographics,
                        [key]: e.target.value,
                      },
                    });
                  }}
                />
              </WithCopilot>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pain & Desire section
// ---------------------------------------------------------------------------

interface PainDesireProps {
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

function safeStr(value: unknown): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

function objectArrayToText(arr: Record<string, unknown>[]): string {
  return arr
    .map((item) => (typeof item.text === "string" ? item.text : JSON.stringify(item)))
    .join("\n");
}

function textToObjectArray(text: string): Record<string, unknown>[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => ({ text: line }));
}

function PainDesireSection({ persona, onSave }: PainDesireProps) {
  const painText = objectArrayToText(persona.pain_points);
  const desiresText = objectArrayToText(persona.desires);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Dolores & Deseos</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Qué le duele y qué quiere lograr esta persona.
        </p>
      </div>
      <div className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="pain-points" className="text-sm font-medium">
            Dolores principales
          </label>
          <p className="text-xs text-muted-foreground">Un ítem por línea.</p>
          <WithCopilot
            fieldId="persona_pain_desire_pain_points"
            fieldLabel="Dolores principales"
            getValue={() => painText}
          >
            <Textarea
              id="pain-points"
              defaultValue={painText}
              placeholder="Ej: No tiene tiempo para hacer marketing..."
              rows={5}
              onChange={(e) => {
                onSave({ pain_points: textToObjectArray(e.target.value) });
              }}
            />
          </WithCopilot>
        </div>
        <div className="space-y-2">
          <label htmlFor="desires" className="text-sm font-medium">
            Deseos & aspiraciones
          </label>
          <p className="text-xs text-muted-foreground">Un ítem por línea.</p>
          <WithCopilot
            fieldId="persona_pain_desire_desires"
            fieldLabel="Deseos & aspiraciones"
            getValue={() => desiresText}
          >
            <Textarea
              id="desires"
              defaultValue={desiresText}
              placeholder="Ej: Quiere hacer crecer su negocio sin trabajar más horas..."
              rows={5}
              onChange={(e) => {
                onSave({ desires: textToObjectArray(e.target.value) });
              }}
            />
          </WithCopilot>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Psychographics section
// ---------------------------------------------------------------------------

interface PsychographicsProps {
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

const PSYCHOGRAPHIC_FIELDS: { key: string; label: string }[] = [
  { key: "values", label: "Valores" },
  { key: "beliefs", label: "Creencias" },
  { key: "lifestyle", label: "Estilo de vida" },
  { key: "media_consumption", label: "Consumo de medios" },
];

function PsychographicsSection({ persona, onSave }: PsychographicsProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Psicografía</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Valores, creencias y comportamientos de esta persona.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {PSYCHOGRAPHIC_FIELDS.map(({ key, label }) => {
          const currentValue = safeStr(persona.psychographics[key]);
          return (
            <div key={key} className="space-y-2">
              <label htmlFor={`psycho-${key}`} className="text-sm font-medium">
                {label}
              </label>
              <WithCopilot
                fieldId={`persona_psychographics_${key}`}
                fieldLabel={label}
                getValue={() => currentValue}
              >
                <Textarea
                  id={`psycho-${key}`}
                  defaultValue={currentValue}
                  placeholder={label}
                  rows={3}
                  onChange={(e) => {
                    onSave({
                      psychographics: {
                        ...persona.psychographics,
                        [key]: e.target.value,
                      },
                    });
                  }}
                />
              </WithCopilot>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Objections section
// ---------------------------------------------------------------------------

interface ObjectionsProps {
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

function ObjectionsSection({ persona, onSave }: ObjectionsProps) {
  const objectionsText = objectArrayToText(persona.objections);
  const triggersText = persona.purchase_triggers.join("\n");
  const antiPatternsText = persona.anti_patterns.join("\n");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Objeciones</h2>
        <p className="text-sm text-muted-foreground mt-1">Qué frena la compra y qué la activa.</p>
      </div>
      <div className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="objections" className="text-sm font-medium">
            Objeciones de compra
          </label>
          <p className="text-xs text-muted-foreground">Un ítem por línea.</p>
          <WithCopilot
            fieldId="persona_objections_objections"
            fieldLabel="Objeciones de compra"
            getValue={() => objectionsText}
          >
            <Textarea
              id="objections"
              defaultValue={objectionsText}
              placeholder="Ej: Es muy caro para lo que ofrece..."
              rows={4}
              onChange={(e) => {
                onSave({ objections: textToObjectArray(e.target.value) });
              }}
            />
          </WithCopilot>
        </div>
        <div className="space-y-2">
          <label htmlFor="purchase-triggers" className="text-sm font-medium">
            Disparadores de compra
          </label>
          <p className="text-xs text-muted-foreground">Un ítem por línea.</p>
          <WithCopilot
            fieldId="persona_objections_purchase_triggers"
            fieldLabel="Disparadores de compra"
            getValue={() => triggersText}
          >
            <Textarea
              id="purchase-triggers"
              defaultValue={triggersText}
              placeholder="Ej: Ver prueba social de alguien similar..."
              rows={4}
              onChange={(e) => {
                const lines = e.target.value
                  .split("\n")
                  .map((l) => l.trim())
                  .filter(Boolean);
                onSave({ purchase_triggers: lines });
              }}
            />
          </WithCopilot>
        </div>
        <div className="space-y-2">
          <label htmlFor="anti-patterns" className="text-sm font-medium">
            Antipatrones (qué la aleja)
          </label>
          <p className="text-xs text-muted-foreground">Un ítem por línea.</p>
          <WithCopilot
            fieldId="persona_objections_anti_patterns"
            fieldLabel="Antipatrones"
            getValue={() => antiPatternsText}
          >
            <Textarea
              id="anti-patterns"
              defaultValue={antiPatternsText}
              placeholder="Ej: Mensajes demasiado técnicos o complicados..."
              rows={4}
              onChange={(e) => {
                const lines = e.target.value
                  .split("\n")
                  .map((l) => l.trim())
                  .filter(Boolean);
                onSave({ anti_patterns: lines });
              }}
            />
          </WithCopilot>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Channels & Journey section
// ---------------------------------------------------------------------------

interface ChannelsJourneyProps {
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

const JOURNEY_KEYS: { key: string; label: string }[] = [
  { key: "awareness", label: "Conciencia (Awareness)" },
  { key: "consideration", label: "Consideración" },
  { key: "decision", label: "Decisión" },
];

function ChannelsJourneySection({ persona, onSave }: ChannelsJourneyProps) {
  const channelsText = persona.preferred_channels
    .map((ch) => {
      if (typeof ch.name === "string") return ch.name;
      return JSON.stringify(ch);
    })
    .join("\n");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Canales & Journey</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Dónde está y cómo recorre el camino hacia la compra.
        </p>
      </div>
      <div className="space-y-6">
        <div className="space-y-2">
          <label htmlFor="preferred-channels" className="text-sm font-medium">
            Canales preferidos
          </label>
          <p className="text-xs text-muted-foreground">Un canal por línea.</p>
          <WithCopilot
            fieldId="persona_channels_preferred_channels"
            fieldLabel="Canales preferidos"
            getValue={() => channelsText}
          >
            <Textarea
              id="preferred-channels"
              defaultValue={channelsText}
              placeholder="Ej: Instagram&#10;YouTube&#10;WhatsApp"
              rows={4}
              onChange={(e) => {
                const channels = e.target.value
                  .split("\n")
                  .map((l) => l.trim())
                  .filter(Boolean)
                  .map((name) => ({ name }));
                onSave({ preferred_channels: channels });
              }}
            />
          </WithCopilot>
        </div>
        {JOURNEY_KEYS.map(({ key, label }) => {
          const currentValue = safeStr(persona.buyer_journey[key]);
          return (
            <div key={key} className="space-y-2">
              <label htmlFor={`journey-${key}`} className="text-sm font-medium">
                {label}
              </label>
              <WithCopilot
                fieldId={`persona_channels_journey_${key}`}
                fieldLabel={label}
                getValue={() => currentValue}
              >
                <Textarea
                  id={`journey-${key}`}
                  defaultValue={currentValue}
                  placeholder={`Describe la etapa de ${label.toLowerCase()}...`}
                  rows={3}
                  onChange={(e) => {
                    onSave({
                      buyer_journey: {
                        ...persona.buyer_journey,
                        [key]: e.target.value,
                      },
                    });
                  }}
                />
              </WithCopilot>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section content dispatcher
// ---------------------------------------------------------------------------

interface SectionContentProps {
  section: SectionId;
  persona: BuyerPersona;
  onSave: (updates: BuyerPersonaSectionUpdateDTO, delayMs?: number) => void;
}

function SectionContent({ section, persona, onSave }: SectionContentProps) {
  switch (section) {
    case "demographics":
      return <DemographicsSection persona={persona} onSave={onSave} />;
    case "pain_desire":
      return <PainDesireSection persona={persona} onSave={onSave} />;
    case "psychographics":
      return <PsychographicsSection persona={persona} onSave={onSave} />;
    case "objections":
      return <ObjectionsSection persona={persona} onSave={onSave} />;
    case "channels_journey":
      return <ChannelsJourneySection persona={persona} onSave={onSave} />;
    default:
      return null;
  }
}

// ---------------------------------------------------------------------------
// Main view
// ---------------------------------------------------------------------------

interface PersonaDetailViewProps {
  personaId: string;
}

export function PersonaDetailView({ personaId }: PersonaDetailViewProps) {
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const { persona, isLoading, isSaving, savedAt, debouncedSave } = useBuyerPersona(
    tenantId,
    personaId,
  );
  const [activeSection, setActiveSection] = useState<SectionId>("demographics");

  if (isLoading) return <LoadingSkeleton />;
  if (!persona) return <NotFound />;

  return (
    <div className="flex h-full flex-col">
      {/* Topbar */}
      <div className="flex items-center justify-between border-b border-border/50 px-6 py-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <button
            type="button"
            onClick={() => router.push(`/${tenantId}/brand-studio/publico`)}
            className="transition-colors hover:text-foreground"
          >
            Buyer Personas
          </button>
          <span>/</span>
          <span className="font-medium text-foreground">{persona.name}</span>
        </div>
        <SaveIndicator isSaving={isSaving} savedAt={savedAt} />
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left nav */}
        <aside className="w-56 shrink-0 overflow-y-auto border-r border-border/50 p-4">
          {/* Mini profile */}
          <div className="mb-6 flex flex-col items-center pt-2">
            <Avatar className="mb-2 h-16 w-16">
              <AvatarFallback className="bg-gradient-to-br from-purple-500 to-indigo-600 text-lg font-bold text-white">
                {persona.name.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <p className="text-center text-sm font-semibold">{persona.name}</p>
            {persona.tagline && (
              <p className="mt-1 text-center text-xs text-muted-foreground">{persona.tagline}</p>
            )}
          </div>

          {/* Section nav */}
          <nav className="space-y-1">
            {SECTIONS.map((section) => (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveSection(section.id)}
                className={cn(
                  "w-full rounded-lg px-3 py-2 text-left text-sm transition-colors",
                  activeSection === section.id
                    ? "bg-primary/10 font-medium text-primary"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
                )}
              >
                {section.label}
              </button>
            ))}
          </nav>

          {/* Completeness */}
          <div className="mt-6 border-t border-border/50 pt-4">
            <div className="mb-1 flex justify-between text-xs text-muted-foreground">
              <span>Completitud</span>
              <span>{Math.round(persona.completeness_score)}%</span>
            </div>
            <Progress value={persona.completeness_score} className="h-1.5" />
          </div>
        </aside>

        {/* Form area */}
        <main className="flex-1 overflow-y-auto p-8">
          <SectionContent section={activeSection} persona={persona} onSave={debouncedSave} />
        </main>
      </div>
    </div>
  );
}
