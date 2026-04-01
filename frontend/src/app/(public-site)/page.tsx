import { headers } from "next/headers";
import { redirect, notFound } from "next/navigation";
import { config } from "@/lib/config";

interface LandingItem {
  slug: string;
  is_published: boolean;
}

async function getFirstPublishedLanding(tenantId: string): Promise<string | null> {
  try {
    const res = await fetch(`${config.api.baseUrl}/api/v1/landings/`, {
      headers: { "X-Tenant-ID": tenantId },
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    const landings = (await res.json()) as LandingItem[];
    const published = landings.find((l) => l.is_published);
    return published?.slug ?? null;
  } catch {
    return null;
  }
}

export default async function TenantHomepage() {
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";

  if (!tenantId) notFound();

  const slug = await getFirstPublishedLanding(tenantId);
  if (slug) {
    redirect(`/landing/${slug}`);
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 text-center">
      <h1 className="text-2xl font-semibold text-foreground">Sitio en construcción</h1>
      <p className="mt-2 text-muted-foreground">Este sitio estará disponible pronto.</p>
    </main>
  );
}
