# UI-SPEC — PR-1 telegram-bot-foundation (Frontend)

> Owner: PM main thread (post architect agent timeout). Frontend builder consume este file + CONTRACT.md.

## §1 User journey

```
[1] Settings sidebar → "Copilot" → "Conectar Telegram"
   ↓
[2] /settings/copilot/telegram page
   - state idle: muestra explicación + botón "Conectar Telegram"
   - state linked: muestra "Tu cuenta Telegram está conectada (●***12345)" + botón "Desvincular"
   ↓
[3] Click "Conectar Telegram"
   - POST /api/v1/copilot/telegram/link-tokens (auth)
   - recibe {token_id, deep_link_url, expires_at}
   - state requesting → waiting
   - window.open(deep_link_url, '_blank') → abre Telegram (app o web)
   - inicia polling /link-status?token_id=X cada 3s × 60s
   ↓
[4a] Bot bind exitoso (DB linked_at set)
   - polling detecta linked: true
   - state linked: muestra success + chat_id masked
[4b] Timeout 60s sin link
   - state timeout: muestra "No detectamos conexión. ¿Quieres intentar de nuevo?"
   - botón "Reintentar" (regenera token)
[4c] Token expira (15 min en DB)
   - manejado igual que timeout
[4d] Error red
   - state error: muestra mensaje + botón "Reintentar"
```

## §2 Route

`frontend/src/app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/page.tsx`

Server Component default. Toda interacción dentro de Client Component island.

## §3 File tree

```
frontend/src/
├── app/(main)/[tenantId]/(dashboard)/settings/copilot/telegram/
│   ├── page.tsx                          ← Server Component (metadata + shell)
│   └── _components/
│       └── TelegramLinkingClient.tsx     ← "use client" — todo el state interactivo
├── features/copilot/
│   ├── api/
│   │   ├── use-create-telegram-link-token.ts    ← React Query mutation
│   │   ├── use-telegram-link-status.ts          ← React Query polling
│   │   ├── use-unlink-telegram.ts               ← React Query mutation
│   │   └── use-telegram-current-link.ts         ← React Query query (current state)
│   └── types/
│       └── telegram.ts                          ← Zod schemas + inferred TS types
```

## §4 Components

### `page.tsx` (Server Component)

```tsx
import { Metadata } from "next";
import { TelegramLinkingClient } from "./_components/TelegramLinkingClient";

export const metadata: Metadata = {
  title: "Conectar Telegram | Nicolify Copilot",
};

export default function TelegramSettingsPage() {
  return (
    <div className="container max-w-2xl py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Conectar Telegram</h1>
        <p className="text-muted-foreground mt-2">
          Conversa con tu copilot desde Telegram. Consulta tu negocio, deja
          encargos y recibe alertas, todo desde tu celular.
        </p>
      </header>
      <TelegramLinkingClient />
    </div>
  );
}
```

### `TelegramLinkingClient.tsx` (Client Component)

State machine: `idle | requesting | waiting | linked | timeout | error`

