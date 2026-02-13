import type { Metadata } from "next";
import { ClerkProvider } from '@clerk/nextjs'
import "../globals.css";
import { Toaster } from "@/components/ui/sonner";

export const metadata: Metadata = {
  title: "Visionary Canvas | Editor",
  description: "Visionarias Landing Page Editor",
};

export default function EditorLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        {/* Editor Layout: Clean, no Sidebar, minimal styles */}
        <body className="font-sans antialiased bg-white text-slate-900 overflow-hidden">
            {children}
            <Toaster />
        </body>
      </html>
    </ClerkProvider>
  );
}