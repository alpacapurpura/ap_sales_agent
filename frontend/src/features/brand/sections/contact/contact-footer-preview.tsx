import {
  Edit2,
  Mail,
  Phone,
  MapPin,
  Instagram,
  Linkedin,
  Youtube,
  MessageCircle,
  Scale,
  Facebook,
  Twitter,
  Video,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { getContrastColor } from "@/lib/utils/colors";

import type { ContactData, BrandVisuals, BrandIdentity } from "@/features/brand/types";

interface ContactFooterSectionProps {
  contact: ContactData;
  identity: BrandIdentity;
  visuals: BrandVisuals;
  onEditContact: () => void;
  onEditLegal: () => void;
}

export function FooterSection({
  contact,
  identity,
  visuals,
  onEditContact,
  onEditLegal,
}: ContactFooterSectionProps) {
  // Logic for visual consistency
  const bgColor = visuals?.primary_color || "#0f172a";
  const textColor = getContrastColor(bgColor);

  return (
    <footer
      className="relative rounded-xl p-8 md:p-12 overflow-hidden transition-all shadow-lg"
      style={{
        backgroundColor: bgColor,
        color: textColor,
      }}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative z-10">
        {/* Column 1: Contact */}
        <div className="space-y-4 relative group">
          <div className="flex justify-between items-center border-b border-white/20 pb-2 mb-4">
            <h4 className="font-bold text-lg">Contacto</h4>
            <Button
              size="icon"
              variant="ghost"
              onClick={onEditContact}
              className="h-6 w-6 text-white/50 hover:text-white hover:bg-white/10"
              title="Editar Contacto"
            >
              <Edit2 className="h-3 w-3" />
            </Button>
          </div>

          <ul className="space-y-3 text-sm opacity-90">
            {contact.sales_email && (
              <li className="flex items-center gap-3">
                <span className="font-semibold text-xs bg-white/20 px-1.5 rounded">Ventas</span>
                {contact.sales_email}
              </li>
            )}
            {contact.support_email ? (
              <li className="flex items-center gap-3">
                <Mail className="w-4 h-4 opacity-70" /> {contact.support_email}
              </li>
            ) : (
              <li className="italic opacity-50">Email no definido</li>
            )}

            {contact.whatsapp && (
              <li className="flex items-center gap-3">
                <MessageCircle className="w-4 h-4 opacity-70" /> {contact.whatsapp}
              </li>
            )}
            {contact.address && (
              <li className="flex items-center gap-3">
                <MapPin className="w-4 h-4 opacity-70" /> {contact.address}
              </li>
            )}
          </ul>

          {/* Socials */}
          <div className="pt-4 flex flex-wrap gap-2">
            {contact.social_instagram && (
              <a
                href={contact.social_instagram}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Instagram className="w-4 h-4" />
              </a>
            )}
            {contact.social_linkedin && (
              <a
                href={contact.social_linkedin}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Linkedin className="w-4 h-4" />
              </a>
            )}
            {contact.social_youtube && (
              <a
                href={contact.social_youtube}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Youtube className="w-4 h-4" />
              </a>
            )}
            {contact.social_tiktok && (
              <a
                href={contact.social_tiktok}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Video className="w-4 h-4" />
              </a>
            )}
            {contact.social_facebook && (
              <a
                href={contact.social_facebook}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Facebook className="w-4 h-4" />
              </a>
            )}
            {contact.social_twitter && (
              <a
                href={contact.social_twitter}
                target="_blank"
                rel="noreferrer"
                className="p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
              >
                <Twitter className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>

        {/* Column 2: Legal Data */}
        <div id="legal" className="space-y-4 relative group">
          <div className="flex justify-between items-center border-b border-white/20 pb-2 mb-4">
            <h4 className="font-bold text-lg">Datos Legales</h4>
            <Button
              size="icon"
              variant="ghost"
              onClick={onEditLegal}
              className="h-6 w-6 text-white/50 hover:text-white hover:bg-white/10"
              title="Editar Legales"
            >
              <Edit2 className="h-3 w-3" />
            </Button>
          </div>

          <ul className="space-y-3 text-sm opacity-90">
            {identity.legal_name ? (
              <li className="flex flex-col gap-0.5">
                <span className="text-xs opacity-50 uppercase tracking-wider">Razón Social</span>
                <span className="font-medium">{identity.legal_name}</span>
              </li>
            ) : (
              <li className="italic opacity-50">Razón social pendiente</li>
            )}

            {identity.tax_id && (
              <li className="flex flex-col gap-0.5">
                <span className="text-xs opacity-50 uppercase tracking-wider">ID Fiscal</span>
                <span>{identity.tax_id}</span>
              </li>
            )}

            {identity.fiscal_address && (
              <li className="flex flex-col gap-0.5">
                <span className="text-xs opacity-50 uppercase tracking-wider">
                  Dirección Fiscal
                </span>
                <span>{identity.fiscal_address}</span>
              </li>
            )}

            {(identity.terms_url || identity.privacy_url) && (
              <li className="pt-2 flex gap-4 text-xs underline opacity-70">
                {identity.terms_url && (
                  <a href={identity.terms_url} target="_blank">
                    Términos
                  </a>
                )}
                {identity.privacy_url && (
                  <a href={identity.privacy_url} target="_blank">
                    Privacidad
                  </a>
                )}
              </li>
            )}
          </ul>
        </div>

        {/* Column 3: Brand Seal */}
        <div className="hidden md:flex flex-col items-end justify-between opacity-30">
          <Scale className="w-32 h-32 opacity-50" />
          <div className="text-right">
            <p className="text-xs font-mono">
              {identity.founding_year ? `Est. ${identity.founding_year}` : ""}
            </p>
            <p className="text-xs font-mono">{identity.tagline}</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
