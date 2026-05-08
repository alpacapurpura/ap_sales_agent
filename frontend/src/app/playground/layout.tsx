import { ClerkProvider } from "@clerk/nextjs";
import { redirect } from "next/navigation";

/**
 * Playground layout — dev-only. Wraps children with ClerkProvider so
 * action components that call useAuth() work without errors.
 * Redirects to "/" in production (guard for accidental public access).
 */
export default function PlaygroundLayout({ children }: { children: React.ReactNode }) {
  if (process.env.NODE_ENV === "production") {
    redirect("/");
  }
  return <ClerkProvider>{children}</ClerkProvider>;
}
