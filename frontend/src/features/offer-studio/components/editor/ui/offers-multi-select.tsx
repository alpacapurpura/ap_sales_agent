import * as React from "react"
import { Check, ChevronsUpDown, X } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { useAuth } from "@clerk/nextjs"

import { cn } from "@/lib/utils"
import { Button, buttonVariants } from "@/components/ui/button"
import {
  Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, } from "@/components/ui/command"
import {
  Popover, PopoverContent, PopoverTrigger, } from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { offerApi } from "@/features/offer-studio/api";

interface OffersMultiSelectProps {
  value?: string[]
  onChange: (value: string[]) => void
  currentOfferId?: string
}

export function OffersMultiSelect({ value = [], onChange, currentOfferId }: OffersMultiSelectProps) {
  const [open, setOpen] = React.useState(false)
  const { getToken } = useAuth()

  const { data: offers = [], isLoading } = useQuery({
    queryKey: ["offers-list"],
    queryFn: async () => {
      const token = await getToken()
      if (!token) return []
      return offerApi.listOffers(token)
    },
  })

  // Filter out current offer to avoid self-reference if needed
  const availableOffers = React.useMemo(() => {
    return offers.filter(o => o.id !== currentOfferId)
  }, [offers, currentOfferId])

  const selectedOffers = React.useMemo(() => {
    // Ensure value is an array before filtering
    const currentValues = Array.isArray(value) ? value : []
    return availableOffers.filter(o => currentValues.includes(o.id))
  }, [availableOffers, value])

  const handleSelect = (offerId: string) => {
    const currentValues = Array.isArray(value) ? value : []
    if (currentValues.includes(offerId)) {
      onChange(currentValues.filter((id) => id !== offerId))
    } else {
      onChange([...currentValues, offerId])
    }
  }

  const handleRemove = (offerId: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent Popover from toggling
    const currentValues = Array.isArray(value) ? value : []
    onChange(currentValues.filter((id) => id !== offerId))
  }

  // Count unknown IDs (e.g. deleted offers or not yet loaded)
  const unknownCount = (Array.isArray(value) ? value.length : 0) - selectedOffers.length

  return (
    <div className="flex flex-col gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <div
            role="combobox"
            aria-expanded={open}
            aria-controls="offers-listbox"
            className={cn(
              buttonVariants({ variant: "outline" }),
              "w-full justify-between h-auto min-h-[2.5rem] px-3 py-2 cursor-pointer"
            )}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                setOpen((prev) => !prev)
              }
            }}
          >
            <div className="flex flex-wrap gap-1 items-center text-left">
              {(Array.isArray(value) ? value.length : 0) === 0 && (
                <span className="text-muted-foreground font-normal">Seleccionar ofertas...</span>
              )}
              {selectedOffers.map((offer) => (
                <Badge variant="secondary" key={offer.id} className="mr-1 mb-1">
                  {offer.name}
                  <button
                    className="ml-1 ring-offset-background rounded-full outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleRemove(offer.id, e as any)
                      }
                    }}
                    onMouseDown={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                    }}
                    onClick={(e) => handleRemove(offer.id, e)}
                  >
                    <X className="h-3 w-3 text-muted-foreground hover:text-foreground" />
                  </button>
                </Badge>
              ))}
               {/* Show count of unknown IDs if any */}
               {unknownCount > 0 && (
                <Badge variant="outline" className="mb-1">
                  +{unknownCount} desconocidos
                </Badge>
              )}
            </div>
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </div>
        </PopoverTrigger>
        <PopoverContent className="w-[400px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Buscar oferta..." />
            <CommandList id="offers-listbox">
                <CommandEmpty>No se encontraron ofertas.</CommandEmpty>
                <CommandGroup className="max-h-[300px] overflow-auto">
                {isLoading ? (
                    <div className="p-4 text-sm text-center text-muted-foreground">Cargando...</div>
                ) : (
                    availableOffers.map((offer) => (
                        <CommandItem
                        key={offer.id}
                        value={offer.name} // Search by name
                        onSelect={() => handleSelect(offer.id)}
                        >
                        <div className={cn(
                            "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                            (Array.isArray(value) ? value : []).includes(offer.id)
                            ? "bg-primary text-primary-foreground"
                            : "opacity-50 [&_svg]:invisible"
                        )}>
                            <Check className={cn("h-4 w-4")} />
                        </div>
                        <div className="flex flex-col">
                            <span>{offer.name}</span>
                            {offer.headline_promise && (
                                <span className="text-xs text-muted-foreground truncate max-w-[300px]">
                                    {offer.headline_promise}
                                </span>
                            )}
                        </div>
                        </CommandItem>
                    ))
                )}
                </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
