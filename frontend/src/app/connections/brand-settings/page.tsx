"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

function GoogleOAuthCallbackContent() {
  const searchParams = useSearchParams();

  useEffect(() => {
    const code = searchParams.get("code");
    const error = searchParams.get("error");

    if (!window.opener) return;

    if (code) {
      window.opener.postMessage(
        { type: "GOOGLE_OAUTH_SUCCESS", code },
        window.location.origin
      );
    } else {
      window.opener.postMessage(
        { type: "GOOGLE_OAUTH_ERROR", error: error || "Unknown error" },
        window.location.origin
      );
    }

    window.close();
  }, [searchParams]);

  return (
    <div className="flex h-screen w-full items-center justify-center flex-col gap-4">
      <Loader2 className="h-8 w-8 animate-spin" />
      <p className="text-sm text-muted-foreground">Conectando con Google...</p>
    </div>
  );
}

export default function GoogleOAuthCallbackPage() {
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
