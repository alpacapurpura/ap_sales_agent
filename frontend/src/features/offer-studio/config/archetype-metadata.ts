import { LucideIcon, Package, Map, Wrench, RefreshCw, Tent } from "lucide-react";
import { OfferArchetype } from "../types";

export interface ArchetypeMetadata {
  label: string;
  subtitle: string;
  icon: LucideIcon;
  examples: string;
  detailsModel: "product" | "program" | "service" | "subscription" | "event";
}

export const ARCHETYPE_METADATA: Record<OfferArchetype, ArchetypeMetadata> = {
  [OfferArchetype.PRODUCTO]: {
    label: "Producto",
    subtitle: "Algo que cree y empaquete",
    icon: Package,
    examples: "Ebook, curso grabado, template, guia, producto fisico",
    detailsModel: "product",
  },
  [OfferArchetype.PROGRAMA]: {
    label: "Programa",
    subtitle: "Un proceso con inicio, pasos y resultado",
    icon: Map,
    examples: "Mentoria grupal, plan personalizado, bootcamp, cohorte",
    detailsModel: "program",
  },
  [OfferArchetype.SERVICIO]: {
    label: "Servicio",
    subtitle: "Trabajo que hago para o con alguien",
    icon: Wrench,
    examples: "Consulta, auditoria, diseno web, VIP Day, retainer",
    detailsModel: "service",
  },
  [OfferArchetype.MEMBRESIA]: {
    label: "Membresia",
    subtitle: "Acceso continuo por suscripcion",
    icon: RefreshCw,
    examples: "Comunidad premium, newsletter paga, mastermind, club",
    detailsModel: "subscription",
  },
  [OfferArchetype.EXPERIENCIA]: {
    label: "Experiencia",
    subtitle: "Un momento o evento unico",
    icon: Tent,
    examples: "Webinar, retiro, taller, conferencia, capacitacion",
    detailsModel: "event",
  },
};
