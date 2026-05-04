"use client";

import dynamic from "next/dynamic";

const SignIn = dynamic(
  () => import("@clerk/nextjs").then((m) => ({ default: m.SignIn })),
  { ssr: false, loading: () => null },
);

export default function Page() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-100 dark:bg-slate-900">
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
    </div>
  );
}
