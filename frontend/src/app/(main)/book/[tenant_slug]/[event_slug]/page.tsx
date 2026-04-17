"use client";

import {
  format,
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  isSameMonth,
  isSameDay,
  isToday,
  addMinutes,
} from "date-fns";
import { es } from "date-fns/locale";
import {
  Loader2,
  Calendar as CalendarIcon,
  Clock,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Globe,
} from "lucide-react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import { useState, useEffect, use } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { publicApi } from "@/lib/api/public";
import { cn } from "@/lib/utils";

import type { EventTypeResolveResponse, BookingLinkResolveResponse } from "@/lib/api/public";

/**
 *
 */
export default function BookingPage({
  params,
}: {
  params: Promise<{ tenant_slug: string; event_slug: string }>;
}) {
  const { tenant_slug, event_slug } = use(params);
  const searchParams = useSearchParams();
  const token = searchParams?.get("token");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<EventTypeResolveResponse | null>(null);
  const [bookingLinkData, setBookingLinkData] = useState<BookingLinkResolveResponse | null>(null);

  // Booking State - Initialize undefined to auto-select first available day
  const [date, setDate] = useState<Date | undefined>(undefined);
  const [month, setMonth] = useState<Date>(new Date()); // Control Calendar View Month
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [availableDays, setAvailableDays] = useState<Date[]>([]); // Days with at least one slot
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [step, setStep] = useState<"date" | "form" | "success">("date");

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    notes: "",
  });
  const [bookingLoading, setBookingLoading] = useState(false);

  useEffect(() => {
    setLoading(true);

    const promises: Promise<unknown>[] = [publicApi.resolveEventType(tenant_slug, event_slug)];

    if (token) {
      promises.push(publicApi.resolveBookingLink(token));
    }

    Promise.all(promises)
      .then((results) => {
        const etData = results[0] as EventTypeResolveResponse;
        setData(etData);

        if (token) {
          const linkData = results[1] as BookingLinkResolveResponse;
          if (linkData.event_slug !== event_slug) {
            throw new Error("El enlace no es válido para este tipo de evento");
          }
          setBookingLinkData(linkData);
          setFormData((prev) => ({
            ...prev,
            name: linkData.lead_name || "",
            email: linkData.lead_email || "",
            phone: linkData.lead_phone || "",
          }));
        }
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [tenant_slug, event_slug, token]);

  // Fetch Availability Window (Current date + max advance days)
  useEffect(() => {
    if (!data) return;

    const fetchAvailability = async () => {
      const start = new Date(); // Start from today to show current month context
      const maxDays = data.event_type.scheduling_limits.max_advance_days || 60;
      const end = addDays(start, maxDays);

      const startStr = format(start, "yyyy-MM-dd");
      const endStr = format(end, "yyyy-MM-dd");

      try {
        const response = await publicApi.getEventTypeSlots(
          tenant_slug,
          event_slug,
          startStr,
          endStr,
        );
        // Extract unique days from slots
        const days = new Set<string>();
        response.forEach((slotIso) => {
          // Convert to local date object to determine "day" correctly in user's browser
          const slotDate = new Date(slotIso);
          days.add(format(slotDate, "yyyy-MM-dd"));
        });

        // Convert back to Date objects for the Calendar modifier
        const availableDates = Array.from(days).map((d) => new Date(`${d}T12:00:00`)); // Adding time to avoid timezone shifts on parsing
        setAvailableDays(availableDates);
      } catch (error) {
        console.error("Failed to fetch availability", error);
      }
    };

    void fetchAvailability();
  }, [data, tenant_slug, event_slug]);

  // Auto-select the first available day when availability loads
  useEffect(() => {
    if (availableDays.length > 0 && !date) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const sorted = [...availableDays].sort((a, b) => a.getTime() - b.getTime());
      const nextAvailable = sorted.find((d) => {
        const dDate = new Date(d);
        dDate.setHours(0, 0, 0, 0);
        return dDate >= today;
      });

      if (nextAvailable) {
        setDate(nextAvailable);
      }
    }
  }, [availableDays, date]);

  useEffect(() => {
    if (date && data) {
      setSlotsLoading(true);
      const dateStr = format(date, "yyyy-MM-dd");
      // Fetch slots for the selected date
      publicApi
        .getEventTypeSlots(tenant_slug, event_slug, dateStr, dateStr)
        .then(setSlots)
        .catch(() => toast.error("Error cargando horarios"))
        .finally(() => setSlotsLoading(false));
    } else {
      setSlots([]);
    }
  }, [date, tenant_slug, event_slug, data]);

  // Sync month when date is selected (optional but good UX)
  useEffect(() => {
    if (date) {
      setMonth(date);
    }
  }, [date]);

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot || !data) return;

    setBookingLoading(true);
    try {
      await publicApi.bookEventType(tenant_slug, event_slug, {
        slot_time: selectedSlot,
        duration_minutes: data.event_type.duration,
        booking_token: token || undefined,
        ...formData,
      });
      setStep("success");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al agendar");
    } finally {
      setBookingLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950 text-white">
        <Loader2 className="h-8 w-8 animate-spin text-neutral-500" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950 text-white">
        <div className="text-center space-y-4">
          <div className="bg-red-500/10 p-4 rounded-full w-fit mx-auto">
            <CalendarIcon className="h-8 w-8 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold">Enlace no válido</h1>
          <p className="text-neutral-400">{error || "El enlace ha expirado o no existe."}</p>
        </div>
      </div>
    );
  }

  // Success View
  if (step === "success") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-950 text-white p-4">
        <Card className="max-w-md w-full bg-neutral-900 border-neutral-800 text-neutral-100 p-8 text-center space-y-6">
          <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="h-8 w-8 text-green-500" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">¡Reserva Confirmada!</h2>
            <p className="text-neutral-400">Hemos enviado los detalles a tu correo.</p>
          </div>
          <div className="bg-neutral-800/50 p-4 rounded-lg text-left space-y-3">
            <div className="flex items-center gap-3">
              <CalendarIcon className="h-5 w-5 text-neutral-400" />
              <div>
                <p className="font-medium capitalize">
                  {selectedSlot &&
                    format(new Date(selectedSlot), "EEEE d 'de' MMMM", { locale: es })}
                </p>
                <p className="text-sm text-neutral-400">
                  {selectedSlot && format(new Date(selectedSlot), "HH:mm")} -{" "}
                  {selectedSlot &&
                    format(
                      new Date(new Date(selectedSlot).getTime() + data.event_type.duration * 60000),
                      "HH:mm",
                    )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Globe className="h-5 w-5 text-neutral-400" />
              <p className="text-sm text-neutral-400">Google Meet</p>
            </div>
          </div>
          {data.event_type.confirmation_button?.enabled &&
          data.event_type.confirmation_button.url ? (
            <Button
              onClick={() =>
                (window.location.href = data.event_type.confirmation_button?.url ?? "")
              }
              variant="outline"
              className="w-full border-neutral-700 hover:bg-neutral-800 text-white"
            >
              {data.event_type.confirmation_button.text || "Volver al inicio"}
            </Button>
          ) : null}
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center p-4 md:p-8 font-sans">
      <Card className="w-full max-w-5xl bg-neutral-900 border-neutral-800 text-neutral-100 shadow-2xl overflow-hidden flex flex-col md:flex-row min-h-[600px]">
        {/* Left Sidebar: Context Info */}
        <div className="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-neutral-800 p-6 md:p-8 space-y-6 bg-neutral-900/50">
          <div className="space-y-4">
            {data.tenant_avatar && (
              <div className="relative w-16 h-16 rounded-full overflow-hidden border border-neutral-700">
                <Image
                  src={data.tenant_avatar}
                  alt={data.tenant_name}
                  fill
                  className="object-cover"
                />
              </div>
            )}
            <div>
              <p className="text-neutral-400 font-medium text-sm uppercase tracking-wider">
                {data.tenant_name}
              </p>
              <h1 className="text-2xl font-bold mt-1">{data.event_type.title}</h1>
            </div>

            <div className="space-y-3 pt-4">
              {selectedSlot ? (
                <div className="space-y-3 animate-in fade-in slide-in-from-left-4">
                  <div className="flex items-start gap-3 text-neutral-300">
                    <CalendarIcon className="h-5 w-5 text-neutral-500 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium capitalize text-neutral-200">
                        {format(new Date(selectedSlot), "EEEE, d 'de' MMMM 'de' yyyy", {
                          locale: es,
                        })}
                      </p>
                      <p className="text-neutral-400 mt-1">
                        {format(new Date(selectedSlot), "HH:mm")} -{" "}
                        {format(
                          addMinutes(new Date(selectedSlot), data.event_type.duration),
                          "HH:mm",
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-neutral-300">
                    <Globe className="h-5 w-5 text-neutral-500" />
                    <span className="font-medium text-sm">
                      {Intl.DateTimeFormat().resolvedOptions().timeZone}
                    </span>
                  </div>
                </div>
              ) : null}

              <div className="flex items-center gap-3 text-neutral-300">
                <Clock className="h-5 w-5 text-neutral-500" />
                <span className="font-medium">{data.event_type.duration} min</span>
              </div>
              {/* Assuming video call for now as default */}
              <div className="flex items-center gap-3 text-neutral-300">
                <Globe className="h-5 w-5 text-neutral-500" />
                <span className="font-medium">Google Meet</span>
              </div>
            </div>

            {data.event_type.description && (
              <div className="pt-4 border-t border-neutral-800">
                <p className="text-sm text-neutral-400 whitespace-pre-wrap leading-relaxed">
                  {data.event_type.description}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Content: Calendar & Form */}
        <div className="flex-1 p-6 md:p-8 bg-neutral-900">
          <div className="h-full flex flex-col">
            {step === "date" ? (
              <div className="flex-1 flex flex-col md:flex-row gap-8">
                {/* Calendar */}
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-4">Selecciona una fecha</h3>
                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={(d) => {
                      if (d) {
                        setDate(d);
                        setSelectedSlot(null); // Reset slot when date changes
                      }
                    }}
                    month={month}
                    onMonthChange={setMonth}
                    startMonth={new Date()}
                    endMonth={addDays(
                      new Date(),
                      data.event_type.scheduling_limits.max_advance_days || 60,
                    )}
                    modifiers={{
                      available: availableDays,
                    }}
                    modifiersClassNames={{
                      available: "bg-neutral-800 font-medium text-white hover:bg-neutral-700",
                    }}
                    locale={es}
                    className="p-0 border rounded-lg border-neutral-800 bg-neutral-900 w-full"
                    classNames={{
                      day_selected:
                        "bg-white text-black hover:bg-white hover:text-black focus:bg-white focus:text-black",
                      day_today: "bg-neutral-800 text-white",
                      day: "h-full w-full m-1 font-normal aria-selected:opacity-100 hover:bg-neutral-800/50 rounded-md transition-colors text-neutral-500",
                      head_cell: "text-neutral-500 rounded-md w-10 font-normal text-[0.8rem]",
                      caption: "flex justify-center pt-1 relative items-center text-neutral-200",
                      nav_button: "border border-neutral-800 hover:bg-neutral-800 hover:text-white",
                    }}
                    disabled={(date) => {
                      const now = new Date();
                      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                      const maxDate = addDays(
                        today,
                        data.event_type.scheduling_limits.max_advance_days || 60,
                      );
                      return date < today || date > maxDate;
                    }}
                  />
                </div>

                {/* Slots Column */}
                <div className="relative w-full md:w-48 border-l border-neutral-800 min-h-[400px]">
                  <div className="absolute inset-0 flex flex-col md:pl-8 pb-1">
                    <h3 className="text-md font-semibold mb-4 capitalize text-center shrink-0">
                      {date ? format(date, "EEEE dd 'de' MMMM", { locale: es }) : "Horarios"}
                    </h3>

                    <div className="space-y-2 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                      {slotsLoading ? (
                        <div className="flex justify-center py-8">
                          <Loader2 className="animate-spin text-neutral-500" />
                        </div>
                      ) : slots.length > 0 ? (
                        slots.map((slot) => {
                          const timeStr = format(new Date(slot), "HH:mm");
                          return (
                            <Button
                              key={slot}
                              variant={selectedSlot === slot ? "default" : "outline"}
                              className={cn(
                                "w-full justify-center font-medium transition-all flex items-center gap-2",
                                selectedSlot === slot
                                  ? "bg-white text-black hover:bg-white/90"
                                  : "bg-transparent border-neutral-700 text-neutral-300 hover:bg-neutral-800 hover:text-white",
                              )}
                              onClick={() => {
                                setSelectedSlot(slot);
                                setStep("form");
                              }}
                            >
                              <div
                                className={cn(
                                  "w-2 h-2 rounded-full",
                                  selectedSlot === slot ? "bg-black" : "bg-green-500",
                                )}
                              />
                              {timeStr}
                            </Button>
                          );
                        })
                      ) : (
                        <div className="text-sm text-neutral-500 text-center py-8">
                          No hay horarios disponibles para este día.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="max-w-md mx-auto w-full animate-in fade-in slide-in-from-right-4 pt-4">
                <div className="space-y-6">
                  <div>
                    {bookingLinkData && (
                      <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-md text-blue-200 text-sm flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>
                          Reserva personalizada para <strong>{bookingLinkData.lead_name}</strong>
                        </span>
                      </div>
                    )}
                    <h3 className="text-xl font-bold">Ingresa tus datos</h3>
                  </div>

                  <form onSubmit={handleBook} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-neutral-300">
                        Tu Nombre *
                      </Label>
                      <Input
                        id="name"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        disabled={!!bookingLinkData}
                        className="h-10 bg-neutral-950 border-neutral-800 text-white placeholder:text-neutral-600 focus:border-neutral-700 focus:ring-1 focus:ring-neutral-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-neutral-300">
                        Email *
                      </Label>
                      <Input
                        id="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        disabled={!!bookingLinkData?.lead_email}
                        className="h-10 bg-neutral-950 border-neutral-800 text-white placeholder:text-neutral-600 focus:border-neutral-700 focus:ring-1 focus:ring-neutral-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-neutral-300">
                        WhatsApp
                      </Label>
                      <Input
                        id="phone"
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        disabled={!!bookingLinkData?.lead_phone}
                        className="h-10 bg-neutral-950 border-neutral-800 text-white placeholder:text-neutral-600 focus:border-neutral-700 focus:ring-1 focus:ring-neutral-700 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="notes" className="text-neutral-300">
                        Notas Adicionales
                      </Label>
                      <Textarea
                        id="notes"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        className="min-h-[100px] bg-neutral-950 border-neutral-800 text-white placeholder:text-neutral-600 focus:border-neutral-700 focus:ring-1 focus:ring-neutral-700 rounded-md resize-none"
                        placeholder="Por favor, comparta cualquier cosa que ayude a preparar nuestra reunión."
                      />
                    </div>

                    <div className="pt-8 flex justify-end items-center gap-3">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => setStep("date")}
                        className="text-neutral-400 hover:text-white hover:bg-neutral-800"
                      >
                        Atrás
                      </Button>
                      <Button
                        type="submit"
                        disabled={bookingLoading}
                        className="h-10 px-6 bg-white text-black hover:bg-neutral-200 font-medium rounded-full"
                      >
                        {bookingLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Confirmar
                      </Button>
                    </div>
                  </form>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
