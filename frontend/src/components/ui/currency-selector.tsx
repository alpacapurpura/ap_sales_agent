"use client";

import * as React from "react";
import { Check, ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { CURRENCIES, Currency } from "@/lib/constants/currencies";

interface CurrencySelectorProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}

export function CurrencySelector({
  value,
  onValueChange,
  className,
}: CurrencySelectorProps) {
  const [open, setOpen] = React.useState(false);

  const selectedCurrency = CURRENCIES.find((c) => c.code === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className={cn("w-full justify-between", className)}
        >
          {selectedCurrency ? (
            <span className="flex items-center gap-2">
              <span className="text-lg">{selectedCurrency.flag}</span>
              <span>{selectedCurrency.code}</span>
              <span className="text-muted-foreground text-xs">
                - {selectedCurrency.name}
              </span>
            </span>
          ) : (
            "Select currency..."
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] p-0">
        <Command>
          <CommandInput placeholder="Search currency..." />
          <CommandList>
            <CommandEmpty>No currency found.</CommandEmpty>
            <CommandGroup>
              {CURRENCIES.map((currency) => (
                <CommandItem
                  key={currency.code}
                  value={currency.code}
                  onSelect={(currentValue) => {
                    // CommandItem converts value to lowercase, so we need to find the original code
                    // But here we passed currency.code as value, which is usually uppercase.
                    // However, shadcn command might normalize it.
                    // Safer to just use the currency.code from closure.
                    onValueChange(currency.code);
                    setOpen(false);
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === currency.code ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <span className="mr-2 text-lg">{currency.flag}</span>
                  <span className="font-medium">{currency.code}</span>
                  <span className="ml-2 text-muted-foreground">
                    {currency.name}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
