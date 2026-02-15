import type { Metadata } from "next";
import { ClerkProvider } from '@clerk/nextjs'
import { currentUser } from '@clerk/nextjs/server';
import ForbiddenPage from "./forbidden/page";
import "../globals.css";
import Providers from "../providers";

export const metadata: Metadata = {
  title: "Client Dashboard",
  description: "Visionarias Client Dashboard",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = await currentUser();
  // Check if user is authenticated but has no tenant linked
  // Note: Middleware ensures user is logged in for protected routes, 
  // but we double check here to prevent rendering the app without context.
  const isAuth = !!user;
  const hasTenant = user?.publicMetadata?.tenant_id;
  const showForbidden = isAuth && !hasTenant;

  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="font-sans antialiased">
            <Providers>
            {showForbidden ? <ForbiddenPage /> : children}
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}