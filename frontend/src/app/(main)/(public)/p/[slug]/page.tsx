import { notFound } from "next/navigation";

import { SqueezeServerTpl } from "@/features/offer-studio/components/landing/templates/server/SqueezeServerTpl";
import { LandingPageArchetype } from "@/features/offer-studio/components/landing/types/schema";
import { config } from "@/lib/config";

import type {
  LandingPageConfig,
  SqueezeContent,
} from "@/features/offer-studio/components/landing/types/schema";
import type { Metadata } from "next";

// --- DATA FETCHING ---

async function getLandingPage(slug: string, tenantId: string): Promise<LandingPageConfig | null> {
  try {
    const res = await fetch(`${config.api.baseUrl}/api/v1/public/landing/${slug}`, {
      headers: {
        ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
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
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

// 1. GENERATE METADATA (SEO)
/**
 *
 */
export async function generateMetadata({ params, searchParams }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const query = await searchParams;
  const tenantId = typeof query.tenant === "string" ? query.tenant : "";
  const landing = await getLandingPage(slug, tenantId);

  if (!landing) {
    return { title: "Página no encontrada" };
  }

  return {
    title: landing.seo_title ?? (landing.content as SqueezeContent).headline,
    description: landing.seo_description,
    openGraph: {
      title: landing.seo_title ?? undefined,
      description: landing.seo_description ?? undefined,
      type: "website",
    },
    robots: {
      index: landing.is_published,
      follow: landing.is_published,
    },
  };
}

// 2. PAGE COMPONENT (SERVER SIDE)
/**
 *
 */
export default async function LandingPage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const query = await searchParams;
  // Backward-compat: tenant UUID passed as ?tenant=<uuid> query param
  const tenantId = typeof query.tenant === "string" ? query.tenant : "";

  const landing = await getLandingPage(slug, tenantId);

  if (!landing?.is_published) {
    notFound();
  }

  switch (landing.archetype) {
    case LandingPageArchetype.THE_SQUEEZE:
      return <SqueezeServerTpl content={landing.content as SqueezeContent} theme={landing.theme} />;
    case LandingPageArchetype.THE_EVENT:
      return <div>Event Template Coming Soon</div>;
    default:
      return <div>Template Not Found</div>;
  }
}
