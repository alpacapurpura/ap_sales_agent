import { AccommodationType, EventLocationType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * EXPERIENCIA archetype details — date + location + logistics of a salida.
 *
 * EDITION_LEVEL scope: every field is inherently per-salida. The offer-wide
 * framing (promise, avatar, psychology) lives in the other offer-level
 * sections; this one covers the operational logistics of *this* event.
 *
 * Only renders on ``/edition/<N>/`` URLs — editors cannot fill it on the
 * virtual ``evergreen`` code because there is no LaunchEdition row to
 * persist to.
 */
export const offerEventDetailsSchema: SectionSchema = {
  key: "offer.event_details",
  title: "Detalles del evento",
  description: "Fecha, ubicación y capacidad de esta salida específica.",
  scope: "edition_level",
  fields: [
    {
      id: "start_date",
      label: "Fecha y hora de inicio",
      type: "text",
      path: "start_date",
      required: true,
      placeholder: "2026-05-10T10:00:00-05:00",
      hint: "ISO 8601 con timezone. Obligatorio para publicar la salida.",
    },
    {
      id: "end_date",
      label: "Fecha y hora de fin",
      type: "text",
      path: "end_date",
      placeholder: "2026-05-10T18:00:00-05:00",
    },
    {
      id: "timezone",
      label: "Zona horaria",
      type: "text",
      path: "timezone",
      placeholder: "America/Lima",
      hint: "IANA timezone ID. Determina cómo se muestra la fecha al avatar.",
    },
    {
      id: "location_type",
      label: "Tipo de ubicación",
      type: "enum",
      path: "specific_details.location_type",
      options: [
        { value: EventLocationType.VIRTUAL, label: "Virtual" },
        { value: EventLocationType.PHYSICAL_LOCAL, label: "Presencial local" },
        { value: EventLocationType.DESTINATION_RETREAT, label: "Retiro destino" },
      ],
    },
    {
      id: "virtual_meeting_url",
      label: "URL de reunión virtual",
      type: "url",
      path: "specific_details.virtual_meeting_url",
    },
    {
      id: "venue_name",
      label: "Nombre del venue",
      type: "text",
      path: "specific_details.venue_name",
    },
    {
      id: "venue_address",
      label: "Dirección del venue",
      type: "textarea",
      path: "specific_details.venue_address",
      rows: 3,
    },
    {
      id: "capacity",
      label: "Capacidad máxima",
      type: "number",
      path: "capacity",
    },
    {
      id: "accommodation_type",
      label: "Alojamiento incluido",
      type: "enum",
      path: "specific_details.accommodation_type",
      options: [
        { value: AccommodationType.NOT_INCLUDED, label: "No incluido" },
        { value: AccommodationType.SHARED_ROOM, label: "Cuarto compartido" },
        { value: AccommodationType.PRIVATE_ROOM, label: "Cuarto privado" },
        { value: AccommodationType.LUXURY_SUITE, label: "Suite de lujo" },
      ],
    },
    {
      id: "agenda_highlights",
      label: "Puntos altos de la agenda",
      type: "textarea",
      path: "specific_details.agenda_highlights",
      rows: 4,
      hint: "Uno por línea. Los hitos que se destacan en landing + email.",
    },
    {
      id: "dress_code",
      label: "Dress code",
      type: "text",
      path: "specific_details.dress_code",
    },
    {
      id: "is_recorded",
      label: "¿Se graba?",
      type: "boolean",
      path: "specific_details.is_recorded",
      hint: "Si se activa, los asistentes reciben el recording post-evento.",
    },
  ],
};
