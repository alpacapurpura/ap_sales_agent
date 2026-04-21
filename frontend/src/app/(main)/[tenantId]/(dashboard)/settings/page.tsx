import { redirect } from "next/navigation";

import { OAuthCallbackHandler } from "@/features/connections/components/OauthCallbackHandler";

interface Props {
  params: Promise<{ tenantId: string }>;
  searchParams: Promise<{
    tab?: string;
    code?: string;
    error?: string;
    state?: string;
  }>;
}

/**
 * Settings root page.
 *
 * Handles three cases:
 * 1. OAuth popup callback (?code= or ?error=) — render OAuthCallbackHandler
 *    in-place so the popup can post a message to the opener and close itself.
 * 2. Legacy ?tab= redirects — map old tab slugs to new section slugs (308).
 * 3. Plain /settings → redirect to /settings/general.
 */
export default async function SettingsRootPage({ params, searchParams }: Props) {
  const { tenantId } = await params;
  const { tab, code, error } = await searchParams;

  // OAuth popup callback — must render before any redirect
  if (code ?? error) {
    return <OAuthCallbackHandler provider="auto" />;
  }

  const legacyMap: Record<string, string> = {
    profile: "perfil",
    team: "equipo",
    "ai-keys": "llm-keys",
    scheduling: "agenda",
    payments: "pagos",
    // these slugs are unchanged but still accepted
    general: "general",
    webhooks: "webhooks",
  };

  const resolved = tab ? (legacyMap[tab] ?? tab) : "general";
  redirect(`/${tenantId}/settings/${resolved}`);
}
