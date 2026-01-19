"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  LayoutDashboard, 
  Database, 
  Activity, 
  Settings,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Briefcase,
  Users
} from "lucide-react";
import { UserButton } from "@clerk/nextjs";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { useSidebar } from "./sidebar-context";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { ModeToggle } from "@/components/mode-toggle";

const navItems = [
  {
    title: "Resumen",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Offer Studio",
    href: "/offer-studio",
    icon: Briefcase,
  },
  {
    title: "Avatares de Marca",
    href: "/avatars",
    icon: Users,
  },
  {
    title: "Conocimiento",
    href: "/knowledge",
    icon: Database,
  },
  {
    title: "Auditoría",
    href: "/audit",
    icon: Activity,
  },
  {
    title: "Configuración",
    href: "/settings",
    icon: Settings,
  },
];

interface NavContentProps {
  mobile?: boolean;
  isCollapsed: boolean;
  toggleSidebar: () => void;
  setIsMobileOpen: (open: boolean) => void;
  pathname: string;
}

// Extracted component to avoid re-creation on render and scope issues
function NavContent({ mobile = false, isCollapsed, toggleSidebar, setIsMobileOpen, pathname }: NavContentProps) {
  return (
    <div className="flex h-full flex-col gap-4">
      <div className={cn("flex h-16 items-center px-4 border-b", isCollapsed && !mobile ? "justify-center" : "justify-between")}>
        {!isCollapsed || mobile ? (
          <span className="text-lg font-bold tracking-tight text-primary truncate">Visionarias AI</span>
        ) : (
          <span className="text-lg font-bold tracking-tight text-primary">V</span>
        )}
        
        {!mobile && (
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={toggleSidebar} 
            className="hidden md:flex h-8 w-8 text-muted-foreground"
          >
            {isCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
          </Button>
        )}
      </div>

      <div className="flex-1 px-3 py-2">
        <nav className="grid gap-1">
          <TooltipProvider delayDuration={0}>
            {navItems.map((item, index) => {
              const isActive = pathname === item.href;
              
              const LinkContent = (
                <Link
                  key={index}
                  href={item.href}
                  onClick={() => mobile && setIsMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all group relative",
                    isActive 
                      ? "bg-primary/10 text-primary" 
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    isCollapsed && !mobile && "justify-center px-2"
                  )}
                >
                  <item.icon className={cn("h-4 w-4 shrink-0", isActive && "text-primary")} />
                  {(!isCollapsed || mobile) && <span>{item.title}</span>}
                </Link>
              );

              if (isCollapsed && !mobile) {
                return (
                  <Tooltip key={index}>
                    <TooltipTrigger asChild>
                      {LinkContent}
                    </TooltipTrigger>
                    <TooltipContent side="right" className="font-medium">
                      {item.title}
                    </TooltipContent>
                  </Tooltip>
                );
              }

              return LinkContent;
            })}
          </TooltipProvider>
        </nav>
      </div>

      <div className="border-t p-4">
        <div className={cn("flex items-center justify-between px-2", isCollapsed && !mobile && "flex-col justify-center gap-4 px-0")}>
          <div className="flex items-center gap-3">
            <UserButton afterSignOutUrl="/sign-in" />
            {(!isCollapsed || mobile) && (
              <div className="flex flex-col overflow-hidden">
                <span className="text-sm font-medium truncate">Cuenta</span>
                <span className="text-xs text-muted-foreground truncate">Gestión de perfil</span>
              </div>
            )}
          </div>
          <ModeToggle />
        </div>
      </div>
    </div>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { isCollapsed, toggleSidebar } = useSidebar();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside 
        className={cn(
          "hidden border-r bg-card md:flex md:flex-col fixed inset-y-0 z-50 transition-all duration-300 ease-in-out",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        <NavContent 
          isCollapsed={isCollapsed} 
          toggleSidebar={toggleSidebar} 
          setIsMobileOpen={setIsMobileOpen}
          pathname={pathname}
        />
      </aside>

      {/* Mobile Header & Sidebar */}
      <div className="flex h-16 items-center border-b bg-background px-4 md:hidden fixed inset-x-0 top-0 z-50">
        <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="mr-2">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="p-0 w-72" aria-describedby="mobile-nav-desc">
            <SheetTitle className="sr-only">Menú de Navegación</SheetTitle>
            <div id="mobile-nav-desc" className="sr-only">Menú de navegación principal</div>
            <NavContent 
              mobile 
              isCollapsed={isCollapsed} 
              toggleSidebar={toggleSidebar} 
              setIsMobileOpen={setIsMobileOpen}
              pathname={pathname}
            />
          </SheetContent>
        </Sheet>
        <span className="font-bold">Visionarias Dashboard</span>
      </div>
    </>
  );
}
