import type { SectionSchema } from "@/lib/form-runtime/schema";

export const contactSchema: SectionSchema = {
  key: "brand.contact",
  title: "Contacto",
  description: "Canales oficiales y redes sociales.",
  fields: [
    { id: "support_email", label: "Email de soporte", type: "email", path: "support_email" },
    { id: "sales_email", label: "Email de ventas", type: "email", path: "sales_email" },
    { id: "phone", label: "Teléfono", type: "text", path: "phone" },
    { id: "whatsapp", label: "WhatsApp", type: "text", path: "whatsapp" },
    { id: "address", label: "Dirección", type: "textarea", path: "address", rows: 2 },
    { id: "social_instagram", label: "Instagram", type: "text", path: "social_instagram" },
    { id: "social_linkedin", label: "LinkedIn", type: "url", path: "social_linkedin" },
    { id: "social_youtube", label: "YouTube", type: "url", path: "social_youtube" },
    { id: "social_tiktok", label: "TikTok", type: "text", path: "social_tiktok" },
    { id: "social_facebook", label: "Facebook", type: "text", path: "social_facebook" },
    { id: "social_twitter", label: "Twitter / X", type: "text", path: "social_twitter" },
    { id: "testimonials_url", label: "URL de testimonios", type: "url", path: "testimonials_url" },
  ],
};
