import { redirect } from 'next/navigation';
import { currentUser } from '@clerk/nextjs/server';

export default async function RootPage() {
  const user = await currentUser();
  
  // Default to first tenant or a specific one if stored in user metadata
  // Ideally, we fetch the list of tenants and pick the last active one.
  // For now, we can redirect to a "select-org" page or just try to resolve via client side if server side is hard.
  // But this is a Server Component.
  
  // If user has a tenant_id in metadata (set by our backend on login usually), use it.
  const lastTenantId = user?.publicMetadata?.tenant_id as string;
  
  if (lastTenantId) {
    // Redirect to the default landing page for the tenant (Brand Settings)
    // Note: (dashboard) is a route group, so the URL is just /[tenantId]/brand-settings
    redirect(`/${lastTenantId}/brand-settings`);
  }
  
  // If no tenant found, redirect to onboarding or tenant selection
  // Assuming /onboarding exists or we let the middleware handle it.
  // For now, let's redirect to a safe "select-org" or "onboarding" if available.
  // Or if we don't have that, we might need to fetch tenants.
  
  // Since we don't have easy access to DB here without backend call, 
  // and we moved the dashboard to [tenantId], we can't show dashboard here.
  
  redirect('/onboarding');
}
