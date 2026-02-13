"use client"

import * as React from "react"
import { CalendarIcon, Clock } from "lucide-react"
import { format } from "date-fns"
import { es } from "date-fns/locale"
import { toZonedTime, fromZonedTime } from "date-fns-tz"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Input } from "@/components/ui/input"

interface SmartDateTimePickerProps {
  value?: string // UTC ISO String
  onChange: (value: string) => void
  timezone: string // "America/Lima"
  className?: string
  placeholder?: string
}

export function SmartDateTimePicker({
  value,
  onChange,
  timezone,
  className,
  placeholder = "Seleccionar fecha"
}: SmartDateTimePickerProps) {
  // Compute "Fake Local Date" for display
  // This date object's internal time corresponds to the Wall Time in the target timezone
  const date = React.useMemo(() => {
    if (!value) return undefined
    try {
      return toZonedTime(value, timezone)
    } catch (e) {
      console.error("Invalid date or timezone", e)
      return undefined
    }
  }, [value, timezone])

  // Time string (HH:mm) from the "Fake Local Date"
  // Default to 09:00 if creating new
  const [timeStr, setTimeStr] = React.useState(
    date ? format(date, "HH:mm") : "09:00"
  )
  
  // Sync state when prop changes
  React.useEffect(() => {
    if (date) {
      setTimeStr(format(date, "HH:mm"))
    }
  }, [date])

  const handleDateSelect = (newDate: Date | undefined) => {
    if (!newDate) return
    // newDate comes from Calendar, so it's a "Fake Local" date (Browser Local)
    
    // Combine with current timeStr
    const [hours, minutes] = timeStr.split(":").map(Number)
    newDate.setHours(hours, minutes, 0, 0)
    
    // Convert "Fake Local" -> UTC
    try {
      const utcDate = fromZonedTime(newDate, timezone)
      onChange(utcDate.toISOString())
    } catch (e) {
      console.error("Error converting date", e)
    }
  }

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = e.target.value
    setTimeStr(newTime)
    
    // If we have a date selected, update the value immediately
    if (date) {
       // Create new "Fake Local" base from the existing one
       const newDate = new Date(date)
       const [hours, minutes] = newTime.split(":").map(Number)
       newDate.setHours(hours, minutes, 0, 0)
       
       // Convert -> UTC
       try {
         const utcDate = fromZonedTime(newDate, timezone)
         onChange(utcDate.toISOString())
       } catch (e) {
         console.error("Error converting time", e)
       }
    }
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-full justify-start text-left font-normal",
            !date && "text-muted-foreground",
            className
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? (
            format(date, "dd/MM/yyyy HH:mm", { locale: es })
          ) : (
            <span>{placeholder}</span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto min-w-[280px] p-0" align="start">
        <div className="p-4 border-b border-border flex gap-2 items-center bg-muted/20">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <Input 
                type="time" 
                value={timeStr} 
                onChange={handleTimeChange}
                className="w-full bg-background font-mono"
            />
        </div>
        <Calendar
          mode="single"
          selected={date}
          onSelect={handleDateSelect}
          initialFocus
          locale={es}
          className="p-3 pointer-events-auto"
        />
      </PopoverContent>
    </Popover>
  )
}
