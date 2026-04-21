"use client";

import { Search, Bot, User } from "lucide-react";
import { useRouter, usePathname, useParams } from "next/navigation";
import { useCallback, useState } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { useConversations } from "../../hooks/use-conversations";
import { useCloserStore } from "../../store/closer-store";

import { ConversationItem } from "./ConversationItem";

import type { Temperature, HandlerMode } from "../../types";

const FILTER_CHIPS: {
  label: string;
  key: "temperature" | "handler_mode";
  value: string | null;
  icon?: React.ReactNode;
}[] = [
  { label: "Todas", key: "temperature", value: null },
  { label: "Hot", key: "temperature", value: "hot" },
  { label: "Warm", key: "temperature", value: "warm" },
  { label: "Cold", key: "temperature", value: "cold" },
  { label: "AI", key: "handler_mode", value: "ai", icon: <Bot className="h-3 w-3" /> },
  { label: "Manual", key: "handler_mode", value: "human", icon: <User className="h-3 w-3" /> },
];

/**
 *
 */
export function ConversationList() {
  const router = useRouter();
  const pathname = usePathname() ?? "";
  const params = useParams();
  const tenantId = (params?.tenantId as string) ?? "";
  const { data, isLoading } = useConversations();
  const selectedLeadId = useCloserStore((s) => s.selectedLeadId);
  const setSelectedLeadId = useCloserStore((s) => s.setSelectedLeadId);
  const filters = useCloserStore((s) => s.filters);
  const setFilter = useCloserStore((s) => s.setFilter);
  const resetFilters = useCloserStore((s) => s.resetFilters);
  const [searchInput, setSearchInput] = useState(filters.search);

  const handleSelect = useCallback(
    (leadId: string) => {
      setSelectedLeadId(leadId);
      // Persist last conversation per tenant
      try {
        localStorage.setItem(`closer-studio:lastLead:${tenantId}`, leadId);
      } catch {
        /* quota exceeded — non-critical */
      }
      router.replace(`${pathname}?lead=${leadId}`, { scroll: false });
    },
    [setSelectedLeadId, router, pathname, tenantId],
  );

  const handleSearch = useCallback(
    (value: string) => {
      setSearchInput(value);
      // Debounce via timeout
      const id = setTimeout(() => setFilter("search", value), 300);
      return () => clearTimeout(id);
    },
    [setFilter],
  );

  const handleChipClick = useCallback(
    (key: "temperature" | "handler_mode", value: string | null) => {
      if (key === "temperature") {
        if (value === null) {
          resetFilters();
        } else {
          setFilter("temperature", value as Temperature);
          setFilter("handler_mode", null);
        }
      } else {
        setFilter("handler_mode", value as HandlerMode);
        setFilter("temperature", null);
      }
    },
    [setFilter, resetFilters],
  );

  const conversations = data?.conversations ?? [];

  return (
    <>
      {/* Search */}
      <div className="p-3 border-b">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar conversacion..."
            value={searchInput}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-8 h-9 text-sm"
          />
        </div>
      </div>

      {/* Filter chips */}
      <div className="flex gap-1 px-3 py-2 border-b overflow-x-auto">
        {FILTER_CHIPS.map((chip) => {
          const isActive =
            chip.value === null
              ? !filters.temperature && !filters.handler_mode
              : filters[chip.key] === chip.value;
          return (
            <button
              key={`${chip.key}-${chip.value}`}
              onClick={() => handleChipClick(chip.key, chip.value)}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80",
              )}
            >
              {chip.icon}
              {chip.label}
            </button>
          );
        })}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
            Cargando...
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
            No hay conversaciones
          </div>
        ) : (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.lead_id}
              conversation={conv}
              isSelected={conv.lead_id === selectedLeadId}
              onSelect={handleSelect}
            />
          ))
        )}
      </div>

      {/* Total count */}
      {data && (
        <div className="px-3 py-1.5 border-t text-xs text-muted-foreground">
          {data.total} conversaciones
        </div>
      )}
    </>
  );
}
