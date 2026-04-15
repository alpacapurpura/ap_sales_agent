"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { toast } from "sonner";

import { offerApi } from "@/features/offer-studio/api";

import { PuckEditor } from "./PuckEditor";

import type { LandingPageConfig } from "@/features/offer-studio/components/landing/types/schema";

export function LandingPageEditor({
  initialConfig,
  offerId,
}: {
  initialConfig?: LandingPageConfig;
  offerId?: string;
}) {
  const { getToken } = useAuth();
  const [config, setConfig] = useState<LandingPageConfig | undefined>(initialConfig);
  const [isLoading, setIsLoading] = useState(!initialConfig && !!offerId);

  // Fetch config if not provided
  useEffect(() => {
    const fetchConfig = async () => {
      if (!offerId || initialConfig) return;

      try {
        const token = await getToken();
        if (!token) return;

        setIsLoading(true);
        const data = await offerApi.getLandingConfig(offerId, token);
        if (data) {
          setConfig(data);
        }
      } catch (error) {
        console.error("Failed to load landing config", error);
        toast.error("Error al cargar la configuración de la landing.");
      } finally {
        setIsLoading(false);
      }
    };

    void fetchConfig();
  }, [offerId, initialConfig, getToken]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    );
  }

  if (!config || !offerId) {
    return <div>No se encontró la configuración de la landing page.</div>;
  }

  return <PuckEditor initialConfig={config} offerId={offerId} />;
}
