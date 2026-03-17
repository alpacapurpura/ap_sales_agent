import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nicolify",
  description: "AI Sales & Marketing Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {process.env.NODE_ENV === 'development' && (
          <script src="https://mcp.figma.com/mcp/html-to-design/capture.js" async />
        )}
      </head>
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
