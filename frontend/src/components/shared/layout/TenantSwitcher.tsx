"use client";

import { ChevronsUpDown, Check } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTenants } from "@/features/settings/hooks/use-tenants";
import { cn } from "@/lib/utils";

import type { TenantProfile } from "@/lib/api/settings";

interface TenantSwitcherProps {
  currentTenant: TenantProfile | null;
  isCollapsed: boolean;
  activeTenantId?: string;
}

/**
 *
 */
export function TenantSwitcher({
  currentTenant,
  isCollapsed,
  activeTenantId,
}: TenantSwitcherProps) {
  const { data: tenants } = useTenants();
  const [open, setOpen] = React.useState(false);

  // Use prop or fallback to local storage/profile
  const effectiveTenantId = activeTenantId || currentTenant?.id;

  const handleTenantChange = (tenantId: string) => {
    // 1. Update localStorage for API client fallback
    localStorage.setItem("x-tenant-id", tenantId);

    // 2. Navigate to new URL: /[newTenantId]/dashboard
    // We redirect to dashboard to avoid 404s if the current subpage doesn't exist in the new tenant
    // or if the ID structure is different.
    const newPath = `/${tenantId}/brand-studio/identity`;

    // Force a hard reload to ensure all application state is cleared and
    // the new tenant context is loaded fresh. This prevents data leakage
    // and stale cache issues common in SPA transitions between tenants.
    // eslint-disable-next-line react-hooks/immutability -- intentional browser navigation
    window.location.href = newPath;
  };

  const currentTenantName =
    tenants?.find((t) => t.id === effectiveTenantId)?.name || currentTenant?.name || "Nicolify";
  const currentTenantInitial = currentTenantName.charAt(0);

  if (isCollapsed) {
    return (
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-xl"
            suppressHydrationWarning
          >
            <div className="w-full h-full rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-sm">
              <span className="text-white font-bold text-lg leading-none mt-[2px]">
                {currentTenantInitial}
              </span>
            </div>
            <span className="sr-only">Cambiar organización</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="right" className="w-64 rounded-xl p-2">
          <DropdownMenuLabel className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
            Mis organizaciones
          </DropdownMenuLabel>
          {tenants?.map((tenant) => (
            <DropdownMenuItem
              key={tenant.id}
              onClick={() => handleTenantChange(tenant.id)}
              className={cn(
                "gap-3 p-2 cursor-pointer rounded-lg mb-1",
                activeTenantId === tenant.id ? "bg-primary/10 text-primary" : "hover:bg-muted",
              )}
            >
              <div
                className={cn(
                  "flex size-8 items-center justify-center rounded-md shrink-0",
                  activeTenantId === tenant.id
                    ? "bg-gradient-to-br from-primary to-primary/80"
                    : "bg-gradient-to-br from-muted-foreground/20 to-muted-foreground/40",
                )}
              >
                <span
                  className={cn(
                    "font-bold text-xs leading-none mt-[1px]",
                    activeTenantId === tenant.id ? "text-white" : "text-foreground",
                  )}
                >
                  {tenant.name.charAt(0)}
                </span>
              </div>
              <span className="truncate font-medium">{tenant.name}</span>
              {activeTenantId === tenant.id && <Check className="ml-auto h-4 w-4" />}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          role="combobox"
          aria-expanded={open}
          aria-label="Seleccionar organización"
          className="w-full flex items-center justify-between p-2 h-auto rounded-xl hover:bg-muted/50 transition-all duration-200 border border-transparent hover:border-border group focus:outline-none focus:ring-2 focus:ring-primary/20 shadow-sm bg-muted/20"
          suppressHydrationWarning
        >
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-sm flex-shrink-0 relative overflow-hidden">
              <span className="text-white font-bold text-lg leading-none mt-[2px]">
                {currentTenantInitial}
              </span>
            </div>

            <div className="flex flex-col text-left truncate">
              <span
                className="text-sm font-bold text-foreground truncate"
                title={currentTenantName}
              >
                {currentTenantName}
              </span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary uppercase tracking-wider">
                  Workspace
                </span>
              </div>
            </div>
          </div>
          {open ? (
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 text-foreground" />
          ) : (
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-[260px] rounded-xl p-2" align="start">
        <DropdownMenuLabel className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
          Mis Organizaciones
        </DropdownMenuLabel>
        <div className="max-h-[300px] overflow-y-auto pr-1">
          {tenants?.map((tenant) => (
            <DropdownMenuItem
              key={tenant.id}
              onClick={() => handleTenantChange(tenant.id)}
              className={cn(
                "gap-3 p-2 cursor-pointer rounded-lg mb-1",
                activeTenantId === tenant.id ? "bg-primary/10 text-primary" : "hover:bg-muted",
              )}
            >
              <div
                className={cn(
                  "flex size-8 items-center justify-center rounded-md shrink-0",
                  activeTenantId === tenant.id
                    ? "bg-gradient-to-br from-primary to-primary/80"
                    : "bg-gradient-to-br from-muted-foreground/20 to-muted-foreground/40",
                )}
              >
                <span
                  className={cn(
                    "font-bold text-xs leading-none mt-[1px]",
                    activeTenantId === tenant.id ? "text-white" : "text-foreground",
                  )}
                >
                  {tenant.name.charAt(0)}
                </span>
              </div>
              <div className="flex flex-col overflow-hidden">
                <span className="truncate font-medium">{tenant.name}</span>
                <span className="text-[10px] text-muted-foreground">
                  ID: {tenant.id.substring(0, 8)}...
                </span>
              </div>
              {activeTenantId === tenant.id && <Check className="ml-auto h-4 w-4" />}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
