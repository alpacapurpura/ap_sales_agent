"use client";

import * as React from "react";
import { ChevronsUpDown, Check, Building2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter, usePathname } from "next/navigation";
import { useTenants } from "@/features/settings/hooks/use-tenants";
import { TenantProfile } from "@/lib/api/settings";

interface TenantSwitcherProps {
  currentTenant: TenantProfile | null;
  isCollapsed: boolean;
  activeTenantId?: string;
}

export function TenantSwitcher({ currentTenant, isCollapsed, activeTenantId }: TenantSwitcherProps) {
  const { data: tenants } = useTenants();
  const [open, setOpen] = React.useState(false);
  const router = useRouter();
  const pathname = usePathname();
  
  // Use prop or fallback to local storage/profile
  const effectiveTenantId = activeTenantId || currentTenant?.id;

  const handleTenantChange = (tenantId: string) => {
    console.log("[TenantSwitcher] Switching to tenant:", tenantId);
    
    // 1. Update localStorage for API client fallback
    localStorage.setItem("x-tenant-id", tenantId);
    
    // 2. Navigate to new URL: /[newTenantId]/dashboard
    // We redirect to dashboard to avoid 404s if the current subpage doesn't exist in the new tenant
    // or if the ID structure is different.
    const newPath = `/${tenantId}/brand-settings`; // Defaulting to brand-settings or dashboard
    console.log("[TenantSwitcher] Navigating to:", newPath);
    
    // Force a hard reload to ensure all application state is cleared and 
    // the new tenant context is loaded fresh. This prevents data leakage 
    // and stale cache issues common in SPA transitions between tenants.
    window.location.href = newPath;
  };

  const currentTenantName = tenants?.find(t => t.id === effectiveTenantId)?.name || currentTenant?.name || "Visionarias AI";
  const currentTenantInitial = currentTenantName.charAt(0);

  if (isCollapsed) {
    return (
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-9 w-9">
             <span className="text-lg font-bold tracking-tight text-primary">
                {currentTenantInitial}
             </span>
             <span className="sr-only">Cambiar organización</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="right" className="w-56">
            <DropdownMenuLabel>Mis organizaciones</DropdownMenuLabel>
            <DropdownMenuSeparator />
             {tenants?.map((tenant) => (
            <DropdownMenuItem
              key={tenant.id}
              onClick={() => handleTenantChange(tenant.id)}
              className="gap-2 p-2 cursor-pointer"
            >
              <div className="flex size-6 items-center justify-center rounded-sm border">
                <Building2 className="size-4 shrink-0" />
              </div>
              <span className="truncate">{tenant.name}</span>
              {activeTenantId === tenant.id && (
                  <Check className="ml-auto h-4 w-4" />
              )}
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
          className="w-full justify-between hover:bg-background/50 px-2 h-auto py-1"
        >
          <div className="flex flex-col items-start overflow-hidden">
              <span className="text-lg font-bold tracking-tight text-primary truncate text-left" title={currentTenantName}>
                {currentTenantName}
              </span>
              {/* DEBUG: Show ID */}
              <span className="text-[10px] text-muted-foreground truncate w-full">
                ID: {currentTenant?.id?.substring(0, 8)}...
              </span>
          </div>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-[200px]" align="start">
        <DropdownMenuLabel className="text-xs text-muted-foreground">
            Organizaciones
        </DropdownMenuLabel>
         <DropdownMenuSeparator />
        {tenants?.map((tenant) => (
          <DropdownMenuItem
            key={tenant.id}
            onClick={() => handleTenantChange(tenant.id)}
            className="gap-2 p-2 cursor-pointer"
          >
            <div className="flex size-6 items-center justify-center rounded-sm border">
              <Building2 className="size-4 shrink-0" />
            </div>
            <div className="flex flex-col overflow-hidden">
                <span className="truncate">{tenant.name}</span>
                <span className="text-[10px] text-muted-foreground">{tenant.id.substring(0, 8)}...</span>
            </div>
            {activeTenantId === tenant.id && (
              <Check className="ml-auto h-4 w-4" />
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
