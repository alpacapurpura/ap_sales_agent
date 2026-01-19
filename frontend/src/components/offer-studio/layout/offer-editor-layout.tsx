"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { 
  LayoutDashboard, 
  Users, 
  ShieldAlert, 
  Library, 
  ChevronLeft 
} from "lucide-react";

interface SidebarProps {
  offerId: string;
}

export function OfferEditorLayout({ children, offerId }: { children: React.ReactNode, offerId: string }) {
  const pathname = usePathname();
  
  const items = [
    {
      title: "Resumen",
      href: `/offer-studio/offer/${offerId}`,
      icon: LayoutDashboard,
      exact: true
    },
    {
      title: "Avatar & Personalidad",
      href: `/offer-studio/offer/${offerId}/avatar`,
      icon: Users
    },
    {
      title: "Matriz de Objeciones",
      href: `/offer-studio/offer/${offerId}/objections`,
      icon: ShieldAlert
    },
    {
      title: "Base de Conocimiento",
      href: `/offer-studio/offer/${offerId}/knowledge`,
      icon: Library
    }
  ];

  return (
    <div className="flex flex-col h-full">
       {/* Header de Navegación */}
       <div className="flex items-center gap-4 px-6 py-4 border-b bg-background">
          <Link href="/offer-studio">
            <Button variant="ghost" size="icon">
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h2 className="text-lg font-semibold">High Ticket Mentorship</h2>
            <p className="text-xs text-muted-foreground">Editando Oferta</p>
          </div>
       </div>

       <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Lateral */}
          <aside className="w-64 border-r bg-muted/10 hidden md:block overflow-y-auto">
             <nav className="flex flex-col gap-1 p-4">
                {items.map((item) => {
                  const isActive = item.exact 
                    ? pathname === item.href
                    : pathname.startsWith(item.href);
                  
                  return (
                    <Link key={item.href} href={item.href}>
                       <Button 
                        variant={isActive ? "secondary" : "ghost"} 
                        className={cn("w-full justify-start", isActive && "bg-secondary font-medium")}
                       >
                         <item.icon className="mr-2 h-4 w-4" />
                         {item.title}
                       </Button>
                    </Link>
                  );
                })}
             </nav>
          </aside>

          {/* Contenido Principal */}
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
       </div>
    </div>
  );
}
