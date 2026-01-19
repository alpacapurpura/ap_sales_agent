import type { Metadata } from "next";
import { ClerkProvider, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/nextjs'
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "Client Dashboard",
  description: "Visionarias Client Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="font-sans antialiased">
            <Providers>
            {children}
          </Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
