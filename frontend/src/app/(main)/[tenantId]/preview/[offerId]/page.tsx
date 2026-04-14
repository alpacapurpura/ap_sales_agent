import { notFound } from "next/navigation";
import { cookies } from "next/headers";
import { SqueezeServerTpl } from "@/features/offer-studio/components/landing/templates/server/SqueezeServerTpl";
import { TransformerServerTpl } from "@/features/offer-studio/components/landing/templates/server/TransformerServerTpl";
import {
  LandingPageArchetype,
  LandingPageConfig,
  SqueezeContent,
  TransformerContent,
} from "@/features/offer-studio/components/landing/types/schema";
import { config } from "@/lib/config";

// --- DATA FETCHING (Authenticated) ---
async function getLandingPageConfig(
  offerId: string,
  tenantId: string,
): Promise<LandingPageConfig | null> {
  try {
    const apiUrl = config.api.baseUrl;
    const cookieStore = await cookies();
    // Use Clerk session token logic if available, or custom auth_token
    // In Clerk, usually '__session' or verify token via auth() helper
    // Assuming simple auth_token cookie for this custom implementation
    const token = cookieStore.get("__session")?.value || cookieStore.get("auth_token")?.value;

    if (!token) {
      // --- DEV BYPASS ---
      // If we are in dev mode, we might want to fetch without token for debugging or if cookies are not set properly in SSR
      if (process.env.NODE_ENV === "development") {
        try {
          const res = await fetch(`${apiUrl}/api/v1/offers/${offerId}/landing`, {
            headers: {
              "X-Tenant-ID": tenantId,
            },
            cache: "no-store",
          });
          if (res.ok) return await res.json();
        } catch (e) {
          console.error(`[Preview] Dev fetch exception:`, e);
        }
      }

      return null;
    }

    // Fetch from Backend Authenticated API
    // Using the same endpoint the editor uses
    const res = await fetch(`${apiUrl}/api/v1/offers/${offerId}/landing`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "X-Tenant-ID": tenantId,
      },
      cache: "no-store", // Always fresh for preview
    });

    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch landing page config:", error);
    return null;
  }
}

// Preview Banner (extracted to module scope for ESLint react-hooks/static-components)
function PreviewBanner() {
  return (
    <div className="fixed top-0 left-0 right-0 bg-indigo-600 text-white text-xs font-bold py-2 text-center z-50 shadow-md">
      MODO VISTA PREVIA - Solo tú puedes ver esto
    </div>
  );
}

// PREVIEW PAGE COMPONENT (SERVER SIDE)
export default async function LandingPreviewPage({
  params,
}: {
  params: Promise<{ offerId: string; tenantId: string }>;
}) {
  const { offerId, tenantId } = await params;
  const landing = await getLandingPageConfig(offerId, tenantId);

  if (!landing) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50">
        <div className="text-center p-8">
          <h1 className="text-2xl font-bold text-slate-800 mb-2">Vista Previa No Disponible</h1>
          <p className="text-slate-600">
            No se pudo cargar la configuración de la landing. Asegúrate de haber guardado los
            cambios.
          </p>
        </div>
      </div>
    );
  }

  // ROUTER: Decide which template to render based on Archetype
  let template;
  switch (landing.archetype) {
    case LandingPageArchetype.THE_SQUEEZE:
      template = (
        <SqueezeServerTpl content={landing.content as SqueezeContent} theme={landing.theme} />
      );
      break;

    case LandingPageArchetype.THE_TRANSFORMER:
      template = (
        <TransformerServerTpl
          content={landing.content as TransformerContent}
          theme={landing.theme}
        />
      );
      break;

    // TODO: Add other cases
    case LandingPageArchetype.THE_EVENT:
      template = <div>Event Template Coming Soon</div>;
      break;

    default:
      template = <div>Template Not Found: {landing.archetype}</div>;
  }

  return (
    <div className="pt-8">
      {" "}
      {/* Padding for banner */}
      <PreviewBanner />
      {template}
    </div>
  );
}
