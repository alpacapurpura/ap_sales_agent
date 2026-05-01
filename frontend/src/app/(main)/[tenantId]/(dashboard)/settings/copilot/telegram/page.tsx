/**
 * Settings page: Conectar Telegram al Copilot (PI-5 PR-1).
 *
 * Server Component shell. Interactive state in `<TelegramLinkingClient />`.
 * Spanish neutro tuteo (rule `spanish-text.md`).
 */

import { TelegramLinkingClient } from "./_components/TelegramLinkingClient";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Conectar Telegram | Nicolify Copilot",
  description:
    "Conecta tu Telegram al copilot para consultar tu negocio y dejar encargos desde tu celular.",
};

/**
 *
 */
export default function CopilotTelegramSettingsPage() {
  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Conectar Telegram</h1>
        <p className="text-muted-foreground mt-2">
          Conversa con tu copilot desde Telegram. Consulta tu negocio, deja encargos y recibe
          alertas, todo desde tu celular.
        </p>
      </header>
      <TelegramLinkingClient />
    </div>
  );
}
