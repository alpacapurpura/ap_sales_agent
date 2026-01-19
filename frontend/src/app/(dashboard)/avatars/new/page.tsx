"use client";

import { useRouter } from "next/navigation";
import { AvatarForm } from "@/components/avatars/avatar-form";
import { avatarApi, CreateAvatarDTO } from "@/lib/api/avatar";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from "lucide-react";

export default function NewAvatarPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (data: CreateAvatarDTO) => {
    setIsSubmitting(true);
    try {
      await avatarApi.createAvatar(data);
      router.push("/avatars");
    } catch (error) {
      console.error("Error creating avatar:", error);
      alert("Error al crear el avatar");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Crear Nuevo Avatar</h1>
          <p className="text-muted-foreground">Define un nuevo perfil de cliente ideal.</p>
        </div>
      </div>

      <AvatarForm onSubmit={handleSubmit} isSubmitting={isSubmitting} />
    </div>
  );
}
