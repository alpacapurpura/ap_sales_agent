"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { BrandVisuals } from "@/features/brand/types";
import { Users, Star, Plus } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { avatarApi } from "@/lib/api/avatar";

import { Badge } from "@/components/ui/badge";
import { validateAvatar } from "../../utils/brand-validation";
import { cn } from "@/lib/utils";

interface AvatarsSectionProps {
  visuals: BrandVisuals;
  onEdit: (avatar?: any) => void;
}

export function AvatarsSection({ visuals, onEdit }: AvatarsSectionProps) {
  const { getToken } = useAuth();

  const { data: avatars, isLoading } = useQuery({
    queryKey: ["avatars"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      try {
          // Assuming listAvatars can handle filtered queries or returns all
          return await avatarApi.listAvatars(token, "GLOBAL"); 
      } catch (e) {
          console.error(e);
          // Return empty array instead of throwing to prevent component crash
          return [];
      }
    },
    // Prevent retry on 404 or auth errors to avoid spamming console
    retry: (failureCount, error: any) => {
        if (error.message.includes("404") || error.message.includes("401")) return false;
        return failureCount < 2;
    }
  });

  if (isLoading) {
    return (
        <div className="pl-0 md:pl-14 py-6">
            <div className="flex gap-4">
                <Skeleton className="h-20 w-20 rounded-full" />
                <Skeleton className="h-20 w-20 rounded-full" />
                <Skeleton className="h-20 w-20 rounded-full" />
            </div>
        </div>
    );
  }

  // Ensure avatars is an array
  const safeAvatars = Array.isArray(avatars) ? avatars : [];
  const hasContent = safeAvatars.length > 0;

  return (
    <section 
        className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors cursor-pointer" onClick={() => onEdit()}>
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
            <Users className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">Target & Buyer Personas</h3>
      </div>

      {!hasContent ? (
        <div className="pl-0 md:pl-14 cursor-pointer" onClick={() => onEdit()}>
            <p className="text-lg text-muted-foreground italic mb-2">
                &quot;Si le hablas a todos, no le hablas a nadie. Define a tu cliente ideal.&quot;
            </p>
            <span className="text-sm text-primary font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
                <Plus className="w-4 h-4" />
                Definir Buyer Persona
            </span>
        </div>
      ) : (
        <div className="pl-0 md:pl-14">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-8">
                {safeAvatars.map((avatar: any) => {
                    const status = validateAvatar(avatar);
                    const isComplete = status.status === "complete";
                    
                    return (
                    <div key={avatar.id} className="flex flex-col items-center text-center group/avatar cursor-pointer" onClick={() => onEdit(avatar)}>
                        <div className="relative mb-3">
                            <Avatar className="h-20 w-20 border-2 border-transparent group-hover/avatar:border-primary transition-colors">
                                {/* Assuming avatar object has these fields */}
                                <AvatarImage src={avatar.headshot_url || avatar.avatar_url} />
                                <AvatarFallback className="text-lg font-bold bg-muted">
                                    {avatar.name?.substring(0, 2).toUpperCase()}
                                </AvatarFallback>
                            </Avatar>
                            {/* Status Indicator */}
                            <div className={cn(
                                "absolute bottom-0 right-0 h-4 w-4 rounded-full border-2 border-background",
                                isComplete ? "bg-green-500" : "bg-amber-500"
                            )} title={isComplete ? "Completo" : "Faltan datos"} />
                        </div>
                        <h4 className="font-medium text-foreground text-sm truncate w-full px-2">{avatar.name}</h4>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                            {avatar.role || "Cliente Ideal"}
                        </p>
                    </div>
                    );
                })}
                
                {/* Add New Trigger (Visual) */}
                <div className="flex flex-col items-center justify-center text-center group/add cursor-pointer" onClick={() => onEdit()}>
                    <div className="h-20 w-20 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-3 group-hover/add:border-primary/50 group-hover/add:bg-primary/5 transition-colors">
                        <Plus className="w-6 h-6 text-muted-foreground group-hover/add:text-primary" />
                    </div>
                    <span className="text-sm text-muted-foreground group-hover/add:text-primary">Nuevo</span>
                </div>
            </div>
        </div>
      )}
    </section>
  );
}
