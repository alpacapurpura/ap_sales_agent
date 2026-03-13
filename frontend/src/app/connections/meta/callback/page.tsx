"use client";

import { useEffect, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const processedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");
    
    if (!code) {
      return;
    }

    if (processedRef.current) return;
    processedRef.current = true;

    const handleCallback = async () => {
      try {
        const token = await getToken();
        if (!token) {
          toast.error("No autenticado");
          router.push("/sign-in");
          return;
        }

        const redirect_uri = `${window.location.origin}/connections/meta/callback`;
        const response = await fetchClient(`${config.api.baseUrl}/api/v1/connections/meta/callback`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ code, redirect_uri }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || "Error al procesar la conexión con Meta");
        }

        toast.success("Meta conectado exitosamente");
        const tenantId = sessionStorage.getItem("meta_oauth_tenant_id");
        sessionStorage.removeItem("meta_oauth_tenant_id");
        router.push(tenantId ? `/${tenantId}/settings?tab=meta` : "/");
      } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Falló la conexión con Meta");
        const tenantId = sessionStorage.getItem("meta_oauth_tenant_id");
        sessionStorage.removeItem("meta_oauth_tenant_id");
        router.push(tenantId ? `/${tenantId}/settings?tab=meta` : "/");
      }
    };

    handleCallback();
  }, [searchParams, router, getToken]);

  return (
    <div className="flex h-screen w-full items-center justify-center flex-col gap-4">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-muted-foreground">Conectando con Meta...</p>
    </div>
  );
}

export default function MetaCallbackPage() {
  return (
    <Suspense fallback={<div className="flex h-screen w-full items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>}>
      <CallbackContent />
    </Suspense>
  );
}
