import NextTopLoader from "nextjs-toploader";

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nicolify - Dashboard",
  description: "AI Sales & Marketing Dashboard",
  icons: {
    icon: "/_temp/ico/ico-nicolify.ico",
  },
};

/**
 *
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <NextTopLoader
          color="hsl(222.2, 47.4%, 11.2%)"
          height={3}
          showSpinner={false}
          shadow={false}
          zIndex={9999}
        />
        {children}
      </body>
    </html>
  );
}
