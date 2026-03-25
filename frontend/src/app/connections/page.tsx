import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import { OAuthCallbackHandler } from "@/features/connections/components/oauth-callback-handler";

export default function ConnectionsCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      }
    >
      <OAuthCallbackHandler provider="auto" />
    </Suspense>
  );
}
