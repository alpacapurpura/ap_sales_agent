"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  EventType,
  eventTypesApi,
  EventTypeUpdate
} from "@/lib/api/event-types";
import { AvailabilitySchedule, availabilityApi } from "@/lib/api/availability";
import { settingsApi } from "@/lib/api/settings";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import {
  Settings2,
  Plus,
  MoreHorizontal,
  ExternalLink,
  Copy,
  Edit,
  Trash2,
  Clock,
  Code,
  Link as LinkIcon
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { EventTypeSidebar } from "./event-type-form";
import { GenerateLinkModal } from "./generate-link-modal";

export function EventTypeView() {
  const { getToken } = useAuth();
  const [eventTypes, setEventTypes] = useState<EventType[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEventType, setSelectedEventType] = useState<EventType | null>(null);
  const [selectedEventForLink, setSelectedEventForLink] = useState<EventType | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [availabilities, setAvailabilities] = useState<AvailabilitySchedule[]>([]);
  const [tenantSlug, setTenantSlug] = useState<string>("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const token = await getToken();
      if (!token) return;

      const [etData, avData, profile] = await Promise.all([
        eventTypesApi.listEventTypes(token),
        availabilityApi.listSchedules(token),
        settingsApi.getProfile(token)
      ]);

      setEventTypes(etData);
      setAvailabilities(avData);
      if (profile.tenant?.slug) {
        setTenantSlug(profile.tenant.slug);
      }
    } catch (error) {
      console.error(error);
      toast.error("Error cargando tipos de cita");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = () => {
    setSelectedEventType(null); // Null means create new
    setIsSidebarOpen(true);
  };

  const handleEdit = (et: EventType) => {
    setSelectedEventType(et);
    setIsSidebarOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm("¿Estás seguro de eliminar este tipo de cita?")) return;
    try {
      const token = await getToken();
      if (!token) return;
      await eventTypesApi.deleteEventType(id, token);
      toast.success("Tipo de cita eliminado");
      fetchData();
    } catch (error) {
      toast.error("Error al eliminar");
    }
  };

  const handleDuplicate = async (et: EventType) => {
    try {
      const token = await getToken();
      if (!token) return;
      const { id, ...rest } = et;
      const newEt = {
        ...rest,
        title: `${rest.title} (Copia)`,
        slug: `${rest.slug}-copy`
      };
      await eventTypesApi.createEventType(newEt, token);
      toast.success("Duplicado correctamente");
      fetchData();
    } catch (error) {
      toast.error("Error al duplicar");
    }
  };

  const handleCopyLink = (slug: string) => {
    const url = `${window.location.origin}/book/${tenantSlug}/${slug}`;
    navigator.clipboard.writeText(url);
    toast.success("Link copiado al portapapeles");
  };

  const handleToggleHidden = async (et: EventType, checked: boolean) => {
    // Optimistic update
    const updated = eventTypes.map(e => e.id === et.id ? { ...e, is_hidden: !checked } : e);
    setEventTypes(updated);

    try {
      const token = await getToken();
      if (!token) return;
      await eventTypesApi.updateEventType(et.id, { is_hidden: !checked }, token);
      toast.success(checked ? "Visible en perfil" : "Oculto del perfil");
    } catch (error) {
      toast.error("Error al actualizar estado");
      fetchData(); // Revert
    }
  };

  return (
    <>
      Crea eventos para que la gente reserve en tu calendario.
      <Button onClick={handleCreate} className="gap-2">
        <Plus className="h-4 w-4" /> Nuevo
      </Button>
      {loading ? (
        <div className="text-center py-10">Cargando...</div>
      ) : (
        <div className="grid gap-4">
          {eventTypes.map((et) => (
            <Card
              key={et.id}
              className="group border hover:border-primary transition-all shadow-sm hover:shadow-md"
            >
              <CardContent className="p-6 flex flex-col sm:flex-row sm:items-center justify-between">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-base">{et.title}</h3>
                    <span className="text-xs text-muted-foreground font-mono">/{et.slug}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground ">
                    <Badge variant="secondary" className="font-normal">
                      <Clock className="mr-1 h-3 w-3" />
                      {et.duration}m
                    </Badge>
                    {et.is_hidden && <Badge variant="outline" className="text-muted-foreground">Oculto</Badge>}
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4 sm:mt-0" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center gap-2 mr-2">
                    <span className="text-sm text-muted-foreground hidden sm:inline-block">
                      {et.is_hidden ? "Oculto" : "Visible"}
                    </span>
                    <Switch
                      checked={!et.is_hidden}
                      onCheckedChange={(c) => handleToggleHidden(et, c)}
                    />
                  </div>

                  <Button
                    variant="outline"
                    size="sm"
                    className="mr-2 hidden md:flex gap-2"
                    onClick={() => setSelectedEventForLink(et)}
                  >
                    <LinkIcon className="h-4 w-4" />
                    Link Lead
                  </Button>

                  <div className="flex items-center border rounded-md bg-background">
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-none border-r" onClick={() => window.open(`/book/${tenantSlug}/${et.slug}`, '_blank')}>
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-none border-r" onClick={() => handleCopyLink(et.slug)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-none">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(et)}>
                          <Edit className="mr-2 h-4 w-4" /> Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleDuplicate(et)}>
                          <Copy className="mr-2 h-4 w-4" /> Duplicado
                        </DropdownMenuItem>
                        <DropdownMenuItem disabled>
                          <Code className="mr-2 h-4 w-4" /> Insertar
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => handleDelete(et.id)}>
                          <Trash2 className="mr-2 h-4 w-4" /> Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {eventTypes.length === 0 && (
            <div className="text-center p-8 border border-dashed rounded-lg text-muted-foreground">
              No hay tipos de cita configurados. Crea uno para empezar.
            </div>
          )}
        </div>
      )}

      <EventTypeSidebar
        open={isSidebarOpen}
        onOpenChange={setIsSidebarOpen}
        initialData={selectedEventType}
        availabilities={availabilities}
        onSave={() => {
          setIsSidebarOpen(false);
          fetchData();
        }}
      />

      {selectedEventForLink && (
        <GenerateLinkModal
          open={!!selectedEventForLink}
          onOpenChange={(open) => !open && setSelectedEventForLink(null)}
          eventSlug={selectedEventForLink.slug}
        />
      )}
    </>
  );
}
