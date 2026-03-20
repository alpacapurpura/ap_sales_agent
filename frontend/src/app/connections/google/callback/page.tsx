"use client";

/**
 * Google OAuth Popup Callback Handler
 *
 * Dedicated redirect target for Google Workspace OAuth.
 * Extracts code/error from URL and posts message to opener window.
 *
 * GOOGLE_REDIRECT_URI in .env must point to this page.
 */

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

function GoogleOAuthCallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");

  useEffect(() => {
    const code = searchParams?.get("code");
    const error = searchParams?.get("error");

    if (!window.opener) {
      window.location.href = "/";
      return;
    }

    if (code) {
      window.opener.postMessage({ type: "GOOGLE_OAUTH_SUCCESS", code }, window.location.origin);
      setStatus("success");
    } else if (error) {
      window.opener.postMessage({ type: "GOOGLE_OAUTH_ERROR", error }, window.location.origin);
      setStatus("error");
    }

    const timer = setTimeout(() => window.close(), 1500);
    return () => clearTimeout(timer);
  }, [searchParams]);

  return (
    <div className="flex h-screen w-full items-center justify-center flex-col gap-4 bg-background">
      {status === "processing" && (
        <>
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground text-sm">Autenticando...</p>
        </>
      )}
      {status === "success" && (
        <>
          <CheckCircle className="h-8 w-8 text-green-500" />
          <p className="text-sm text-muted-foreground">Conectado. Cerrando ventana...</p>
        </>
      )}
      {status === "error" && (
        <>
          <XCircle className="h-8 w-8 text-destructive" />
          <p className="text-sm text-muted-foreground">Error al autenticar. Cerrando ventana...</p>
        </>
      )}
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <GoogleOAuthCallbackContent />
    </Suspense>
  );
}
