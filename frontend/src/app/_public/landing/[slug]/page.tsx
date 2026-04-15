import { headers } from "next/headers";
import { notFound } from "next/navigation";

import { SqueezeServerTpl } from "@/features/offer-studio/components/landing/templates/server/SqueezeServerTpl";
import { LandingPageArchetype } from "@/features/offer-studio/components/landing/types/schema";
import { config } from "@/lib/config";

import type {
  LandingPageConfig,
  SqueezeContent,
} from "@/features/offer-studio/components/landing/types/schema";
import type { Metadata } from "next";

async function getPublicLanding(slug: string, tenantId: string): Promise<LandingPageConfig | null> {
  try {
    const res = await fetch(`${config.api.baseUrl}/api/v1/public/landing/${slug}`, {
      headers: {
        "X-Tenant-ID": tenantId,
      },
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json() as Promise<LandingPageConfig>;
  } catch {
    return null;
  }
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";
  const landing = await getPublicLanding(slug, tenantId);

  if (!landing) return { title: "Página no encontrada" };

  return {
    title: landing.seo_title ?? (landing.content as SqueezeContent).headline,
    description: landing.seo_description,
    robots: { index: true, follow: true },
  };
}

export default async function PublicLandingPage({ params }: PageProps) {
  const { slug } = await params;
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";

  if (!tenantId) notFound();

  const landing = await getPublicLanding(slug, tenantId);
  if (!landing) notFound();

  switch (landing.archetype) {
    case LandingPageArchetype.THE_SQUEEZE:
      return <SqueezeServerTpl content={landing.content as SqueezeContent} theme={landing.theme} />;
    default:
      return <div>Template en construcción</div>;
  }
}
