"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Loader2, PenLine, Sparkles, Users } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useState } from "react";

import { PageContainer } from "@/components/shared/layout/PageContainer";
import { useNavigation } from "@/components/shared/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { startInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { buyerPersonaApi } from "@/lib/api/buyer-persona";

import { BuyerPersonaCard } from "./BuyerPersonaCard";

import type { BuyerPersona } from "@/lib/api/buyer-persona";

const SKELETON_COUNT = 3;
const DEFAULT_PERSONA_NAME = "Nueva persona";

type CreationMode = "manual" | "interview";

async function activateInterview(token: string, personaId: string, personaName: string) {
  try {
    const interview = await startInterview(token, "buyer_persona", personaId);
    const store = useCopilotStore.getState();
    store.setSession({
      sectionKey: "brand.buyer-persona",
      label: personaName,
      entityId: personaId,
      procedure: "interview",
      sessionId: interview.session_id,
      startedAt: new Date(),
      snapshot: {},
    });
    store.setConversationId(interview.conversation_id);
    store.addMessage({
      id: crypto.randomUUID(),
      role: "assistant",
      content: interview.initial_message,
      timestamp: Date.now(),
    });
    store.setSidebarState("open");
  } catch (err) {
    console.error("Failed to start buyer persona interview", err);
  }
}

function nextDefaultName(currentCount: number): string {
  return currentCount === 0 ? DEFAULT_PERSONA_NAME : `${DEFAULT_PERSONA_NAME} ${currentCount + 1}`;
}

/** Buyer personas index — lists existing personas and exposes Modo Manual / Modo Inteligente create flows. */
export function BuyerPersonasDashboard() {
  const { getToken } = useAuth();
  const { navigate } = useNavigation();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  const [creating, setCreating] = useState<CreationMode | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useQuery<BuyerPersona[]>({
    queryKey: ["buyer_personas", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return buyerPersonaApi.list(token);
    },
  });

  const personas = data ?? [];

  const handleNavigate = useCallback(
    (personaId: string) => {
      navigate(`/${tenantId}/brand-studio/publico/persona/${personaId}`);
    },
    [navigate, tenantId],
  );

  const handleCreate = useCallback(
    async (mode: CreationMode) => {
      if (creating) return;
      setCreating(mode);
      setCreateError(null);
      try {
        const token = await getToken();
        if (!token) throw new Error("No auth token");
        const persona = await buyerPersonaApi.create(token, {
          name: nextDefaultName(personas.length),
          scope: "GLOBAL",
        });
        if (mode === "interview") {
          await activateInterview(token, persona.id, persona.name);
        }
        handleNavigate(persona.id);
      } catch (err) {
        console.error("Failed to create buyer persona", err);
        setCreateError("No se pudo crear la buyer persona. Intenta de nuevo.");
      } finally {
        setCreating(null);
      }
    },
    [creating, getToken, handleNavigate, personas.length],
  );

  const handleRefetch = useCallback(() => {
    void refetch();
  }, [refetch]);

  if (isLoading) {
    return <DashboardLoadingState onCreate={handleCreate} creating={creating} />;
  }

  if (error) {
    return (
      <DashboardErrorState onCreate={handleCreate} creating={creating} onRetry={handleRefetch} />
    );
  }

  return (
    <PageContainer className="space-y-6">
      <DashboardHeader onCreate={handleCreate} creating={creating} />
      {createError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{createError}</AlertDescription>
        </Alert>
      )}
      {personas.length === 0 ? (
        <EmptyState onCreate={handleCreate} creating={creating} />
      ) : (
        <PersonaGrid personas={personas} onNavigate={handleNavigate} />
      )}
    </PageContainer>
  );
}

interface ActionsProps {
  readonly onCreate: (mode: CreationMode) => void;
  readonly creating: CreationMode | null;
  readonly disabled?: boolean;
}

function DashboardHeader({ onCreate, creating, disabled = false }: ActionsProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Buyer personas</h1>
        <p className="text-sm text-muted-foreground">
          Perfiles arquetípicos que tu SDR usa para segmentar y personalizar mensajes.
        </p>
      </div>
      <CreateActions onCreate={onCreate} creating={creating} disabled={disabled} />
    </div>
  );
}

function CreateActions({ onCreate, creating, disabled = false }: ActionsProps) {
  const handleManual = useCallback(() => onCreate("manual"), [onCreate]);
  const handleInterview = useCallback(() => onCreate("interview"), [onCreate]);
  const isDisabled = disabled || Boolean(creating);
  return (
    <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto">
      <Button variant="outline" disabled={isDisabled} onClick={handleManual} className="gap-2">
        {creating === "manual" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <PenLine className="h-4 w-4" />
        )}
        Modo Manual
      </Button>
      <Button disabled={isDisabled} onClick={handleInterview} className="gap-2">
        {creating === "interview" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Sparkles className="h-4 w-4" />
        )}
        Modo Inteligente
      </Button>
    </div>
  );
}

function EmptyState({ onCreate, creating }: Omit<ActionsProps, "disabled">) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
        <Users className="h-7 w-7 text-muted-foreground" />
      </div>
      <div className="space-y-1">
        <h3 className="text-lg font-semibold">Sin Buyer Personas</h3>
        <p className="max-w-md text-sm text-muted-foreground">
          Construye un perfil arquetípico con la entrevista guiada o crea uno a mano y edítalo campo
          por campo.
        </p>
      </div>
      <CreateActions onCreate={onCreate} creating={creating} />
    </div>
  );
}

interface PersonaGridProps {
  readonly personas: readonly BuyerPersona[];
  readonly onNavigate: (personaId: string) => void;
}

function PersonaGrid({ personas, onNavigate }: PersonaGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {personas.map((persona) => (
        <PersonaGridItem key={persona.id} persona={persona} onNavigate={onNavigate} />
      ))}
    </div>
  );
}

function PersonaGridItem({
  persona,
  onNavigate,
}: {
  readonly persona: BuyerPersona;
  readonly onNavigate: (personaId: string) => void;
}) {
  const handleClick = useCallback(() => onNavigate(persona.id), [onNavigate, persona.id]);
  return <BuyerPersonaCard persona={persona} onClick={handleClick} />;
}

function DashboardLoadingState({ onCreate, creating }: Omit<ActionsProps, "disabled">) {
  return (
    <PageContainer className="space-y-6">
      <DashboardHeader onCreate={onCreate} creating={creating} disabled />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: SKELETON_COUNT }).map((_, index) => (
          <Skeleton
            key={index}
            data-testid="persona-skeleton"
            className="h-[168px] w-full rounded-xl"
          />
        ))}
      </div>
    </PageContainer>
  );
}

function DashboardErrorState({
  onCreate,
  creating,
  onRetry,
}: Omit<ActionsProps, "disabled"> & { readonly onRetry: () => void }) {
  return (
    <PageContainer className="space-y-6">
      <DashboardHeader onCreate={onCreate} creating={creating} />
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription className="flex items-center gap-4">
          No se pudieron cargar las buyer personas.
          <Button variant="outline" size="sm" onClick={onRetry}>
            Reintentar
          </Button>
        </AlertDescription>
      </Alert>
    </PageContainer>
  );
}
