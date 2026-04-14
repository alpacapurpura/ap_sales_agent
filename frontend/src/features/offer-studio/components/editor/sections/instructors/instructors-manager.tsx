"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { KeyFigure } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import { InstructorsForm } from "./instructors-form";
import { UseFormReturn } from "react-hook-form";
import { OfferFormValues } from "../../../../types/schema";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface InstructorsManagerProps {
  defaultValues: Partial<OfferFormValues>;
  onSave: (data: Partial<OfferFormValues>) => Promise<void>;
  form?: UseFormReturn<OfferFormValues>;
}

export function InstructorsManager(props: InstructorsManagerProps) {
  const { getToken } = useAuth();
  const [team, setTeam] = useState<KeyFigure[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialized, setInitialized] = useState(false);

  const fetchTeam = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;
      const settings = await brandApi.getBrandSettings(token);
      setTeam(settings.team || []);
    } catch (error) {
      console.error("Error fetching team:", error);
      toast.error("Error al cargar el equipo");
    } finally {
      setLoading(false);
      setInitialized(true);
    }
  }, [getToken]);

  useEffect(() => {
    fetchTeam();
  }, [fetchTeam]);

  if (!initialized && loading) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="animate-spin text-muted-foreground w-8 h-8" />
      </div>
    );
  }

  return <InstructorsForm {...props} availableInstructors={team} onRefresh={fetchTeam} />;
}
