import { headers } from "next/headers";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { config } from "@/lib/config";

interface EventType {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  duration: number;
}

interface EventTypeResolveResponse {
  event_type: EventType;
  tenant_name: string;
  tenant_avatar: string | null;
  tenant_id: string;
}

async function getEventType(
  eventSlug: string,
  tenantId: string,
): Promise<EventTypeResolveResponse | null> {
  try {
    const res = await fetch(
      `${config.api.baseUrl}/api/v1/scheduling/public/event-types/by-id/${eventSlug}`,
      {
        headers: { "X-Tenant-ID": tenantId },
        next: { revalidate: 60 },
      },
    );
    if (!res.ok) return null;
    return res.json() as Promise<EventTypeResolveResponse>;
  } catch {
    return null;
  }
}

interface PageProps {
  params: Promise<{ eventSlug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { eventSlug } = await params;
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";
  const data = tenantId ? await getEventType(eventSlug, tenantId) : null;

  if (!data) return { title: "Reserva de cita" };

  return {
    title: `Reservar — ${data.event_type.title} | ${data.tenant_name}`,
    description: data.event_type.description ?? undefined,
  };
}

export default async function BookingPage({ params }: PageProps) {
  const { eventSlug } = await params;
  const headersList = await headers();
  const tenantId = headersList.get("X-Tenant-ID") ?? "";

  if (!tenantId) notFound();

  const data = await getEventType(eventSlug, tenantId);
  if (!data) notFound();

  const { event_type, tenant_name, tenant_avatar } = data;

  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 w-full max-w-md p-8 space-y-6">
        {/* Tenant identity */}
        <div className="flex items-center gap-3">
          {tenant_avatar && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={tenant_avatar}
              alt={tenant_name}
              className="h-10 w-10 rounded-full object-cover"
            />
          )}
          <span className="text-sm font-medium text-gray-500">{tenant_name}</span>
        </div>

        {/* Event info */}
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-gray-900">{event_type.title}</h1>
          {event_type.description && (
            <p className="text-gray-600 text-sm leading-relaxed">{event_type.description}</p>
          )}
          <p className="text-sm text-gray-400">{event_type.duration} min</p>
        </div>

        {/* Coming soon notice */}
        <div className="rounded-xl bg-indigo-50 border border-indigo-100 p-4 text-center">
          <p className="text-indigo-700 font-medium text-sm">Calendario de reservas</p>
          <p className="text-indigo-500 text-xs mt-1">Disponible próximamente</p>
        </div>
      </div>
    </main>
  );
}
