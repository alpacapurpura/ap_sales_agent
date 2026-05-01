"use client";

/**
 * Client island: state machine + interactive flow for Telegram linking.
 *
 * PI-5 PR-1. Linked state derived from queries; transient states
 * (idle/requesting/waiting/timeout/error) tracked locally. Polling stops
 * auto when linked. 60s timeout. Spanish neutro tuteo.
 */

import { AlertCircle, CheckCircle2, Loader2, Send } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateTelegramLinkToken } from "@/features/copilot/api/use-create-telegram-link-token";
import { useTelegramCurrentLink } from "@/features/copilot/api/use-telegram-current-link";
import { useTelegramLinkStatus } from "@/features/copilot/api/use-telegram-link-status";
import { useUnlinkTelegram } from "@/features/copilot/api/use-unlink-telegram";

import type { LinkStatusResponse } from "@/features/copilot/types/telegram";

/** Local transient state (NOT including 'linked' — that's derived from queries). */
type TransientState =
  | { kind: "idle" }
  | { kind: "requesting" }
  | { kind: "waiting"; tokenId: string; deepLinkUrl: string; expiresAt: string }
  | { kind: "timeout"; tokenId: string }
  | { kind: "error"; message: string };

/**
 * Telegram linking flow client component.
 */
export function TelegramLinkingClient() {
  const currentLink = useTelegramCurrentLink();
  const createToken = useCreateTelegramLinkToken();
  const unlink = useUnlinkTelegram();

  const [transient, setTransient] = useState<TransientState>({ kind: "idle" });

  // Polling (only active when transient.kind === "waiting")
  const linkStatus = useTelegramLinkStatus(transient.kind === "waiting" ? transient.tokenId : null);

  // Timeout 60s — runs only when waiting
  useEffect(() => {
    if (transient.kind !== "waiting") return undefined;
    const { tokenId } = transient;
    const timer = setTimeout(() => {
      setTransient((s) => (s.kind === "waiting" ? { kind: "timeout", tokenId } : s));
    }, 60_000);
    return () => clearTimeout(timer);
  }, [transient]);

  const handleConnect = async () => {
    setTransient({ kind: "requesting" });
    try {
      const data = await createToken.mutateAsync();
      window.open(data.deep_link_url, "_blank", "noopener,noreferrer");
      setTransient({
        kind: "waiting",
        tokenId: data.token_id,
        deepLinkUrl: data.deep_link_url,
        expiresAt: data.expires_at,
      });
    } catch (err) {
      setTransient({ kind: "error", message: (err as Error).message });
    }
  };

  const handleUnlink = async () => {
    try {
      await unlink.mutateAsync();
      setTransient({ kind: "idle" });
    } catch (err) {
      setTransient({ kind: "error", message: (err as Error).message });
    }
  };

  const handleRetry = () => setTransient({ kind: "idle" });

  // Derived: linked from query (preferred over transient when waiting → linked)
  const linkedView = resolveLinkedView(currentLink.data, linkStatus.data, transient);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Telegram
        </CardTitle>
      </CardHeader>
      <CardContent>
        {linkedView ? (
          <LinkedView
            chatIdMasked={linkedView.chatIdMasked}
            linkedAt={linkedView.linkedAt}
            onUnlink={handleUnlink}
            isUnlinking={unlink.isPending}
          />
        ) : (
          <TransientRender
            transient={transient}
            isCreating={createToken.isPending}
            onConnect={handleConnect}
            onCancel={handleRetry}
            onRetry={handleRetry}
          />
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Compute which "linked" data to show (if any) without doing setState in effect.
 *
 * Priority: pollingStatus (during waiting flow) > currentLink (initial load).
 * Returns `null` when no link active or transient flow is in error/timeout state.
 */
function resolveLinkedView(
  currentLinkData: LinkStatusResponse | undefined,
  pollingData: LinkStatusResponse | undefined,
  transient: TransientState,
): { chatIdMasked: string; linkedAt: string } | null {
  // Don't show "linked" when user is in error/timeout transient flow
  if (transient.kind === "error" || transient.kind === "timeout") {
    return null;
  }

  // Polling result wins during active waiting flow
  if (
    transient.kind === "waiting" &&
    pollingData?.linked &&
    pollingData.channel_user_id_masked &&
    pollingData.linked_at
  ) {
    return {
      chatIdMasked: pollingData.channel_user_id_masked,
      linkedAt: pollingData.linked_at,
    };
  }

  // Initial / fallback: current link state
  if (
    currentLinkData?.linked &&
    currentLinkData.channel_user_id_masked &&
    currentLinkData.linked_at
  ) {
    return {
      chatIdMasked: currentLinkData.channel_user_id_masked,
      linkedAt: currentLinkData.linked_at,
    };
  }

  return null;
}

/**
 * Render the active transient state view.
 */
function TransientRender({
  transient,
  isCreating,
  onConnect,
  onCancel,
  onRetry,
}: {
  transient: TransientState;
  isCreating: boolean;
  onConnect: () => void;
  onCancel: () => void;
  onRetry: () => void;
}) {
  if (transient.kind === "idle") {
    return <IdleView onConnect={onConnect} isLoading={isCreating} />;
  }
  if (transient.kind === "requesting") {
    return <RequestingView />;
  }
  if (transient.kind === "waiting") {
    return <WaitingView deepLinkUrl={transient.deepLinkUrl} onCancel={onCancel} />;
  }
  if (transient.kind === "timeout") {
    return <TimeoutView onRetry={onRetry} />;
  }
  return <ErrorView message={transient.message} onRetry={onRetry} />;
}

/**
 * Default state: explanation + connect button.
 */
function IdleView({ onConnect, isLoading }: { onConnect: () => void; isLoading: boolean }) {
  return (
    <div className="space-y-4">
      <p className="text-sm">
        Solo usa Telegram con la cuenta del bot oficial <strong>@nicolify_copilot_bot</strong>. NO
        compartas el link con nadie.
      </p>
      <Button onClick={onConnect} disabled={isLoading}>
        {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        Conectar Telegram
      </Button>
    </div>
  );
}

/**
 * Generating link token view.
 */
function RequestingView() {
  return (
    <div className="flex items-center gap-2 text-sm" aria-live="polite">
      <Loader2 className="h-4 w-4 animate-spin" />
      Generando enlace...
    </div>
  );
}

/**
 * Waiting for user to bind chat in Telegram.
 */
function WaitingView({ deepLinkUrl, onCancel }: { deepLinkUrl: string; onCancel: () => void }) {
  return (
    <div className="space-y-4" aria-live="polite">
      <div className="flex items-start gap-2">
        <Loader2 className="h-4 w-4 animate-spin mt-1" />
        <p className="text-sm">
          Abrimos Telegram en otra pestaña. Habla al bot para terminar la conexión.
        </p>
      </div>
      <p className="text-sm text-muted-foreground">
        Si no se abre,{" "}
        <a href={deepLinkUrl} target="_blank" rel="noopener noreferrer" className="underline">
          abre Telegram aquí
        </a>
        .
      </p>
      <Button variant="outline" onClick={onCancel}>
        Cancelar
      </Button>
    </div>
  );
}

/**
 * Telegram chat is linked. Show success + unlink button.
 */
function LinkedView({
  chatIdMasked,
  linkedAt,
  onUnlink,
  isUnlinking,
}: {
  chatIdMasked: string;
  linkedAt: string;
  onUnlink: () => void;
  isUnlinking: boolean;
}) {
  const linkedDate = new Date(linkedAt).toLocaleDateString("es", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2">
        <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
        <div>
          <p className="text-sm font-medium">Tu Telegram está conectado.</p>
          <p className="text-xs text-muted-foreground">
            Chat: {chatIdMasked} · Vinculado el {linkedDate}
          </p>
        </div>
      </div>
      <Button variant="destructive" onClick={onUnlink} disabled={isUnlinking}>
        {isUnlinking ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
        Desvincular
      </Button>
    </div>
  );
}

/**
 * 60s passed without link confirmation.
 */
function TimeoutView({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2">
        <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5" />
        <p className="text-sm">No detectamos la conexión. Revisa Telegram o inténtalo de nuevo.</p>
      </div>
      <Button onClick={onRetry}>Reintentar</Button>
    </div>
  );
}

/**
 * Network or unexpected error.
 */
function ErrorView({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="space-y-4">
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>Algo salió mal: {message}</AlertDescription>
      </Alert>
      <Button onClick={onRetry}>Reintentar</Button>
    </div>
  );
}
