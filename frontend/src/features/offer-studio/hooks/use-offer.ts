import { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { offerApi } from "../api";
import { offerToFormValues } from "../api/adapter";
import { Offer } from "../types";
import { OfferFormValues } from "../types/schema";

export function useOffer(offerId: string) {
  const { getToken } = useAuth();
  const [offer, setOffer] = useState<Offer | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOffer = useCallback(async () => {
    if (!offerId || offerId === "undefined") {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const token = await getToken();
      if (!token) throw new Error("No autenticado");

      const data = await offerApi.getOffer(offerId, token);
      setOffer(data);
    } catch (err) {
      console.error("Error fetching offer:", err);
      setError("Error al cargar la oferta");
      toast.error("Error al cargar la oferta");
    } finally {
      setLoading(false);
    }
  }, [offerId, getToken]);

  useEffect(() => {
    fetchOffer();
  }, [fetchOffer]);

  const formValues = useMemo(() => {
    return offer ? offerToFormValues(offer) : undefined;
  }, [offer]);

  const saveOffer = async (data: Partial<OfferFormValues>) => {
    if (!offerId) return;

    try {
      setSaving(true);
      const token = await getToken();
      if (!token) throw new Error("No autenticado");

      await offerApi.saveOffer(offerId, data, token);
      
      const updatedOffer = await offerApi.getOffer(offerId, token);
      setOffer(updatedOffer);
      
      toast.success("Oferta guardada correctamente");
      return updatedOffer;
    } catch (err) {
      console.error("Error saving offer:", err);
      toast.error("Error al guardar la oferta");
      throw err;
    } finally {
      setSaving(false);
    }
  };

  return {
    offer,
    formValues,
    loading,
    error,
    saveOffer,
    saving,
    refetch: fetchOffer
  };
}
