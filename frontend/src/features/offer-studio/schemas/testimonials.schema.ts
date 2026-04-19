import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Testimonials — reseñas de clientes reales en texto, video, audio o
 * antes/después. El generador de landings los muestra en carrusel y el
 * agente de ventas los cita en objeciones ("otro cliente tuyo tenía la
 * misma duda y así la resolvió").
 *
 * Latam: mezclar país de origen (PE/MX/CO/AR/CL/BR) da credibilidad
 * regional y evita que se perciba como "todos de USA". Para ofertas de
 * transformación (fitness, salud estética, coaching), los pares
 * antes/después convierten ~3x más que texto solo.
 */
export const offerTestimonialsSchema: SectionSchema = {
  key: "offer.testimonials",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    {
      id: "testimonials",
      label: "Testimonios",
      type: "array",
      path: "testimonials",
      hint: "Cada testimonio: tipo, contenido, autor, resultado, país, foto. Apuntá a 6-12 con diversidad de perfil y geografía.",
      itemSchema: {
        description: "Un testimonio individual — texto, video, audio o antes/después.",
        fields: [
          {
            id: "type",
            label: "Tipo",
            type: "enum",
            path: "type",
            options: [
              { value: "text", label: "Texto" },
              { value: "video", label: "Video" },
              { value: "audio", label: "Audio" },
              { value: "before_after", label: "Antes / después" },
              { value: "screenshot", label: "Captura de pantalla" },
            ],
            required: true,
          },
          {
            id: "content",
            label: "Contenido del testimonio",
            type: "textarea",
            path: "content",
            rows: 4,
            required: true,
            placeholder: "En 3 meses pasé de cero clientes a 14 reservas activas...",
            hint: "Usá las palabras exactas del cliente. Testimonios editados/limpiados se sienten falsos.",
          },
          {
            id: "video_url",
            label: "URL de video (si aplica)",
            type: "url",
            path: "video_url",
            hint: "YouTube, Vimeo o link directo. Video testimonial pesa más que texto largo.",
          },
          {
            id: "author_name",
            label: "Nombre",
            type: "text",
            path: "author_name",
            required: true,
            placeholder: "María Paula Ríos",
          },
          {
            id: "author_role",
            label: "Profesión o cargo",
            type: "text",
            path: "author_role",
            placeholder: "Odontóloga con consultorio propio",
            hint: "Credencial corta del cliente. Da contexto de quién habla.",
          },
          {
            id: "author_country",
            label: "País",
            type: "enum",
            path: "author_country",
            options: [
              { value: "PE", label: "Perú" },
              { value: "MX", label: "México" },
              { value: "CO", label: "Colombia" },
              { value: "AR", label: "Argentina" },
              { value: "CL", label: "Chile" },
              { value: "BR", label: "Brasil" },
              { value: "UY", label: "Uruguay" },
              { value: "EC", label: "Ecuador" },
              { value: "BO", label: "Bolivia" },
              { value: "PY", label: "Paraguay" },
              { value: "DO", label: "Rep. Dominicana" },
              { value: "CR", label: "Costa Rica" },
              { value: "PA", label: "Panamá" },
              { value: "GT", label: "Guatemala" },
              { value: "VE", label: "Venezuela" },
              { value: "ES", label: "España" },
              { value: "US", label: "Estados Unidos" },
              { value: "OT", label: "Otro" },
            ],
            hint: "Mostrar bandera da credibilidad regional.",
          },
          {
            id: "author_photo_url",
            label: "Foto del autor",
            type: "url",
            path: "author_photo_url",
            hint: "Foto real, rostro visible. Evitá iconos genéricos.",
          },
          {
            id: "rating",
            label: "Calificación (1-5)",
            type: "number",
            path: "rating",
            hint: "Opcional. Si mostrás rating agregado, todos los testimonios deberían tenerlo.",
          },
          {
            id: "result_achieved",
            label: "Resultado concreto logrado",
            type: "text",
            path: "result_achieved",
            placeholder: "Cerró 14 pacientes nuevos en 90 días",
            hint: "Números duros. Es lo que diferencia un testimonio vago de uno que vende.",
          },
          {
            id: "is_featured",
            label: "¿Destacar en landing?",
            type: "boolean",
            path: "is_featured",
            hint: "Los destacados aparecen arriba del fold. 2-3 máximo.",
          },
          {
            id: "permission_to_publish",
            label: "¿Tenés permiso documentado para publicarlo?",
            type: "boolean",
            path: "permission_to_publish",
            hint: "Legal Latam — LGPD Brasil, Habeas Data Colombia, LOPD Perú exigen consentimiento informado para publicar datos personales (foto + nombre + testimonio). WhatsApp o email con el OK del cliente basta; guardá el comprobante.",
          },
          {
            id: "consent_date",
            label: "Fecha de consentimiento",
            type: "text",
            path: "consent_date",
            placeholder: "2026-03-15",
            hint: "Opcional pero recomendado. ISO 8601 (YYYY-MM-DD). Rastro legal en caso de disputa. Si el cliente retira consentimiento, remové el testimonio dentro de 30 días.",
          },
        ],
      },
    },
    {
      id: "aggregate_rating",
      label: "Calificación promedio pública",
      type: "number",
      path: "aggregate_rating",
      hint: "Opcional. Si querés mostrar '4.8 ⭐ sobre 120 reseñas' en la landing.",
    },
    {
      id: "total_reviews_count",
      label: "Total de reseñas acumuladas",
      type: "number",
      path: "total_reviews_count",
      hint: "Número total de reseñas recibidas (incluyendo las que no están acá). Da peso al rating.",
    },
    {
      id: "external_reviews_url",
      label: "URL a reseñas externas",
      type: "url",
      path: "external_reviews_url",
      hint: "Link a Google My Business, Trustpilot, Facebook, etc. Verificable = trust real.",
    },
  ],
};
