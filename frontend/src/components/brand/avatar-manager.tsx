"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { Plus, Users, Star, Edit, Trash2, CheckCircle2, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { avatarApi, Avatar, CreateAvatarDTO } from "@/lib/api/avatar";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AvatarForm } from "@/components/avatars/avatar-form";

export function AvatarManager() {
  const queryClient = useQueryClient();
  const { getToken } = useAuth();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAvatar, setEditingAvatar] = useState<Avatar | null>(null);

  const { data: avatars, isLoading, isError } = useQuery({
    queryKey: ["avatars"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.listAvatars(token, "GLOBAL");
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: CreateAvatarDTO) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.createAvatar(token, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      setIsDialogOpen(false);
      toast.success("Avatar creado exitosamente");
    },
    onError: () => toast.error("Error al crear el avatar"),
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CreateAvatarDTO> }) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.updateAvatar(token, id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      setIsDialogOpen(false);
      toast.success("Avatar actualizado exitosamente");
    },
    onError: () => toast.error("Error al actualizar el avatar"),
  });

  const setDefaultMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.setDefault(token, id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      toast.success("Avatar principal actualizado");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return avatarApi.deleteAvatar(token, id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      toast.success("Avatar eliminado");
    },
  });

  const handleOpenNew = () => {
    setEditingAvatar(null);
    setIsDialogOpen(true);
  };

  const handleOpenEdit = (avatar: Avatar) => {
    setEditingAvatar(avatar);
    setIsDialogOpen(true);
  };

  const handleFormSubmit = async (data: CreateAvatarDTO) => {
    if (editingAvatar) {
      await updateMutation.mutateAsync({ id: editingAvatar.id, data });
    } else {
      await createMutation.mutateAsync(data);
    }
  };

  if (isLoading) {
    return (
      <Card className="w-full min-h-[600px]">
        <CardHeader>
           <CardTitle>Avatares de Marca</CardTitle>
           <CardDescription>Gestiona las diferentes identidades y perfiles de cliente ideal.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
            <div className="flex justify-between">
                <Skeleton className="h-8 w-48" />
                <Skeleton className="h-10 w-32" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Skeleton className="h-64" />
                <Skeleton className="h-64" />
                <Skeleton className="h-64" />
            </div>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="w-full min-h-[600px]">
         <CardHeader>
           <CardTitle>Avatares de Marca</CardTitle>
         </CardHeader>
         <CardContent>
            <div className="p-8 text-red-500">Error al cargar los avatares.</div>
         </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="w-full min-h-[600px]">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-6 w-6 " />
              Avatares de Marca
            </CardTitle>
            <CardDescription className="mt-1.5">Gestiona las diferentes identidades y perfiles de cliente ideal.</CardDescription>
          </div>
          <Button onClick={handleOpenNew} className="gap-2">
            <Plus className="h-4 w-4" /> Nuevo
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
              {avatars?.map((avatar) => (
              <Card key={avatar.id} className={`relative flex flex-col ${avatar.is_default ? "border-primary shadow-md" : ""}`}>
                  {avatar.is_default && (
                  <div className="absolute top-0 right-0 p-2">
                      <Badge variant="default" className="gap-1">
                          <Star className="h-3 w-3 fill-current" /> Principal
                      </Badge>
                  </div>
                  )}
                  <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                      <Users className="h-5 w-5 text-muted-foreground" />
                      {avatar.name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2 min-h-[40px]">
                      {avatar.icp_description || "Sin descripción definida."}
                  </CardDescription>
                  </CardHeader>
                  <CardContent className="flex-grow">
                  <div className="text-sm text-muted-foreground">
                      <span className="font-semibold text-foreground">Anti-Avatar:</span>{" "}
                      {avatar.anti_avatar ? (
                          <span className="line-clamp-2">{avatar.anti_avatar}</span>
                      ) : (
                          <span className="italic">No configurado</span>
                      )}
                  </div>
                  </CardContent>
                  <CardFooter className="border-t pt-4 flex justify-between gap-2">
                      {!avatar.is_default ? (
                          <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => setDefaultMutation.mutate(avatar.id)}
                              disabled={setDefaultMutation.isPending}
                          >
                              {setDefaultMutation.isPending ? <CheckCircle2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                              Hacer Principal
                          </Button>
                      ) : (
                          <div className="text-sm font-medium text-primary flex items-center px-3">
                              Seleccionado por defecto
                          </div>
                      )}
                      
                      <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="icon"
                            onClick={() => handleOpenEdit(avatar)}
                          >
                              <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                              variant="outline" 
                              size="icon" 
                              className="text-red-500 hover:text-red-600 hover:bg-red-50"
                              onClick={() => {
                                  if(confirm("¿Estás seguro de eliminar este avatar?")) {
                                      deleteMutation.mutate(avatar.id);
                                  }
                              }}
                          >
                              <Trash2 className="h-4 w-4" />
                          </Button>
                      </div>
                  </CardFooter>
              </Card>
              ))}

              {avatars?.length === 0 && (
                  <div className="col-span-full flex flex-col items-center justify-center p-12 border-2 border-dashed rounded-lg text-muted-foreground">
                      <Users className="h-12 w-12 mb-4 opacity-20" />
                      <h3 className="text-lg font-semibold">No hay avatares creados</h3>
                      <p className="mb-4">Crea tu primer avatar para definir tu cliente ideal.</p>
                      <Button variant="outline" onClick={handleOpenNew}>Crear Avatar</Button>
                  </div>
              )}
          </div>
        </CardContent>
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle>{editingAvatar ? "Editar Avatar" : "Nuevo Avatar"}</DialogTitle>
          </DialogHeader>
          <AvatarForm 
            key={editingAvatar?.id || 'new'}
            initialData={editingAvatar || undefined}
            onSubmit={handleFormSubmit}
            isSubmitting={createMutation.isPending || updateMutation.isPending}
            embedded={true}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