```tsx
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle2, AlertCircle, Send } from "lucide-react";

import { useCreateTelegramLinkToken } from "@/features/copilot/api/use-create-telegram-link-token";
import { useTelegramLinkStatus } from "@/features/copilot/api/use-telegram-link-status";
import { useUnlinkTelegram } from "@/features/copilot/api/use-unlink-telegram";
import { useTelegramCurrentLink } from "@/features/copilot/api/use-telegram-current-link";

type LinkingState =
  | { kind: "idle" }
  | { kind: "linked"; chatIdMasked: string; linkedAt: string }
  | { kind: "requesting" }
  | { kind: "waiting"; tokenId: string; deepLinkUrl: string; expiresAt: string }
  | { kind: "timeout"; tokenId: string }
  | { kind: "error"; message: string };

export function TelegramLinkingClient() {
  const currentLink = useTelegramCurrentLink();
  const createToken = useCreateTelegramLinkToken();
  const unlink = useUnlinkTelegram();

  const [state, setState] = useState<LinkingState>({ kind: "idle" });

  // Initialize state from current link query
  useEffect(() => {
    if (currentLink.data?.linked) {
      setState({
        kind: "linked",
        chatIdMasked: currentLink.data.channel_user_id_masked!,
        linkedAt: currentLink.data.linked_at!,
      });
    }
  }, [currentLink.data]);

  // Polling hook (only active when state.kind === "waiting")
  const linkStatus = useTelegramLinkStatus(
    state.kind === "waiting" ? state.tokenId : null
  );

  // Transition: waiting → linked when polling detects linked
  useEffect(() => {
    if (state.kind === "waiting" && linkStatus.data?.linked) {
      setState({
        kind: "linked",
        chatIdMasked: linkStatus.data.channel_user_id_masked!,
        linkedAt: linkStatus.data.linked_at!,
      });
    }
  }, [linkStatus.data, state.kind]);

  // Timeout 60s
  useEffect(() => {
    if (state.kind !== "waiting") return;
    const timer = setTimeout(() => {
      setState((s) =>
        s.kind === "waiting" ? { kind: "timeout", tokenId: s.tokenId } : s
      );
    }, 60_000);
    return () => clearTimeout(timer);
  }, [state.kind]);

  const handleConnect = async () => {
    setState({ kind: "requesting" });
    try {
      const data = await createToken.mutateAsync();
      window.open(data.deep_link_url, "_blank", "noopener,noreferrer");
      setState({
        kind: "waiting",
        tokenId: data.token_id,
        deepLinkUrl: data.deep_link_url,
        expiresAt: data.expires_at,
      });
    } catch (err) {
      setState({ kind: "error", message: (err as Error).message });
    }
  };

  const handleUnlink = async () => {
    try {
      await unlink.mutateAsync();
      setState({ kind: "idle" });
    } catch (err) {
      setState({ kind: "error", message: (err as Error).message });
    }
  };

  const handleRetry = () => setState({ kind: "idle" });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Telegram
        </CardTitle>
      </CardHeader>
      <CardContent>
        {state.kind === "idle" && <IdleView onConnect={handleConnect} />}
        {state.kind === "requesting" && <RequestingView />}
        {state.kind === "waiting" && (
          <WaitingView
            deepLinkUrl={state.deepLinkUrl}
            onCancel={handleRetry}
          />
        )}
        {state.kind === "linked" && (
          <LinkedView
            chatIdMasked={state.chatIdMasked}
            linkedAt={state.linkedAt}
            onUnlink={handleUnlink}
            isUnlinking={unlink.isPending}
          />
        )}
        {state.kind === "timeout" && <TimeoutView onRetry={handleRetry} />}
        {state.kind === "error" && (
          <ErrorView message={state.message} onRetry={handleRetry} />
        )}
      </CardContent>
    </Card>
  );
}
```

### Sub-views (resumen)

| View | Contenido principal |
|---|---|
| `IdleView` | Explicación 2 líneas + Shadcn `<Button>` "Conectar Telegram" |
| `RequestingView` | `<Loader2 className="animate-spin" />` "Generando enlace..." |
| `WaitingView` | "Abrimos Telegram en otra pestaña. Habla al bot para terminar." + botón "Cancelar" + helper "Si no se abre, abre Telegram aquí: <a href={deepLinkUrl}>Abrir Telegram</a>" |
| `LinkedView` | `<CheckCircle2 className="text-green-600" />` "Tu Telegram está conectado (chat ●***{chatIdMasked}). Vinculado el {linkedAt formatted}." + Shadcn `<Button variant="destructive" disabled={isUnlinking}>` "Desvincular" |
| `TimeoutView` | `<AlertCircle />` "No detectamos la conexión. Revisa Telegram o inténtalo de nuevo." + botón "Reintentar" |
| `ErrorView` | Shadcn `<Alert variant="destructive">` "Algo salió mal: {message}" + botón "Reintentar" |

## §5 Hooks (React Query — `tessl__react-patterns` rule)

### `use-create-telegram-link-token.ts`

```ts
import { useMutation } from "@tanstack/react-query";
import { fetchClient } from "@/lib/fetch-client";
import { LinkTokenResponseSchema, type LinkTokenResponse } from "../types/telegram";

export function useCreateTelegramLinkToken() {
  return useMutation<LinkTokenResponse, Error>({
    mutationFn: async () => {
      const res = await fetchClient("/api/v1/copilot/telegram/link-tokens", {
        method: "POST",
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to create link token");
      const json = await res.json();
      return LinkTokenResponseSchema.parse(json);
    },
  });
}
```

### `use-telegram-link-status.ts` (polling)

```ts
import { useQuery } from "@tanstack/react-query";
import { fetchClient } from "@/lib/fetch-client";
import { LinkStatusResponseSchema, type LinkStatusResponse } from "../types/telegram";

export function useTelegramLinkStatus(tokenId: string | null) {
  return useQuery<LinkStatusResponse>({
    queryKey: ["copilot-telegram-link-status", tokenId],
    enabled: !!tokenId,
    refetchInterval: (data) => (data?.linked ? false : 3000),
    refetchIntervalInBackground: false,
    queryFn: async () => {
      const res = await fetchClient(
        `/api/v1/copilot/telegram/link-status?token_id=${tokenId}`,
      );
      if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
      return LinkStatusResponseSchema.parse(await res.json());
    },
  });
}
```

