import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Pricing — precio base offer-level + ventanas temporales edition-level
 * + métodos de pago aceptados (referenciados del módulo Connections).
 *
 * **Integración con módulo Connections (no duplica):** el catálogo de
 * providers de pago (Stripe, MercadoPago, Culqi, PayPal, manual) se define
 * en ``sales_agent/domain/enrollment.py::PaymentProvider`` y cada tenant
 * configura cuáles están habilitados en Conexiones. El campo
 * ``accepted_payment_providers`` de esta sección es un multi-select
 * **dinámico** (via ``use-available-payment-providers`` hook) que sólo
 * muestra los que el tenant tiene conectados.
 *
 * **Scope MIXED:** precios base + providers + cuotas son offer-level;
 * ventanas temporales (early-bird → regular → last-call) son edition-level.
 *
 * **Latam:**
 * - Cuotas sin interés 3/6/12 son decisivas en decisión de compra PE/MX/CO/AR.
 * - Moneda local + equivalente USD dual display es estándar.
 * - IVA/IGV/ICMS incluido/no-incluido debe ser explícito — evita disputas.
 * - Para 🩺 salud: obras sociales/EPS aceptadas (OSDE, IMSS, Sura, etc.)
 *   se modelan como JSONB ``insurance_coverage`` cuando aplica.
 */
export const offerPricingSchema: SectionSchema = {
  key: "offer.pricing",
  scope: "mixed",
  fields: [
    {
      id: "pricing_options",
      label: "Opciones de precio",
      type: "custom",
      path: "pricing_options",
      owner: "offer",
      action: "offer-pricing-options-builder",
      hint: "El menú que ve el cliente: pago único, suscripción, cuotas, planes. Cada opción tiene su monto, frecuencia y moneda. El agente de ventas presenta las opciones según el interés del lead.",
    },
    {
      id: "currency",
      label: "Moneda principal",
      type: "text",
      path: "currency",
      owner: "offer",
      placeholder: "PEN · MXN · COP · ARS · CLP · BRL · USD",
      hint: "ISO 4217 (3 letras). Usa la moneda en la que cobras habitualmente — el sistema calcula equivalentes USD para reportes cross-moneda. Si lo dejas vacío toma la moneda configurada en tu tenant.",
    },
    {
      id: "price_pay_in_full_usd",
      label: "Precio pago único (equivalente USD)",
      type: "number",
      path: "price_pay_in_full",
      owner: "offer",
      hint: "Sólo para reportes comparables entre monedas. El precio REAL que ve el cliente viene de ``pricing_options``. El sistema lo usa para benchmarks sector/geografía.",
    },
    {
      id: "tax_included",
      label: "¿El precio incluye IVA / IGV / ICMS?",
      type: "boolean",
      path: "tax_included",
      owner: "offer",
      hint: "CRÍTICO en Latam — evita disputas en checkout. Si dejas unclear, el cliente discute. Argentina IVA 21%, Perú IGV 18%, Chile IVA 19%, Colombia IVA 19%, México IVA 16%, Brasil ICMS variable.",
    },
    {
      id: "accepted_payment_providers",
      label: "Métodos de pago aceptados",
      type: "custom",
      path: "accepted_payment_providers",
      owner: "offer",
      action: "payment-provider-picker",
      hint: "Métodos de pago habilitados para esta oferta. Solo muestra los providers conectados en Configuración → Conexiones. Si no conectaste ninguno, hazlo primero.",
    },
    {
      id: "installments_available",
      label: "Cuotas sin interés disponibles",
      type: "text",
      path: "installments_available",
      owner: "offer",
      placeholder: "ej. 3, 6, 12",
      hint: "Números separados por coma. Las cuotas sin interés son DECISIVAS en Latam para tickets >USD 100. El agente de ventas las menciona en el argumento de cierre. Consulta con tu provider qué planes acepta.",
    },
    {
      id: "pricing_tiers",
      label: "Precio escalonado por ventana (esta edición)",
      type: "custom",
      path: "pricing_tiers",
      owner: "edition",
      action: "offer-pricing-tiers-builder",
      hint: "Early-bird → regular → last-call: cada tier es una ventana temporal con su precio. Al salir una ventana entra la siguiente automáticamente. Vacío = usa ``pricing_options`` base sin variación temporal.",
    },
  ],
};
