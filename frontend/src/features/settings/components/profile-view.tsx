"use client";

import { useUser, useClerk } from "@clerk/nextjs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Globe, Clock, Shield, LogOut } from "lucide-react";

export function ProfileView() {
  const { user, isLoaded } = useUser();
  const { openUserProfile, signOut } = useClerk();

  if (!isLoaded) {
    return <ProfileSkeleton />;
  }

  if (!user) {
    return <div>No se encontró información del usuario.</div>;
  }

  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return (
    <div className="space-y-6">
        {/* Identity Card */}
        <Card>
            <CardHeader>
                <CardTitle>Identidad</CardTitle>
                <CardDescription>Información personal gestionada por tu proveedor de autenticación.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="flex flex-col md:flex-row items-center gap-6">
                    <Avatar className="h-20 w-20">
                        <AvatarImage src={user.imageUrl} />
                        <AvatarFallback>{user.firstName?.[0]}{user.lastName?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="space-y-1 text-center md:text-left">
                        <h3 className="text-xl font-medium">{user.fullName}</h3>
                        <p className="text-sm text-muted-foreground">{user.primaryEmailAddress?.emailAddress}</p>
                        <div className="flex justify-center md:justify-start gap-2 pt-1">
                            {/* Example Badge if roles were implemented */}
                            {/* <Badge variant="secondary">Usuario</Badge> */}
                        </div>
                    </div>
                    <div className="md:ml-auto flex flex-col md:flex-row gap-2">
                         <Button variant="outline" onClick={() => openUserProfile()}>
                            Editar Perfil
                         </Button>
                         <Button variant="destructive" onClick={() => signOut({ redirectUrl: '/' })}>
                            <LogOut className="mr-2 h-4 w-4" />
                            Cerrar Sesión
                         </Button>
                    </div>
                </div>
            </CardContent>
        </Card>

        {/* System Context Card */}
        <Card>
            <CardHeader>
                <CardTitle>Preferencias del Agente</CardTitle>
                <CardDescription>Contexto que utiliza la IA para personalizar tu experiencia.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                    <Label className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        Zona Horaria
                    </Label>
                    <div className="p-3 bg-muted/50 rounded-md text-sm font-medium border">
                        {timeZone}
                    </div>
                    <p className="text-[0.8rem] text-muted-foreground">Detectada automáticamente de tu sistema.</p>
                </div>
                
                <div className="space-y-2">
                     <Label className="flex items-center gap-2">
                        <Globe className="h-4 w-4 text-muted-foreground" />
                        Idioma
                    </Label>
                    <div className="p-3 bg-muted/50 rounded-md text-sm font-medium border">
                        Español
                    </div>
                     <p className="text-[0.8rem] text-muted-foreground">Idioma predeterminado del sistema.</p>
                </div>

                <div className="space-y-2 md:col-span-2">
                    <Label className="flex items-center gap-2">
                        <Shield className="h-4 w-4 text-muted-foreground" />
                        ID de Usuario
                    </Label>
                    <div className="flex items-center gap-2">
                        <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold truncate w-full md:w-auto block">
                            {user.id}
                        </code>
                    </div>
                    <p className="text-[0.8rem] text-muted-foreground">Identificador único para soporte técnico.</p>
                </div>
            </CardContent>
        </Card>
    </div>
  );
}

function ProfileSkeleton() {
    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <Skeleton className="h-4 w-[200px]" />
                <Skeleton className="h-4 w-[300px]" />
            </div>
            <Skeleton className="h-[200px] w-full rounded-lg" />
            <Skeleton className="h-[200px] w-full rounded-lg" />
        </div>
    )
}
