import type { Metadata } from "next";
import { ClerkProvider } from '@clerk/nextjs';
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
      {/* Editor Layout: Clean, no Sidebar, minimal styles */}
      <div className="bg-white text-slate-900 overflow-hidden min-h-screen">
        {children}
        <Toaster />
      </div>
    </ClerkProvider>
  );
}