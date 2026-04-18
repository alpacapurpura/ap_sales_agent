import type { SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Pricing — offer-level baseline + per-edition time-window overrides.
 *
 * Mixed scope because the baseline ``pricing_options[]`` lives on the
 * ``Offer`` row while ``pricing_tiers[]`` (early-bird → regular → last-call
 * timelines) lives on each ``LaunchEdition``. Rendered under
 * ``/edition/evergreen/`` the schema hides edition-owned fields; under
 * ``/edition/<N>/`` it renders both so the user sees the baseline and
 * the launch override side by side.
 *
 * The ``offer-pricing-tiers-builder`` custom action renders a temporal
 * editor (valid_from / valid_until windows) instead of a generic array
 * input — windowed pricing has domain-specific UX (overlap detection,
 * half-open interval semantics) that the generic runtime cannot provide.
 */
export const offerPricingSchema: SectionSchema = {
  key: "offer.pricing",
  // title + description resolved from the backend SectionCatalog.
  scope: "mixed",
  fields: [
    {
      id: "pricing_options",
      label: "Opciones de precio base",
      type: "custom",
      path: "pricing_options",
      owner: "offer",
      action: "offer-pricing-options-builder",
      hint: "El menú de precios que ve el cliente cuando compra (pago único, cuotas, suscripción).",
    },
    {
      id: "currency",
      label: "Moneda",
      type: "text",
      path: "currency",
      owner: "offer",
      placeholder: "USD",
      hint: "ISO 4217. Si lo dejas vacío se usa la moneda del tenant.",
    },
    {
      id: "price_pay_in_full",
      label: "Precio pago único (USD equivalente)",
      type: "number",
      path: "price_pay_in_full",
      owner: "offer",
      hint: "Solo para reportes cross-moneda. El precio real al cliente viene de pricing_options.",
    },
    {
      id: "pricing_tiers",
      label: "Overrides por ventana de tiempo (esta edición)",
      type: "custom",
      path: "pricing_tiers",
      owner: "edition",
      action: "offer-pricing-tiers-builder",
      hint:
        "Early-bird → regular → last-call: cada tier define una ventana temporal y el precio " +
        "vigente durante ella. Vacío = usa pricing_options base.",
    },
  ],
};
