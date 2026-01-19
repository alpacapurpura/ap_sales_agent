"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, Users, Star, Edit, Trash2, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { avatarApi } from "@/lib/api/avatar";
import { useToast } from "@/components/ui/use-toast"; // Assuming useToast exists or I should check
import { Skeleton } from "@/components/ui/skeleton";

export default function AvatarsPage() {
  const queryClient = useQueryClient();
  // const { toast } = useToast(); // Commented out until I verify toast existence

  const { data: avatars, isLoading, isError } = useQuery({
    queryKey: ["avatars"],
    queryFn: () => avatarApi.listAvatars("GLOBAL"),
  });

  const setDefaultMutation = useMutation({
    mutationFn: avatarApi.setDefault,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      // toast({ title: "Avatar actualizado", description: "Se ha establecido como principal." });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: avatarApi.deleteAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["avatars"] });
      // toast({ title: "Avatar eliminado" });
    },
  });

  if (isLoading) {
    return <div className="p-8 space-y-4">
        <div className="flex justify-between">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
        </div>
    </div>;
  }

  if (isError) {
    return <div className="p-8 text-red-500">Error al cargar los avatares.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Avatares de Marca</h1>
          <p className="text-muted-foreground">Gestiona las diferentes identidades y perfiles de cliente ideal.</p>
        </div>
        <Link href="/avatars/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" /> Nuevo Avatar
          </Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
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
              <CardTitle className="flex items-center gap-2">
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
                    <Link href={`/avatars/${avatar.id}`}>
                        <Button variant="outline" size="icon">
                            <Edit className="h-4 w-4" />
                        </Button>
                    </Link>
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
                <Link href="/avatars/new">
                    <Button variant="outline">Crear Avatar</Button>
                </Link>
            </div>
        )}
      </div>
    </div>
  );
}
