"use client";

import { useAuth } from "@clerk/nextjs";
import { Loader2, AlertCircle, ArrowLeft, RefreshCw } from "lucide-react";
import { useSearchParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState, useCallback, Suspense } from "react";
import { toast } from "sonner";

import { config } from "@/lib/config";

function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const processedRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("Conectando con Meta...");

  /**
   * Wait for Clerk to restore the session after a full-page redirect.
   * Polls getToken() up to 10 times with 500ms intervals (5s total).
   */
  const waitForToken = useCallback(async (): Promise<string | null> => {
    const MAX_ATTEMPTS = 10;
    const INTERVAL_MS = 500;

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
      try {
        const token = await getToken();
        if (token) {
          console.log(`[Meta OAuth] Token obtained on attempt ${attempt}`);
          return token;
        }
      } catch (e) {
        console.warn(`[Meta OAuth] getToken() attempt ${attempt} threw:`, e);
      }

      if (attempt < MAX_ATTEMPTS) {
        await new Promise((resolve) => setTimeout(resolve, INTERVAL_MS));
      }
    }

    console.error("[Meta OAuth] Failed to obtain auth token after 10 attempts (5s)");
    return null;
  }, [getToken]);

  const handleCallback = useCallback(async () => {
    const code = searchParams?.get("code") || sessionStorage.getItem("meta_oauth_code");

    if (!code) {
      console.error("[Meta OAuth] No code found in URL params or sessionStorage");
      setError("No se recibio el codigo de autorizacion de Meta. Intenta conectar de nuevo.");
      return;
    }

    // Persist code in sessionStorage as defense-in-depth
    sessionStorage.setItem("meta_oauth_code", code);

    setStatus("Esperando autenticacion...");
    const token = await waitForToken();

    if (!token) {
      console.error(
        "[Meta OAuth] Could not get auth token - Clerk session not restored after redirect",
      );
      setError(
        "No se pudo restaurar la sesion despues de volver de Facebook. " +
          "Intenta de nuevo o inicia sesion primero.",
      );
      return;
    }

    setStatus("Procesando conexion con Meta...");

    // Read tenant ID from sessionStorage (saved before redirect) or localStorage
    const tenantId =
      sessionStorage.getItem("meta_oauth_tenant_id") || localStorage.getItem("x-tenant-id") || "";

    const redirect_uri = `${window.location.origin}/connections/meta/callback`;

    // Use native fetch to avoid fetchClient's 401/403 interceptors that silently redirect
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
    if (tenantId) {
      headers["X-Tenant-ID"] = tenantId;
    }

    try {
      console.log("[Meta OAuth] Sending callback to backend...", {
        redirect_uri,
        codeLength: code.length,
        hasTenantId: !!tenantId,
      });

      const response = await fetch(`${config.api.baseUrl}/api/v1/connections/meta/callback`, {
        method: "POST",
        headers,
        body: JSON.stringify({ code, redirect_uri }),
      });

      if (!response.ok) {
        const errorData = (await response.json().catch(() => ({}))) as { detail?: string };
        const detail = errorData.detail ?? `Error ${response.status}`;
        console.error("[Meta OAuth] Backend returned error:", {
          status: response.status,
          detail,
        });
        throw new Error(detail);
      }

      const data = (await response.json()) as {
        status: string;
        is_connected: boolean;
        assets_synced: boolean;
      };
      console.log("[Meta OAuth] Backend success:", {
        status: data.status,
        is_connected: data.is_connected,
        assets_synced: data.assets_synced,
      });

      // Auto-sync assets (non-blocking, backend may have already done it)
      try {
        await fetch(`${config.api.baseUrl}/api/v1/connections/meta/assets/sync`, {
          method: "POST",
          headers,
        });
      } catch {
        // Non-blocking
      }

      // Cleanup sessionStorage
      sessionStorage.removeItem("meta_oauth_code");
      sessionStorage.removeItem("meta_oauth_tenant_id");

      toast.success("Meta conectado - activos sincronizados");
      router.push(tenantId ? `/${tenantId}/connections/meta` : "/");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      console.error("[Meta OAuth] Callback failed:", message);
      setError(message);
    }
  }, [searchParams, waitForToken, router]);

  useEffect(() => {
    const code = searchParams?.get("code");

    if (!code) {
      return;
    }

    if (processedRef.current) return;
    processedRef.current = true;

    void handleCallback();
  }, [searchParams, handleCallback]);

  const handleRetry = () => {
    setError(null);
    setStatus("Reintentando conexion...");
    processedRef.current = false;
    void handleCallback();
  };

  const handleGoBack = () => {
    const tenantId =
      sessionStorage.getItem("meta_oauth_tenant_id") || localStorage.getItem("x-tenant-id") || "";
    sessionStorage.removeItem("meta_oauth_code");
    sessionStorage.removeItem("meta_oauth_tenant_id");
    router.push(tenantId ? `/${tenantId}/connections/meta` : "/");
  };

  // Error state UI
  if (error) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4 max-w-md text-center p-6">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <h2 className="text-lg font-semibold">Error al conectar con Meta</h2>
          <p className="text-sm text-muted-foreground">{error}</p>
          <p className="text-xs text-muted-foreground">
            Revisa la consola del navegador para mas detalles (F12 &gt; Console).
          </p>
          <div className="flex gap-3 mt-2">
            <button
              onClick={handleRetry}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90"
            >
              <RefreshCw className="h-4 w-4" />
              Reintentar
            </button>
            <button
              onClick={handleGoBack}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-input bg-background text-sm font-medium hover:bg-accent hover:text-accent-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Volver
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full items-center justify-center flex-col gap-4">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-muted-foreground">{status}</p>
    </div>
  );
}

/**
 *
 */
export default function MetaCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
