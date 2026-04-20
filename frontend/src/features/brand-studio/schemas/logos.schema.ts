import type { SectionSchema } from "@/lib/form-runtime/schema";

export const logosSchema: SectionSchema = {
  key: "brand.logos",
  title: "Logos",
  description: "Variantes de logo para cada superficie.",
  fields: [
    {
      id: "logo_kit",
      label: "Kit completo de logos",
      type: "custom",
      path: "primary",
      action: "logo-kit",
      hint: "Sube y posiciona cada variante (primaria, oscuro, claro, favicon).",
    },
    { id: "primary", label: "Logo primario (URL)", type: "url", path: "primary" },
    { id: "secondary", label: "Icono (URL)", type: "url", path: "secondary" },
    { id: "dark_mode", label: "Para fondos oscuros (URL)", type: "url", path: "dark_mode" },
    { id: "light_mode", label: "Para fondos claros (URL)", type: "url", path: "light_mode" },
    { id: "favicon", label: "Favicon (URL)", type: "url", path: "favicon" },
  ],
};
