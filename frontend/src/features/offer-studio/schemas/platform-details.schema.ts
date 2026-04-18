import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Platform Details — específico de ofertas SaaS / software: features,
 * integraciones, seguridad, uptime, soporte, residencia de datos.
 *
 * Latam: destacar LGPD (Brasil) y Habeas Data (Colombia, Perú, Argentina)
 * suma trust B2B en mercados con normativa de datos madurando. Mercado
 * Pago + WhatsApp Business API son las integraciones más demandadas en
 * la región para SaaS PYME.
 */
export const offerPlatformDetailsSchema: SectionSchema = {
  key: "offer.platform_details",
  scope: "offer_level",
  fields: [
    {
      id: "core_features",
      label: "Funcionalidades core",
      type: "array",
      path: "platform_features",
      hint: "Features que el usuario recibe. Para feature matrix por plan, marcá en qué planes está disponible cada una.",
      itemSchema: {
        description: "Una funcionalidad del software con su disponibilidad por plan.",
        fields: [
          {
            id: "name",
            label: "Nombre de la feature",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Automatización de emails · Dashboards en vivo · API de integración",
          },
          {
            id: "description",
            label: "Qué hace",
            type: "textarea",
            path: "description",
            rows: 2,
            placeholder: "Envía secuencias de 3-7 emails automáticos cuando un lead completa el formulario.",
          },
          {
            id: "plans_available",
            label: "Planes que la incluyen",
            type: "text",
            path: "plans_available",
            placeholder: "Starter, Pro, Business, Enterprise",
            hint: "Lista separada por coma. Para feature matrix.",
          },
          {
            id: "is_highlighted",
            label: "¿Destacar?",
            type: "boolean",
            path: "is_highlighted",
            hint: "Features diferenciadoras que van en el hero de la landing.",
          },
        ],
      },
    },
    {
      id: "integrations",
      label: "Integraciones disponibles",
      type: "array",
      path: "platform_integrations",
      hint: "Plataformas con las que se conecta. En Latam destacar Mercado Pago, WhatsApp Business, Manychat.",
      itemSchema: {
        description: "Una integración con una plataforma externa.",
        fields: [
          {
            id: "name",
            label: "Nombre",
            type: "text",
            path: "name",
            required: true,
            placeholder: "Mercado Pago · WhatsApp Business API · Stripe · Zapier",
          },
          {
            id: "category",
            label: "Categoría",
            type: "enum",
            path: "category",
            options: [
              { value: "payments", label: "Pagos" },
              { value: "messaging", label: "Mensajería / chatbots" },
              { value: "email", label: "Email marketing" },
              { value: "crm", label: "CRM" },
              { value: "analytics", label: "Analytics" },
              { value: "storage", label: "Almacenamiento" },
              { value: "automation", label: "Automatización" },
              { value: "scheduling", label: "Agenda / reservas" },
              { value: "social", label: "Redes sociales" },
              { value: "other", label: "Otro" },
            ],
          },
          {
            id: "logo_url",
            label: "URL del logo",
            type: "url",
            path: "logo_url",
          },
          {
            id: "setup_guide_url",
            label: "Link a la guía de configuración",
            type: "url",
            path: "setup_guide_url",
          },
        ],
      },
    },
    {
      id: "security_compliance",
      label: "Seguridad y compliance",
      type: "textarea",
      path: "security_compliance",
      rows: 4,
      placeholder: "SOC 2 Type II (2025)\nISO 27001 certificado\nLGPD (Brasil) compliant\nHabeas Data (Colombia, Perú)\nEncriptación AES-256 en reposo y TLS 1.3 en tránsito",
      hint: "Certificaciones + frameworks. LGPD/Habeas Data suman trust B2B Latam. Una por línea.",
    },
    {
      id: "data_residency",
      label: "Residencia de datos",
      type: "text",
      path: "data_residency",
      placeholder: "Región AWS São Paulo (sa-east-1) · Los datos viven en Brasil",
      hint: "Crítico para clientes que requieren datos en su país/región. Sé específico.",
    },
    {
      id: "uptime_guarantee",
      label: "Garantía de uptime (%)",
      type: "text",
      path: "uptime_guarantee",
      placeholder: "99.9% mensual — penalty por incumplimiento escalonado",
      hint: "Si tenés SLA publicado, ponelo. Linkealo desde la landing al status page.",
    },
    {
      id: "status_page_url",
      label: "URL del status page",
      type: "url",
      path: "status_page_url",
      hint: "Página pública de estado (status.tuempresa.com). Transparencia = trust.",
    },
    {
      id: "support_channels",
      label: "Canales de soporte y horarios",
      type: "textarea",
      path: "support_channels",
      rows: 4,
      placeholder: "Chat in-app: Lun-Vie 9-19 COT · Respuesta <4h\nEmail 24/7 · Respuesta <24h\nWhatsApp Business (plan Pro+): Lun-Vie 9-19\nSlack Connect (Enterprise)",
      hint: "Canales, horarios, SLA de respuesta. WhatsApp Business es diferenciador Latam PYME.",
    },
    {
      id: "api_available",
      label: "¿API pública disponible?",
      type: "boolean",
      path: "api_available",
      hint: "Clientes técnicos valoran mucho tener API. Si es sólo en planes altos, aclaralo.",
    },
    {
      id: "api_docs_url",
      label: "URL de documentación de API",
      type: "url",
      path: "api_docs_url",
    },
    {
      id: "migration_tools",
      label: "Herramientas de migración",
      type: "textarea",
      path: "migration_tools",
      rows: 3,
      placeholder: "Importer desde Mailchimp, ActiveCampaign, Hubspot — 1-click.\nServicio de migración asistida en plan Business+.",
      hint: "Cómo migra un cliente que viene de competidor. Reduce fricción de switch.",
    },
    {
      id: "public_roadmap_url",
      label: "URL del roadmap público",
      type: "url",
      path: "public_roadmap_url",
      hint: "Si tenés roadmap público (Trello, Productboard, Canny), linkealo. Transparencia = trust.",
    },
    {
      id: "changelog_url",
      label: "URL del changelog",
      type: "url",
      path: "changelog_url",
      hint: "Página pública de releases recientes. Muestra velocidad de producto.",
    },
  ],
};
