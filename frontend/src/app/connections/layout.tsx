import { ClerkProvider } from "@clerk/nextjs";

export const dynamic = "force-dynamic";

export default function ConnectionsLayout({ children }: { children: React.ReactNode }) {
  return <ClerkProvider>{children}</ClerkProvider>;
}
