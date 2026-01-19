"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { AvatarForm } from "@/components/avatars/avatar-form";
import { avatarApi, CreateAvatarDTO } from "@/lib/api/avatar";
import { Button } from "@/components/ui/button";
import { ChevronLeft, Loader2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export default function EditAvatarPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: avatar, isLoading, isError } = useQuery({
    queryKey: ["avatar", id],
    queryFn: () => avatarApi.getAvatar(id),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<CreateAvatarDTO>) => avatarApi.updateAvatar(id, data),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["avatars"] });
        queryClient.invalidateQueries({ queryKey: ["avatar", id] });
        router.push("/avatars");
    },
    onError: (err) => {
        console.error(err);
        alert("Error al actualizar");
    }
  });

  if (isLoading) {
    return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>;
  }

  if (isError || !avatar) {
    return <div className="p-8 text-red-500">Avatar no encontrado.</div>;
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Editar Avatar</h1>
          <p className="text-muted-foreground">Modifica la configuración de {avatar.name}.</p>
        </div>
      </div>

      <AvatarForm 
        initialData={avatar} 
        onSubmit={async (data) => updateMutation.mutate(data)} 
        isSubmitting={updateMutation.isPending} 
      />
    </div>
  );
}
