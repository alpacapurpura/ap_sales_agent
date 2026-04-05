import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { offerApi } from "../api";
import { offerToFormValues } from "../api/adapter";
import { getSectionData } from "../utils/section-helpers";
import { Offer } from "../types";
import { OfferFormValues } from "../types/schema";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

export function useOffer(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  // REAL API IMPLEMENTATION
  const { data: offer, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['offer', offerId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return offerApi.getOffer(offerId, token);
    },
    enabled: !!offerId && offerId !== "undefined",
    retry: 1,
    staleTime: 5 * 60 * 1000
  });

  const formValues = useMemo(() => {
    return offer ? offerToFormValues(offer) : undefined;
  }, [offer]);

  const saveOfferMutation = useMutation({
    mutationFn: async (data: Partial<OfferFormValues>) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      await offerApi.saveOffer(offerId, data, token);
      return offerApi.getOffer(offerId, token);
    },
    onSuccess: (updatedOffer) => {
      queryClient.setQueryData(['offer', offerId], updatedOffer);
      toast.success("Oferta guardada");
    },
    onError: (err) => {
      console.error("Error saving offer:", err);
      toast.error("Error al guardar la oferta");
    }
  });

  const saveSectionMutation = useMutation({
    mutationFn: async ({ sectionId, allValues }: { sectionId: string, allValues: OfferFormValues }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const data = getSectionData(sectionId, allValues);
      await offerApi.saveSection(offerId, sectionId, data, token);
      return offerApi.getOffer(offerId, token);
    },
    onSuccess: (updatedOffer) => {
      queryClient.setQueryData(['offer', offerId], updatedOffer);
      toast.success("Sección guardada");
    },
    onError: (err) => {
      console.error(`Error saving section:`, err);
      toast.error("Error al guardar la sección");
    }
  });

  const saveOffer = async (data: Partial<OfferFormValues>) => {
     return saveOfferMutation.mutateAsync(data);
  };
  
  const saveSection = async (sectionId: string, allValues: OfferFormValues) => {
     return saveSectionMutation.mutateAsync({ sectionId, allValues });
  };

  return {
    offer: offer || null,
    formValues,
    loading,
    error: error ? (error as Error).message : null,
    saveOffer,
    saveSection,
    saving: saveOfferMutation.isPending || saveSectionMutation.isPending,
    refetch
  };
}
