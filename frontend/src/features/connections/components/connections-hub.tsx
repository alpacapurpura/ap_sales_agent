"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, Cable } from "lucide-react";
import { cn } from "@/lib/utils";
import { PROVIDER_REGISTRY, getAllTags } from "@/features/connections/config/provider-registry";
import { useAllConnectionsStatus } from "@/features/connections/hooks/use-all-connections-status";
import { ConnectionCard } from "./connection-card";

const ALL_TAGS = getAllTags();

export function ConnectionsHub() {
  const params = useParams();
  const tenantId = params?.tenantId as string;
  const { data: statusMap, isLoading } = useAllConnectionsStatus();

  const [search, setSearch] = useState("");
  const [activeTags, setActiveTags] = useState<Set<string>>(new Set());
  const [showConnectedOnly, setShowConnectedOnly] = useState(false);

  const toggleTag = (tag: string) => {
    setActiveTags((prev) => {
      const next = new Set(prev);
      if (next.has(tag)) {
        next.delete(tag);
      } else {
        next.add(tag);
      }
      return next;
    });
  };

  // Filter & sort providers
  const filteredProviders = useMemo(() => {
    const searchLower = search.toLowerCase();
    let providers = PROVIDER_REGISTRY.filter((p) => {
      // Connected-only filter
      if (showConnectedOnly && !statusMap?.[p.id]?.isConnected) return false;
      // Search filter
      if (searchLower) {
        const matchesSearch =
          p.name.toLowerCase().includes(searchLower) ||
          p.description.toLowerCase().includes(searchLower) ||
          p.tags.some((t) => t.includes(searchLower));
        if (!matchesSearch) return false;
      }
      // Tag filter
      if (activeTags.size > 0) {
        const hasTag = p.tags.some((t) => activeTags.has(t));
        if (!hasTag) return false;
      }
      return true;
    });

    // Connected-first sorting, then coming_soon at the end
    providers = [...providers].sort((a, b) => {
      const aConnected = statusMap?.[a.id]?.isConnected ? 1 : 0;
      const bConnected = statusMap?.[b.id]?.isConnected ? 1 : 0;
      if (aConnected !== bConnected) return bConnected - aConnected;
      // coming_soon at the end
      if (a.status !== b.status) return a.status === "coming_soon" ? 1 : -1;
      return 0;
    });

    return providers;
  }, [search, activeTags, statusMap, showConnectedOnly]);

  const connectedCount = useMemo(() => {
    if (!statusMap) return 0;
    return PROVIDER_REGISTRY.filter((p) => statusMap[p.id]?.isConnected).length;
  }, [statusMap]);

  return (
    <div className="space-y-6 p-6 md:p-10 pb-16">
      {/* Header */}
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Conexiones</h2>
        <p className="text-muted-foreground">
          Conecta tus plataformas y herramientas para potenciar tu negocio.
        </p>
      </div>

      <div className="border-t" />

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar integraciones..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={!showConnectedOnly && activeTags.size === 0 ? "default" : "outline"}
          size="sm"
          className="h-7 text-xs rounded-full"
          onClick={() => {
            setActiveTags(new Set());
            setShowConnectedOnly(false);
          }}
        >
          Todos
        </Button>
        <Button
          variant={showConnectedOnly ? "default" : "outline"}
          size="sm"
          className={cn(
            "h-7 text-xs rounded-full",
            showConnectedOnly
              ? "bg-green-600 hover:bg-green-700 text-white"
              : connectedCount > 0
                ? "border-green-500/50 text-green-700 dark:text-green-400"
                : "",
          )}
          onClick={() => setShowConnectedOnly((prev) => !prev)}
        >
          Conectados{connectedCount > 0 && ` (${connectedCount})`}
        </Button>
        {ALL_TAGS.map((tag) => (
          <Button
            key={tag}
            variant={activeTags.has(tag) ? "default" : "outline"}
            size="sm"
            className="h-7 text-xs rounded-full capitalize"
            onClick={() => toggleTag(tag)}
          >
            {tag}
          </Button>
        ))}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-[100px] rounded-xl" />
          ))}
        </div>
      ) : filteredProviders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Cable className="h-12 w-12 mb-4 opacity-30" />
          <p className="text-sm">No se encontraron integraciones</p>
          {search && (
            <Button
              variant="link"
              size="sm"
              className="mt-2"
              onClick={() => {
                setSearch("");
                setActiveTags(new Set());
              }}
            >
              Limpiar filtros
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProviders.map((provider) => (
            <ConnectionCard
              key={provider.id}
              provider={provider}
              status={statusMap?.[provider.id]}
              tenantId={tenantId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
