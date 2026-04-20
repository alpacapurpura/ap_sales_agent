import { AccommodationType, EventLocationType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * EXPERIENCIA archetype details — logística concreta de una salida.
 *
 * Scope EDITION_LEVEL: todos los campos cambian por salida (una misma
 * experiencia puede repetirse en distintas fechas/ciudades con distintos
 * speakers o precios). Solo renderiza sobre URLs ``/edition/<N>/`` — la
 * URL virtual ``evergreen`` lo oculta porque no hay ``LaunchEdition`` a
 * la que persistir.
 *
 * **Latam — decisiones de diseño:**
 * - ``what_to_bring`` y ``meals_included`` son decisivos en retiros:
 *   el 40% de no-shows o reclamos viene de expectativas mal seteadas
 *   sobre qué traer y qué se come.
 * - ``live_streamed_secondary_url`` captura el caso cada vez más común
 *   de eventos híbridos presenciales + streaming pago con descuento.
 * - ``refund_deadline_days`` comunica la ventana de cancelación sin
 *   penalidad. Sin este campo los atendees asumen 100% refund hasta el
 *   día del evento → disputas.
 * - ``accessibility_notes`` es requisito legal en Argentina (Ley 26.378),
 *   Chile (Ley 20.422), y recomendación ética en Latam general.
 * - ``checkin_start_time`` evita la confusión "llegué al venue y estaba
 *   cerrado 1h antes".
 */
export const offerEventDetailsSchema: SectionSchema = {
  key: "offer.event_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "edition_level",
  fields: [
    // ─── Fecha, hora, timezone ────────────────────────────────────────────
    {
      id: "start_date",
      label: "Fecha y hora de inicio",
      type: "text",
      path: "start_date",
      required: true,
      placeholder: "2026-05-10T10:00:00-05:00",
      hint: "ISO 8601 con offset. Obligatorio para publicar la salida. El sistema convierte a timezone del visitante al mostrarlo en landing.",
    },
    {
      id: "end_date",
      label: "Fecha y hora de fin",
      type: "text",
      path: "end_date",
      placeholder: "2026-05-10T18:00:00-05:00",
      hint: "Obligatorio si es multi-día (retiros). Para eventos de 1 día puedes dejar vacío y usar solo start_date.",
    },
    {
      id: "timezone",
      label: "Zona horaria",
      type: "text",
      path: "timezone",
      placeholder: "America/Lima",
      hint: "IANA timezone ID. Ej: America/Bogota, America/Mexico_City, America/Argentina/Buenos_Aires. Si la salida es presencial, usa el timezone del venue; si es virtual, el timezone principal de tu audiencia.",
    },
    {
      id: "checkin_start_time",
      label: "Apertura del venue / check-in",
      type: "text",
      path: "specific_details.checkin_start_time",
      placeholder: "09:00",
      hint: "Hora local. Cuándo abren puertas. Típico: 1h antes del inicio formal. Esto se comunica en el email de recordatorio 24h antes.",
    },
    {
      id: "rsvp_deadline",
      label: "Fecha límite de confirmación / RSVP",
      type: "text",
      path: "specific_details.rsvp_deadline",
      placeholder: "2026-05-05T23:59:00-05:00",
      hint: "Hasta cuándo aceptas compradores. Para retiros con alojamiento conviene cerrar 2-4 semanas antes (logística). Para eventos 1 día, hasta 24h antes está bien.",
    },

    // ─── Tipo de ubicación ────────────────────────────────────────────────
    {
      id: "location_type",
      label: "Tipo de ubicación",
      type: "enum",
      path: "specific_details.location_type",
      options: [
        { value: EventLocationType.VIRTUAL, label: "Virtual (online, sin venue físico)" },
        { value: EventLocationType.PHYSICAL_LOCAL, label: "Presencial local (en tu ciudad habitual)" },
        { value: EventLocationType.DESTINATION_RETREAT, label: "Retiro destino (viajan tú y los atendees)" },
      ],
      hint: "Virtual escala al infinito. Presencial local retiene mejor a la audiencia local. Destination retreat es el mayor valor percibido pero la logística más compleja.",
    },
    {
      id: "virtual_meeting_url",
      label: "URL de la reunión virtual (Zoom / Meet / Riverside)",
      type: "url",
      path: "specific_details.virtual_meeting_url",
      placeholder: "https://us06web.zoom.us/j/...",
      hint: "Solo si es virtual o híbrido. Se envía post-checkout + recordatorio 1h antes. Zoom recurrente es lo más adoptado Latam. Valida que el link soporta tu capacidad.",
    },
    {
      id: "venue_name",
      label: "Nombre del venue",
      type: "text",
      path: "specific_details.venue_name",
      placeholder: "Hotel Country Club / Casa Nova Cartagena",
      hint: "Solo si es presencial. Nombre que reconoce la audiencia. Si es venue desconocido, usa 'Quinta El Laurel (zona Chacarilla, Lima)' para referencia geográfica.",
    },
    {
      id: "venue_address",
      label: "Dirección del venue",
      type: "textarea",
      path: "specific_details.venue_address",
      rows: 3,
      placeholder: "Av. Santa Cruz 858, Miraflores — Lima 15074, Perú",
      hint: "Dirección completa con barrio/colonia (más relevante que CP en Latam), ciudad y país. Útil para tomar Uber/Didi/Cabify desde el aeropuerto.",
    },
    {
      id: "map_link",
      label: "Link de Google Maps",
      type: "url",
      path: "specific_details.map_link",
      placeholder: "https://maps.app.goo.gl/...",
      hint: "Link corto de Google Maps al venue. Se incluye en el email de recordatorio. Ahorra que el atendee tipee la dirección.",
    },
    {
      id: "capacity",
      label: "Capacidad máxima",
      type: "number",
      path: "capacity",
      placeholder: "20",
      hint: "Cupos reales. Escasez honesta convierte mejor. Para retiros con alojamiento, la capacidad viene dada por la configuración de cuartos.",
    },

    // ─── Alojamiento + logística (retiros / destination) ──────────────────
    {
      id: "accommodation_type",
      label: "Alojamiento incluido",
      type: "enum",
      path: "specific_details.accommodation_type",
      options: [
        { value: AccommodationType.NOT_INCLUDED, label: "No incluido (el atendee gestiona su hotel)" },
        { value: AccommodationType.SHARED_ROOM, label: "Cuarto compartido (doble/triple)" },
        { value: AccommodationType.PRIVATE_ROOM, label: "Cuarto privado estándar" },
        { value: AccommodationType.LUXURY_SUITE, label: "Suite de lujo" },
      ],
      hint: "Decisivo en retiros. Incluir alojamiento sube el ticket pero elimina fricción (el atendee no reserva). Si no incluye, recomienda al menos 2-3 hoteles cercanos.",
    },
    {
      id: "meals_included",
      label: "Comidas incluidas",
      type: "enum",
      path: "specific_details.meals_included",
      options: [
        { value: "none", label: "Ninguna" },
        { value: "coffee_breaks", label: "Coffee breaks / snacks" },
        { value: "lunch_only", label: "Solo almuerzo" },
        { value: "full_pension", label: "Pensión completa (3 comidas)" },
        { value: "all_inclusive", label: "All inclusive (comidas + bebidas)" },
      ],
      hint: "En retiros Latam pensión completa es el estándar y justifica ticket alto. Si no incluye, ofrece lista de restaurantes cerca o app de delivery.",
    },
    {
      id: "dietary_restrictions_form_url",
      label: "Formulario de restricciones alimentarias",
      type: "url",
      path: "specific_details.dietary_restrictions_form_url",
      placeholder: "https://tally.so/r/...",
      hint: "Se envía post-checkout cuando el evento incluye comidas. Captura alergias, vegetarianos, veganos, halal, kosher. Tally/Typeform resuelven bien.",
    },
    {
      id: "recommended_airport_code",
      label: "Aeropuerto recomendado (IATA)",
      type: "text",
      path: "specific_details.recommended_airport_code",
      placeholder: "LIM / BOG / MEX / EZE / SCL",
      hint: "Solo destination retreats internacionales. Código IATA de 3 letras. Ej: LIM (Lima), BOG (Bogotá), MEX (CDMX), EZE (Buenos Aires Ezeiza), SCL (Santiago).",
    },
    {
      id: "is_transfer_included",
      label: "¿Transfer desde aeropuerto incluido?",
      type: "boolean",
      path: "specific_details.is_transfer_included",
      hint: "Transfer de ida y vuelta eleva valor percibido y evita líos de taxi/Uber. Si lo incluyes, coordinas horarios de arribo con los atendees.",
    },

    // ─── Agenda + preparación ─────────────────────────────────────────────
    {
      id: "agenda_highlights",
      label: "Agenda / hitos principales",
      type: "textarea",
      path: "specific_details.agenda_highlights",
      rows: 5,
      placeholder:
        "09:00 — Apertura y bienvenida\n09:30 — Keynote: Estado del mercado digital Latam 2026\n11:00 — Panel: Casos de éxito SaaS Latam\n13:00 — Almuerzo y networking\n15:00 — Workshop práctico",
      hint: "Uno por línea. El nivel de detalle depende del evento: un retiro de 5 días puedes listar actividades por día; un evento de 1 día lista hora + actividad. Se renderiza en landing y email de recordatorio.",
    },
    {
      id: "what_to_bring",
      label: "Qué traer",
      type: "textarea",
      path: "specific_details.what_to_bring",
      rows: 4,
      placeholder:
        "• Laptop con cargador\n• Cuaderno + bolígrafo para ejercicios offline\n• Ropa cómoda para actividades outdoor\n• Protector solar y repelente\n• DNI o pasaporte para el check-in del hotel",
      hint: "Uno por línea. Crítico en retiros presenciales — evita que el atendee llegue sin lo necesario. Incluye ropa (formal/casual/deportiva), documentación requerida y tecnología.",
    },
    {
      id: "dress_code",
      label: "Dress code",
      type: "text",
      path: "specific_details.dress_code",
      placeholder: "Smart casual / Business / Cómodo para actividades outdoor",
      hint: "Ayuda al atendee a preparar la valija. Retiros wellness: casual cómodo. Conferencias B2B: business casual o smart casual.",
    },
    {
      id: "language_spoken",
      label: "Idioma del evento",
      type: "enum",
      path: "specific_details.language_spoken",
      options: [
        { value: "es", label: "Español (Latam neutro)" },
        { value: "es_with_en_translation", label: "Español con traducción simultánea al inglés" },
        { value: "en", label: "Inglés" },
        { value: "en_with_es_translation", label: "Inglés con traducción simultánea al español" },
        { value: "pt", label: "Portugués (Brasil)" },
        { value: "bilingual", label: "Bilingüe (speakers en ambos idiomas)" },
      ],
      hint: "Claridad sobre idioma evita compradores frustrados. Si tu evento es en español pero tienes speakers internacionales, declaralo como 'Español con traducción' para atraer audiencia que no habla inglés.",
    },

    // ─── Accesibilidad + inclusión ────────────────────────────────────────
    {
      id: "is_family_friendly",
      label: "¿Admite acompañantes / familiares?",
      type: "boolean",
      path: "specific_details.is_family_friendly",
      hint: "Si es retiro o evento prolongado, algunos atendees quieren venir con pareja o hijos. Definir política (cupo extra con costo, sin niños, todo público) antes evita preguntas repetitivas.",
    },
    {
      id: "age_restrictions",
      label: "Restricciones de edad",
      type: "text",
      path: "specific_details.age_restrictions",
      placeholder: "Mayores de 18 / Recomendado 25+ / Todo público",
      hint: "Ideal ser explícito si la temática lo requiere (mastermind profesional vs retiro familiar).",
    },
    {
      id: "accessibility_notes",
      label: "Notas de accesibilidad",
      type: "textarea",
      path: "specific_details.accessibility_notes",
      rows: 3,
      placeholder:
        "• Venue con acceso para sillas de ruedas en todas las áreas principales\n• Baños adaptados en planta baja\n• No hay intérprete de lengua de señas (contáctanos si lo necesitas)\n• Materiales impresos disponibles en letra grande bajo pedido",
      hint: "Argentina (Ley 26.378) y Chile (Ley 20.422) exigen declarar accesibilidad. Además es buena práctica. Si hay limitaciones, declárelas — los atendees con necesidades especiales lo agradecen.",
    },

    // ─── Grabación + streaming ────────────────────────────────────────────
    {
      id: "is_recorded",
      label: "¿Se graba el evento?",
      type: "boolean",
      path: "specific_details.is_recorded",
      hint: "Si se activa, los asistentes reciben el recording post-evento (típico: 48-72h después). Reposición por 14-30 días aumenta valor percibido sin diluir urgencia.",
    },
    {
      id: "live_streamed_secondary_url",
      label: "URL de streaming en vivo (opcional, para evento híbrido)",
      type: "url",
      path: "specific_details.live_streamed_secondary_url",
      placeholder: "https://youtube.com/live/...",
      hint: "Solo si haces evento presencial con streaming pago para audiencia remota. Variant separado como 'Pase streaming' funciona mejor.",
    },

    // ─── Política de cancelación ──────────────────────────────────────────
    {
      id: "refund_deadline_days",
      label: "Plazo de reembolso total (días antes del evento)",
      type: "number",
      path: "specific_details.refund_deadline_days",
      placeholder: "30",
      hint: "Hasta cuántos días antes puede el atendee cancelar con reembolso 100%. 30 días es estándar en retiros (la logística ya está pagada). 7 días para eventos 1 día. Pasado el plazo: reembolso parcial o no-show.",
    },
  ],
};
