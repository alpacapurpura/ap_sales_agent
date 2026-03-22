"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  AvailabilitySchedule,
  WeeklySchedule,
  DaySchedule,
  TimeRange,
  availabilityApi
} from "@/lib/api/availability";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Plus, Trash2, Copy, Globe, Clock, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

// --- Constants & Helpers ---

const DAYS: { key: keyof WeeklySchedule; label: string }[] = [
  { key: "monday", label: "Lunes" },
  { key: "tuesday", label: "Martes" },
  { key: "wednesday", label: "Miércoles" },
  { key: "thursday", label: "Jueves" },
  { key: "friday", label: "Viernes" },
  { key: "saturday", label: "Sábado" },
  { key: "sunday", label: "Domingo" },
];

const TIMEZONES = [
  "America/Bogota",
  "America/Mexico_City",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/Madrid",
  "UTC"
];

const generateTimeOptions = () => {
  const options = [];
  for (let h = 0; h < 24; h++) {
    for (let m = 0; m < 60; m += 15) {
      const hh = h.toString().padStart(2, "0");
      const mm = m.toString().padStart(2, "0");
      options.push(`${hh}:${mm}`);
    }
  }
  return options;
};

const TIME_OPTIONS = generateTimeOptions();

// --- Components ---

function TimeSelect({ value, onChange }: { value: string, onChange: (val: string) => void }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[100px]">
        <SelectValue placeholder="Select time" />
      </SelectTrigger>
      <SelectContent>
        {TIME_OPTIONS.map((t) => (
          <SelectItem key={t} value={t}>
            {t}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function AvailabilityView() {
  const { getToken } = useAuth();
  const [schedules, setSchedules] = useState<AvailabilitySchedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSchedule, setSelectedSchedule] = useState<AvailabilitySchedule | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);

  const fetchSchedules = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await availabilityApi.listSchedules(token);
      setSchedules(data);
    } catch (error) {
      console.error(error);
      toast.error("Error cargando disponibilidades");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchSchedules();
  }, [fetchSchedules]);

  const handleCreate = async () => {
    const newSchedule: any = {
      name: "Nueva Disponibilidad",
      is_default: schedules.length === 0,
      timezone: "America/Bogota",
      schedule: {
        monday: { active: true, ranges: [{ start: "09:00", end: "17:00" }] },
        tuesday: { active: true, ranges: [{ start: "09:00", end: "17:00" }] },
        wednesday: { active: true, ranges: [{ start: "09:00", end: "17:00" }] },
        thursday: { active: true, ranges: [{ start: "09:00", end: "17:00" }] },
        friday: { active: true, ranges: [{ start: "09:00", end: "17:00" }] },
        saturday: { active: false, ranges: [] },
        sunday: { active: false, ranges: [] },
      }
    };

    try {
      const token = await getToken();
      if (!token) return;
      const created = await availabilityApi.createSchedule(newSchedule, token);
      setSchedules([...schedules, created]);
      setSelectedSchedule(created);
      setIsSheetOpen(true);
      toast.success("Disponibilidad creada");
    } catch (error) {
      toast.error("Error al crear");
    }
  };

  const handleEdit = (schedule: AvailabilitySchedule) => {
    setSelectedSchedule(JSON.parse(JSON.stringify(schedule))); // Deep copy
    setIsSheetOpen(true);
  };

  return (
    <>
      Configure los horarios en los que está disponible para realizar reservas.
      <Button onClick={handleCreate} className="gap-2">
        <Plus className="h-4 w-4" /> Nuevo
      </Button>
      {loading ? (
        <div className="flex justify-center p-8"><Loader2 className="animate-spin" /></div>
      ) : (
        <div className="grid gap-4">
          {schedules.map((schedule) => (
            <Card
              key={schedule.id}
              className="cursor-pointer border hover:border-primary transition-all shadow-sm hover:shadow-md"
              onClick={() => handleEdit(schedule)}
            >
              <CardContent className="p-6 flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-base">{schedule.name}</h4>
                    {schedule.is_default && <Badge variant="secondary">Predeterminado</Badge>}
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1"><Globe className="h-3 w-3" /> {schedule.timezone}</span>
                  </div>
                </div>
                <Button variant="ghost" size="icon"><Clock className="h-4 w-4" /></Button>
              </CardContent>
            </Card>
          ))}
          {schedules.length === 0 && (
            <div className="text-center p-8 border border-dashed rounded-lg text-muted-foreground">
              No hay horarios configurados. Crea uno para empezar.
            </div>
          )}
        </div>
      )}

      <Sheet open={isSheetOpen} onOpenChange={(open) => {
        setIsSheetOpen(open);
        if (!open) {
          fetchSchedules(); // Refresh on close to ensure sync
          setSelectedSchedule(null);
        }
      }}>
        <SheetContent className="sm:max-w-xl w-full overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Editar Disponibilidad</SheetTitle>
            <SheetDescription>Configure los días y horas disponibles.</SheetDescription>
          </SheetHeader>
          {selectedSchedule && (
            <ScheduleEditor
              initialSchedule={selectedSchedule}
              onSave={() => {
                setIsSheetOpen(false);
                fetchSchedules();
              }}
            />
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function ScheduleEditor({ initialSchedule, onSave }: { initialSchedule: AvailabilitySchedule, onSave: () => void }) {
  const { getToken } = useAuth();
  const [schedule, setSchedule] = useState<AvailabilitySchedule>(initialSchedule);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const updateDay = (day: keyof WeeklySchedule, updates: Partial<DaySchedule>) => {
    setSchedule(prev => ({
      ...prev,
      schedule: {
        ...prev.schedule,
        [day]: { ...prev.schedule[day], ...updates }
      }
    }));
  };

  const addRange = (day: keyof WeeklySchedule) => {
    const currentRanges = schedule.schedule[day].ranges;
    const lastRange = currentRanges[currentRanges.length - 1];
    let newStart = "09:00";
    let newEnd = "17:00";

    // Try to be smart about next slot
    if (lastRange) {
      // Logic to find next slot could go here, keeping simple for now
    }

    updateDay(day, {
      ranges: [...currentRanges, { start: newStart, end: newEnd }]
    });
  };

  const removeRange = (day: keyof WeeklySchedule, index: number) => {
    const newRanges = [...schedule.schedule[day].ranges];
    newRanges.splice(index, 1);
    updateDay(day, { ranges: newRanges });
  };

  const updateRange = (day: keyof WeeklySchedule, index: number, field: 'start' | 'end', value: string) => {
    const newRanges = [...schedule.schedule[day].ranges];
    newRanges[index] = { ...newRanges[index], [field]: value };
    updateDay(day, { ranges: newRanges });
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const token = await getToken();
      if (!token) return;
      await availabilityApi.updateSchedule(schedule.id!, schedule, token);
      toast.success("Guardado correctamente");
      onSave();
    } catch (error) {
      toast.error("Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("¿Estás seguro de borrar este horario?")) return;
    try {
      setDeleting(true);
      const token = await getToken();
      if (!token) return;
      await availabilityApi.deleteSchedule(schedule.id!, token);
      toast.success("Horario eliminado");
      onSave();
    } catch (error) {
      toast.error("No se puede eliminar (quizás es el último o único)");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="mt-6 space-y-6 pb-10">
      {/* Header Settings */}
      <div className="space-y-4 p-4 border rounded-lg bg-muted/20">
        <div className="grid gap-2">
          <label className="text-sm font-medium">Nombre</label>
          <Input
            value={schedule.name}
            onChange={(e) => setSchedule({ ...schedule, name: e.target.value })}
          />
        </div>
        <div className="grid gap-2">
          <label className="text-sm font-medium">Zona Horaria</label>
          <Select
            value={schedule.timezone}
            onValueChange={(v) => setSchedule({ ...schedule, timezone: v })}
          >
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {TIMEZONES.map(tz => <SelectItem key={tz} value={tz}>{tz}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Establecer como predeterminado</label>
          <Switch
            checked={schedule.is_default}
            onCheckedChange={(c) => setSchedule({ ...schedule, is_default: c })}
          />
        </div>
      </div>

      {/* Weekly Schedule */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium">Horario Semanal</h4>
        </div>

        <div className="space-y-4">
          {DAYS.map(({ key, label }) => {
            const daySchedule = schedule.schedule[key];
            return (
              <div key={key} className="flex flex-col gap-3 p-3 border rounded-md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Switch
                      checked={daySchedule.active}
                      onCheckedChange={(c) => updateDay(key, { active: c })}
                    />
                    <span className="font-medium w-24">{label}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8"
                    disabled={!daySchedule.active}
                    onClick={() => addRange(key)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>

                {daySchedule.active && (
                  <div className="pl-12 space-y-2">
                    {daySchedule.ranges.length === 0 ? (
                      <div className="text-xs text-muted-foreground italic">No disponible</div>
                    ) : (
                      daySchedule.ranges.map((range, idx) => (
                        <div key={idx} className="flex items-center gap-2">
                          <TimeSelect
                            value={range.start}
                            onChange={(v) => updateRange(key, idx, 'start', v)}
                          />
                          <span className="text-muted-foreground">-</span>
                          <TimeSelect
                            value={range.end}
                            onChange={(v) => updateRange(key, idx, 'end', v)}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-destructive"
                            onClick={() => removeRange(key, idx)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t">
        <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
          {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
          Eliminar
        </Button>
        <Button onClick={handleSave} disabled={saving}>
          {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
          Guardar Cambios
        </Button>
      </div>
    </div>
  );
}
