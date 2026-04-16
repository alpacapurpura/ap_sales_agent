"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

import { brandApi } from "@/features/brand/api";

import { InstructorsForm } from "./InstructorsForm";

import type { OfferFormValues } from "../../../../types/schema";
import type { KeyFigure } from "@/features/brand/types";
import type { UseFormReturn } from "react-hook-form";

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
    void fetchTeam();
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
