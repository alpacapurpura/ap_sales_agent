"use client";

import { useEffect, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

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
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/connections/meta/callback`, {
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
        if (tenantId) {
          sessionStorage.removeItem("meta_oauth_tenant_id");
          // Redirigir al dashboard específico del tenant y a la pestaña de conexiones si es posible
          // Como MarketingStudio usa Tabs, podemos intentar pasar un query param si lo soporta,
          // o simplemente ir a la página. Asumimos que la URL es /[tenantId]/marketing-studio
          router.push(`/${tenantId}/marketing-studio`);
        } else {
          router.push("/marketing-studio");
        }
      } catch (error: any) {
        console.error(error);
        toast.error(error.message || "Falló la conexión con Meta");
        router.push("/marketing-studio");
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
