import { notFound } from 'next/navigation';
import { Metadata } from 'next';
import { SqueezeServerTpl } from '@/features/offer-studio/components/landing/templates/server/SqueezeServerTpl';
import { LandingPageArchetype, LandingPageConfig, SqueezeContent } from '@/features/offer-studio/components/landing/types/schema';
import { config } from '@/lib/config';

// --- DATA FETCHING ---

async function getLandingPage(slug: string): Promise<LandingPageConfig | null> {
  try {
    // Use centralized config for consistent URL resolution
    const apiUrl = config.api.baseUrl;
    
    // Fetch from Backend Public API
    // Revalidate every 60 seconds (ISR)
    const res = await fetch(`${apiUrl}/api/v1/offers/public/${slug}`, {
      next: { revalidate: 60 }
    });

    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error("Failed to fetch landing page:", error);
    return null;
  }
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

// 1. GENERATE METADATA (SEO)
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const landing = await getLandingPage(slug);
  
  if (!landing) {
    return { title: 'Página no encontrada' };
  }

  return {
    title: landing.seo_title || (landing.content as any).headline,
    description: landing.seo_description || (landing.content as any).subheadline,
    openGraph: {
      title: landing.seo_title,
      description: landing.seo_description,
      type: 'website',
    },
    robots: {
      index: landing.is_published,
      follow: landing.is_published,
    }
  };
}

// 2. STATIC PARAMS (SSG) - Optional
// We can omit this to use purely ISR on demand, or fetch list of all published offers
// For high traffic, implementing this with a list endpoint is better.
// For now, let's skip pre-building ALL pages to save build time.
// export async function generateStaticParams() { ... }

// 3. PAGE COMPONENT (SERVER SIDE)
export default async function LandingPage({ params }: PageProps) {
  const { slug } = await params;
  const landing = await getLandingPage(slug);

  if (!landing || !landing.is_published) {
    notFound();
  }

  // ROUTER: Decide which template to render based on Archetype
  switch (landing.archetype) {
    case LandingPageArchetype.THE_SQUEEZE:
      return (
        <SqueezeServerTpl 
          content={landing.content as SqueezeContent} 
          theme={landing.theme} 
        />
      );
    
    // TODO: Add other cases (Event, Flash, etc.)
    case LandingPageArchetype.THE_EVENT:
      return <div>Event Template Coming Soon</div>;
      
    default:
      return <div>Template Not Found</div>;
  }
}
