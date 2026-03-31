"use client";

import { useEffect, useRef } from "react";
import { OAUTH_MESSAGE_TYPES } from "@/features/connections/lib/oauth-constants";

interface UseGoogleOAuthListenerOptions {
  onSuccess: (code: string) => void | Promise<void>;
  onError?: (error: string) => void;
  enabled?: boolean;
}

export function useGoogleOAuthListener({
  onSuccess,
  onError,
  enabled = true,
}: UseGoogleOAuthListenerOptions) {
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  });

  useEffect(() => {
    if (!enabled) return;

    const handleMessage = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;

      if (event.data?.type === OAUTH_MESSAGE_TYPES.GOOGLE_SUCCESS && event.data?.code) {
        await onSuccessRef.current(event.data.code);
      } else if (event.data?.type === OAUTH_MESSAGE_TYPES.GOOGLE_ERROR) {
        onErrorRef.current?.(event.data?.error || "Unknown error");
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [enabled]);
}
