import { useAuth } from "@clerk/nextjs";
import { useState, useEffect, useRef, useCallback } from "react";
import { toast } from "sonner";

import { whatsappApi } from "@/lib/api/whatsapp";

import type { WhatsAppDashboardStatus } from "@/lib/api/whatsapp";

/**
 *
 */
export function useWhatsApp() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<WhatsAppDashboardStatus | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  const stopPolling = useCallback(() => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollInterval.current) return;
    pollInterval.current = setInterval(async () => {
      const token = await getToken();
      if (!token) return;
      const data = await whatsappApi.getStatus(token);
      setStatus(data);
      if (data.evolution.status === "connected") {
        stopPolling();
        setIsScanning(false);
        toast.success("¡WhatsApp Conectado!");
      }
    }, 3000);
  }, [getToken, stopPolling]);

  // Initial Check
  useEffect(() => {
    const checkOnMount = async () => {
      try {
        const token = await getToken();
        if (!token) return;

        const data = await whatsappApi.getStatus(token);
        setStatus(data);

        if (data.evolution.status === "connected") {
          setIsScanning(false);
          stopPolling();
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    void checkOnMount();
    return () => stopPolling();
  }, [getToken, stopPolling]);

  const generateQR = async () => {
    setIsScanning(true);
    setLoading(true);
    try {
      const token = await getToken();
      if (!token) return;

      // 1. Ensure session exists
      await whatsappApi.createSession(token, "evolution");

      // 2. Fetch QR with retry
      let attempts = 0;
      let qrFound = false;
      const maxAttempts = 20;

      while (attempts < maxAttempts && !qrFound) {
        const qrData = await whatsappApi.getQR(token);

        if (qrData.code && typeof qrData.code === "string" && qrData.code.length > 10) {
          const src = qrData.code.startsWith("data:")
            ? qrData.code
            : `data:image/png;base64,${qrData.code}`;
          setQrCode(src);
          qrFound = true;
          startPolling();
        } else if (qrData.status === "crashed") {
          console.error("Instance crashed:", qrData.detail);
          toast.error(`Error: ${qrData.detail || "El servicio falló."}`);
          qrFound = true;
          setIsScanning(false);
        } else {
          await new Promise((r) => setTimeout(r, 2000));
          attempts++;
        }
      }

      if (!qrFound) {
        toast.error("El servicio de WhatsApp está tardando en iniciar. Intenta de nuevo.");
        setIsScanning(false);
      }
    } catch (error) {
      console.error("WhatsApp Session Error:", error);
      toast.error("Error iniciando sesión de WhatsApp");
      setIsScanning(false);
    } finally {
      setLoading(false);
    }
  };

  const disconnect = async (provider: "evolution" | "meta") => {
    try {
      const token = await getToken();
      if (!token) return;
      await whatsappApi.disconnect(token, provider);

      // Refresh status locally
      if (status) {
        const newStatus = { ...status };
        newStatus[provider] = { status: "disconnected" };
        setStatus(newStatus);
      }

      if (provider === "evolution") {
        setQrCode(null);
        setIsScanning(false);
        stopPolling();
      }
      toast.success("Desconectado correctamente");
    } catch {
      toast.error("Error desconectando");
    }
  };

  return {
    loading,
    status,
    qrCode,
    isScanning,
    setIsScanning,
    generateQR,
    disconnect,
  };
}
