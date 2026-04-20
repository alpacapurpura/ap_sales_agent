import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Instructors — las personas que respaldan la oferta con su autoridad.
 *
 * Arquitectónicamente: reutilizamos el equipo de ``brand-studio`` como
 * fuente canónica. Esta sección guarda solamente IDs de ``KeyFigure``,
 * no duplica biografía ni credenciales. Si la persona cambia su bio en
 * Brand Studio, la oferta refleja el cambio automáticamente.
 *
 * Scope OFFER_LEVEL: el lineup de instructores no cambia por cohorte.
 * Para eventos con speakers rotativos por edición, usa el campo
 * ``agenda_highlights`` de EventDetails con los nombres del día.
 *
 * **Latam — decisiones de diseño:**
 * - ``authority_positioning_for_sales`` es el field que el sales-agent
 *   lee cuando el lead pregunta "¿quién dicta?". Sin este campo el agent
 *   lista nombres planos; con él cuenta la historia ("Tu instructora es
 *   María Paula Ríos, odontóloga con 15 años atendiendo en Lima y 3 años
 *   formando colegas por su método X").
 * - ``authority_notes`` reserva credenciales específicas de esta oferta
 *   sin tocar el perfil maestro — útil cuando una oferta tiene un
 *   speaker invitado con credencial relevante solo para ese tema.
 */
export const offerInstructorsSchema: SectionSchema = {
  key: "offer.instructors",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "instructors",
      label: "Instructores de esta oferta",
      type: "custom",
      path: "instructors",
      action: "offer-instructors-picker",
      hint: "Selecciona miembros de tu equipo de marca. La biografía, foto y credenciales vienen del perfil en Brand Studio > Equipo — si cambian allá, se actualiza acá automáticamente. Para agregar a alguien nuevo, primero crea su ficha en Brand Studio.",
    },
    {
      id: "authority_positioning_for_sales",
      label: "Posicionamiento de autoridad (cómo lo presenta el sales-agent)",
      type: "textarea",
      path: "authority_positioning_for_sales",
      rows: 4,
      placeholder:
        "Tu instructora es María Paula Ríos — odontóloga con 15 años de práctica privada en Lima y 3 años formando colegas a través de su método 'Consulta Sin Huecos'. Ha ayudado a más de 200 profesionales de la salud a llenar su agenda sin invertir en publicidad.",
      hint: "Cómo el agente de ventas presenta al instructor cuando el lead pregunta '¿quién dicta?'. Narrativa + credenciales + proof de resultados. Sin este campo el agent lista nombres sin contexto.",
    },
    {
      id: "authority_notes",
      label: "Credenciales específicas para esta oferta",
      type: "textarea",
      path: "authority_notes",
      rows: 4,
      placeholder:
        "Para esta cohorte además contamos con:\n• Dr. Fabián Torres (invitado) — cirujano maxilofacial, 2 publicaciones en revistas ISI\n• Ale Vargas (coach grupal) — ex-directora de comunicación en grupo odontológico de 40 consultorios",
      hint: "Credenciales adicionales que aplican solo a esta oferta (speakers invitados, coaches extras, certificaciones específicas). No tocan el perfil maestro del instructor en Brand Studio. El agent las cita cuando son relevantes a la conversación.",
    },
  ],
};
