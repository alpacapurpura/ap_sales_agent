import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Location — ubicación física + canales de reserva. Agrupa los venues
 * donde se atiende (consultorio, gimnasio, salón, oficina) + cómo se
 * agenda/reserva.
 *
 * Latam: barrio/colonia es más relevante que el código postal cuando el
 * cliente busca "cerca de". WhatsApp es el canal dominante de reserva —
 * teléfono + app propia + Calendly siguen. Para consultorios y negocios
 * locales, si no se entiende cómo agendar, no hay venta.
 *
 * Scope MIXED: venues + booking channels son offer-level (comunes a toda
 * la oferta); event_specific_venue es edition-level (cuando un evento
 * rota venues por edición).
 */
export const offerLocationSchema: SectionSchema = {
  key: "offer.location",
  scope: "mixed",
  fields: [
    {
      id: "venues",
      label: "Sedes y consultorios",
      type: "array",
      path: "venues",
      owner: "offer",
      hint: "Una entrada por sede. Si atendés en un solo lugar, una sola entrada. El frontend los muestra en mapa.",
      itemSchema: {
        description: "Un venue físico con sus datos operativos.",
        fields: [
          {
            id: "name",
            label: "Nombre de la sede",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Sede Miraflores · Consultorio Centro · Estudio Palermo",
          },
          {
            id: "address_line",
            label: "Calle y número",
            type: "text",
            path: "address_line",
            required: true,
            placeholder: "Av. Arequipa 3450, piso 4",
          },
          {
            id: "district",
            label: "Barrio / colonia / distrito",
            type: "text",
            path: "district",
            required: true,
            placeholder: "Miraflores, Polanco, El Poblado, Palermo",
            hint: "Más importante que el código postal en Latam — los clientes buscan por zona.",
          },
          {
            id: "city",
            label: "Ciudad",
            type: "text",
            path: "city",
            required: true,
            placeholder: "Lima, Ciudad de México, Bogotá, Buenos Aires",
          },
          {
            id: "country",
            label: "País",
            type: "text",
            path: "country",
            required: true,
            placeholder: "Perú, México, Colombia, Argentina",
          },
          {
            id: "google_maps_url",
            label: "Link de Google Maps",
            type: "url",
            path: "google_maps_url",
            hint: "Link directo a la ubicación. Vale más que la dirección escrita.",
          },
          {
            id: "phone",
            label: "Teléfono",
            type: "text",
            path: "phone",
            placeholder: "+51 999 888 777",
            hint: "Formato internacional con +código país.",
          },
          {
            id: "whatsapp",
            label: "WhatsApp",
            type: "text",
            path: "whatsapp",
            placeholder: "+51 999 888 777",
            hint: "En Latam el WhatsApp es el canal de contacto dominante — casi siempre es el mismo número que el teléfono.",
          },
          {
            id: "hours_of_operation",
            label: "Horarios de atención",
            type: "textarea",
            path: "hours_of_operation",
            rows: 3,
            placeholder: "Lun-Vie: 9:00-19:00\nSáb: 10:00-14:00\nDom: cerrado",
            hint: "Un día por línea. Aclará días festivos si cerrás.",
          },
          {
            id: "parking_available",
            label: "¿Estacionamiento disponible?",
            type: "boolean",
            path: "parking_available",
            hint: "En grandes ciudades Latam es decisivo.",
          },
          {
            id: "accessibility",
            label: "Accesibilidad",
            type: "text",
            path: "accessibility",
            placeholder: "Rampa, ascensor, baño accesible, amigable silla de ruedas",
            hint: "Detalles para clientes con movilidad reducida.",
          },
          {
            id: "transport_nearby",
            label: "Transporte cercano",
            type: "text",
            path: "transport_nearby",
            placeholder: "Estación Metro Central a 2 cuadras · Parada BRT en frente",
            hint: "Especialmente útil en ciudades con transporte público fuerte (CDMX, BA, Bogotá).",
          },
          {
            id: "photos_urls",
            label: "Fotos del espacio",
            type: "textarea",
            path: "photos_urls",
            rows: 3,
            hint: "URLs de fotos del local (una por línea). Recepción, sala principal, detalles.",
          },
        ],
      },
    },
    {
      id: "booking_channels",
      label: "Canales de reserva",
      type: "array",
      path: "booking_channels",
      owner: "offer",
      hint: "Cómo agendar: WhatsApp, teléfono, app propia, Calendly. El cliente elige el que le resulte cómodo.",
      itemSchema: {
        description: "Un canal por el que se puede reservar.",
        fields: [
          {
            id: "channel_type",
            label: "Tipo de canal",
            type: "enum",
            path: "channel_type",
            required: true,
            options: [
              { value: "whatsapp", label: "WhatsApp" },
              { value: "phone", label: "Teléfono" },
              { value: "calendly", label: "Calendly / Calendario online" },
              { value: "app", label: "App propia" },
              { value: "web_form", label: "Formulario web" },
              { value: "walk_in", label: "Sin reserva (walk-in)" },
              { value: "email", label: "Email" },
              { value: "instagram_dm", label: "Mensaje directo Instagram" },
            ],
          },
          {
            id: "value",
            label: "Valor (número, link, etc.)",
            type: "text",
            path: "value",
            placeholder: "+51999888777 · calendly.com/usuario · app://reservas",
          },
          {
            id: "is_primary",
            label: "¿Canal principal?",
            type: "boolean",
            path: "is_primary",
            hint: "El canal que recomendás. Sólo uno debería ser primary.",
          },
        ],
      },
    },
    {
      id: "booking_lead_time_hours",
      label: "Antelación mínima para reservar (horas)",
      type: "number",
      path: "booking_lead_time_hours",
      owner: "offer",
      placeholder: "24",
      hint: "Cuánto antes debe agendar el cliente. 0 = mismo día disponible.",
    },
    {
      id: "booking_instructions",
      label: "Cómo reservar (pasos)",
      type: "textarea",
      path: "booking_instructions",
      owner: "offer",
      rows: 4,
      placeholder: "1. Escribinos al WhatsApp\n2. Confirmá día y hora\n3. Pagá 50% para bloquear el turno\n4. Llegá 10 min antes",
      hint: "Un paso por línea. Simplifica. Reduce ansiedad pre-compra.",
    },
    {
      id: "confirmation_method",
      label: "Cómo se confirma la reserva",
      type: "enum",
      path: "confirmation_method",
      owner: "offer",
      options: [
        { value: "whatsapp", label: "WhatsApp" },
        { value: "sms", label: "SMS" },
        { value: "email", label: "Email" },
        { value: "call", label: "Llamada" },
      ],
      hint: "WhatsApp es el estándar Latam.",
    },
    {
      id: "no_show_policy",
      label: "Política de no-show",
      type: "textarea",
      path: "no_show_policy",
      owner: "offer",
      rows: 2,
      placeholder: "Si no avisás con 24h de antelación, se pierde el adelanto.",
      hint: "Explicá qué pasa si el cliente no se presenta. Reduce no-shows.",
    },
    {
      id: "event_specific_venue",
      label: "Venue específico de esta edición",
      type: "textarea",
      path: "event_specific_venue",
      owner: "edition",
      rows: 3,
      placeholder: "Cohorte Q2: Hotel Sheraton Lima, Salón Conquistadores (día único)",
      hint: "Usar cuando una edición específica ocurre en venue distinto al habitual. Opcional.",
    },
  ],
};
