"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Loader2, Sparkles, Users } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback } from "react";

import { PageContainer } from "@/components/shared/layout/PageContainer";
import { useNavigation } from "@/components/shared/navigation";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useGuidedEntityCreation } from "@/features/copilot/hooks/use-guided-entity-creation";
import { buyerPersonaApi, type BuyerPersona } from "@/lib/api/buyer-persona";

import { BuyerPersonaCard } from "./BuyerPersonaCard";

const SKELETON_COUNT = 3;
const DEFAULT_PERSONA_NAME = "Nueva persona";

function nextDefaultName(currentCount: number): string {
  return currentCount === 0 ? DEFAULT_PERSONA_NAME : `${DEFAULT_PERSONA_NAME} ${currentCount + 1}`;
}

/** Buyer personas index — lists existing personas and exposes the AI-led create flow. */
export function BuyerPersonasDashboard() {
  const { getToken } = useAuth();
  const { navigate } = useNavigation();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";

  const { data, isLoading, error, refetch } = useQuery<BuyerPersona[]>({
    queryKey: ["buyer_personas", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return buyerPersonaApi.list(token);
    },
  });

  const personas = data ?? [];

  const {
    create,
    creating,
    error: createError,
  } = useGuidedEntityCreation<BuyerPersona>({
    domain: "buyer_persona",
    tenantId,
    createEntity: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return buyerPersonaApi.create(token, {
        name: nextDefaultName(personas.length),
        scope: "GLOBAL",
      });
    },
  });

  const handleNavigate = useCallback(
    (personaId: string) => {
      navigate(`/${tenantId}/brand-studio/publico/persona/${personaId}`);
    },
    [navigate, tenantId],
  );

  const handleRefetch = useCallback(() => {
    void refetch();
  }, [refetch]);

  if (isLoading) {
    return <DashboardLoadingState onCreate={create} creating={creating} />;
  }

  if (error) {
    return <DashboardErrorState onCreate={create} creating={creating} onRetry={handleRefetch} />;
  }

  return (
    <PageContainer className="space-y-6">
      <DashboardHeader onCreate={create} creating={creating} />
      {createError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{createError}</AlertDescription>
        </Alert>
      )}
      {personas.length === 0 ? (
        <EmptyState onCreate={create} creating={creating} />
      ) : (
        <PersonaGrid personas={personas} onNavigate={handleNavigate} />
      )}
    </PageContainer>
  );
}

interface ActionsProps {
  readonly onCreate: () => void;
  readonly creating: boolean;
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
      <CreateAction onCreate={onCreate} creating={creating} disabled={disabled} />
    </div>
  );
}

function CreateAction({ onCreate, creating, disabled = false }: ActionsProps) {
  const isDisabled = disabled || creating;
  return (
    <Button disabled={isDisabled} onClick={onCreate} className="gap-2 self-start sm:self-auto">
      {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
      Crear nueva persona
    </Button>
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
          El copilot te entrevista, lee la URL o el documento que le pases y arma un perfil
          completo. Tú revisas y ajustas.
        </p>
      </div>
      <CreateAction onCreate={onCreate} creating={creating} />
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
