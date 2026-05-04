"use client";

import { SignIn } from "@clerk/nextjs";

import { useIsMounted } from "@/hooks/use-is-mounted";

/**
 * Sign-in page.
 *
 * Why the mount gate
 * ------------------
 * Clerk's `<SignIn />` component injects a host div with
 * `data-clerk-component="SignIn"` only on the client. If we render it
 * during SSR / RSC pre-render, the server emits the wrapper without that
 * host node and the first client paint adds it, which React reports as a
 * hydration mismatch (the previous attempt fixed it via
 * `dynamic(...,{ ssr: false })`, but the Suspense boundary that wraps
 * had its own SSR/CSR drift on Next 16 + React 19).
 *
 * `useIsMounted` keeps both the server output and the first client paint
 * at the same `<div>{null}</div>`, then mounts `<SignIn />` after React
 * commits. No Suspense boundary, no `dynamic`, no mismatch.
 */
export default function Page() {
  const isMounted = useIsMounted();
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100 dark:bg-slate-900">
      {isMounted ? (
        <SignIn
          routing="path"
          path="/sign-in"
          appearance={{
            elements: {
              footerAction: "!hidden",
              footerActionText: "!hidden",
              footerActionLink: "!hidden",
            },
            layout: {
              socialButtonsPlacement: "bottom",
              showOptionalFields: false,
            },
          }}
          signUpUrl={undefined}
          fallbackRedirectUrl="/"
        />
      ) : null}
    </div>
  );
}
