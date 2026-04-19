import { AccessDuration, DigitalFormat, FulfillmentType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * PRODUCTO archetype details — entrega digital o producto físico.
 *
 * Scope OFFER_LEVEL: el producto es la oferta. No hay variaciones
 * por edition/cohorte — si necesitás SKUs variantes (tallas, colores),
 * usá ``VariantStructure.SKU_VARIANT`` a nivel oferta.
 *
 * **Latam — decisiones de diseño:**
 * - ``shipping_carriers_accepted`` enumera los carriers Latam realmente
 *   usados. Evita el error común de copiar una lista gringa (UPS, FedEx)
 *   que no aplica en la realidad regional — Mercado Envíos integra
 *   50%+ de las entregas Latam.
 * - ``shipping_estimate_by_region`` es JSONB con tiempos por zona
 *   (Capital / Interior / Internacional). Expectativa realista reduce
 *   reclamos y malas reseñas.
 * - ``return_policy_days`` cumple con Ley del Consumidor (7 días AR/PE,
 *   30 días MX para compras a distancia, 10 días CO). Declarar más que
 *   el mínimo legal es argumento de venta.
 * - ``sample_preview_url`` para digitales es decisivo: un ebook o curso
 *   sin sample vende 30-50% menos que uno que te muestra las primeras
 *   páginas o una lección gratuita.
 * - ``packaging_description`` para físicos: en cosmética y regalo, el
 *   unboxing es el 30% de la experiencia. Documentarlo es branding.
 */
export const offerProductDetailsSchema: SectionSchema = {
  key: "offer.product_details",
  // title + description resolved from the backend SectionCatalog.
  scope: "offer_level",
  fields: [
    // ─── Modalidad de entrega ─────────────────────────────────────────────
    {
      id: "fulfillment_type",
      label: "¿Cómo se entrega?",
      type: "enum",
      path: "specific_details.fulfillment_type",
      options: [
        { value: FulfillmentType.DIGITAL_DOWNLOAD, label: "Descarga digital (PDF, zip, video)" },
        { value: FulfillmentType.LMS_ACCESS, label: "Acceso a plataforma (Hotmart, Kajabi, propia)" },
        { value: FulfillmentType.MANUAL_PROVISIONING, label: "Provisión manual (vos enviás credenciales)" },
        { value: FulfillmentType.PHYSICAL_SHIPPING, label: "Envío físico a domicilio" },
      ],
      hint: "Define toda la experiencia post-checkout. Descarga digital = instantáneo. LMS = login recurrente, retención más alta. Manual = personal pero no escala. Físico = logística real.",
    },
    {
      id: "format",
      label: "Formato del producto",
      type: "enum",
      path: "specific_details.format",
      options: [
        { value: DigitalFormat.PDF_EBOOK, label: "PDF / Ebook" },
        { value: DigitalFormat.VIDEO_COURSE, label: "Curso en video" },
        { value: DigitalFormat.AUDIO_SERIES, label: "Serie de audio / podcast curso" },
        { value: DigitalFormat.NOTION_TEMPLATE, label: "Template (Notion, Framer, Figma)" },
        { value: DigitalFormat.SOFTWARE_SAAS, label: "Software / acceso SaaS" },
        { value: DigitalFormat.PHYSICAL_ITEM, label: "Producto físico" },
      ],
      hint: "El formato afecta el packaging marketing: un 'ebook' se percibe de menor valor que una 'guía completa' con el mismo contenido. Revisá el naming.",
    },
    {
      id: "is_downloadable",
      label: "¿El contenido es descargable?",
      type: "boolean",
      path: "specific_details.is_downloadable",
      hint: "Descargable = el cliente tiene el archivo para siempre. Streaming = protege piratería pero frustra si pierde internet. Híbrido (streaming + descarga para offline) es el balance óptimo en Latam por conectividad variable.",
    },
    {
      id: "estimated_consumption_time_minutes",
      label: "Tiempo estimado de consumo (minutos)",
      type: "number",
      path: "specific_details.estimated_consumption_time_minutes",
      placeholder: "240",
      hint: "Útil para estimar esfuerzo del cliente. Ebook de 80 páginas ≈ 120min. Curso de video ≈ suma de duraciones + 30% para ejercicios. El cliente lo mira antes de comprar para evaluar si le rinde.",
    },

    // ─── Acceso digital (si aplica) ───────────────────────────────────────
    {
      id: "access_url",
      label: "URL de acceso post-compra",
      type: "url",
      path: "specific_details.access_url",
      placeholder: "https://tu-academia.hotmart.com/curso / https://drive.google.com/...",
      hint: "Dónde accede el cliente después de pagar. Hotmart/Eduzz/Kiwify/Teachable generan URLs. Google Drive funciona pero menos profesional. Se envía automático post-checkout.",
    },
    {
      id: "access_instructions",
      label: "Instrucciones de acceso",
      type: "textarea",
      path: "specific_details.access_instructions",
      rows: 4,
      placeholder:
        "1. Recibirás un email de Kiwify con tu link de acceso en los próximos 5 minutos.\n2. Usá el mismo email con el que compraste para iniciar sesión.\n3. Si no llega en 15 minutos, revisá spam o escribinos a soporte@tudominio.com.\n4. La plataforma funciona en desktop y app móvil iOS/Android.",
      hint: "Reduce tickets de soporte 'no puedo acceder'. Paso-a-paso. Incluí qué revisar si no llega el email y link al soporte. Se usa en el email de bienvenida.",
    },
    {
      id: "access_duration",
      label: "Duración del acceso",
      type: "enum",
      path: "access_duration",
      options: [
        { value: AccessDuration.LIFETIME, label: "Acceso de por vida (value prop fuerte)" },
        { value: AccessDuration.LIMITED_TIME, label: "Tiempo limitado (1 año, 6 meses)" },
        { value: AccessDuration.SUBSCRIPTION_ACTIVE, label: "Mientras mantenga suscripción" },
      ],
      hint: "'De por vida' sube conversión pero te ata — si el curso se desactualiza, heredás todos los compradores. Limitado + actualizaciones por $ extra es más sostenible.",
    },
    {
      id: "sample_preview_url",
      label: "URL de preview / sample gratuito",
      type: "url",
      path: "specific_details.sample_preview_url",
      placeholder: "https://drive.google.com/.../sample.pdf / https://youtu.be/... (primera lección)",
      hint: "Ebook: primeras 10-20 páginas en PDF. Curso: la primera lección abierta. Template: screenshot o preview interactivo. Producto físico: video unboxing. Productos con sample convierten 30-50% más.",
    },

    // ─── Producto físico (si aplica) ──────────────────────────────────────
    {
      id: "requires_shipping",
      label: "¿Requiere envío físico?",
      type: "boolean",
      path: "specific_details.requires_shipping",
      hint: "Activá si es producto físico. Desactivado = digital puro. Desbloquea los campos de envío abajo.",
    },
    {
      id: "sku_inventory_code",
      label: "Código SKU (interno)",
      type: "text",
      path: "specific_details.sku_inventory_code",
      placeholder: "CREM-HID-50ML-V2",
      hint: "Para tracking interno de inventario. Convención típica: CATEGORIA-VARIANTE-TAMAÑO-VERSION. Se usa en reportes y logística, no se muestra al cliente.",
    },
    {
      id: "stock_quantity",
      label: "Stock disponible",
      type: "number",
      path: "specific_details.stock_quantity",
      placeholder: "50",
      hint: "Unidades en inventario. Se decrementa automáticamente con cada venta. Vacío = digital ilimitado o inventario manual. Escasez real convierte mejor que urgencia fake.",
    },
    {
      id: "shipping_weight_grams",
      label: "Peso para envío (gramos)",
      type: "number",
      path: "specific_details.shipping_weight_grams",
      placeholder: "350",
      hint: "Necesario para calcular costo de envío en carriers que cobran por peso. En cosmética considerá el peso del packaging. Mercado Envíos usa esto para su cotización automática.",
    },
    {
      id: "shipping_carriers_accepted",
      label: "Carriers de envío soportados",
      type: "textarea",
      path: "specific_details.shipping_carriers_accepted",
      rows: 3,
      placeholder:
        "• Mercado Envíos (por defecto, cobertura nacional)\n• Andreani (para envíos urgentes en AR)\n• OCA (alternativa económica)",
      hint: "Uno por línea. Carriers Latam más usados: Mercado Envíos (cross-Latam vía MercadoLibre), OCA/Andreani (AR), Estafeta/FedEx MX (MX), Servientrega/Envía (CO), Chilexpress (CL), Correios (BR), Serpost (PE).",
    },
    {
      id: "shipping_estimate_by_region",
      label: "Tiempo de entrega estimado por región",
      type: "textarea",
      path: "specific_details.shipping_estimate_by_region",
      rows: 4,
      placeholder:
        "• Capital / CABA: 2-3 días hábiles\n• Interior del país: 5-7 días hábiles\n• Países limítrofes (UY, PY, CL): 10-15 días hábiles\n• Resto de Latam: 15-21 días hábiles",
      hint: "Expectativa realista reduce 60% de tickets '¿cuándo me llega?'. Separá Capital / Interior / Internacional. Agregá un buffer de 1-2 días sobre el tiempo del carrier.",
    },
    {
      id: "packaging_description",
      label: "Experiencia de packaging / unboxing",
      type: "textarea",
      path: "specific_details.packaging_description",
      rows: 3,
      placeholder:
        "Tu pedido llega en una caja kraft reciclada con sello de cera, papel seda interior y una tarjeta escrita a mano. Envolvemos cada producto individualmente para regalo sin costo extra.",
      hint: "En cosmética, regalo o artesanía el unboxing es parte del producto y justifica el ticket. Compartible en Instagram = publicidad gratuita. Si no aplica (suplemento, consumo masivo), dejá vacío.",
    },
    {
      id: "return_policy_days",
      label: "Política de devolución (días)",
      type: "number",
      path: "specific_details.return_policy_days",
      placeholder: "14",
      hint: "Cuántos días tiene el cliente para devolver. Mínimo legal: 7 días (AR/PE), 10 días (CO), 30 días (MX para compras a distancia). Declarar más que el mínimo es diferencial de venta. Productos digitales: 7-14 días estándar.",
    },
  ],
};
