"use client";

/**
 * OAuth Popup Callback Handler
 *
 * This page is the redirect target for Google Workspace OAuth.
 * It detects that it's running inside a popup (window.opener exists),
 * extracts the code/error from the URL, and posts a message to the
 * opener window so the parent page can exchange the code for tokens.
 *
 * GOOGLE_REDIRECT_URI in config.py must point to this page.
 */

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, CheckCircle, XCircle } from "lucide-react";

function OAuthCallbackContent() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");

  useEffect(() => {
    const code = searchParams.get("code");
    const error = searchParams.get("error");
    const state = searchParams.get("state");

    if (!window.opener) {
      // Not a popup — nothing to do, just show a blank page or redirect home
      window.location.href = "/";
      return;
    }

    if (code) {
      const isMetaCallback = state && state.startsWith("meta");
      const messageType = isMetaCallback ? "META_OAUTH_SUCCESS" : "GOOGLE_OAUTH_SUCCESS";
      window.opener.postMessage({ type: messageType, code }, window.location.origin);
      setStatus("success");
    } else if (error) {
      const isMetaCallback = state && state.startsWith("meta");
      const messageType = isMetaCallback ? "META_OAUTH_ERROR" : "GOOGLE_OAUTH_ERROR";
      window.opener.postMessage({ type: messageType, error }, window.location.origin);
      setStatus("error");
    }

    // Close popup after a brief delay so the user sees feedback
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

export default function ConnectionsCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}
