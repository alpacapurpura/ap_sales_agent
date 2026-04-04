"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { KeyFigure } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import { InstructorsForm } from "./instructors-form";
import { OfferFormValues } from "../../../../types/schema";
import { UseFormReturn } from "react-hook-form";
import { Loader2 } from "lucide-react";

const EMPTY_TEAM: KeyFigure[] = [];

interface InstructorsManagerProps {
    defaultValues: Partial<OfferFormValues>;
    onSave: (data: Partial<OfferFormValues>) => Promise<void>;
    form?: UseFormReturn<OfferFormValues>;
}

export function InstructorsManager(props: InstructorsManagerProps) {
    const { getToken } = useAuth();

    const { data: team = EMPTY_TEAM, isLoading, refetch } = useQuery({
        queryKey: ["brand-team"],
        queryFn: async () => {
            const token = await getToken();
            if (!token) return [];
            const settings = await brandApi.getBrandSettings(token);
            return settings.team || [];
        },
        staleTime: 5 * 60 * 1000,
    });

    if (isLoading) {
        return <div className="flex justify-center p-8"><Loader2 className="animate-spin text-muted-foreground w-8 h-8" /></div>;
    }

    return (
        <InstructorsForm
            {...props}
            availableInstructors={team}
            onRefresh={() => void refetch()}
        />
    );
}
