"use client";

import { forwardRef } from "react";

import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

import { useSlashCommands } from "../hooks/use-slash-commands";

import type { SlashCommand } from "../types/conversations";

// ── Types ────────────────────────────────────────────────────────────

// `onSelect` has a domain shape that clashes with React's
// `HTMLAttributes<HTMLDivElement>['onSelect']` (SyntheticEvent handler), so we
// explicitly Omit it before extending.
interface SlashCommandAutocompleteProps extends Omit<
  React.HTMLAttributes<HTMLDivElement>,
  "onSelect"
> {
  /** The text after "/" used to filter commands */
  query: string;
  /** Called when user selects a command */
  onSelect: (command: SlashCommand) => void;
  /** Called when user presses Escape or dismisses */
  onDismiss: () => void;
  /** Whether the popover is open */
  open: boolean;
  /** Anchor element (the textarea) */
  children: React.ReactNode;
}

// ── Component ────────────────────────────────────────────────────────

/**
 * Slash command autocomplete popover.
 * Triggered when textarea input starts with "/".
 * Uses Shadcn Command for keyboard-accessible list navigation.
 */
export const SlashCommandAutocomplete = forwardRef<HTMLDivElement, SlashCommandAutocompleteProps>(
  ({ query, onSelect, onDismiss, open, children, className, ...props }, ref) => {
    const { data: commands = [], isLoading } = useSlashCommands();

    const filtered = query
      ? commands.filter(
          (cmd) =>
            cmd.name.toLowerCase().includes(query.toLowerCase()) ||
            cmd.description.toLowerCase().includes(query.toLowerCase()),
        )
      : commands;

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onDismiss();
      }
    };

    return (
      <div ref={ref} className={cn(className)} {...props}>
        <Popover open={open} onOpenChange={(o) => !o && onDismiss()}>
          <PopoverTrigger asChild>{children}</PopoverTrigger>
          <PopoverContent
            side="top"
            align="start"
            className="w-72 p-0"
            onKeyDown={handleKeyDown}
            onOpenAutoFocus={(e) => e.preventDefault()}
          >
            <Command shouldFilter={false}>
              <CommandInput
                value={`/${query}`}
                onValueChange={() => undefined}
                placeholder="Buscar comando..."
                className="h-8 text-sm"
                readOnly
              />
              <CommandList>
                {isLoading && (
                  <div className="space-y-1 p-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                )}

                {!isLoading && (
                  <CommandEmpty>No hay comandos para &quot;{query}&quot;</CommandEmpty>
                )}

                {!isLoading &&
                  filtered.map((cmd) => (
                    <CommandItem
                      key={cmd.name}
                      value={cmd.name}
                      onSelect={() => onSelect(cmd)}
                      className="flex flex-col items-start gap-0.5 py-2 cursor-pointer"
                    >
                      <span className="font-mono text-sm font-medium">/{cmd.name}</span>
                      <span className="text-xs text-muted-foreground leading-tight">
                        {cmd.description}
                      </span>
                    </CommandItem>
                  ))}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      </div>
    );
  },
);
SlashCommandAutocomplete.displayName = "SlashCommandAutocomplete";
