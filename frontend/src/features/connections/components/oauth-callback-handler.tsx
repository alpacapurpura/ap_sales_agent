"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, CheckCircle, XCircle } from "lucide-react";
import { OAUTH_MESSAGE_TYPES, POPUP_CLOSE_DELAY } from "@/features/connections/lib/oauth-constants";

interface OAuthCallbackHandlerProps {
  provider?: "google" | "meta" | "auto";
}

export function OAuthCallbackHandler({ provider = "auto" }: OAuthCallbackHandlerProps) {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");

  useEffect(() => {
    const code = searchParams?.get("code");
    const error = searchParams?.get("error");
    const state = searchParams?.get("state");

    if (!window.opener) {
      window.location.href = "/";
      return;
    }

    const isMetaCallback =
      provider === "meta" || (provider === "auto" && state?.startsWith("meta"));

    if (code) {
      const messageType = isMetaCallback
        ? OAUTH_MESSAGE_TYPES.META_SUCCESS
        : OAUTH_MESSAGE_TYPES.GOOGLE_SUCCESS;
      window.opener.postMessage({ type: messageType, code }, window.location.origin);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- fire-and-forget OAuth popup; no re-render alternative
      setStatus("success");
    } else if (error) {
      const messageType = isMetaCallback
        ? OAUTH_MESSAGE_TYPES.META_ERROR
        : OAUTH_MESSAGE_TYPES.GOOGLE_ERROR;
      window.opener.postMessage({ type: messageType, error }, window.location.origin);

      setStatus("error");
    }

    const timer = setTimeout(() => window.close(), POPUP_CLOSE_DELAY);
    return () => clearTimeout(timer);
  }, [searchParams, provider]);

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
