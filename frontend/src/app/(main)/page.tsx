"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";

export default function RootPage() {
  const { user, isLoaded } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!isLoaded) return;

    if (user) {
      const lastTenantId = user.publicMetadata?.tenant_id as string;
      if (lastTenantId) {
        router.replace(`/${lastTenantId}/brand-studio/esencia`);
      } else {
        router.replace('/onboarding');
      }
    } else {
      // In case middleware missed it
      router.replace('/sign-in');
    }
  }, [user, isLoaded, router]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground animate-pulse">Redirigiendo...</p>
      </div>
    </div>
  );
}
