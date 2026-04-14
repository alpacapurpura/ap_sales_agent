"use client";

import { useNavigation } from "@/components/shared/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { avatarApi, CreateAvatarDTO } from "@/lib/api/avatar";
import { AvatarForm } from "@/features/brand/sections/avatars/avatar-form";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface AvatarEditViewProps {
  avatarId: string;
  callbackUrl: string | null;
}

export function AvatarEditView({ avatarId, callbackUrl }: AvatarEditViewProps) {
  const { navigate } = useNavigation();
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const {
    data: avatar,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["avatar", avatarId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.getAvatar(token, avatarId);
    },
    enabled: !!avatarId,
  });

  const updateMutation = useMutation({
    mutationFn: async (data: CreateAvatarDTO) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.updateAvatar(token, avatarId, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      queryClient.invalidateQueries({ queryKey: ["avatar", avatarId] });
      toast.success("Avatar actualizado exitosamente");

      if (callbackUrl) {
        navigate(callbackUrl);
      } else {
        window.history.back();
      }
    },
    onError: () => toast.error("Error al actualizar el avatar"),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-muted-foreground">Cargando avatar...</p>
      </div>
    );
  }

  if (isError || !avatar) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] gap-4">
        <h2 className="text-xl font-semibold text-destructive">Error al cargar el avatar</h2>
        <p className="text-muted-foreground">
          No se pudo encontrar el avatar solicitado o no tienes permisos.
        </p>
        <Button
          onClick={() => (callbackUrl ? navigate(callbackUrl) : window.history.back())}
          variant="outline"
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Volver
        </Button>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => (callbackUrl ? navigate(callbackUrl) : window.history.back())}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Editar Avatar</h1>
          <p className="text-muted-foreground">
            Modifica los detalles psicográficos de tu cliente ideal.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{avatar.name}</CardTitle>
          <CardDescription>
            Editando identidad {avatar.scope === "GLOBAL" ? "Global" : "Específica"}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AvatarForm
            initialData={avatar}
            onSubmit={async (data) => {
              await updateMutation.mutateAsync(data);
            }}
            isSubmitting={updateMutation.isPending}
            embedded={true}
          />
        </CardContent>
      </Card>
    </div>
  );
}
