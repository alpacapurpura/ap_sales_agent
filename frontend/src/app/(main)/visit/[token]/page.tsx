"use client";

import { format, parseISO, addMonths, subMonths } from "date-fns";
import { es } from "date-fns/locale";
import {
  Loader2,
  Calendar as CalendarIcon,
  Clock,
  CheckCircle2,
  Video,
  Globe,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import Image from "next/image";
import { use, useEffect, useState } from "react";
import { toast } from "sonner";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { publicApi } from "@/lib/api/public";
import { cn } from "@/lib/utils";

import type { LinkResolveResponse } from "@/lib/api/public";

export default function PublicVisitPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<LinkResolveResponse | null>(null);

  // Booking State - Initialize with today
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [month, setMonth] = useState<Date>(new Date()); // Control Calendar View Month
  const [slots, setSlots] = useState<string[]>([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
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
    publicApi
      .resolveLink(token)
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    if (date && data) {
      setSlotsLoading(true);
      const dateStr = format(date, "yyyy-MM-dd");
      // Fetch slots for the selected date
      publicApi
        .getSlots(token, dateStr, dateStr)
        .then(setSlots)
        .catch(() => toast.error("Error cargando horarios"))
        .finally(() => setSlotsLoading(false));
    } else {
      setSlots([]);
    }
  }, [date, token, data]);

  // Sync month when date is selected (optional but good UX)
  useEffect(() => {
    if (date) {
      setMonth(date);
    }
  }, [date]);

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) return;

    setBookingLoading(true);
    try {
      await publicApi.bookMeeting(token, {
        slot_time: selectedSlot,
        duration_minutes: 30, // Default or from params
        ...formData,
      });
      setStep("success");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al agendar");
    } finally {
      setBookingLoading(false);
    }
  };

  const handleSlotSelect = (slot: string) => {
    setSelectedSlot(slot);
    setStep("form");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <Loader2 className="w-8 h-8 animate-spin text-neutral-900" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50 p-4">
        <Card className="w-full max-w-md text-center py-8">
          <CardHeader>
            <CardTitle className="text-destructive">Enlace No Válido</CardTitle>
            <CardDescription>
              Este enlace ha expirado o no existe. Por favor contacta a la persona que te lo envió.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  if (step === "success") {
    if (!selectedSlot) return null;
    return (
      <div className="min-h-screen flex items-center justify-center bg-black/95 p-4">
        <Card className="w-full max-w-md text-center py-8 border-green-900/30 bg-green-950/10">
          <CardHeader>
            <div className="mx-auto w-12 h-12 bg-green-900/20 rounded-full flex items-center justify-center mb-4">
              <CheckCircle2 className="w-6 h-6 text-green-500" />
            </div>
            <CardTitle className="text-green-500">¡Reserva Confirmada!</CardTitle>
            <CardDescription className="text-green-400/80">
              Hemos enviado los detalles a tu correo electrónico ({formData.email}).
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-black/40 p-4 rounded-lg mb-6 border border-green-900/30">
              <p className="font-medium text-green-400">
                {format(new Date(selectedSlot), "EEEE d 'de' MMMM", { locale: es })}
              </p>
              <p className="text-green-500/80">
                {format(new Date(selectedSlot), "h:mm a", { locale: es })} -{" "}
                {format(new Date(new Date(selectedSlot).getTime() + 30 * 60000), "h:mm a")}
              </p>
            </div>
            <Button
              onClick={() => window.location.reload()}
              variant="outline"
              className="w-full border-white/10 hover:bg-white/5 text-white hover:text-white"
            >
              Agendar otra reunión
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4 md:p-8 font-sans">
      {/* Meta Robots NoIndex */}
      <meta name="robots" content="noindex" />

      <Card className="w-full max-w-5xl shadow-2xl overflow-hidden border border-white/10 bg-black/40 backdrop-blur-xl">
        <div className="flex flex-col md:flex-row min-h-[600px]">
          {/* Col 1: Sidebar (Host Info) */}
          <div className="w-full md:w-[300px] p-6 border-b md:border-b-0 md:border-r border-white/10 bg-black/20 flex flex-col gap-6">
            {step === "form" && (
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden self-start -ml-2 mb-2 text-white hover:bg-white/10"
                onClick={() => setStep("date")}
              >
                <ChevronLeft className="h-5 w-5" />
              </Button>
            )}

            <div className="space-y-4">
              {data.tenant_avatar ? (
                <div className="relative w-16 h-16">
                  <Image
                    src={data.tenant_avatar}
                    alt="Logo"
                    fill
                    className="rounded-full object-cover shadow-sm border border-white/10"
                  />
                </div>
              ) : (
                <Avatar className="h-16 w-16 border border-white/10">
                  <AvatarImage src="" />
                  <AvatarFallback className="text-lg bg-neutral-900 text-white">
                    {data.tenant_name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
              )}

              <div>
                <h3 className="text-neutral-400 font-medium text-sm mb-1">{data.tenant_name}</h3>
                <h1 className="text-2xl font-bold text-white leading-tight">
                  Sesión de Estrategia
                </h1>
              </div>

              <div className="space-y-3 text-neutral-400">
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-neutral-500" />
                  <span className="font-medium">30 min</span>
                </div>
                <div className="flex items-center gap-3">
                  <Video className="w-5 h-5 text-neutral-500" />
                  <span className="font-medium">Videollamada</span>
                </div>
              </div>

              <p className="text-sm text-neutral-400 leading-relaxed pt-2">
                Agenda una llamada para explorar cómo podemos ayudarte a escalar tus resultados.
              </p>
            </div>

            <div className="mt-auto hidden md:block">
              <div className="flex items-center gap-2 text-xs text-neutral-500 font-medium">
                <Globe className="h-3 w-3" />
                <span>Hora de Lima (GMT-5)</span>
              </div>
            </div>
          </div>

          {/* Main Area: Calendar or Form */}
          <div className="flex-1 flex flex-col md:flex-row relative">
            {step === "date" ? (
              <>
                {/* Col 2: Calendar */}
                <div
                  className={cn(
                    "flex-1 p-6 md:p-8 flex flex-col items-center justify-start border-b md:border-b-0 md:border-r border-white/10 transition-all",
                    date ? "md:w-[400px]" : "w-full",
                  )}
                >
                  {/* Manual Calendar Header */}
                  <div className="flex items-center justify-between mb-4 w-full max-w-[400px] px-2">
                    <h3 className="text-base font-medium text-white capitalize pl-2">
                      {format(month, "MMMM yyyy", { locale: es })}
                    </h3>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 bg-transparent hover:bg-white/10 text-white"
                        onClick={() => setMonth(subMonths(month, 1))}
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 bg-transparent hover:bg-white/10 text-white"
                        onClick={() => setMonth(addMonths(month, 1))}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <Calendar
                    mode="single"
                    selected={date}
                    onSelect={setDate}
                    month={month}
                    onMonthChange={setMonth}
                    className="p-4 rounded-md w-full max-w-[400px] bg-transparent text-white"
                    classNames={{
                      month: "space-y-4 w-full",
                      caption: "hidden !hidden", // Force hide default caption
                      nav: "hidden !hidden",
                      caption_label: "hidden !hidden",
                      table: "w-full border-collapse space-y-1",
                      head_row: "flex",
                      head_cell:
                        "text-neutral-500 rounded-md w-12 font-normal text-[0.8rem] h-10 uppercase",
                      row: "flex w-full mt-2",
                      cell: "h-12 w-12 text-center text-sm p-0 relative [&:has([aria-selected].day-range-end)]:rounded-r-md [&:has([aria-selected].day-outside)]:bg-accent/50 [&:has([aria-selected])]:bg-accent first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
                      day: "h-12 w-12 p-0 font-normal aria-selected:opacity-100 hover:bg-white/10 rounded-md transition-colors text-white",
                      day_selected:
                        "bg-white !text-black hover:bg-white/90 focus:bg-white/90 font-bold",
                      day_today: "bg-white/10 text-white font-bold border border-white/20",
                      day_outside: "text-neutral-700 opacity-50",
                      day_disabled: "text-neutral-700 opacity-50",
                      day_range_middle:
                        "aria-selected:bg-accent aria-selected:text-accent-foreground",
                      day_hidden: "invisible",
                    }}
                    locale={es}
                    disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
                  />
                </div>

                {/* Col 3: Slots */}
                {date && (
                  <div className="w-full md:w-[280px] p-4 animate-in slide-in-from-right-4 fade-in duration-300 border-l border-white/10">
                    <h3 className="text-sm font-medium text-neutral-400 mb-4 uppercase tracking-wider">
                      {format(date, "EEEE d", { locale: es })}
                    </h3>

                    <ScrollArea className="h-[400px] pr-4">
                      {slotsLoading ? (
                        <div className="flex justify-center py-8">
                          <Loader2 className="h-6 w-6 animate-spin text-white" />
                        </div>
                      ) : slots.length > 0 ? (
                        <div className="space-y-2.5">
                          {slots.map((slot) => (
                            <Button
                              key={slot}
                              variant="outline"
                              className="w-full justify-center font-semibold text-white border-white/20 bg-transparent hover:bg-white hover:text-black transition-all py-6"
                              onClick={() => handleSlotSelect(slot)}
                            >
                              {format(parseISO(slot), "h:mm a")}
                            </Button>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-neutral-500 text-sm">
                          No hay horarios disponibles para esta fecha.
                        </div>
                      )}
                    </ScrollArea>
                  </div>
                )}
              </>
            ) : (
              /* Form View (Replaces Calendar/Slots area) */
              <div className="flex-1 p-6 md:p-12 animate-in fade-in slide-in-from-right-4">
                <Button
                  variant="ghost"
                  className="mb-6 -ml-2 text-neutral-400 hover:text-white hover:bg-white/10"
                  onClick={() => setStep("date")}
                >
                  <ChevronLeft className="mr-2 h-4 w-4" />
                  Volver al calendario
                </Button>

                <div className="max-w-md">
                  <h2 className="text-xl font-bold mb-1 text-white">Confirma tus datos</h2>
                  <p className="text-sm text-neutral-400 mb-8">
                    Para agendar el{" "}
                    {selectedSlot
                      ? format(new Date(selectedSlot), "EEEE d 'de' MMMM 'a las' h:mm a", {
                          locale: es,
                        })
                      : ""}
                  </p>

                  <form onSubmit={handleBook} className="space-y-5">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-neutral-300">
                        Nombre Completo *
                      </Label>
                      <Input
                        id="name"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="h-10 bg-black/20 border-white/10 text-white placeholder:text-neutral-600 focus:border-white/30"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-neutral-300">
                        Correo Electrónico *
                      </Label>
                      <Input
                        id="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="h-10 bg-black/20 border-white/10 text-white placeholder:text-neutral-600 focus:border-white/30"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone" className="text-neutral-300">
                        Teléfono (Opcional)
                      </Label>
                      <Input
                        id="phone"
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="h-10 bg-black/20 border-white/10 text-white placeholder:text-neutral-600 focus:border-white/30"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="notes" className="text-neutral-300">
                        Notas adicionales
                      </Label>
                      <Textarea
                        id="notes"
                        value={formData.notes}
                        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                        className="min-h-[100px] bg-black/20 border-white/10 text-white placeholder:text-neutral-600 focus:border-white/30"
                        placeholder="¿De qué te gustaría hablar?"
                      />
                    </div>

                    <div className="pt-4">
                      <Button
                        type="submit"
                        disabled={bookingLoading}
                        className="w-full h-11 text-base bg-white text-black hover:bg-white/90"
                      >
                        {bookingLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Confirmar Reserva
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
