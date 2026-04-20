import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Location — ubicación física + link al flujo de reserva configurado
 * en el módulo Scheduling. Para consultorios, gimnasios, salones, centros
 * de estética y similares.
 *
 * **Integración con módulo Scheduling (no duplica):** la lógica de
 * horarios, slots disponibles, sync con Google Calendar y generación de
 * ``BookingLink`` ya vive en ``backend/src/modules/scheduling/``. Esta
 * sección sólo **referencia** el ``event_type_id`` configurado en ese
 * módulo via el custom action ``scheduling-event-type-picker``.
 *
 * **Latam:** barrio/colonia > código postal para búsqueda "cerca de".
 * WhatsApp es el canal de contacto dominante — siempre se expone aunque
 * el booking use Scheduling.
 *
 * **Scope MIXED:** venues + scheduling link son offer-level;
 * ``event_specific_venue`` es edition-level (retiros/eventos que rotan
 * venue por edición).
 */
export const offerLocationSchema: SectionSchema = {
  key: "offer.location",
  scope: "mixed",
  fields: [
    {
      id: "venues",
      label: "Sedes donde atiendes",
      type: "array",
      path: "venues",
      owner: "offer",
      hint: "Una entrada por sede. Si atiendes en un solo lugar, una sola entrada. El agente de ventas y la landing usan estos datos para mostrar cómo llegar. Si tu negocio no es presencial, deja vacío.",
      itemSchema: {
        description: "Una sede física (consultorio, gimnasio, salón, oficina).",
        fields: [
          {
            id: "name",
            label: "Nombre de la sede",
            type: "text",
            path: "name",
            required: true,
            placeholder: "ej. Sede Miraflores · Consultorio Centro",
            hint: "Cómo llamas a esta sede. Si tienes una sola, usa el nombre del negocio.",
          },
          {
            id: "address_line",
            label: "Dirección (calle y número)",
            type: "text",
            path: "address_line",
            required: true,
            placeholder: "ej. Av. Arequipa 3450, piso 4",
          },
          {
            id: "district",
            label: "Barrio / colonia / distrito",
            type: "text",
            path: "district",
            required: true,
            placeholder: "ej. Miraflores · Polanco · El Poblado · Palermo",
            hint: "En Latam los clientes buscan por zona, no por código postal. Ponlo.",
          },
          {
            id: "city",
            label: "Ciudad",
            type: "text",
            path: "city",
            required: true,
            placeholder: "ej. Lima · CDMX · Bogotá · Buenos Aires",
          },
          {
            id: "country",
            label: "País",
            type: "text",
            path: "country",
            required: true,
            placeholder: "ej. Perú · México · Colombia",
          },
          {
            id: "google_maps_url",
            label: "Link de Google Maps",
            type: "url",
            path: "google_maps_url",
            hint: "Link directo a la ubicación. Vale más que la dirección escrita — el cliente hace tap y abre Maps.",
          },
          {
            id: "whatsapp_contact",
            label: "WhatsApp de esta sede",
            type: "text",
            path: "whatsapp_contact",
            placeholder: "ej. +51 999 888 777",
            hint: "Formato internacional con +código país. En Latam el WhatsApp es el canal dominante de contacto — aunque la reserva use Scheduling, este número sigue siendo útil para consultas.",
          },
          {
            id: "hours_of_operation",
            label: "Horarios de atención",
            type: "textarea",
            path: "hours_of_operation",
            rows: 3,
            placeholder: "Lun-Vie: 9:00-19:00\nSáb: 10:00-14:00\nDom: cerrado",
            hint: "Un día por línea. Aclara feriados si cierras. El agente usa esto para responder '¿a qué hora atienden?'.",
          },
          {
            id: "facilities",
            label: "Instalaciones destacadas",
            type: "text",
            path: "facilities",
            placeholder: "ej. Estacionamiento gratis · WiFi · Baño accesible · Piscina",
            hint: "Lista separada por punto. Lo que diferencia la experiencia in situ (estacionamiento, accesibilidad, sala de espera, etc.).",
          },
          {
            id: "transport_nearby",
            label: "Transporte público cerca",
            type: "text",
            path: "transport_nearby",
            placeholder: "ej. Metro Central a 2 cuadras · Parada BRT en frente",
            hint: "Opcional. En ciudades con transporte público fuerte (CDMX, BA, Bogotá, Santiago) suma mucho.",
          },
          {
            id: "photos_urls",
            label: "Fotos del espacio",
            type: "textarea",
            path: "photos_urls",
            rows: 3,
            placeholder: "https://...\nhttps://...",
            hint: "Una URL por línea. Recepción, sala principal, detalles. Suman credibilidad en la landing.",
          },
        ],
      },
    },
    {
      id: "scheduling_event_type_id",
      label: "Tipo de evento de Scheduling para reservar",
      type: "custom",
      path: "scheduling_event_type_id",
      owner: "offer",
      action: "scheduling-event-type-picker",
      hint: "Selecciona el event type configurado en el módulo Scheduling. Con esto el agente genera BookingLinks temporales, sincroniza con Google Calendar y muestra la landing de disponibilidad. Si no configuraste Scheduling todavía, hazlo en Configuración → Agenda y vuelve acá.",
    },
    {
      id: "booking_fallback_whatsapp",
      label: "WhatsApp alternativo para reservar",
      type: "text",
      path: "booking_fallback_whatsapp",
      owner: "offer",
      placeholder: "ej. +51 999 888 777",
      hint: "Úsalo si aún no tienes Scheduling configurado. El agente ofrece este WhatsApp como vía alternativa de reserva. Cuando el cliente prefiere humano sobre el calendario automático, este número lo resuelve.",
    },
    {
      id: "event_specific_venue",
      label: "Sede específica de esta edición",
      type: "textarea",
      path: "event_specific_venue",
      owner: "edition",
      rows: 3,
      placeholder: "ej. Cohorte Q2: Hotel Sheraton Lima, Salón Conquistadores",
      hint: "Usar SOLO cuando esta edición concreta ocurre en un venue distinto al habitual. Retiros, workshops itinerantes, eventos en hoteles. Para uso diario el sistema toma la sede principal de arriba.",
    },
  ],
};
