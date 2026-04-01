import type { Metadata } from "next";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "Nicolify",
};

export default function PublicSiteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="antialiased">{children}</body>
    </html>
  );
}
