"use client";

import { UserButton, useUser } from "@clerk/nextjs";
import {
  Settings,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Briefcase,
  Building2,
  CalendarCheck,
  Megaphone,
  ChevronDown,
  Crosshair,
  UserSearch,
  Palette,
  LayoutDashboard,
  Headset,
  Users,
  Magnet,
  Sprout,
  ShoppingCart,
  UserCheck,
  Rocket,
  SlidersHorizontal,
  Cable,
  type LucideIcon,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { memo, useState, useEffect, useCallback, useMemo, useRef } from "react";

import { TenantSwitcher } from "@/components/shared/layout/tenant-switcher";
import { ModeToggle } from "@/components/shared/mode-toggle";
import { NavLink } from "@/components/shared/navigation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useUserProfile } from "@/features/settings/hooks/use-profile";
import { cn } from "@/lib/utils";

import { useSidebar } from "./sidebar-context";

// ---------------------------------------------------------------------------
// Navigation Configuration
// ---------------------------------------------------------------------------

interface NavChild {
  title: string;
  href: string;
  icon: LucideIcon;
}

interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  children?: NavChild[];
}

const getNavItems = (tenantId: string): NavItem[] => [
  {
    title: "Brand Studio",
    href: `/${tenantId}/brand-studio`,
    icon: Building2,
    children: [
      { title: "Esencia", href: `/${tenantId}/brand-studio/esencia`, icon: Building2 },
      { title: "Estrategia", href: `/${tenantId}/brand-studio/estrategia`, icon: Crosshair },
      { title: "Publico", href: `/${tenantId}/brand-studio/publico`, icon: UserSearch },
      {
        title: "Identidad Creativa",
        href: `/${tenantId}/brand-studio/identidad-creativa`,
        icon: Palette,
      },
    ],
  },
  {
    title: "Offer Studio",
    href: `/${tenantId}/offer-studio`,
    icon: Briefcase,
  },
  {
    title: "Growth Studio",
    href: `/${tenantId}/growth-studio`,
    icon: Megaphone,
    children: [
      { title: "Atracción", href: `/${tenantId}/growth-studio/atraccion-captura`, icon: Magnet },
      {
        title: "Nutrición",
        href: `/${tenantId}/growth-studio/nutricion-oportunidad`,
        icon: Sprout,
      },
      { title: "Ventas", href: `/${tenantId}/growth-studio/ventas`, icon: ShoppingCart },
      { title: "Adopción", href: `/${tenantId}/growth-studio/adopcion`, icon: UserCheck },
      {
        title: "Expansión",
        href: `/${tenantId}/growth-studio/expansion-evangelizacion`,
        icon: Rocket,
      },
    ],
  },
  {
    title: "Closer Studio",
    href: `/${tenantId}/sales`,
    icon: CalendarCheck,
    children: [
      { title: "Resumen", href: `/${tenantId}/sales/resumen`, icon: LayoutDashboard },
      { title: "Studio", href: `/${tenantId}/sales/studio/inbox`, icon: Headset },
      { title: "Contactos", href: `/${tenantId}/sales/contactos`, icon: Users },
    ],
  },
  {
    title: "Configuracion",
    href: `/${tenantId}/settings`,
    icon: Settings,
    children: [
      { title: "General", href: `/${tenantId}/settings`, icon: SlidersHorizontal },
      { title: "Conexiones", href: `/${tenantId}/connections`, icon: Cable },
    ],
  },
];

// ---------------------------------------------------------------------------
// Navigation Item Components
// ---------------------------------------------------------------------------

interface NavItemRendererProps {
  item: NavItem;
  pathname: string;
  mobile: boolean;
  isCollapsed: boolean;
  mounted: boolean;
  onMobileClose: () => void;
  expandedHref: string | null;
  onToggleExpand: (href: string) => void;
}

/** Renders a simple (leaf) nav item with optional tooltip when sidebar is collapsed. */
function SimpleNavItem({
  item,
  pathname,
  mobile,
  isCollapsed,
  mounted,
  showExpanded,
  onMobileClose,
}: Pick<NavItemRendererProps, "item" | "pathname" | "mobile" | "isCollapsed" | "mounted" | "onMobileClose"> & {
  showExpanded: boolean;
}) {
  const isActive = pathname.startsWith(item.href);
  const link = (
    <NavLink
      href={item.href}
      onClick={() => mobile && onMobileClose()}
      showLoadingIcon={showExpanded}
      loadingClassName="opacity-70"
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-all w-full group",
        isActive
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted/80 hover:text-foreground",
        isCollapsed && !mobile && "justify-center px-2",
      )}
    >
      <item.icon
        className={cn(
          "h-5 w-5 shrink-0 transition-colors",
          isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
        )}
      />
      {showExpanded && mounted && <span>{item.title}</span>}
    </NavLink>
  );

  if (isCollapsed && !mobile) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right" className="font-medium">
          {item.title}
        </TooltipContent>
      </Tooltip>
    );
  }
  return link;
}

