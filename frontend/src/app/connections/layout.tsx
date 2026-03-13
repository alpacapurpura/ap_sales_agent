import { ClerkProvider } from "@clerk/nextjs";
import "../globals.css";

export default function ConnectionsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="font-sans antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}
