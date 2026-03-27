import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";

export const dynamic = 'force-dynamic';
import Providers from "../providers";
import { Suspense } from "react";
import { TenantGuard } from "@/components/auth/tenant-guard";

export const metadata: Metadata = {
  title: "Nicolify - Dashboard",
  description: "AI Sales & Marketing Dashboard",
};

function LoadingScreen() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground animate-pulse">Cargando dashboard...</p>
      </div>
    </div>
  );
}

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <Providers>
        <Suspense fallback={<LoadingScreen />}>
          <TenantGuard>
            {children}
          </TenantGuard>
        </Suspense>
      </Providers>
    </ClerkProvider>
  );
}