/** Renders a collapsible group as a tooltip flyout (used when sidebar is collapsed). */
function CollapsedGroupItem({
  item,
  pathname,
  isParentActive,
}: Pick<NavItemRendererProps, "item" | "pathname"> & { isParentActive: boolean }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <NavLink
          href={item.children![0].href}
          showLoadingIcon={false}
          loadingClassName="opacity-70"
          className={cn(
            "flex items-center justify-center rounded-lg px-2 py-2.5 text-sm font-semibold transition-all w-full group",
            isParentActive
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:bg-muted/80 hover:text-foreground",
          )}
        >
          <item.icon
            className={cn(
              "h-5 w-5 shrink-0 transition-colors",
              isParentActive
                ? "text-primary"
                : "text-muted-foreground group-hover:text-foreground",
            )}
          />
        </NavLink>
      </TooltipTrigger>
      <TooltipContent side="right" className="p-0">
        <div className="py-1 min-w-[160px]">
          <div className="px-3 py-1.5 text-xs font-semibold text-muted-foreground">
            {item.title}
          </div>
          {item.children!.map((child) => {
            const isChildActive = pathname.startsWith(child.href);
            return (
              <NavLink
                key={child.href}
                href={child.href}
                loadingClassName="opacity-70"
                className={cn(
                  "flex items-center gap-2 px-2 py-1.5 text-sm transition-colors",
                  isChildActive ? "text-primary font-medium" : "text-foreground hover:bg-muted",
                )}
              >
                <child.icon className="h-4 w-4 shrink-0" />
                <span>{child.title}</span>
              </NavLink>
            );
          })}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}

