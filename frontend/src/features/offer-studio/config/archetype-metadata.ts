import { LucideIcon, Package, Map, Wrench, RefreshCw, Tent } from "lucide-react";
import { OfferArchetype } from "../types";

export interface ArchetypeMetadata {
  label: string;
  subtitle: string;
  icon: LucideIcon;
  examples: string;
  defaultFormats: string[];
  detailsModel: "product" | "program" | "service" | "subscription" | "event";
}

export const ARCHETYPE_METADATA: Record<OfferArchetype, ArchetypeMetadata> = {
  [OfferArchetype.PRODUCTO]: {
    label: "Producto",
    subtitle: "Algo que cree y empaquete",
    icon: Package,
    examples: "Ebook, curso grabado, template, guia, producto fisico",
    defaultFormats: ["Ebook / PDF", "Curso Grabado", "Template Pack", "Checklist", "Producto Fisico"],
    detailsModel: "product",
  },
  [OfferArchetype.PROGRAMA]: {
    label: "Programa",
    subtitle: "Un proceso con inicio, pasos y resultado",
    icon: Map,
    examples: "Mentoria grupal, plan personalizado, bootcamp, cohorte",
    defaultFormats: ["Mentoria Grupal", "Mentoria 1:1", "Cohorte", "Plan Personalizado", "Bootcamp"],
    detailsModel: "program",
  },
  [OfferArchetype.SERVICIO]: {
    label: "Servicio",
    subtitle: "Trabajo que hago para o con alguien",
    icon: Wrench,
    examples: "Consulta, auditoria, diseno web, VIP Day, retainer",
    defaultFormats: ["Consulta Puntual", "Paquete de Sesiones", "Servicio Productizado", "VIP Day", "Retainer Mensual", "Auditoria"],
    detailsModel: "service",
  },
  [OfferArchetype.MEMBRESIA]: {
    label: "Membresia",
    subtitle: "Acceso continuo por suscripcion",
    icon: RefreshCw,
    examples: "Comunidad premium, newsletter paga, mastermind, club",
    defaultFormats: ["Comunidad Premium", "Newsletter Paga", "Mastermind", "Membership Site"],
    detailsModel: "subscription",
  },
  [OfferArchetype.EXPERIENCIA]: {
    label: "Experiencia",
    subtitle: "Un momento o evento unico",
    icon: Tent,
    examples: "Webinar, retiro, taller, conferencia, capacitacion",
    defaultFormats: ["Webinar / Reto", "Taller", "Retiro Inmersivo", "Conferencia", "Capacitacion Corporativa"],
    detailsModel: "event",
  },
};
