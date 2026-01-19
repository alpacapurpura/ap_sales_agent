"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { OfferEditorLayout } from "@/components/offer-studio/layout/offer-editor-layout";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { avatarApi } from "@/lib/api/avatar";
import { offerApi } from "@/lib/api/offer";
import { CheckCircle2, ExternalLink, Loader2, Star, Users } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AvatarPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  // Fetch Offer to get current avatar_id
  const { data: offer, isLoading: isLoadingOffer } = useQuery({
    queryKey: ["offer", id],
    queryFn: () => offerApi.getOffer(id),
  });

  // Fetch Avatars
  const { data: avatars, isLoading: isLoadingAvatars } = useQuery({
    queryKey: ["avatars"],
    queryFn: () => avatarApi.listAvatars("GLOBAL"),
  });

  const selectAvatarMutation = useMutation({
    mutationFn: (avatarId: string) => offerApi.saveOffer(id, { ...offer!, name: offer!.name, avatar_id: avatarId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offer", id] });
    },
  });

  const isLoading = isLoadingOffer || isLoadingAvatars;

  // Auto-select default if none selected
  useEffect(() => {
    if (avatars && offer && !offer.avatar_id) {
        const defaultAvatar = avatars.find(a => a.is_default);
        if (defaultAvatar) {
            selectAvatarMutation.mutate(defaultAvatar.id);
        }
    }
  }, [avatars, offer]);

  if (isLoading) {
    return (
        <OfferEditorLayout offerId={id}>
            <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>
        </OfferEditorLayout>
    );
  }

  return (
    <OfferEditorLayout offerId={id}>
       <div className="space-y-6 max-w-5xl">
          <div className="flex justify-between items-start">
            <div>
                <h1 className="text-2xl font-bold">Selección de Avatar</h1>
                <p className="text-muted-foreground">Elige qué identidad de marca representará esta oferta.</p>
            </div>
            <Link href="/avatars">
                <Button variant="outline" size="sm">
                    <ExternalLink className="mr-2 h-4 w-4" /> Gestionar Avatares
                </Button>
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {avatars?.map((avatar) => {
                const isSelected = offer?.avatar_id === avatar.id;
                return (
                    <Card 
                        key={avatar.id} 
                        className={cn(
                            "cursor-pointer transition-all hover:border-primary/50 relative",
                            isSelected ? "border-primary bg-primary/5 ring-2 ring-primary ring-offset-2" : ""
                        )}
                        onClick={() => !isSelected && selectAvatarMutation.mutate(avatar.id)}
                    >
                        {avatar.is_default && (
                            <Badge variant="secondary" className="absolute top-2 right-2 z-10 gap-1">
                                <Star className="h-3 w-3 fill-current text-yellow-500" /> Default
                            </Badge>
                        )}
                        
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-lg">
                                <Users className="h-5 w-5 text-muted-foreground" />
                                {avatar.name}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2 text-sm text-muted-foreground">
                                <p className="line-clamp-3">{avatar.icp_description || "Sin descripción"}</p>
                            </div>
                        </CardContent>
                        <CardFooter>
                            {isSelected ? (
                                <Button className="w-full" variant="default" disabled>
                                    <CheckCircle2 className="mr-2 h-4 w-4" /> Seleccionado
                                </Button>
                            ) : (
                                <Button 
                                    className="w-full" 
                                    variant="outline"
                                    disabled={selectAvatarMutation.isPending}
                                >
                                    Seleccionar
                                </Button>
                            )}
                        </CardFooter>
                    </Card>
                );
            })}
          </div>

          {avatars?.length === 0 && (
             <div className="p-8 border-2 border-dashed rounded-lg flex flex-col items-center justify-center text-center">
                <Users className="h-10 w-10 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">No hay avatares disponibles</h3>
                <p className="text-muted-foreground mb-4">Necesitas crear un avatar de marca antes de asignarlo.</p>
                <Link href="/avatars/new">
                    <Button>Crear mi primer Avatar</Button>
                </Link>
             </div>
          )}
       </div>
    </OfferEditorLayout>
  );
}