/** Renders a collapsible group with accordion expand/collapse (used when sidebar is expanded). */
function ExpandedGroupItem({
  item,
  pathname,
  mobile,
  mounted,
  isParentActive,
  isExpanded,
  onMobileClose,
  onToggleExpand,
}: Pick<NavItemRendererProps, "item" | "pathname" | "mobile" | "mounted" | "onMobileClose" | "onToggleExpand"> & {
  isParentActive: boolean;
  isExpanded: boolean;
}) {
  return (
    <div className="space-y-1">
      <button
        onClick={() => onToggleExpand(item.href)}
        className={cn(
          "flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-semibold transition-all w-full group",
          isParentActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-muted/80 hover:text-foreground",
        )}
      >
        <div className="flex items-center gap-3">
          <item.icon
            className={cn(
              "h-5 w-5 shrink-0 transition-colors",
              isParentActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
            )}
          />
          {mounted && <span className="flex-1 text-left">{item.title}</span>}
        </div>
        {mounted && (
          <ChevronDown
            className={cn(
              "h-4 w-4 shrink-0 transition-transform duration-200",
              isExpanded ? "rotate-0" : "-rotate-90",
              isParentActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
            )}
          />
        )}
      </button>

      {/* Children */}
      <div
        className={cn(
          "overflow-hidden transition-all duration-200",
          isExpanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0",
        )}
      >
        <div className="ml-5 pl-4 border-l-2 border-border/50 space-y-1 py-1">
          {item.children!.map((child) => {
            const isChildActive = pathname.startsWith(child.href);
            return (
              <NavLink
                key={child.href}
                href={child.href}
                onClick={() => mobile && onMobileClose()}
                showLoadingIcon
                loadingClassName="opacity-70"
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all relative group",
                  isChildActive
                    ? "text-primary bg-background shadow-sm border border-border/50"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
                )}
              >
                {/* Active indicator pill (Hostinger style) */}
                {isChildActive && (
                  <div className="absolute left-[-18px] w-[3px] h-[70%] bg-primary rounded-r-full" />
                )}
                <child.icon
                  className={cn(
                    "h-4 w-4 shrink-0",
                    isChildActive
                      ? "text-primary"
                      : "text-muted-foreground group-hover:text-foreground",
                  )}
                />
                {mounted && <span>{child.title}</span>}
              </NavLink>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function NavItemRenderer({
  item,
  pathname,
  mobile,
  isCollapsed,
  mounted,
  onMobileClose,
  expandedHref,
  onToggleExpand,
}: NavItemRendererProps) {
  const isParentActive =
    pathname.startsWith(item.href) ||
    (item.children?.some((child) => pathname.startsWith(child.href)) ?? false);
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = item.href === expandedHref;
  const showExpanded = !isCollapsed || mobile;

  if (!hasChildren) {
    return (
      <SimpleNavItem
        item={item}
        pathname={pathname}
        mobile={mobile}
        isCollapsed={isCollapsed}
        mounted={mounted}
        showExpanded={showExpanded}
        onMobileClose={onMobileClose}
      />
    );
  }

  if (isCollapsed && !mobile) {
    return <CollapsedGroupItem item={item} pathname={pathname} isParentActive={isParentActive} />;
  }

  return (
    <ExpandedGroupItem
      item={item}
      pathname={pathname}
      mobile={mobile}
      mounted={mounted}
      isParentActive={isParentActive}
      isExpanded={isExpanded}
      onMobileClose={onMobileClose}
      onToggleExpand={onToggleExpand}
    />
  );
}

// ---------------------------------------------------------------------------
// NavContent
// ---------------------------------------------------------------------------

interface NavContentProps {
  mobile?: boolean;
  isCollapsed: boolean;
  toggleSidebar: () => void;
  setIsMobileOpen: (open: boolean) => void;
  pathname: string;
  mounted: boolean;
}

// eslint-disable-next-line sonarjs/cognitive-complexity -- Irreducible: interleaves logo/theme state, expanded-href sync via ref (avoids useEffect flush), tenant ID derivation from path, and accordion state — all tightly coupled to prevent hydration mismatch.
const NavContent = memo(function NavContent({
  mobile = false,
  isCollapsed,
  toggleSidebar,
  setIsMobileOpen,
  pathname,
  mounted,
}: NavContentProps) {
  const { user } = useUser();
  const { data: profile } = useUserProfile();
  const { resolvedTheme } = useTheme();
  const [logoError, setLogoError] = useState(false);
  const [isoError, setIsoError] = useState(false);

  const pathSegments = pathname.split("/").filter(Boolean);
  const currentTenantId = pathSegments[0] || profile?.tenant?.id || "";

  const navItems = useMemo(() => getNavItems(currentTenantId), [currentTenantId]);

  // Check if pathname matches parent or any of its children
  const matchesNavItem = useCallback((item: NavItem, path: string) => {
    if (path.startsWith(item.href)) return true;
    return item.children?.some((child) => path.startsWith(child.href)) ?? false;
  }, []);

  // Accordion: only one parent expanded at a time
  // Derive the active parent from pathname so we don't need a setState-in-effect.
  const activeParentHref = useMemo(() => {
    const active = navItems.find((item) => item.children?.length && matchesNavItem(item, pathname));
    return active?.href ?? null;
  }, [navItems, pathname, matchesNavItem]);

  const [expandedHref, setExpandedHref] = useState<string | null>(activeParentHref);

  // Sync expandedHref when activeParentHref changes (pathname navigation)
  const prevActiveParentHref = useRef(activeParentHref);
  if (prevActiveParentHref.current !== activeParentHref) {
    prevActiveParentHref.current = activeParentHref;
    if (activeParentHref) {
      setExpandedHref(activeParentHref);
    }
  }

  const handleToggleExpand = useCallback((href: string) => {
    setExpandedHref((prev) => (prev === href ? null : href));
  }, []);

  // Use a stable src during SSR/hydration to avoid mismatch; switch after mount.
  const fullLogoSrc =
    mounted && resolvedTheme === "dark"
      ? "/nico-assets/logotipo/logotipo-fondooscuro-nicolify.svg"
      : "/nico-assets/logotipo/logotipo-fondoclaro-nicolify.svg";

  return (
    <div className="flex h-full flex-col gap-0 group/sidebar">
      {/* HEADER: APP LOGO + COLLAPSE BUTTON */}
      <div
        className={cn(
          "h-16 border-b flex items-center relative",
          isCollapsed && !mobile ? "justify-center px-0" : "justify-between px-6",
        )}
      >
        {!isCollapsed || mobile ? (
          logoError ? (
            <span className="font-bold text-xl tracking-tight">Nicolify</span>
          ) : (
            <img
              src={fullLogoSrc}
              alt="Nicolify"
              className="w-full max-w-[120px] object-contain"
              onError={() => setLogoError(true)}
            />
          )
        ) : isoError ? (
          <span className="font-bold text-xl">N</span>
        ) : (
          <img
            src="/nico-assets/isotipo/isotipo-nicolify.svg"
            alt="N"
            className="w-8 h-8 object-contain"
            onError={() => setIsoError(true)}
          />
        )}
      </div>

      {/* TENANT SWITCHER */}
      <div className={cn("px-4 py-4", isCollapsed && !mobile && "px-2 py-4 center")}>
        <TenantSwitcher
          currentTenant={profile?.tenant ?? null}
          isCollapsed={isCollapsed && !mobile}
          activeTenantId={currentTenantId}
        />
      </div>

      {/* NAVIGATION */}
      <div className="flex-1 px-3 py-2 overflow-y-auto scrollbar-hide">
        <nav className="grid gap-2">
          <TooltipProvider delayDuration={0}>
            {navItems.map((item) => (
              <NavItemRenderer
                key={item.href}
                item={item}
                pathname={pathname}
                mobile={!!mobile}
                isCollapsed={isCollapsed}
                mounted={mounted}
                onMobileClose={() => setIsMobileOpen(false)}
                expandedHref={expandedHref}
                onToggleExpand={handleToggleExpand}
              />
            ))}
          </TooltipProvider>
        </nav>
      </div>

      {/* EXPAND/COLLAPSE BUTTON (Bottom) */}
      {!mobile && (
        <div className={cn("px-3 flex", isCollapsed ? "justify-center" : "justify-end")}>
          <TooltipProvider delayDuration={0}>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleSidebar}
                  className={cn(
                    "h-10 rounded-lg text-muted-foreground bg-background hover:bg-background/80 hover:text-foreground transition-all",
                    isCollapsed ? "w-10" : "w-full flex justify-between px-3",
                  )}
                >
                  {!isCollapsed && <span className="text-sm font-medium">Ocultar menú</span>}
                  {isCollapsed ? (
                    <PanelLeftOpen className="h-5 w-5" />
                  ) : (
                    <PanelLeftClose className="h-5 w-5" />
                  )}
                  <span className="sr-only">{isCollapsed ? "Expandir menú" : "Ocultar menú"}</span>
                </Button>
              </TooltipTrigger>
              {isCollapsed && (
                <TooltipContent side="right" className="font-medium">
                  Expandir menú
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>
        </div>
      )}

      {/* USER PROFILE & SETTINGS */}
      <div className="border-t bg-muted/10">
        <div
          className={cn(
            "flex items-center justify-between py-4 px-4 max-w-[220px]",
            isCollapsed && !mobile && "flex-col justify-center gap-4 px-4",
          )}
        >
          <ModeToggle />
          <div className="flex items-center">
            {mounted && <UserButton />}
            {(!isCollapsed || mobile) && mounted && (
              <div className="px-2 flex flex-col overflow-hidden text-left min-w-0 flex-1">
                <NavLink
                  href={`/${currentTenantId}/settings?tab=profile`}
                  className="hover:text-primary transition-colors"
                  loadingClassName="opacity-70"
                  onClick={() => mobile && setIsMobileOpen(false)}
                >
                  <span className="text-sm font-semibold truncate block">
                    {user?.fullName || "Usuario"}
                  </span>
                </NavLink>
                <span className="text-xs text-muted-foreground truncate">
                  {user?.primaryEmailAddress?.emailAddress || "Gestión de perfil"}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
NavContent.displayName = "NavContent";

// ---------------------------------------------------------------------------
// AppSidebar
// ---------------------------------------------------------------------------

export function AppSidebar() {
  const pathname = usePathname() ?? "";
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const { isCollapsed, toggleSidebar } = useSidebar();
  const [isMounted, setIsMounted] = useState(false);

  // Track client-side mount to avoid hydration mismatch for components
  // that depend on browser APIs (Sheet, UserButton, theme-aware images).
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsMounted(true);
  }, []);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden border-r bg-card md:flex md:flex-col fixed inset-y-0 z-50 transition-all duration-300 ease-in-out",
          isCollapsed ? "w-20" : "w-64",
        )}
      >
        <NavContent
          isCollapsed={isCollapsed}
          toggleSidebar={toggleSidebar}
          setIsMobileOpen={setIsMobileOpen}
          pathname={pathname}
          mounted={isMounted}
        />
      </aside>

      {/* Mobile Header & Sidebar */}
      <div className="flex h-16 items-center justify-between border-b bg-background px-4 md:hidden fixed inset-x-0 top-0 z-50">
        <div className="flex items-center gap-3">
          {isMounted ? (
            <Sheet open={isMobileOpen} onOpenChange={setIsMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="-ml-2">
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="p-0 w-72" aria-describedby="mobile-nav-desc">
                <SheetTitle className="sr-only">Menú de Navegación</SheetTitle>
                <div id="mobile-nav-desc" className="sr-only">
                  Menú de navegación principal
                </div>
                <NavContent
                  mobile
                  isCollapsed={isCollapsed}
                  toggleSidebar={toggleSidebar}
                  setIsMobileOpen={setIsMobileOpen}
                  pathname={pathname}
                  mounted={isMounted}
                />
              </SheetContent>
            </Sheet>
          ) : (
            <Button variant="ghost" size="icon" className="-ml-2">
              <Menu className="h-5 w-5" />
            </Button>
          )}
          <img
            src="/_temp/logotipo/logotipo-fondoclaro-nicolify.svg"
            alt="Nicolify"
            className="h-6 object-contain"
          />
        </div>
      </div>
    </>
  );
}
