import { useState, useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { whatsappApi, WhatsAppDashboardStatus } from "@/lib/api/whatsapp";
import { toast } from "sonner";

export function useWhatsApp() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<WhatsAppDashboardStatus | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  // Initial Check
  useEffect(() => {
    checkStatus();
    return () => stopPolling();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const checkStatus = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      
      const data = await whatsappApi.getStatus(token);
      setStatus(data);
      
      // Stop polling if connected
      if (data.evolution.status === "connected") {
        setIsScanning(false);
        stopPolling();
      } else if (isScanning) {
          if (!pollInterval.current) startPolling();
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const startPolling = () => {
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
  };

  const stopPolling = () => {
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
  };

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
            
            if (qrData.code && typeof qrData.code === 'string' && qrData.code.length > 10) {
                const src = qrData.code.startsWith("data:") ? qrData.code : `data:image/png;base64,${qrData.code}`;
                setQrCode(src);
                qrFound = true;
                startPolling();
            } else if (qrData.status === "crashed") {
                console.error("Instance crashed:", qrData.detail);
                toast.error(`Error: ${qrData.detail || "El servicio falló."}`);
                qrFound = true; 
                setIsScanning(false);
            } else {
                await new Promise(r => setTimeout(r, 2000)); 
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
      } catch (error) {
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
    disconnect
  };
}
