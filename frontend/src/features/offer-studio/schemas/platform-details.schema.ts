import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Platform Details — específico de ofertas SaaS / software. Cubre features,
 * integraciones, seguridad, residencia de datos, uptime, soporte y
 * transparencia de IA.
 *
 * Scope OFFER_LEVEL: la plataforma es la misma para todos los planes de
 * la misma oferta. Si tu SaaS tiene 3 planes (Starter/Pro/Enterprise)
 * cada uno es una oferta distinta con su propio platform_features donde
 * marcás las features por plan.
 *
 * **Latam — decisiones de diseño:**
 * - Los frameworks legales Latam relevantes son LGPD (BR), Habeas Data
 *   (CO/PE), LOPD/PDPL (AR/UY/CL). Copiar "GDPR compliant" de landings
 *   gringas no suma trust en Latam: los compradores B2B buscan su
 *   normativa nacional específica.
 * - Integraciones Latam core: Mercado Pago, WhatsApp Business API (con
 *   BSP autorizado), MODO, Culqi, Yape, Pix. Son diferenciadores reales
 *   vs SaaS con solo Stripe.
 * - ``ai_features_disclosure`` captura la creciente exigencia Latam
 *   (AR, BR, MX) sobre transparencia de uso de IA — qué datos se
 *   procesan, qué modelos, si hay decisiones automatizadas que afecten
 *   al usuario.
 * - ``data_export_capability`` cumple con el "derecho de portabilidad"
 *   que todos los frameworks Latam reconocen. Sin este campo el
 *   comprador B2B asume lock-in.
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
      hint: "Features que el usuario recibe. Para feature matrix por plan, marca en qué planes está disponible cada una.",
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
      rows: 5,
      placeholder:
        "• SOC 2 Type II (2025) — auditado por Prescient Assurance\n• ISO 27001 certificado\n• LGPD (Brasil) compliant — DPO designado\n• Habeas Data (Colombia, Perú) — registrado ante SIC y DPS\n• PDPL (Ley 25.326 Argentina) compliant\n• Encriptación AES-256 en reposo · TLS 1.3 en tránsito\n• Pen-test anual por terceros",
      hint: "Certificaciones + frameworks legales con detalle. Lista específicamente por país Latam (no solo 'LATAM compliant' vago). Un B2B mexicano busca LFPDPPP, uno colombiano busca Habeas Data. Sé explícito.",
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
      hint: "Si tienes SLA publicado, ponlo. Enlázalo desde la landing al status page.",
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
      hint: "Clientes técnicos valoran mucho tener API. Si es sólo en planes altos, aclárelo.",
    },
    {
      id: "api_docs_url",
      label: "URL de documentación de API",
      type: "url",
      path: "api_docs_url",
      placeholder: "https://docs.tuempresa.com/api / https://developers.tuempresa.com",
      hint: "Link público a los docs de API. ReadMe, Mintlify y GitBook son los hosts más comunes. Sin docs públicos claros, clientes técnicos asumen que la API es inmadura.",
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
      hint: "Si tienes roadmap público (Trello, Productboard, Canny), enlázalo. Transparencia = trust.",
    },
    {
      id: "changelog_url",
      label: "URL del changelog",
      type: "url",
      path: "changelog_url",
      hint: "Página pública de releases recientes. Muestra velocidad de producto.",
    },
    {
      id: "ai_features_disclosure",
      label: "Transparencia de uso de IA",
      type: "textarea",
      path: "ai_features_disclosure",
      rows: 4,
      placeholder:
        "• Generación de copy asistida por GPT-4o — los datos del cliente NO se usan para entrenar modelos\n• Análisis predictivo de churn con modelos propios (random forest)\n• Resumen automático de conversaciones de soporte (datos anonimizados)\n• NO tomamos decisiones automatizadas que afecten al cliente sin supervisión humana",
      hint: "Creciente exigencia regulatoria Latam (AR Res. 161/2023, BR autorregulación LGPD, MX INE normativa). Explicita: qué features usan IA, qué datos se procesan, si hay decisiones automatizadas. Sin esta transparencia, auditores B2B Latam marcan red flag.",
    },
    {
      id: "data_export_capability",
      label: "Capacidad de exportación de datos",
      type: "textarea",
      path: "data_export_capability",
      rows: 3,
      placeholder:
        "• Exportación completa en CSV/JSON desde el panel (self-service, any plan)\n• Backup mensual automático enviado al admin por email\n• API de extracción disponible en plan Business+\n• Deleción de cuenta + purge de datos en 30 días post-solicitud",
      hint: "Derecho de portabilidad (reconocido en GDPR, LGPD, Habeas Data, PDPL AR). Sin declarar cómo exportar y borrar, comprador B2B asume lock-in. Crítico para cerrar cuentas enterprise.",
    },
  ],
};