### `use-telegram-current-link.ts`

Calls `GET /api/v1/copilot/telegram/link-status` WITHOUT `token_id` (returns current link state for tenant+user). NOTE for builder: backend may need to support optional `token_id` param OR add separate endpoint `GET /api/v1/copilot/telegram/link`. Flag during architect.

### `use-unlink-telegram.ts`

```ts
import { useMutation, useQueryClient } from "@tanstack/react-query";

export function useUnlinkTelegram() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await fetchClient("/api/v1/copilot/telegram/link", {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to unlink");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["copilot-telegram-current-link"] });
    },
  });
}
```

## §6 Zod schemas (`features/copilot/types/telegram.ts`)

```ts
import { z } from "zod";

export const LinkTokenResponseSchema = z.object({
  token_id: z.string().uuid(),
  deep_link_url: z.string().url(),
  expires_at: z.string().datetime(),
});
export type LinkTokenResponse = z.infer<typeof LinkTokenResponseSchema>;

export const LinkStatusResponseSchema = z.object({
  linked: z.boolean(),
  channel_user_id_masked: z.string().nullable(),
  linked_at: z.string().datetime().nullable(),
});
export type LinkStatusResponse = z.infer<typeof LinkStatusResponseSchema>;
```

## §7 Spanish neutro tuteo (rule `spanish-text.md`)

| Texto | OK | Anti-pattern |
|---|---|---|
| "Conecta tu Telegram" | ✅ | ❌ "Conectá" voseo |
| "Habla al bot" | ✅ | ❌ "Hablá" voseo |
| "Si no se abre, haz click aquí" | ✅ | ❌ "hace click acá" voseo + LATAM regional |
| "Aquí tienes el link directo" | ✅ | ❌ "Acá tenés el link" |
| "Tu Telegram está conectado" | ✅ | ✅ |

Builder verifica TODOS los strings contra `spanish-glossary.md` antes de commit.

## §8 Accesibilidad (`tessl__react-patterns` baseline)

- Botones todos `<Button>` Shadcn (focus ring + disabled visible)
- Loading: `<Loader2 className="animate-spin" />` + `aria-live="polite"` en text status
- Alerts: Shadcn `<Alert>` con `role="alert"`
- Deep link: `<a target="_blank" rel="noopener noreferrer">` + descriptive text
- Keyboard nav: tab order natural
- Color contrast: tokens Shadcn (WCAG AA)

## §9 Edge cases UI

| Caso | Manejo |
|---|---|
| User abandona modal antes de hablar al bot | timeout 60s → state timeout → cleanup polling |
| User reabre tab durante polling | React Query `refetchOnWindowFocus` default — ok |
| User unmount component durante polling | useQuery auto-cancel via `enabled` switch |
| User vincula Telegram a otra cuenta Nicolify previa | Backend rechaza (UNIQUE constraint) → 409 → state error |
| Bot no responde tras /start TOKEN | timeout 60s → state timeout → user retries |
| Token expira en backend (15 min) antes que polling lo detecte | /link-status devuelve linked=false → eventualmente timeout state |

## §10 Testing (Vitest + React Testing Library)

Cobertura mínima:
- `TelegramLinkingClient.test.tsx` — render por estado (idle, waiting, linked, error, timeout)
- `use-telegram-link-status.test.ts` — polling cancel al unmount, refetchInterval=false cuando linked
- `use-create-telegram-link-token.test.ts` — Zod schema parse correcto
- `use-unlink-telegram.test.ts` — mutation + invalidate query key

## §11 Open questions for PM

1. ¿Existe ya `fetchClient` en `lib/`? Confirma path exacto durante builder. Pattern import: `@/lib/fetch-client`.
2. ¿Settings sidebar tiene grupo "Copilot" hoy o builder añade? Si nuevo grupo → cambio sidebar config (cohesivo con este PR-1).
3. Backend NEED endpoint adicional `GET /api/v1/copilot/telegram/link` (sin `token_id`) para `useTelegramCurrentLink`. CONTRACT debe formalizar — flag § 16.
4. ¿Mostrar warning anti-fraud "Solo usa Telegram con la cuenta del bot oficial @nicolify_copilot_bot — NO compartas el link con nadie"? Recommended yes (anti-phishing).
