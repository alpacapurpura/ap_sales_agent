import { AccessDuration, DigitalFormat, FulfillmentType } from "../types";

import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * PRODUCTO archetype details — digital file or physical product.
 *
 * Persists to ``Offer.specific_details`` (typed as ``ProductDetailsSchema``
 * in ``types/schema.ts``). Offer-level because the product itself is the
 * offer — per-edition overrides do not apply to this archetype.
 */
export const offerProductDetailsSchema: SectionSchema = {
  key: "offer.product_details",
  title: "Detalles del producto",
  description: "Formato, entrega y características del producto digital o físico.",
  scope: "offer_level",
  fields: [
    {
      id: "fulfillment_type",
      label: "Modo de entrega",
      type: "enum",
      path: "specific_details.fulfillment_type",
      options: [
        { value: FulfillmentType.DIGITAL_DOWNLOAD, label: "Descarga digital" },
        { value: FulfillmentType.LMS_ACCESS, label: "Acceso a plataforma / LMS" },
        { value: FulfillmentType.MANUAL_PROVISIONING, label: "Provisión manual" },
        { value: FulfillmentType.PHYSICAL_SHIPPING, label: "Envío físico" },
      ],
    },
    {
      id: "format",
      label: "Formato del producto",
      type: "enum",
      path: "specific_details.format",
      options: [
        { value: DigitalFormat.PDF_EBOOK, label: "PDF / Ebook" },
        { value: DigitalFormat.VIDEO_COURSE, label: "Curso en video" },
        { value: DigitalFormat.AUDIO_SERIES, label: "Serie de audio" },
        { value: DigitalFormat.NOTION_TEMPLATE, label: "Template Notion" },
        { value: DigitalFormat.SOFTWARE_SAAS, label: "Software / SaaS" },
        { value: DigitalFormat.PHYSICAL_ITEM, label: "Producto físico" },
      ],
    },
    {
      id: "access_url",
      label: "URL de acceso",
      type: "url",
      path: "specific_details.access_url",
      placeholder: "https://...",
      hint: "Dónde accede el cliente después de comprar (drive, plataforma, link de descarga).",
    },
    {
      id: "access_instructions",
      label: "Instrucciones de acceso",
      type: "textarea",
      path: "specific_details.access_instructions",
      rows: 3,
      hint: "Qué hace el cliente inmediatamente después de pagar.",
    },
    {
      id: "access_duration",
      label: "Duración del acceso",
      type: "enum",
      path: "access_duration",
      options: [
        { value: AccessDuration.LIFETIME, label: "Acceso de por vida" },
        { value: AccessDuration.LIMITED_TIME, label: "Tiempo limitado" },
        { value: AccessDuration.SUBSCRIPTION_ACTIVE, label: "Mientras mantenga suscripción" },
      ],
    },
    {
      id: "estimated_consumption_time_minutes",
      label: "Tiempo estimado de consumo (min)",
      type: "number",
      path: "specific_details.estimated_consumption_time_minutes",
    },
    {
      id: "requires_shipping",
      label: "Requiere envío físico",
      type: "boolean",
      path: "specific_details.requires_shipping",
    },
    {
      id: "stock_quantity",
      label: "Stock disponible",
      type: "number",
      path: "specific_details.stock_quantity",
      hint: "Para productos físicos con inventario. Dejar vacío si es digital ilimitado.",
    },
  ],
};
